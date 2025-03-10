class CoordFormater:
    """ A simple coordinate recorder """

    LayerCoord = 1  # coordinate in layer crs
    WGS84Coord = 2  # coordinate in WGS84
    MapCoord = 3  # coordinate in project crs
    RasterPixelCord = 4  # coordinate in raster grid
    RasterPixelIndex = 5  # cell index in raster grid
    NI_ITE = 6
    NI_ITE_MARS = 7

    def __init__(self, coordType, x, y, layerName=None):
        self._type = coordType
        self._x = x
        self._y = y
        self._layerName = layerName

    def coordinate_str(self):
        if self._type == CoordFormater.RasterPixelCord:
            return '{y}, {x}'.format(x=self._x, y=self._y)
        elif self._type == CoordFormater.RasterPixelIndex:
            return '{index}'.format(index=self._x)
        else:
            return '{x}, {y}'.format(x=self._x, y=self._y)

    def __repr__(self):
        layerName = self._layerName if self._layerName is not None else 'Map'
        if self._type == CoordFormater.LayerCoord:
            return 'Layer CRS:\t{name}\t{coordinate_str}'.format(name=layerName, coordinate_str=self.coordinate_str())
        elif self._type == CoordFormater.WGS84Coord:
            return 'WGS84:\t{name}\t{coordinate_str}'.format(name=layerName, coordinate_str=self.coordinate_str())
        elif self._type == CoordFormater.MapCoord:
            return 'Project CRS:\t{name}\t{coordinate_str}'.format(name=layerName, coordinate_str=self.coordinate_str())
        elif self._type == CoordFormater.RasterPixelCord:
            return 'Row, Col:\t{name}\t{coordinate_str}'.format(name=layerName, coordinate_str=self.coordinate_str())
        elif self._type == CoordFormater.RasterPixelIndex:
            return 'Cell Index:\t{name}\t{coordinate_str}'.format(name=layerName, coordinate_str=self.coordinate_str())
        elif self._type == CoordFormater.NI_ITE:
            return 'ITE:\t{name}\t{coordinate_str}'.format(name=layerName, coordinate_str=self.coordinate_str())
        elif self._type == CoordFormater.NI_ITE_MARS:
            return 'ITE_MARS:\t{name}\t{coordinate_str}'.format(name=layerName, coordinate_str=self.coordinate_str())

        return 'unknown coordinate type'
