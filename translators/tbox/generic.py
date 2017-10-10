#!/usr/bin/python3

from logging import getLogger
from rdflib.graph import Graph
from rdflib.term import URIRef
from rdflib.namespace import Namespace, OWL

from rdf.metadata import add_metadata
from rdf.operators import gen_hash,\
                        add_label,\
                        add_comment,\
                        add_type,\
                        add_subClassOf,\
                        add_subPropertyOf,\
                        add_domain,\
                        add_range


DEFAULT_NAMESPACE = "http://www.rijkswaterstaat.nl/linked_data/schema/"
DEFAULT_PREFIX = "rws.schema"

logger = getLogger(__name__)

def translate(database, mapper, time):
    """ Translate
    """

    global DEFAULT_NAMESPACE
    DEFAULT_NAMESPACE += "{}".format(database)
    global DEFAULT_PREFIX
    DEFAULT_PREFIX += ".{}".format(database)

    # init graph instance
    g = Graph(identifier=gen_hash(DEFAULT_PREFIX, time))
    # update namespaces
    _update_namespaces(g.namespace_manager)

    for table in mapper.classes():
        logger.info("Processing table {}".format(table))
        _table_to_class(g, table, mapper)

    # add meta-data
    add_metadata(g, DEFAULT_PREFIX, time, database, is_ontology=True)

    return g

def _table_to_class(g, table, mapper):
    ns = dict(g.namespace_manager.namespaces())
    mapping = mapper.schema['schema'][table]

    class_node = URIRef(ns[DEFAULT_PREFIX] + mapping['classname'])
    add_type(g, class_node, URIRef(ns['owl'] + "Class"))
    add_label(g, class_node, mapping['classname'])

    if mapping['subClassOf'] is not None:
        add_subClassOf(g, class_node, URIRef(mapping['subClassOf']))

    for attr in mapper.attributes(table):
        _attribute_to_graph(g, mapping['classname'], class_node, mapping['attributes'][attr])
    for rel in mapper.relations(table):
        _relation_to_graph(g, mapping['classname'], class_node, mapping['relations'][rel])

def _attribute_to_graph(g, classname, class_node, mapping):
    ns = dict(g.namespace_manager.namespaces())

    attr_node = URIRef(ns[DEFAULT_PREFIX] + "{}_{}".format(classname.lower(), mapping['property']))
    add_type(g, attr_node, URIRef(ns['owl'] + 'DatatypeProperty'))
    add_domain(g, attr_node, class_node)
    add_range(g, attr_node, URIRef(mapping['datatype']))
    add_label(g, attr_node, mapping['property'].title())
    add_comment(g, attr_node, "Attribuut '{}' behorende tot class '{}'".format(mapping['property'],
                                                                        classname))

    # make link a subProperty is exists
    if mapping['subPropertyOf'] is not None:
        add_subPropertyOf(g, attr_node, URIRef(mapping['subPropertyOf']))

def property_from_mapping(namespace, classname, propertyname):
    return URIRef(namespace + "{}_{}".format(classname.lower(), propertyname.lower()))

def _relation_to_graph(g, classname, class_node, mapping):
    ns = dict(g.namespace_manager.namespaces())

    # forward link
    rel_node = property_from_mapping(ns[DEFAULT_PREFIX], classname, mapping['property'])
    add_type(g, rel_node, URIRef(ns['owl'] + 'ObjectProperty'))
    add_domain(g, rel_node, class_node)
    add_range(g, rel_node, URIRef(ns[DEFAULT_PREFIX] + mapping['targetclassname']))
    add_label(g, rel_node, mapping['property'].title())
    add_comment(g, rel_node, "Relatie '{}' tussen classen '{}' en '{}'".format(mapping['property'],
                                                                               classname,
                                                                               mapping['targetclassname']))

    # make link a subProperty is exists
    if mapping['subPropertyOf'] is not None:
        add_subPropertyOf(g, rel_node, URIRef(mapping['subPropertyOf']))

    # backwards link
    inverse_rel_node = URIRef(ns[DEFAULT_PREFIX] + "{}_inv_{}".format(mapping['targetclassname'].lower(),
                                                                      classname.lower()))
    add_type(g, inverse_rel_node, URIRef(ns['owl'] + 'ObjectProperty'))
    add_domain(g, inverse_rel_node, URIRef(ns[DEFAULT_PREFIX] + mapping['targetclassname']))
    add_range(g, inverse_rel_node, class_node)
    add_label(g, inverse_rel_node, classname.title() + " (inverse)")
    add_comment(g, inverse_rel_node, "Relatie '{}' (inverse) tussen classen '{}' en '{}'".format(classname,
                                                                                  mapping['targetclassname'],
                                                                                                 classname))

def _update_namespaces(namespace_manager):
    """ Update Namespaces
    """
    namespace_manager.bind(DEFAULT_PREFIX, Namespace(DEFAULT_NAMESPACE))
    namespace_manager.bind('owl', OWL)
