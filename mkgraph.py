#!/usr/bin/python3

import logging
import argparse
from time import time

from data.auxiliarly import is_writable
from data.writers.rdf import write
from interfaces.server import SQLServer
from interfaces.schemas.databases import SchemaDB
from geo.area import Area
from translators.abox.disk import translate as translate_disk
from translators.abox.ultimo import translate as translate_ultimo
from translators.abox.edo import translate as translate_edo
from translators.abox.kernGIS import translate as translate_kernGIS
from ui.progress_indicator import ProgressIndicator


def run(args, timestamp):
    # connect to server
    print("Connecting to server...")
    server = SQLServer(args.server)

    # retrieve database selection
    database = server.server.database

    # validate output path
    output_path = args.output
    if output_path is None:
        output_path = "./{}_{}".format(database, timestamp)
    if not is_writable(output_path):
        return

    if args.area is None:
        scope = Area()
    else:
        scope = Area(float(args.area[0]),
                    float(args.area[1]),
                    float(args.area[2]),
                    float(args.area[3]))

    # load database mapping table
    mapping = SchemaDB(args.database_schema)

    # translate database to RDF
    pi = ProgressIndicator()
    print("Translating {}...".format(database.upper()))
    pi.start()
    graph = translate_database(server, database, mapping, scope, timestamp)
    pi.stop()

    # write graph
    print("Writing graph to disk...")
    write(graph, output_path, args.serialization_format)

def translate_database(server, database, mapping, scope, timestamp):
    if database == "disk":
        return translate_disk(server, mapping, scope, timestamp)
    elif database == "ultimo":
        return translate_ultimo(server, mapping, scope, timestamp)
    elif database == "edo":
        return translate_edo(server, mapping, scope, timestamp)
    elif database == "kernGIS":
        return translate_kernGIS(server, mapping, scope, timestamp)
    else:
        raise NotImplementedError("No support for specified database")

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
    parser.add_argument("--area", help="""[DISK] Limit data points to geographic area encoded as RD coordinates (m):
                        '--area <x_min> <y_min> <x_max> <y_max>'""", nargs=4, default=None)
    parser.add_argument("-f", "--serialization_format", help="serialization format of output",
                        choices=["n3", "nquads", "ntriples", "pretty-xml", "trig", "trix", "turtle", "xml"], default='turtle')
    parser.add_argument("-m", "--database_schema", help="""Database schema (JSON) used to map to RDF""", default=None)
    parser.add_argument("-o", "--output", help="Output file", default=None)
    parser.add_argument("-s", "--server", help="""Login configuration of Microsoft SQL server:
                        '--server <user>:<password>@<server[:<port>]></database>'""",\
                        default=None)
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
