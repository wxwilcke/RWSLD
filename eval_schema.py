#!/usr/bin/python3

import logging
import argparse
from time import time

from data.auxiliarly import is_writable
from data.writers.json import write
from interfaces.schemas.databases import SchemaDB
from ui.inspectors.schema import cli


def run(args, timestamp):
    # load database mapping table
    mapping = SchemaDB(args.database_schema)
    schema = mapping.schema

    # validate output path
    output_path = args.output
    if output_path is None:
        output_path = "./{}_{}".format(schema['metadata']['database'], timestamp)
    if not is_writable(output_path):
        return

    # start evaluation
    cli(schema)

    # write schema
    print("Writing schema to disk...")
    write(schema, output_path)

def print_header():
    header = 'Rijkswaterstaat Linked Data Pilot Project'
    header += '\n\tSchema Evaluator'
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
    parser.add_argument("-m", "--database_schema", help="""Database schema (JSON) used to map to RDF""", default=None)
    parser.add_argument("-o", "--output", help="Output file", default=None)
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
