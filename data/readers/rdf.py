#!/usr/bin/python3.5

import logging

from rdflib import Graph
from rdflib.util import guess_format


logger = logging.getLogger(__name__)

def read(local_path=None, remote_path=None, format=None):
    """ Imports a RDF graph from local or remote file.
    """

    if local_path is None and remote_path is None:
        raise ValueError("Path cannot be left undefined")
    logger.info("Importing RDF Graph from file")

    path = local_path if local_path is not None else remote_path
    logger.info("Path set to '{}'".format(path))

    if not format:
        format = guess_format(path)
    logger.info("Format guessed to be '{}'".format(format))

    graph = Graph()
    graph.parse(path, format=format)
    logger.info("RDF Graph ({} facts) succesfully imported".format(len(graph)))

    return graph

if __name__ == "__main__":
    print("RDF import wrapper")
