#!/usr/bin/python3

import logging
import argparse
from time import time

from data.auxiliarly import is_writable, is_readable
from data.writers.json import write
from interfaces.geodatabase import GeoDataBase
from interfaces.server import SQLServer
from interfaces.schemas.datatypes import SchemaDT
from interfaces.uml import UML
from schema.mssql import generate as generate_mssql
from schema.gdb import generate as generate_gdb
from ui.inspectors.schema import cli
from ui.progress_indicator import ProgressIndicator


DATATYPE_SCHEMA_PATH = "../schema/datatypes.json"

def run(args, timestamp):
    pi = ProgressIndicator()

    # load data types mapping table
    datatypes_map_file = args.datatype_schema
    if not is_readable(datatypes_map_file):
        return
    datatypes_map = SchemaDT(datatypes_map_file)

    # load UML if supported
    uml = None
    uml_filename = args.uml
    if uml_filename is not None and is_readable(uml_filename):
        uml = UML()
        uml.parse(uml_filename)

    print("Generating schema...")
    pi.start()

    # determine database
    database = ""
    schema = None
    if args.gdb is not None:
        schema, database = _run_gdb(args, datatypes_map)
    else:
        schema, database = _run_sql(args, datatypes_map, uml)

    pi.stop()


    # validate output path
    output_path = args.output
    if output_path is None:
        output_path = "./{}_{}.json".format(database, timestamp)
    if not is_writable(output_path):
        return

    # inspect resulting schema
    if args.interactive:
        cli(schema)

    # write schema
    print("Writing schema to disk...")
    write(schema, output_path)

def _run_gdb(args, datatypes_map):
    if not is_readable(args.gdb):
        return {}
    gdb = GeoDataBase(args.gdb)

    return (generate_gdb(gdb, datatypes_map), 'kerngis')

def _run_sql(args, datatypes_map, uml):
    # connect to server
    print("Connecting to server...")
    server = SQLServer(args.server)
    database = server.server.database

    # generate schema
    schema = generate_mssql(server, datatypes_map, uml)

    # close connection
    server.disconnect()

    return (schema, database)

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
    parser.add_argument("--gdb", help="GeoDataBase Path", default=None)
    parser.add_argument("--uml", help="Optional UML diagram", default=None)
    args = parser.parse_args()

    set_logging(args, timestamp)
    logger = logging.getLogger(__name__)
    logger.info("Arguments:\n{}".format(
        "\n".join(["\t{}: {}".format(arg, getattr(args, arg)) for arg in vars(args)])))

    print_header()
    run(args, timestamp)

    logging.shutdown()
