from collections import namedtuple

from PyQt5.QtWidgets import QToolButton
from qgis.PyQt.QtWidgets import QAction, QApplication
from qgis.core import Qgis, QgsPointXY, QgsCoordinateTransform, QgsCsException, \
    QgsCoordinateReferenceSystem, QgsRasterLayer, QgsRectangle
from qgis.core import (
    QgsProject,
    QgsSettings
)
from qgis.gui import QgisInterface

from .coord_transformer import Transform

epsg4326 = QgsCoordinateReferenceSystem('EPSG:4326')

ZoomClass = namedtuple('ZoomClass', ['icon', 'name'])
RasterCoord = namedtuple('RasterCoord', ['row', 'col', 'index'])


class CoordinateZoom:
    LayerCoord = ZoomClass('icons/zoom_layer.svg', 'Layer Coord')
    ProjectCoord = ZoomClass('icons/zoom_project.svg', 'Project Coord')
    WGS84Coord = ZoomClass('icons/zoom_wgs84.svg', 'WGS84 Coord')
    RasterPixelCord = ZoomClass('icons/zoom_rast_coord.svg', 'RasterPixel Coord')
    RasterPixelIndex = ZoomClass('icons/zoom_rast_idx.svg', 'RasterPixel Index')
    NI_ITE = ZoomClass('icons/zoom_ni_ite.svg', 'NI_ITE Coord')
    NI_ITE_MARS = ZoomClass('icons/zoom_ni_ite_mars.svg', 'NI_ITE_MARS Coord')

    ZoomClasses = [LayerCoord, ProjectCoord, WGS84Coord, RasterPixelCord, RasterPixelIndex, NI_ITE, NI_ITE_MARS]

    def __init__(self, iface):
        self._iface = iface

    @staticmethod
    def parseCoordinateStr(coordStr: str):
        try:
            coordStr = coordStr.strip()
            if coordStr.startswith("("):
                coordStr = coordStr[1:]
                coordStr = coordStr.strip()
            if coordStr.endswith(")"):
                coordStr = coordStr[:-1]
                coordStr = coordStr.strip()
            coords = coordStr.split(",")
            if len(coords) == 1:
                index = int(coords[0].strip())
                return tuple([index])
            elif len(coords) == 2:
                x = float(coords[0].strip())
                y = float(coords[1].strip())
                return x, y
            else:
                return None
        except Exception:
            return None

    def createZoomHandler(self, zoomType: ZoomClass, toolBtn: QToolButton, action: QAction, defaultZoomKey):
        def handler():
            iface = self._iface
            clipboard = QApplication.clipboard()
            if not clipboard.mimeData().hasText():
                iface.messageBar().pushMessage("", "Clipboard is empty", level=Qgis.Warning, duration=3)
                return

            coordStr = unicode(clipboard.text())
            if self.zoom(coordStr, zoomType):
                QgsSettings().setValue(defaultZoomKey, zoomType.name)
                toolBtn.setDefaultAction(action)

        return handler

    def zoom(self, coordStr, zoomType: ZoomClass):
        iface = self._iface

        coords = CoordinateZoom.parseCoordinateStr(coordStr)
        if coords is None:
            iface.messageBar().pushMessage("", "Failed parse coordinate string: {}".format(coordStr),
                                           level=Qgis.Warning, duration=3)
            return

        if zoomType != CoordinateZoom.RasterPixelIndex and len(coords) == 1:
            iface.messageBar().pushMessage("", "Failed parse coordinate string: {}".format(coordStr),
                                           level=Qgis.Warning, duration=3)
            return

        return self._zoomToCoords(coords, zoomType)

    def transformToProjectCoord(self, srcCrs, coord):
        iface: QgisInterface = self._iface
        projectCrs = iface.mapCanvas().mapSettings().destinationCrs()

        if not srcCrs.isValid() or not projectCrs.isValid():
            iface.messageBar().pushMessage("",
                                           "Coordinate transform failed, still zooming as project crs: {}, {}".format(
                                               coord[0], coord[1]), level=Qgis.Warning, duration=3)
            return coord
        transform = QgsCoordinateTransform(srcCrs, projectCrs, QgsProject.instance())
        try:
            pt = transform.transform(coord[0], coord[1])
            return pt.x(), pt.y()
        except QgsCsException:
            iface.messageBar().pushMessage("", "Failed to transform coordinates: {}, {}".format(coord[0], coord[1]),
                                           level=Qgis.Warning, duration=3)
            return None

    def layerCoordToProjectCoord(self, layer, coord):
        iface: QgisInterface = self._iface

        if layer is None:
            iface.messageBar().pushMessage("", "No active layer to zoom to", level=Qgis.Warning, duration=3)
            return None

        return self.transformToProjectCoord(layer.crs(), coord)

    def rasterCoordToLayerCoord(self, layer, rasterCoord):
        iface: QgisInterface = self._iface

        if isinstance(layer, QgsRasterLayer):
            if len(rasterCoord) == 2:
                # raster coord is (row, col)
                row = int(rasterCoord[0])
                col = int(rasterCoord[1])
            elif len(rasterCoord) == 1:
                # raster coord is cell index
                row = int(rasterCoord[0] / layer.width())
                col = int(rasterCoord[0] % layer.width())
            else:
                iface.messageBar().pushMessage("", "Invalid raster coordinate", level=Qgis.Warning, duration=3)
                return None

            if row < 0 or row >= layer.height() or col < 0 or col >= layer.width():
                iface.messageBar().pushMessage("", "Raster coordinates out of bounds, row={}, col={}".format(row, col),
                                               level=Qgis.Warning, duration=3)
                return None

            rasterExtent: QgsRectangle = layer.extent()
            pixelXSize = layer.rasterUnitsPerPixelX()
            pixelYSize = layer.rasterUnitsPerPixelY()

            x = rasterExtent.xMinimum() + col * pixelXSize
            y = rasterExtent.yMaximum() - row * pixelYSize

            x += pixelXSize / 2
            y -= pixelYSize / 2

            return x, y

        else:
            iface.messageBar().pushMessage("", "Layer is not a raster layer", level=Qgis.Warning, duration=3)
            return None

    def _zoomToCoords(self, coord: tuple[float, float], zoomType: ZoomClass):
        iface: QgisInterface = self._iface

        projectCoord = coord

        if zoomType.name == self.LayerCoord.name:
            projectCoord = self.layerCoordToProjectCoord(iface.activeLayer(), coord)
            if not projectCoord:
                return
        elif zoomType.name == self.WGS84Coord.name:
            projectCoord = self.transformToProjectCoord(epsg4326, coord)
            if not projectCoord:
                return
        elif zoomType.name == self.ProjectCoord.name:
            pass
        elif zoomType.name == self.RasterPixelCord.name:
            projectCoord = self.rasterCoordToLayerCoord(iface.activeLayer(), coord)
            if not projectCoord:
                return
        elif zoomType.name == self.RasterPixelIndex.name:
            projectCoord = self.rasterCoordToLayerCoord(iface.activeLayer(), coord)
            if not projectCoord:
                return
        elif zoomType.name == self.NI_ITE.name:
            wgsCoord = Transform.nipoint2lonlat(coord[0], coord[1])
            return self._zoomToCoords(wgsCoord, self.WGS84Coord)
        elif zoomType.name == self.NI_ITE_MARS.name:
            marsCoord = Transform.nipoint2lonlat(coord[0], coord[1])
            wgsCoord = Transform.gcj2wgs(marsCoord[0], marsCoord[1])
            return self._zoomToCoords(wgsCoord, self.WGS84Coord)
        else:
            iface.messageBar().pushMessage("", "Unknown zoom type {}".format(zoomType.name), level=Qgis.Warning,
                                           duration=3)
            return

        canvas = self._iface.mapCanvas()
        canvas.setCenter(QgsPointXY(projectCoord[0], projectCoord[1]))
        canvas.refresh()

        return True
