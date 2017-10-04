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
MAX_ITERATIONS = 10

logger = getLogger(__name__)

def translate(server, mapper, references, visited, time):
    """ Translate
    """
    # selected database
    database = mapper.database_name()

    # override variables
    global DEFAULT_NAMESPACE, DEFAULT_PREFIX, DEFAULT_SCHEMA_NAMESPACE, DEFAULT_SCHEMA_PREFIX
    DEFAULT_NAMESPACE = "http://www.rijkswaterstaat.nl/linked_data/{}/".format(database)
    DEFAULT_PREFIX = "rws.{}".format(database)
    DEFAULT_SCHEMA_NAMESPACE = DEFAULT_NAMESPACE + "schema/"
    DEFAULT_SCHEMA_PREFIX = DEFAULT_PREFIX + ".schema"

    # init graph instance
    g = Graph(identifier=gen_hash(database.upper(), time))

    # update namespaces
    _update_namespaces(g.namespace_manager)

    i = 0
    while True:
        for referenced_table, referenced_records in references.references(sync=True):
            if len(referenced_records) <= 0:
                # skip
                continue

            # translate table
            _table_to_graph(g, server, references, referenced_table, mapper)

            # update visited records
            visited.add_references(referenced_table, referenced_records)

        # sync
        references.difference_update(visited)


        i += 1
        if references.is_empty():
            logger.info("No more references")
            break
        if i >= MAX_ITERATIONS:
            logger.info("Maximum number of iterations reached: {}".format(i))
            break

    return g

def _table_to_class(g, mapping):
    ns = dict(g.namespace_manager.namespaces())

    return URIRef(ns[DEFAULT_SCHEMA_PREFIX] + mapping['classname'])

def _table_to_graph(g, server, references, table, mapper):
    ns = dict(g.namespace_manager.namespaces())
    logger.info("Processing table {}".format(table))
    mapping = mapper.schema['schema'][table]

    # define class
    class_node = _table_to_class(g, mapping)

    # translate records
    referenced_nodes = list(references.references(table=table))
    attributes = list(mapper.attributes(table))
    relations = list(mapper.relations(table))

    records = server.records(table)
    for rec in records:
        if mapping['identifier'] is None:
            continue
        if rec[mapping['identifier']] not in referenced_nodes:
            continue

        # node for this record
        rec_node = URIRef(ns[DEFAULT_PREFIX] + gen_hash(mapping['classname'], rec[mapping['identifier']]))
        add_type(g, rec_node, class_node)
        add_label(g, rec_node, "{} {}".format(mapping['classname'], rec[mapping['identifier']]))

        for k,v in rec.items():
            if v is None:
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
                add_property(g, rec_node, attr_node, attr_link)
            if k in relations:
                rel = mapping['relations'][k]

                # create node
                referenced_node = URIRef(ns[DEFAULT_PREFIX] + gen_hash(rel['targetclassname'], v))

                # link to node
                rel_link = URIRef(ns[DEFAULT_SCHEMA_PREFIX] + "{}_{}".format(mapping['classname'].lower(), rel['property']))
                add_property(g, rec_node, referenced_node, rel_link)

                # add back link
                inverse_rel_link = URIRef(ns[DEFAULT_SCHEMA_PREFIX] + "{}_inv_{}".format(rel['targetclassname'].lower(),
                                                                                         mapping['classname'].lower()))
                add_property(g, referenced_node, rec_node, inverse_rel_link)

                # store referenced nodes for further processing
                references.add_reference(rel['targettable'], v)

def _update_namespaces(namespace_manager):
    """ Update Namespaces
    """
    namespace_manager.bind(DEFAULT_PREFIX, Namespace(DEFAULT_NAMESPACE))
    namespace_manager.bind(DEFAULT_SCHEMA_PREFIX, Namespace(DEFAULT_SCHEMA_NAMESPACE))
