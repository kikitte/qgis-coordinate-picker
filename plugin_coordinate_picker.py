from os import path

from qgis.PyQt import QtGui, QtWidgets

from .coord_picker import CoordinatePickerTool


class CoordinatePickerGUI:
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
        self.iface.addPluginToMenu('CoordinatePicker', self.toolAction)

    def unload(self):
        self.iface.removeToolBarIcon(self.toolAction)

    def activeTool(self):
        self.mapCanvas.setMapTool(self.tool)
