#!/usr/bin/python3

from logging import getLogger
from hashlib import sha1
from rdflib.namespace import RDF, RDFS
from rdflib.term import Literal


logger = getLogger(__name__)

DEFAULT_LABEL_LANG="nl"

def gen_hash(node, salt='', pre='r'):
    if type(salt) is not str:
        salt = str(salt)

    salt += str(node)

    return pre + sha1(salt.encode()).hexdigest()

def add_property(g, parent, child, relation):
    g.add((parent, relation, child))

def add_type(g, node, node_type):
    add_property(g, node, node_type, RDF.uri + 'type')

def add_domain(g, node, domain_node):
    add_property(g, node, domain_node, RDFS.uri + 'domain')

def add_range(g, node, range_node):
    add_property(g, node, range_node, RDFS.uri + 'range')

def add_subClassOf(g, subclass, superclass):
    add_property(g, subclass, superclass, RDFS.uri + 'subClassOf')

def add_subPropertyOf(g, subprop, superprop):
    add_property(g, subprop, superprop, RDFS.uri + 'subPropertyOf')

def add_comment(graph, node, comment, lang=DEFAULT_LABEL_LANG):
    comment_node = Literal(comment, lang=lang)
    add_property(graph, node, comment_node, RDFS.uri +'comment')

def add_label(graph, node, label, lang=DEFAULT_LABEL_LANG):
    label_node = Literal(label, lang=lang)
    add_property(graph, node, label_node, RDFS.uri +'label')
