from qgis.PyQt import QtGui, QtWidgets
from qgis.core import Qgis, QgsRasterLayer, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject, \
    QgsCsException
from qgis.gui import QgsMapToolEmitPoint

from .coord_formatter import CoordFormater as Coordinate
from .coord_transformer import Transform

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
            except QgsCsException:
                pass
        if wgs84Coord is not None:
            self.coordinates.append(Coordinate(Coordinate.WGS84Coord, wgs84Coord.x(), wgs84Coord.y(), activeLayerName))

            ni_point = Transform.lonlat2nipoint(wgs84Coord.x(), wgs84Coord.y())
            self.coordinates.append(Coordinate(Coordinate.NI_ITE, ni_point[0], ni_point[1], activeLayerName))
            mars_coord = Transform.wgs2gcj(wgs84Coord.x(), wgs84Coord.y())
            ni_point_mars = Transform.lonlat2nipoint(mars_coord[0], mars_coord[1])
            self.coordinates.append(
                Coordinate(Coordinate.NI_ITE_MARS, ni_point_mars[0], ni_point_mars[1], activeLayerName))

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

            contextMenu.exec_(QtGui.QCursor().pos())

    def getCoordinateActionTriggeredHandler(self, coordinate):
        iface = self.iface

        def handler():
            clipboard = QtWidgets.QApplication.clipboard()
            clipboard.setText(coordinate.coordinate_str())
            iface.messageBar().pushMessage("", "{} copied to the clipboard".format(coordinate.coordinate_str()),
                                           level=Qgis.Info, duration=1)

        return handler
