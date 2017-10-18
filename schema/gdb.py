#!/usr/bin/python3

from logging import getLogger
from re import fullmatch

from schema.auxiliarly import attributename_from_layer,\
                              classname_from_layer


logger = getLogger(__name__)

DATABASE = "kerngis"
INCL_LAYERS = "[a-z][A-Z][a-z]*"

def generate(gdb, datatypes_map):
    # retrieve layer list
    layers = list(gdb.layers())
    logger.info("Retrieved {} layers".format(len(layers)))

    # omit non-included
    layers = [layer for layer in layers if fullmatch(INCL_LAYERS, layer.GetName())]
    logger.info("After filtering: {} layers".format(len(layers)))

    # generate schema
    schema = {}

    # add meta data
    schema['metadata'] = {'database': DATABASE}

    # add content
    schema['schema'] = {}
    for layer in layers:
        logger.info("Processing layer {}".format(layer.GetName()))
        schema['schema'][layer.GetName()] = _layer_to_schema(layer, datatypes_map)

    return schema

def _layer_to_schema(layer, datatypes_map):
    subschema = {}

    subschema['link_table'] = False
    subschema['classname'] = classname_from_layer(layer.GetName())
    subschema['subClassOf'] = "http://www.opengis.net/ont/geosparql#Feature"
    subschema['include'] = True
    subschema['identifier'] = layer.GetFIDColumn()

    subschema['attributes'] = _attributes_from_layer(layer.schema, datatypes_map)
    subschema['relations'] = {}

    return subschema

def _attributes_from_layer(field_defs, datatypes_map):
    attributes = {}

    for field in field_defs:
        attributes[field.GetName()] = {'property': attributename_from_layer(field.GetName()),
                                       'subPropertyOf': None,
                                       'datatype': datatypes_map.as_xsd(field.GetTypeName()),
                                       'include': True}

    return attributes
