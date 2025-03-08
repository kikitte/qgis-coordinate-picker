def classFactory(iface):
    from .plugin_coordinate_picker import CoordinatePickerGUI
    return CoordinatePickerGUI(iface)
