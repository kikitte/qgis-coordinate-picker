from os import path

from PyQt5.QtWidgets import QMenu, QToolButton
from qgis.PyQt import QtGui, QtWidgets
from qgis.core import QgsSettings

from .coord_picker import CoordinatePicker
from .coordinate_zoom import CoordinateZoom


class CoordinatePickZoomGUI:
    DefaultZoomKey = 'CoordinatePicker/DefaultZoom'

    def __init__(self, iface):
        self.iface = iface
        self.mapCanvas = self.iface.mapCanvas()

        self.pluginMenuName = "Coordinate_PickZoom"

        self.toolbar = self.iface.addToolBar(self.pluginMenuName)
        self.toolbar.setObjectName(self.pluginMenuName)

        self.pickTool = None
        self.actionPick = None

        self.zoomTool = None
        self.zoomActions = {}
        self.zoomToolBtn = None

    def initGui(self):
        self.actionPick = self._createAction('icons/pick.svg', 'pick coordinate', self.enablePickTool, True)
        self.pickTool = CoordinatePicker(self.iface)
        self.pickTool.setAction(self.actionPick)

        self.toolbar.addAction(self.actionPick)
        self.iface.addPluginToMenu(self.pluginMenuName, self.actionPick)

        self.zoomToolBtn = QToolButton()
        self.zoomTool = CoordinateZoom(self.iface)
        for zoomType in CoordinateZoom.ZoomClasses:
            action = self._createAction(zoomType.icon, zoomType.name)
            action.triggered.connect(self.zoomTool.createZoomHandler(zoomType, self.zoomToolBtn, action,
                                                                     CoordinatePickZoomGUI.DefaultZoomKey))
            self.zoomActions[zoomType.name] = action
            self.iface.addPluginToMenu(self.pluginMenuName, action)

        zoomMenu = QMenu(self.iface.mainWindow())
        for name, action in self.zoomActions.items():
            zoomMenu.addAction(action)

        self.zoomToolBtn.setMenu(zoomMenu)
        defaultZoom = QgsSettings().value(CoordinatePickZoomGUI.DefaultZoomKey, CoordinateZoom.WGS84Coord.name)
        self.zoomToolBtn.setDefaultAction(self.zoomActions[defaultZoom])
        self.zoomToolBtn.setPopupMode(QToolButton.MenuButtonPopup)

        self.toolbar.addWidget(self.zoomToolBtn)

    def unload(self):
        # remove the plugin menu item and icon
        self.iface.removePluginMenu(self.pluginMenuName, self.actionPick)
        for name, action in self.zoomActions.items():
            self.iface.removePluginMenu(self.pluginMenuName, action)
            self.iface.removeToolBarIcon(action)

        self.toolbar = None
        self.pickTool = None
        self.actionPick = None
        self.zoomTool = None
        self.zoomActions = {}
        self.zoomToolBtn = None

    def _createAction(self, iconPath, text, callback=None, checkable=False, enabled=True):
        icon = QtGui.QIcon(path.join(path.dirname(__file__), iconPath))
        action = QtWidgets.QAction(icon, text, self.iface.mainWindow())
        action.setCheckable(checkable)
        action.setEnabled(enabled)
        if callback:
            action.triggered.connect(callback)

        return action

    def enablePickTool(self):
        if self.mapCanvas.mapTool() == self.pickTool:
            self.mapCanvas.unsetMapTool(self.pickTool)
        else:
            self.mapCanvas.setMapTool(self.pickTool)
