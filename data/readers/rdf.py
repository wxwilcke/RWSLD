#!/usr/bin/python3.5

import logging

from rdflib import Graph
from rdflib.util import guess_format


logger = logging.getLogger(__name__)

def read(path=None, identifier=None, format=None):
    """ Imports a RDF graph from local file.
    """
    graph = Graph(identifier=identifier) if identifier is not None\
            else Graph()

    return _read(graph, path, format)

def multiread(paths=[], identifier=None, format=None):
    graph = Graph(identifier=identifier) if identifier is not None\
            else Graph()

    for path in paths:
        _read(graph, path=path)

    return graph

def _read(graph, path=None, format=None):
    """ Imports a RDF graph from local file.
    """
    if path is None:
        raise ValueError("Path cannot be left undefined")
    logger.info("Importing RDF Graph from file")

    if not format:
        format = guess_format(path)
    logger.info("Format guessed to be '{}'".format(format))

    graph.parse(path, format=format)
    logger.info("RDF Graph ({} facts) succesfully imported".format(len(graph)))

    return graph

if __name__ == "__main__":
    print("RDF import wrapper")
