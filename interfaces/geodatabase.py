#!/usr/bin/python3

import logging

from data.auxiliarly import is_readable
from osgeo import ogr


class GeoDataBase():
    """ GDB Class
    """

    _gdb = None

    def __init__(self, path):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initiating GDB instance")

        ogr.UseExceptions()
        self.load(path)

    def load(self, path):
        driver = ogr.GetDriverByName("OpenFileGDB")

        if not is_readable(path):
            raise Exception("Wrong permissions or file not found: {}".format(path))

        try:
            self._gdb = driver.Open(path, 0)
        except Exception as e:
            print(e)

    def geometry_of(self, feature):
        geom = feature.GetGeometryRef()
        if geom is not None:
            return geom

    def geometryWKT_of(self, feature):
        geom = feature.GetGeometryRef()
        if geom is not None:
            return (geom.ExportToWkt(), geom.GetGeometryName())

    def within(self, geometry, area):
        if geometry is None:
            return False

        if geometry.GetGeometryName() != "POINT":
            geometry = geometry.Centroid()

        if geometry.GetX() >= area.RD_X_MIN and geometry.GetX() <= area.RD_X_MAX and\
           geometry.GetY() >= area.RD_Y_MIN and geometry.GetY() <= area.RD_Y_MAX:
            return True

        return False

    ## generators

    def layers(self):
        for idx in range(self._gdb.GetLayerCount()):
            yield self._gdb.GetLayerByIndex(idx)

    def features_of(self, layer_name):
        # yield dict
        layer = self._gdb.GetLayerByName(layer_name)
        for idx in range(1, layer.GetFeatureCount()+1):
            yield layer.GetFeature(idx)

    def fields_of(self, feature):
        for k,v in feature.items():
            datatype = ogr.GetFieldTypeName(feature.GetFieldType(feature.GetFieldIndex(k)))
            if v is None:
                continue

            yield { 'attribute': k,
                    'value': v,
                    'datatype': datatype }

if __name__ == "__main__":
    print("GeoDataBase Wrapper")
