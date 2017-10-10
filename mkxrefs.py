#!/usr/bin/python3

import logging
import argparse
from time import time

from re import match
from rdflib.namespace import OWL, VOID

from data.auxiliarly import is_readable, is_writable
from data.readers.rdf import read
from data.writers.rdf import write
from interlinkers.abox.generic import link as abox_link
from interlinkers.tbox.generic import link as tbox_link
from interfaces.schemas.crossreferences import SchemaXR
from rdf.namespace_wrapper import default_namespace_of
from ui.progress_indicator import ProgressIndicator


def run(args, timestamp):
    pi = ProgressIndicator()

    # load mapping table
    if not is_readable(args.crossreference_mapping):
        raise Exception("Wrong file permissions: {}".format(args.crossreference_mapping))
    mapping = SchemaXR(args.crossreference_mapping)
    database_pairs = mapping.database_pairs()

    print("Importing referenced graphs...")
    pi.start()
    params = import_graphs(args.source_graph,\
                           args.target_graph,\
                           {db for pair in database_pairs for db in pair})
    pi.stop()

    # generate crossreferences
    print("Generating cross-references...")
    pi.start()
    graph = params['linker'](mapping,\
                             params['source_name'],\
                             params['target_name'],\
                             params['source_graph'],\
                             params['target_graph'],\
                             timestamp)
    pi.stop()

    # validate output path
    output_path = args.output
    if output_path is None:
        output_path = "./xref_{}-{}{}_{}".format(params['source_name'],\
                                                 params['target_name'],\
                                                 "-schema" if params['linker'] is tbox_link else "",\
                                                 timestamp)
    if not is_writable(output_path):
        return

    # write graph
    print("Writing graph to disk...")
    write(graph, output_path, args.serialization_format)

def import_graphs(source, target, schema):
    for filename in [source, target]:
        if not is_readable(filename):
            raise Exception("File missing or wrong permissions: {}".format(filename))

    source_graph = read(source)
    target_graph = read(target)

    source_namespace, source_type = default_namespace_of(source_graph)
    target_namespace, target_type = default_namespace_of(target_graph)

    linker = _determine_type(source_type, target_type)
    databases = _determine_databases(source_namespace, target_namespace)

    for _,v in databases.items():
        if v not in schema:
            raise Exception("Database not contained in mapping: {}".format(v))

    return { 'source_graph': source_graph,
             'target_graph': target_graph,
             'source_name': databases['source'],
             'target_name': databases['target'],
             'linker': linker }

def _determine_type(source_type, target_type):
    linker = None
    if source_type != target_type:
        raise Exception("Graphs are of different type")
    if source_type == OWL.Ontology:
        linker = tbox_link
    elif source_type == VOID.Dataset:
        linker = abox_link
    else:
        raise Exception("Graphs are of unsupported type")

    return linker

def _determine_databases(source_namespace, target_namespace):
    # determine database
    match_string = '.*/linked_data/(?P<schema>schema)?(?:/)?(?P<database>[a-z]*)(?:/)?'
    source_match = match(match_string, source_namespace)
    target_match = match(match_string, target_namespace)

    if source_match is None or target_match is None:
        raise Exception("Cannot determine database from namespace")

    source_database = source_match.group('database')
    target_database = target_match.group('database')
    if source_database == target_database:
        raise Exception("Graphs are of same database")
    for database in [source_database, target_database]:
        if database not in ['disk', 'ultimo', 'edo', 'kerngis']:
            raise Exception("Database unsupported: {}".format(database))

    return {'source': source_database, 'target': target_database}

def print_header():
    header = 'Rijkswaterstaat Linked Data Pilot Project'
    header += "\n\tCross-Reference Generator"
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
    parser.add_argument("-m", "--crossreference_mapping", help="""Mapping table (JSON) used to link graphs""")
    parser.add_argument("-o", "--output", help="Output file", default=None)
    parser.add_argument("--source_graph", help="Source RDF graph")
    parser.add_argument("--target_graph", help="Target RDF graph")
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
