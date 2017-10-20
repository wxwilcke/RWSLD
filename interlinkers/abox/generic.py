#!/usr/bin/python3

from logging import getLogger
from re import match

from rdflib import Graph, URIRef
from rdflib.namespace import Namespace
from rdflib.plugins.sparql import prepareQuery

from rdf.metadata import add_metadata
from rdf.namespace_wrapper import default_namespace_of
from rdf.operators import gen_hash,\
                      add_property
from schema.auxiliarly import classname_from_layer,\
                              classname_from_table,\
                              relationname_from_table
from translators.tbox.generic import property_from_mapping

DEFAULT_NAMESPACE = "http://www.rijkswaterstaat.nl/linked_data/xref/"
DEFAULT_PREFIX = "rws.xref"
DEFAULT_SCHEMA_NAMESPACE = "http://www.rijkswaterstaat.nl/linked_data/schema/xref/"
DEFAULT_SCHEMA_PREFIX = "rws.schema.xref"

logger = getLogger(__name__)

def link(schema, source_database, target_database, source_graph, target_graph, time):
    """ Add interlinks
    """
    # init graph instance
    g = Graph(identifier=gen_hash("xref", time))

    # add links
    _interlink(g, schema, source_database, target_database, source_graph, target_graph)

    # add meta-data
    add_metadata(g, DEFAULT_SCHEMA_PREFIX, time, "EXTRA")

    return g

def _interlink(g, schema, source_database, target_database, source_graph, target_graph):
    ns_tbox_source = _generate_tbox_namespace(source_graph)
    ns_tbox_target = _generate_tbox_namespace(target_graph)

    # update namespaces
    ns_abox_source = default_namespace_of(source_graph)[0]
    ns_abox_target = default_namespace_of(target_graph)[0]
    _update_namespaces(g.namespace_manager,\
                       ('rws.' + source_database.lower(), ns_abox_source),\
                       ('rws.' + target_database.lower(), ns_abox_target))

    for relation in schema.from_database(source_database):
        source_def = relation['source']
        target_def = relation['target']

        if target_def['database'] != target_database:
            continue

        # define relation
        source_class = _classname_from_def(source_database, source_def)
        target_class = _classname_from_def(target_database, target_def)
        rel = _property_from_def(source_class, target_class, target_def['property'])

        # select target references
        q = _generate_query(URIRef(ns_tbox_source + source_class),
                            property_from_mapping(ns_tbox_source, source_class, source_def['property']))

        for source_id, target_id in source_graph.query(q):
            if target_id is None or target_id == "":
                continue

            for match_id in target_graph.subjects(predicate=property_from_mapping(ns_tbox_target,\
                                                                               target_class,\
                                                                               target_def['property']),
                                               object=target_id):
                add_property(g, source_id, match_id, rel)

def _generate_tbox_namespace(graph):
    ns_match = match('(?P<base>.*/linked_data/)(?P<database>[a-z]*/)', default_namespace_of(graph)[0])
    if ns_match is None or ns_match.group('database') == "" or ns_match.group('base') == "":
        raise Exception("Unable to determine namespace")

    return Namespace(ns_match.group('base') + "schema/" + ns_match.group('database'))

def _generate_query(source_class_uri, property_uri):
    return prepareQuery("""SELECT DISTINCT ?source_id ?target_id
                           WHERE {{
                                    ?source_id a <{}>  ;
                                       <{}> ?target_id .
                                    }}""".format(source_class_uri, property_uri))

def _classname_from_def(database, definition):
    if definition['model'] == 'sql':
        return classname_from_table(database, definition['table'])
    else:
        return classname_from_layer(definition['table'])

def _property_from_def(source_class, target_class, target_field):
    p = property_from_mapping(DEFAULT_SCHEMA_NAMESPACE, source_class, target_class)
    if target_field != "":
        p += "-{}".format(relationname_from_table(target_field))

    return p

def _update_namespaces(namespace_manager, *args):
    """ Update Namespaces
    """
    namespace_manager.bind(DEFAULT_PREFIX, Namespace(DEFAULT_NAMESPACE))
    namespace_manager.bind(DEFAULT_SCHEMA_PREFIX, Namespace(DEFAULT_SCHEMA_NAMESPACE))

    for prefix, namespace in args:
        namespace_manager.bind(prefix, namespace)
