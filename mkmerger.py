#!/usr/bin/python3

import logging
import argparse
from time import time

from data.auxiliarly import is_readable, is_writable
from data.readers.rdf import multiread
from data.writers.rdf import write
from rdf.metadata import update_metadata
from rdf.namespace_wrapper import default_namespace_of
from ui.progress_indicator import ProgressIndicator

def run(args, timestamp):
    # validate input paths
    if len(args.graphs) < 2:
        raise Exception("Requires at least 2 input graphs")
    _check_paths(args.graphs)
 
    # validate output path
    output_path = args.output
    if output_path is None:
        output_path = "./merge_{}".format(timestamp)
    if not is_writable(output_path):
        return

    print("Merging graphs...")
    pi = ProgressIndicator()
    pi.start()
    graph = multiread(args.graphs)
    update_metadata(graph, default_namespace_of(graph)[0], timestamp)
    pi.stop()

    # write graph
    print("Writing graph to disk...")
    write(graph, output_path, args.serialization_format)

def _check_paths(graphs):
    for graph in graphs:
        if not is_readable(graph):
            raise Exception("File missing or wrong permissions: {}".format(graph))

def print_header():
    header = 'Rijkswaterstaat Linked Data Pilot Project'
    header += "\n\tRDF Graph Combiner"
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
    parser.add_argument("-o", "--output", help="Output file", nargs='?', default=None)
    parser.add_argument("-g", "--graphs", help="Input RDF graphs", nargs='+')
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
