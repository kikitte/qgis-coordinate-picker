from math import pi
from math import sin, cos, sqrt, fabs, atan2

import numpy as np

# define ellipsoid
a = 6378245.0
f = 1 / 298.3
b = a * (1 - f)
ee = 1 - (b * b) / (a * a)


def outOfChina(lng, lat):
    """check weather lng and lat out of china

    Arguments:
        lng {float} -- longitude
        lat {float} -- latitude

    Returns:
        Bollen -- True or False
    """
    return not (72.004 <= lng <= 137.8347 and 0.8293 <= lat <= 55.8271)


def transformLat(x, y):
    ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * sqrt(fabs(x))
    ret = ret + (20.0 * sin(6.0 * x * pi) + 20.0 * sin(2.0 * x * pi)) * 2.0 / 3.0
    ret = ret + (20.0 * sin(y * pi) + 40.0 * sin(y / 3.0 * pi)) * 2.0 / 3.0
    ret = ret + (160.0 * sin(y / 12.0 * pi) + 320.0 * sin(y * pi / 30.0)) * 2.0 / 3.0
    return ret


def transformLon(x, y):
    ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * sqrt(fabs(x))
    ret = ret + (20.0 * sin(6.0 * x * pi) + 20.0 * sin(2.0 * x * pi)) * 2.0 / 3.0
    ret = ret + (20.0 * sin(x * pi) + 40.0 * sin(x / 3.0 * pi)) * 2.0 / 3.0
    ret = ret + (150.0 * sin(x / 12.0 * pi) + 300.0 * sin(x * pi / 30.0)) * 2.0 / 3.0
    return ret


def wgs2gcj(wgsLon, wgsLat):
    """wgs coord to gcj

    Arguments:
        wgsLon {float} -- lon
        wgsLat {float} -- lat

    Returns:
        tuple -- gcj coords
    """

    if outOfChina(wgsLon, wgsLat):
        return wgsLon, wgsLat
    dLat = transformLat(wgsLon - 105.0, wgsLat - 35.0)
    dLon = transformLon(wgsLon - 105.0, wgsLat - 35.0)
    radLat = wgsLat / 180.0 * pi
    magic = sin(radLat)
    magic = 1 - ee * magic * magic
    sqrtMagic = sqrt(magic)
    dLat = (dLat * 180.0) / ((a * (1 - ee)) / (magic * sqrtMagic) * pi)
    dLon = (dLon * 180.0) / (a / sqrtMagic * cos(radLat) * pi)
    gcjLat = wgsLat + dLat
    gcjLon = wgsLon + dLon
    return gcjLon, gcjLat


def gcj2wgs(gcjLon, gcjLat):
    g0 = (gcjLon, gcjLat)
    w0 = g0
    g1 = wgs2gcj(w0[0], w0[1])
    # w1 = w0 - (g1 - g0)
    w1 = tuple(map(lambda x: x[0] - (x[1] - x[2]), zip(w0, g1, g0)))
    # delta = w1 - w0
    delta = tuple(map(lambda x: x[0] - x[1], zip(w1, w0)))
    while abs(delta[0]) >= 1e-6 or abs(delta[1]) >= 1e-6:
        w0 = w1
        g1 = wgs2gcj(w0[0], w0[1])
        # w1 = w0 - (g1 - g0)
        w1 = tuple(map(lambda x: x[0] - (x[1] - x[2]), zip(w0, g1, g0)))
        # delta = w1 - w0
        delta = tuple(map(lambda x: x[0] - x[1], zip(w1, w0)))
    return w1


def gcj2bd(gcjLon, gcjLat):
    z = sqrt(gcjLon * gcjLon + gcjLat * gcjLat) + 0.00002 * sin(gcjLat * pi * 3000.0 / 180.0)
    theta = atan2(gcjLat, gcjLon) + 0.000003 * cos(gcjLon * pi * 3000.0 / 180.0)
    bdLon = z * cos(theta) + 0.0065
    bdLat = z * sin(theta) + 0.006
    return bdLon, bdLat


def bd2gcj(bdLon, bdLat):
    x = bdLon - 0.0065
    y = bdLat - 0.006
    z = sqrt(x * x + y * y) - 0.00002 * sin(y * pi * 3000.0 / 180.0)
    theta = atan2(y, x) - 0.000003 * cos(x * pi * 3000.0 / 180.0)
    gcjLon = z * cos(theta)
    gcjLat = z * sin(theta)
    return gcjLon, gcjLat


def wgs2bd(wgsLon, wgsLat):
    gcj = wgs2gcj(wgsLon, wgsLat)
    return gcj2bd(gcj[0], gcj[1])


def bd2wgs(bdLon, bdLat):
    gcj = bd2gcj(bdLon, bdLat)
    return gcj2wgs(gcj[0], gcj[1])


def lonlat_to_nipoint(lon, lat):
    # to nds point
    u = 90 / (2 ** 30)
    x_coord = int(lon / u)
    y_coord = int(lat / u)

    x_coord = (np.int64(x_coord) * np.int64(90) * np.int64(100000)) >> 30
    y_coord = (np.int64(y_coord) * np.int64(90) * np.int64(100000)) >> 30

    return x_coord, y_coord


def nipoint_to_lonlat(x, y):
    u = 90 / (2 ** 30)
    x = (np.int64(x) << 30) / (np.int64(90) * np.int64(100000)) * u
    y = (np.int64(y) << 30) / (np.int64(90) * np.int64(100000)) * u

    return x, y


class Transform:
    @staticmethod
    def transformLat(x, y):
        return transformLat(x, y)

    @staticmethod
    def transformLon(x, y):
        return transformLon(x, y)

    @staticmethod
    def wgs2gcj(wgsLon, wgsLat):
        return wgs2gcj(wgsLon, wgsLat)

    @staticmethod
    def gcj2wgs(gcjLon, gcjLat):
        return gcj2wgs(gcjLon, gcjLat)

    @staticmethod
    def gcj2bd(gcjLon, gcjLat):
        return gcj2bd(gcjLon, gcjLat)

    @staticmethod
    def bd2gcj(bdLon, bdLat):
        return bd2gcj(bdLon, bdLat)

    @staticmethod
    def wgs2bd(wgsLon, wgsLat):
        return wgs2bd(wgsLon, wgsLat)

    @staticmethod
    def bd2wgs(bdLon, bdLat):
        return bd2wgs(bdLon, bdLat)

    @staticmethod
    def lonlat2nipoint(lon, lat):
        return lonlat_to_nipoint(lon, lat)

    @staticmethod
    def nipoint2lonlat(x, y):
        return nipoint_to_lonlat(x, y)
