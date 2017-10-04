#!/usr/bin/python3

import logging
import argparse
from time import time

from data.auxiliarly import is_readable, is_writable
from data.readers.rdf import read
from data.writers.rdf import write
from ui.progress_indicator import ProgressIndicator


def run(args, timestamp):
    pi = ProgressIndicator()

    # validate output path
    output_path = args.output
    if output_path is None:
        output_path = "./xref_{}".format(timestamp)
    if not is_writable(output_path):
        return

    print("Importing referenced graphs...")
    pi.start()
    graphs = import_graphs(vars(args.parse_args()), pi)
    pi.stop()

    # generate crossreferences
    print("Generating cross-references...")
    pi.start()
    #graph = translate_database(server, database, mapping, scope, timestamp)
    pi.stop()

    # write graph
    print("Writing graph to disk...")
    write(graph, output_path, args.serialization_format)

def import_graphs(args):
    gfiles = [gf for gf in args.keys() if gf in ['abox-disk',
                                                 'abox-ultimo',
                                                 'abox-edo',
                                                 'abox-kerngis',
                                                 'tbox-disk',
                                                 'tbox-ultimo',
                                                 'tbox-edo',
                                                 'tbox-kerngis']
             and args[gf] is not None]

    for db in ['disk', 'ultimo', 'edo', 'kerngis']:
        if 'abox-{}'.format(db) in gfiles and 'tbox-{}'.format(db) not in gfiles:
            raise Exception("Missing ontology graph for {}".format(db.upper()))
        if not is_readable(args['abox-{}'.format(db)]):
            raise Exception("File missing or wrong permissions: {}".format(args['abox-{}'.format(db)]))
        if not is_readable(args['tbox-{}'.format(db)]):
            raise Exception("File missing or wrong permissions: {}".format(args['tbox-{}'.format(db)]))
    if len(gfiles)/2 < 2:
        raise Exception("Requires at least two graphs")

    return {gf:read(args[gf]) for gf in gfiles}

def print_header():
    header = 'Rijkswaterstaat Linked Data Pilot Project'
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
    parser.add_argument("--abox-disk", help="RDF graph holding DISK data", default=None)
    parser.add_argument("--abox-ultimo", help="RDF graph holding ULTIMO data", default=None)
    parser.add_argument("--abox-edo", help="RDF graph holding EDO data", default=None)
    parser.add_argument("--abox-kerngis", help="RDF graph holding KernGIS data", default=None)
    parser.add_argument("-f", "--serialization_format", help="serialization format of output",
                        choices=["n3", "nquads", "ntriples", "pretty-xml", "trig", "trix", "turtle", "xml"], default='turtle')
    parser.add_argument("-o", "--output", help="Output file", default=None)
    parser.add_argument("--tbox-disk", help="RDF graph holding DISK ontology", default=None)
    parser.add_argument("--tbox-ultimo", help="RDF graph holding ULTIMO ontology", default=None)
    parser.add_argument("--tbox-edo", help="RDF graph holding EDO ontology", default=None)
    parser.add_argument("--tbox-kerngis", help="RDF graph holding KernGIS ontology", default=None)
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
