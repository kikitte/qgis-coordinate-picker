from os import path

from qgis.PyQt import QtGui, QtWidgets
from qgis.core import Qgis, QgsRasterLayer, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject
from qgis.gui import QgsMapToolEmitPoint


class CoordinatePicker:
    def __init__(self, iface):
        self.iface = iface
        self.mapCanvas = self.iface.mapCanvas()
        self.tool = None
        self.toolAction = None

    def initGui(self):
        action_icon = QtGui.QIcon(path.join(path.dirname(__file__), 'icons/pick.svg'))
        self.toolAction = QtWidgets.QAction(action_icon, 'CoordinatePicker', self.iface.mainWindow())
        self.toolAction.setCheckable(True)
        self.toolAction.triggered.connect(self.activeTool)

        self.tool = CoordinatePickerTool(self.iface)
        self.tool.setAction(self.toolAction)

        self.iface.addToolBarIcon(self.toolAction)
        self.iface.addPluginToMenu('CoorinatePicker', self.toolAction)

    def unload(self):
        self.iface.removeToolBarIcon(self.toolAction)

    def activeTool(self):
        self.mapCanvas.setMapTool(self.tool)


epsg4326 = QgsCoordinateReferenceSystem('EPSG:4326')


class CoordinatePickerTool(QgsMapToolEmitPoint):

    def __init__(self, iface):
        self.iface = iface
        self.mapCanvas = self.iface.mapCanvas()
        self.coordinates = None

        super().__init__(self.mapCanvas)

    def canvasReleaseEvent(self, mouseEvent):
        self.updateCoordinates(mouseEvent.originalPixelPoint())
        self.showCoordinates()

    def updateCoordinates(self, screenPoint):
        activeLayer = self.iface.activeLayer()
        activeLayerName = activeLayer.name() if activeLayer is not None else None

        self.coordinates = []

        mapCoord = super().toMapCoordinates(screenPoint)
        self.coordinates.insert(0, Coordinate(Coordinate.MapCoord, mapCoord.x(), mapCoord.y(), activeLayerName))

        wgs84Coord = None
        canvasCRS = self.mapCanvas.mapSettings().destinationCrs()
        if canvasCRS == epsg4326:
            wgs84Coord = mapCoord
        else:
            sourceCRS = activeLayer.crs() if activeLayer else canvasCRS
            transform = QgsCoordinateTransform(sourceCRS, epsg4326, QgsProject.instance())
            try:
                # transformation may throw an error, just ignore it
                wgs84Coord = transform.transform(mapCoord.x(), mapCoord.y())
            except:
                pass
        if wgs84Coord is not None:
            self.coordinates.append(Coordinate(Coordinate.WGS84Coord, wgs84Coord.x(), wgs84Coord.y(), activeLayerName))

        if activeLayer:
            layerCoord = super().toLayerCoordinates(activeLayer, screenPoint)
            self.coordinates.insert(0,
                                    Coordinate(Coordinate.LayerCoord, layerCoord.x(), layerCoord.y(), activeLayerName))

            if isinstance(activeLayer, QgsRasterLayer):
                rasterExtent = activeLayer.extent()
                rasterWidth = activeLayer.width()
                if rasterExtent.contains(layerCoord):
                    rasterPixelX = int((layerCoord.x() - rasterExtent.xMinimum()) / activeLayer.rasterUnitsPerPixelX())
                    rasterPixelY = int((rasterExtent.yMaximum() - layerCoord.y()) / activeLayer.rasterUnitsPerPixelY())
                    self.coordinates.insert(0, Coordinate(Coordinate.RasterPixelCord, rasterPixelX, rasterPixelY,
                                                          activeLayerName))
                    self.coordinates.insert(0, Coordinate(Coordinate.RasterPixelIndex,
                                                          rasterPixelY * rasterWidth + rasterPixelX, None,
                                                          activeLayerName))

    def showCoordinates(self):
        if self.coordinates:
            contextMenu = QtWidgets.QMenu()

            for coord in self.coordinates:
                action = contextMenu.addAction(str(coord))
                action.triggered.connect(self.getCoordinateActionTriggeredHandler(coord))

            contextMenu.exec_(QtGui.QCursor.pos())

    def getCoordinateActionTriggeredHandler(self, coordinate):
        iface = self.iface

        def handler():
            clipboard = QtWidgets.QApplication.clipboard()
            clipboard.setText(coordinate.coordinate_str())
            iface.messageBar().pushMessage("", "{} copied to the clipboard".format(coordinate.coordinate_str()),
                                           level=Qgis.Info, duration=1)

        return handler


class Coordinate:
    """ A simple coordinate recorder """

    LayerCoord = 1  # coordinate in layer crs
    WGS84Coord = 2  # coordinate in WGS84
    MapCoord = 3  # coordinate in project crs
    RasterPixelCord = 4  # coordinate in raster grid
    RasterPixelIndex = 5  # cell index in raster grid

    def __init__(self, type, x, y, layerName=None):
        self.type = type
        self.x = x
        self.y = y
        self.layerName = layerName

    def coordinate_str(self):
        if self.type == Coordinate.RasterPixelCord:
            return '{y}, {x}'.format(x=self.x, y=self.y)
        elif self.type == Coordinate.RasterPixelIndex:
            return '{index}'.format(index=self.x)
        else:
            return '{x}, {y}'.format(x=self.x, y=self.y)

    def __repr__(self):
        layerName = self.layerName if self.layerName is not None else 'Map'
        if self.type == Coordinate.LayerCoord:
            return '{name}(Layer CRS): {coordinate_str}'.format(name=layerName, coordinate_str=self.coordinate_str())
        elif self.type == Coordinate.WGS84Coord:
            return '{name}(WGS84): {coordinate_str}'.format(name=layerName, coordinate_str=self.coordinate_str())
        elif self.type == Coordinate.MapCoord:
            return '{name}(Project CRS): {coordinate_str}'.format(name=layerName, coordinate_str=self.coordinate_str())
        elif self.type == Coordinate.RasterPixelCord:
            return '{name}(Row, Col): {coordinate_str}'.format(name=layerName, coordinate_str=self.coordinate_str())
        elif self.type == Coordinate.RasterPixelIndex:
            return '{name}(Cell Index): {coordinate_str}'.format(name=layerName, coordinate_str=self.coordinate_str())

        return 'unknown coordinate type'
