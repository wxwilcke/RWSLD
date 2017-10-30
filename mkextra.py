#!/usr/bin/python3

import logging
import argparse
from re import fullmatch
from time import time

from rdflib.namespace import OWL

from data.auxiliarly import is_readable, is_writable
from data.readers.rdf import read
from data.writers.rdf import write
from enrichers.generic import enrich
from interfaces.schemas.enrichments import SchemaER
from rdf.namespace_wrapper import default_namespace_of
from ui.progress_indicator import ProgressIndicator


def run(args, timestamp):
    pi = ProgressIndicator()

    # load mapping table
    if not is_readable(args.mapping):
        raise Exception("Wrong file permissions: {}".format(args.mapping))
    mapping = SchemaER(args.mapping)

    print("Importing referenced graph...")
    pi.start()
    params = import_graph(args.graph, mapping)
    pi.stop()

    print("Generating enrichments...")
    pi.start()
    graph = enrich(mapping, params['name'], params['graph'], timestamp)
    pi.stop()

    # validate output path
    output_path = args.output
    if output_path is None:
        output_path = "./{}-extra{}_{}".format(params['name'],\
                                               "-schema" if params['type'] is OWL.Ontology else "",\
                                               timestamp)
    if not is_writable(output_path):
        return

    # write graph
    print("Writing graph to disk...")
    write(graph, output_path, args.serialization_format)

def import_graph(filename, schema):
    if not is_readable(filename):
        raise Exception("File missing or wrong permissions: {}".format(filename))

    graph = read(filename)
    namespace, gtype = default_namespace_of(graph)
    database = _determine_database(namespace)

    if database not in schema.schema.keys():
        raise Exception("Database not contained in mapping: {}".format(database))

    return { 'graph': graph,
             'type': gtype,
             'name': database }

def _determine_database(namespace):
    # determine database
    match_string = '.*/linked_data/(?P<schema>schema)?(?:/)?(?P<database>[a-z]*)(?:/)?'
    m = fullmatch(match_string, namespace)

    if m is None:
        raise Exception("Cannot determine database from namespace")

    database = m.group('database')
    if database not in ['disk', 'ultimo', 'edo', 'kerngis']:
        raise Exception("Database unsupported: {}".format(database))

    return database

def print_header():
    header = 'Rijkswaterstaat Linked Data Pilot Project'
    header += "\n\tGraph Enrichment"
    print('=' * len(header))
    print(header)
    print('=' * len(header))

def set_logging(args, timestamp):
    log_path = args.log_directory
    if not is_writable(log_path):
        return

    filename = "{}{}.log".format(log_path, timestamp) if log_path.endswith("/") \
                    else "{}/{}.log".format(log_path, timestamp)

    logging.basicConfig(filename=filename,
                        format='%(asctime)s %(levelname)s: %(message)s',
                        level=logging.INFO)

    if args.verbose:
        logging.getLogger().addHandler(logging.StreamHandler())

if __name__ == "__main__":
    timestamp = int(time())

    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--serialization_format", help="serialization format of output",
                        choices=["n3", "nquads", "ntriples", "pretty-xml", "trig", "trix", "turtle", "xml"], default='turtle')
    parser.add_argument("-m", "--mapping", help="""Mapping table (JSON) used to enrich graph""")
    parser.add_argument("-o", "--output", help="Output file", default=None)
    parser.add_argument("--graph", help="RDF graph")
    parser.add_argument("-v", "--verbose", help="Increase output verbosity", action="store_true")
    parser.add_argument("--log_directory", help="Where to save the log file", default="../log/")
    args = parser.parse_args()

    set_logging(args, timestamp)
    logger = logging.getLogger(__name__)
    logger.info("Arguments:\n{}".format(
        "\n".join(["\t{}: {}".format(arg, getattr(args, arg)) for arg in vars(args)])))

    print_header()
    run(args, timestamp)

    logging.shutdown()
