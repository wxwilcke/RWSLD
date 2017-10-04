#!/usr/bin/python3

import logging
import argparse
from time import time

from data.auxiliarly import is_writable, is_readable
from data.writers.json import write
from interfaces.server import SQLServer
from interfaces.schemas.datatypes import SchemaDT
from interfaces.uml import UML
from schema.generate import generate
from ui.inspectors.schema import cli
from ui.progress_indicator import ProgressIndicator


DATATYPE_SCHEMA_PATH = "../schema/datatypes.json"

def run(args, timestamp):
    # connect to server
    print("Connecting to server...")
    server = SQLServer(args.server)

    # retrieve database selection
    database = server.server.database

    # validate output path
    output_path = args.output
    if output_path is None:
        output_path = "./{}_{}.json".format(database, timestamp)
    if not is_writable(output_path):
        return

    # load data types mapping table
    datatypes_map_file = args.datatype_schema
    if datatypes_map_file is None:
        datatypes_map_file = DATATYPE_SCHEMA_PATH
    if not is_readable(datatypes_map_file):
        return
    datatypes_map = SchemaDT(datatypes_map_file)

    # load UML if supported
    uml = None
    uml_filename = args.uml
    if uml_filename is not None and is_readable(uml_filename):
        uml = UML()
        uml.parse(uml_filename)

    # generate schema
    pi = ProgressIndicator()
    print("Generating schema for {}...".format(database.upper()))
    pi.start()
    schema = generate(server, datatypes_map, uml)
    pi.stop()

    # close connection
    server.disconnect()

    # inspect resulting schema
    if args.interactive:
        cli(schema)

    # write schema
    print("Writing schema to disk...")
    write(schema, output_path)

def print_header():
    header = 'Rijkswaterstaat Linked Data Pilot Project'
    subheader = '\tDatabase Schema Generator'
    print('=' * len(header))
    print(header)
    print(subheader)
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
    parser.add_argument("-s", "--server", help="""Login configuration of Microsoft SQL server:
                        <user>:<password>@<server[:<port>]></database>""",\
                        default="user:password@http://localhost:1433/master")
    parser.add_argument("-m", "--datatype_schema", help="Mappings from SQL to RDF datatypes", default=None)
    parser.add_argument("-o", "--output", help="Output file", default=None)
    parser.add_argument("-v", "--verbose", help="Increase output verbosity", action="store_true")
    parser.add_argument("--log_directory", help="Where to save the log file", default="../log/")
    parser.add_argument("--interactive", help="Enable interactive mode", default="store_true")
    parser.add_argument("--uml", help="Optional UML diagram", default=None)
    args = parser.parse_args()

    set_logging(args, timestamp)
    logger = logging.getLogger(__name__)
    logger.info("Arguments:\n{}".format(
        "\n".join(["\t{}: {}".format(arg, getattr(args, arg)) for arg in vars(args)])))

    print_header()
    run(args, timestamp)

    logging.shutdown()
