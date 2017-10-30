#!/usr/bin/python3

from logging import getLogger
from re import match

from rdflib import Graph, URIRef
from rdflib.namespace import Namespace
from rdflib.plugins.sparql import prepareQuery
from rdflib.term import Literal, Variable

from rdf.metadata import add_metadata
from rdf.namespace_wrapper import default_namespace_of
from rdf.operators import gen_hash,\
                      add_type,\
                      add_property
from schema.auxiliarly import classname_from_layer,\
                              classname_from_table,\
                              relationname_from_table
from translators.tbox.generic import property_from_mapping

DEFAULT_NAMESPACE = "http://www.rijkswaterstaat.nl/linked_data/extra/"
DEFAULT_PREFIX = "rws.extra"
DEFAULT_SCHEMA_NAMESPACE = "http://www.rijkswaterstaat.nl/linked_data/schema/extra/"
DEFAULT_SCHEMA_PREFIX = "rws.schema.extra"

logger = getLogger(__name__)

def enrich(schema, database, graph, time):
    """ Add enrichments
    """
    # init graph instance
    g = Graph(identifier=gen_hash("extra", time))

    # enrich
    _enrich(g, database, schema, graph)

    # add meta-data
    add_metadata(g, DEFAULT_SCHEMA_PREFIX, time, "EXTRA")

    return g

def _enrich(g, database, schema, graph):
    ns_tbox = _generate_tbox_namespace(graph)

    # update namespaces
    ns_abox = default_namespace_of(graph)[0]
    _update_namespaces(g.namespace_manager,\
                       ('rws.' + database.lower(), ns_abox),
                       ('geo', Namespace("http://www.opengis.net/ont/geosparql#")))

    for entry in schema.from_database(database):
        source_def = entry['source']
        target_def = entry['target']

        source_class = _classname_from_def(database, source_def[0])

        attributes = [ definition['property'] for definition in source_def ]
        properties = [ property_from_mapping(ns_tbox, source_class, attr)\
                      for attr in attributes ]

        # select target references
        q = _generate_query(URIRef(ns_tbox + source_class),
                            attributes,
                            properties)

        for binding in graph.query(q).bindings:
            source_uri = binding[Variable('source_id')]
            if source_uri is None or source_uri == "":
                continue

            values = { '['+attr+']': binding[Variable(attr)].toPython() for attr in attributes\
                      if Variable(attr) in binding.keys() }

            g += _generate_branch(schema, ns_abox, target_def, source_uri, values)

def _generate_branch(schema, ns_abox, tail, parent, values):
    g = Graph()

    if type(tail['tail']) is str:
        if tail['type'] == "URIRef":
            class_node = URIRef(tail['head'])
            node = URIRef(ns_abox + gen_hash(tail['head'], parent.toPython()))

            add_type(g, node, class_node)
            add_property(g, parent, node, URIRef(tail['property']))
        else:
            node = Literal(schema.compile_value(tail, values), datatype=URIRef(tail['head']))
            add_property(g, parent, node, URIRef(tail['property']))
    else:
        class_node = URIRef(tail['head'])
        node = URIRef(ns_abox + gen_hash(tail['head'], parent.toPython()))

        add_type(g, node, class_node)
        add_property(g, parent, node, URIRef(tail['property']))

        g += _generate_branch(schema, ns_abox, tail['tail'], node, values)

    return g

def _generate_tbox_namespace(graph):
    ns_match = match('(?P<base>.*/linked_data/)(?P<database>[a-z]*/)', default_namespace_of(graph)[0])
    if ns_match is None or ns_match.group('database') == "" or ns_match.group('base') == "":
        raise Exception("Unable to determine namespace")

    return Namespace(ns_match.group('base') + "schema/" + ns_match.group('database'))

def _generate_query(source_class_uri, attributes, properties):
    query = "SELECT DISTINCT ?source_id "
    query += " ".join(["?"+attr for attr in attributes])
    query += " WHERE {{ ?source_id a <{}> ;".format(source_class_uri)

    for i in range(len(attributes)):
        query += " <{}> ?{} ".format(properties[i], attributes[i])
        query += ";" if i < len(attributes) - 1 else "."

    query += "}"

    return prepareQuery(query)

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
