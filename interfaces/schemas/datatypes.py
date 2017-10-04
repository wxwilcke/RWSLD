#!/usr/bin/python3

from rdflib import URIRef
from rdflib.namespace import XSD
from interfaces.schema import Schema


class SchemaDT(Schema):
    """
    {
     'uri_1': ['datatype_1', 'datatype_2', ...],
     ...
     }"""

    def __init__(self, path):
         super().__init__(path)

    def as_xsd(self, datatype):
        for xsd_datatype in self.schema:
            if datatype in self.schema[xsd_datatype]:
                return URIRef(xsd_datatype)

        return XSD.anyType
