#!/usr/bin/python3

from os.path import splitext
from logging import getLogger


logger = getLogger(__name__)

def write(graph, filename, sformat='turtle'):
    """ Write RDF graph
    """
    if splitext(filename)[1] == '':
        filename += get_ext(sformat)

    logger.info("Writing RDF graph ({}, {} triples) to {}".format(sformat, len(graph), filename))
    graph.serialize(destination=filename, format=sformat)

def get_ext(sformat):
    if sformat == 'n3':
        return '.n3'
    elif sformat == 'nquads':
        return '.nq'
    elif sformat == 'ntriples':
        return '.nt'
    elif sformat == 'pretty-xml':
        return '.xml'
    elif sformat == 'trig':
        return '.trig'
    elif sformat == 'trix':
        return '.trix'
    elif sformat == 'turtle':
        return '.ttl'
    elif sformat == 'xml':
        return '.xml'
    else:
        return '.rdf'
