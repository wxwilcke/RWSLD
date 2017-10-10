#!/usr/bin/python3

from rdflib.namespace import OWL, RDF, VOID


class PersistentNamespaceManager():
    default_prefix_abox = ""
    default_prefix_tbox = ""

    def __init__(self, namespace_manager):
        self._namespace_manager = namespace_manager

def default_namespace_of(graph):
    # try ontology first as it's ussually smaller
    for ctype in [OWL.Ontology, VOID.Dataset]:
        base_gen = list(graph.subjects(predicate=RDF.type, object=ctype))
        if len(base_gen) > 0:
            return (base_gen[0], ctype)
