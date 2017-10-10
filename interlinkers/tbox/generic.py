#!/usr/bin/python3

from logging import getLogger
from rdflib import Graph, URIRef
from rdflib.namespace import Namespace, OWL

from rdf.metadata import add_metadata
from rdf.namespace_wrapper import default_namespace_of
from rdf.operators import gen_hash,\
                        add_label,\
                        add_type,\
                        add_domain,\
                        add_range
from schema.auxiliarly import classname_from_table,\
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
    g = Graph(identifier=gen_hash("xref.schema", time))

    # add links
    _interlink(g, schema, source_database, target_database, source_graph, target_graph)

    # add meta-data
    add_metadata(g, DEFAULT_SCHEMA_PREFIX, time, "EXTRA", is_ontology=True)

    return g

def _interlink(g, schema, source_database, target_database, source_graph, target_graph):
    ns_tbox_source = default_namespace_of(source_graph)[0]
    ns_tbox_target = default_namespace_of(target_graph)[0]

    # update namespaces
    _update_namespaces(g.namespace_manager,\
                       ('rws.schema.' + source_database.lower(), ns_tbox_source+"/"),\
                       ('rws.schema.' + target_database.lower(), ns_tbox_target+"/"))

    for relation in schema.from_database(source_database):
        source_def = relation['source']
        target_def = relation['target']

        # define relation
        source_class = classname_from_table(source_database, source_def['table'])
        target_class = classname_from_table(target_database, target_def['table'])
        rel = _property_from_def(source_class, target_class, target_def['property'])

        # forward link
        add_type(g, rel, URIRef(OWL + "ObjectProperty"))
        add_domain(g, rel, URIRef(ns_tbox_source + "/" + source_class))
        add_range(g, rel, URIRef(ns_tbox_target + "/" + target_class))
        add_label(g, rel, "Relatie tussen {} and {}".format(source_class,
                                                            target_class))

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
    namespace_manager.bind('owl', OWL)

    for prefix, namespace in args:
        namespace_manager.bind(prefix, namespace)
