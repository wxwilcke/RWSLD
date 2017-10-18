#!/usr/bin/python3

from logging import getLogger
from rdflib.term import URIRef, Literal
from rdflib.graph import Graph
from rdflib.namespace import Namespace

from rdf.operators import gen_hash, add_property, add_label, add_type


DEFAULT_NAMESPACE = "http://www.rijkswaterstaat.nl/linked_data/"
DEFAULT_PREFIX = "rws"
DEFAULT_SCHEMA_NAMESPACE = DEFAULT_NAMESPACE + "schema/"
DEFAULT_SCHEMA_PREFIX = DEFAULT_PREFIX + ".schema"

logger = getLogger(__name__)

EXCL_VALUES = [-111*i for i in range(1,10)]
EXCL_VALUES.extend([str(i) for i in EXCL_VALUES])
EXCL_VALUES.extend(['Niet van toepassing', 'Geen informatie'])

def translate(gdb, mapper, area, time):
    """ Translate
    """
    # selected database
    database = mapper.database_name()

    # override variables
    global DEFAULT_NAMESPACE, DEFAULT_PREFIX, DEFAULT_SCHEMA_NAMESPACE, DEFAULT_SCHEMA_PREFIX
    DEFAULT_NAMESPACE = "http://www.rijkswaterstaat.nl/linked_data/{}/".format(database)
    DEFAULT_PREFIX = "rws.{}".format(database)
    DEFAULT_SCHEMA_NAMESPACE = "http://www.rijkswaterstaat.nl/linked_data/schema/{}/".format(database)
    DEFAULT_SCHEMA_PREFIX = "rws.schema.{}".format(database)

    # init graph instance
    g = Graph(identifier=gen_hash(database.upper(), time))

    # update namespaces
    _update_namespaces(g.namespace_manager)

    for layer in mapper.classes():
        _layer_to_graph(g, gdb, layer, area, mapper)

    return g

def _layer_to_class(g, mapping):
    ns = dict(g.namespace_manager.namespaces())

    return URIRef(ns[DEFAULT_SCHEMA_PREFIX] + mapping['classname'])

def _layer_to_graph(g, gdb, layer_name, area, mapper):
    ns = dict(g.namespace_manager.namespaces())
    logger.info("Processing layer {}".format(layer_name))
    mapping = mapper.schema['schema'][layer_name]

    # define class
    class_node = _layer_to_class(g, mapping)

    # translate features
    attributes = list(mapper.attributes(layer_name))

    for feat in gdb.features_of(layer_name):
        if mapping['identifier'] is None:
            continue
        fid = feat.GetFID()
        if fid is None or fid <= 0:
            continue

        # continue if out of scope
        if not gdb.within(gdb.geometry_of(feat), area):
            continue

        # geometry
        geom_wkt, gtype = gdb.geometryWKT_of(feat)
        if geom_wkt is None:
            continue

        # node for this feature
        feat_node = URIRef(ns[DEFAULT_PREFIX] + gen_hash(layer_name+mapping['classname'], fid))
        add_type(g, feat_node, class_node)
        add_label(g, feat_node, "{} {} ({})".format(mapping['classname'], fid, gtype))

        for k,v in feat.items().items():
            if v is None or v in EXCL_VALUES:
                continue
            if k in attributes:
                # create node
                attr = mapping['attributes'][k]
                try:
                    if type(v) is str:
                        v = v.strip()
                    attr_node = Literal(v, datatype=URIRef(attr['datatype']))
                except UnicodeDecodeError:
                    if type(v) is bytes:
                        v = v.decode('utf-8', 'ignore')
                        attr_node = Literal(v, datatype=URIRef(attr['datatype']))

                # link to node
                attr_link = URIRef(ns[DEFAULT_SCHEMA_PREFIX] + "{}_{}".format(mapping['classname'].lower(), attr['property']))
                add_property(g, feat_node, attr_node, attr_link)

        # add geometry node
        geom_node = URIRef(ns[DEFAULT_PREFIX] + gen_hash(geom_wkt, gtype))
        add_type(g, geom_node, URIRef(ns['sf'] + _geo_type(gtype)))
        add_label(g, geom_node, "{} Geometry".format(_geo_type(gtype)))
        add_property(g, feat_node, geom_node, URIRef(ns['geo'] + 'hasGeometry'))

        # include WKT
        geom_wkt_node = Literal(geom_wkt, datatype=URIRef(ns['geo'] + 'wktLiteral'))
        add_property(g, geom_node, geom_wkt_node, URIRef(ns['geo'] + 'asWKT'))

def _geo_type(gtype):
    if gtype == "POINT":
        return gtype.lower().title()
    elif gtype == "MULTILINESTRING":
        return "MultiLineString"
    elif gtype == "MULTIPOLYGON":
        return "MultiPolygon"
    elif gtype == "MULTISURFACE":
        return "MultiSurface"

def _update_namespaces(namespace_manager):
    """ Update Namespaces
    """
    namespace_manager.bind(DEFAULT_PREFIX, Namespace(DEFAULT_NAMESPACE))
    namespace_manager.bind(DEFAULT_SCHEMA_PREFIX, Namespace(DEFAULT_SCHEMA_NAMESPACE))
    namespace_manager.bind("geo", Namespace("http://www.opengis.net/ont/geosparql#"))
    namespace_manager.bind("sf", Namespace("http://www.opengis.net/ont/sf#"))
