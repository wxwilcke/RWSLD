#!/usr/bin/python3

from logging import getLogger
from re import match

from rdflib import Graph, URIRef
from rdflib.namespace import Namespace
from rdflib.plugins.sparql import prepareQuery

from rdf.metadata import add_metadata
from rdf.namespace_wrapper import default_namespace_of
from rdf.operators import gen_hash,\
                      add_type
from schema.auxiliarly import classname_from_table,\
                              relationname_from_table

DEFAULT_NAMESPACE = "http://www.rijkswaterstaat.nl/linked_data/otl/"
DEFAULT_PREFIX = "rws.otl"
DEFAULT_SCHEMA_NAMESPACE = "http://www.rijkswaterstaat.nl/linked_data/schema/otl/"
DEFAULT_SCHEMA_PREFIX = "rws.schema.otl"

logger = getLogger(__name__)

def enrich(schema, database, graph, time):
    """ Add OTL enrichments
    """
    # init graph instance
    g = Graph(identifier=gen_hash("OTL", time))

    # enrich
    _enrich(g, database, schema, graph)

    # add meta-data
    add_metadata(g, DEFAULT_SCHEMA_PREFIX, time, "OTL")

    return g

def _enrich(g, database, schema, graph):
    # update namespaces
    ns_otl = Namespace("http://otl.rws.nl/otl#")
    ns_abox = default_namespace_of(graph)[0]
    ns_tbox = _generate_tbox_namespace(graph)
    _update_namespaces(g.namespace_manager,\
                       ('rws.' + database.lower(), ns_abox),
                       ('otl', ns_otl))

    for tablename in schema.from_database(database):
        source_class_name = _classname_from_def(database, tablename)

        # build in-memory map
        otl_map = _generate_otl_map(database, tablename, schema)

        source_class = URIRef(ns_tbox + source_class_name)
        for reference in otl_map.keys():
            source_property = URIRef(ns_tbox + source_class_name.lower() + '_' + reference)
            referenced_class = _classname_from_def(database, otl_map[reference]['referenced_table'])
            referenced_property = URIRef(ns_tbox + referenced_class.lower() + '_id')

            q = _generate_query(source_class, source_property, referenced_property)
            for source_instance, target_id in graph.query(q):
                if target_id.toPython() in otl_map[reference].keys():
                    add_type(g, source_instance, URIRef(ns_otl + otl_map[reference][target_id.toPython()]))

def _generate_query(source_class, source_property, referenced_property):
    query = """SELECT DISTINCT ?source ?target_id
                WHERE {{
                        ?source a <{}> ;
                           <{}> ?target .
                        ?target <{}> ?target_id . }}""".format(source_class,
                                                               source_property,
                                                               referenced_property)
    return prepareQuery(query)

def _generate_otl_map(database, table, schema):
    otl_map = {}
    for mapping in schema.from_db_table(database, table):
        r = relationname_from_table(mapping['property'])
        if r not in otl_map.keys():
            otl_map[r] = {}

        for stype in mapping['subtypes']:
            tid = stype['referenced_id']

            if tid is not None and tid != '':
                otl_map[r][int(tid)] = mapping['concept']

        otl_map[r]['referenced_table'] = stype['referenced_table']

    return otl_map

def _generate_tbox_namespace(graph):
    ns_match = match('(?P<base>.*/linked_data/)(?P<database>[a-z]*/)', default_namespace_of(graph)[0])
    if ns_match is None or ns_match.group('database') == "" or ns_match.group('base') == "":
        raise Exception("Unable to determine namespace")

    return Namespace(ns_match.group('base') + "schema/" + ns_match.group('database'))

def _classname_from_def(database, tablename):
    if database == 'disk':
        tablename_stripped = tablename[8:] if tablename[4] == 't' else tablename[9:]  # iff ktbl
        return classname_from_table(database, tablename_stripped)
    else:  # no ultimo support for now
        return None

def _id_property_from_def(ns_tbox, referenced_class_name):
    return URIRef(ns_tbox + referenced_class_name.lower() + '_id')

def _update_namespaces(namespace_manager, *args):
    """ Update Namespaces
    """
    namespace_manager.bind(DEFAULT_PREFIX, Namespace(DEFAULT_NAMESPACE))
    namespace_manager.bind(DEFAULT_SCHEMA_PREFIX, Namespace(DEFAULT_SCHEMA_NAMESPACE))

    for prefix, namespace in args:
        namespace_manager.bind(prefix, namespace)
