#!/usr/bin/python3

from logging import getLogger

from rdf.metadata import add_metadata
from translators.abox.generic_sql import translate as translate_generic
from translators.references.reference_manager import ReferenceManager


DATABASE = "disk"
PRIMARY_TABLE = "tbl_beheerobject"
SECONDARY_TABLES = ["ktbl_beheerobject_gevaarlijkestof",
                    "ktbl_beheerobject_inspectievoorziening",
                    "ktbl_beheerobject_toestand",
                    "ktbl_document_beheerobject",
                    "tbl_ciww",
                    "tbl_gis_miok",
                    "tbl_inspectie",
                    "tbl_maatregelhistorie",
                    "tbl_objectdeel"]

logger = getLogger(__name__)

def translate(server, mapper, area, time):
    """ Translate
    """
    # retrieve table list
    tables = server.list_tables(DATABASE)
    logger.info("Retrieved {} tables".format(len(tables)))

    # initiate reference managers
    references = ReferenceManager()
    visited = ReferenceManager()

    # select relevant subset based on geographic area
    _retrieve_root_references(references, server, PRIMARY_TABLE, area)
    logger.info("Found {} root references".format(len(set(references.references(table=PRIMARY_TABLE)))))

    # start with PRIMARY_TABLE
    g = translate_generic(server, mapper, references, visited, time)

    # secondary tables
    for table in SECONDARY_TABLES:
        _retrieve_secondary_references(g, references, server, table, visited)
        references.difference_update(visited)  # remove those we already visited 
        g += translate_generic(server, mapper, references, visited, time)

    # add meta data
    add_metadata(g, "rws.{}".format(DATABASE), time, DATABASE)

    return g

def _retrieve_root_references(references, server, table, area):
    # set condition
    condition = """rdx >= {} AND rdx <= {} AND rdy >= {} AND rdy <= {}""".format(area.minimum.x/1000,
                                                                                 area.maximum.x/1000,
                                                                                 area.minimum.y/1000,
                                                                                 area.maximum.y/1000)
    records = server.records(table, select='id', where=condition)
    references.add_references(table, {rec['id'] for rec in records})

def _retrieve_secondary_references(g, references, server, table, visited):
    root_references = set(visited.references(table=PRIMARY_TABLE))
    root_referer = PRIMARY_TABLE[4:] + 'id'

    records = server.records(table, select='id, {}'.format(root_referer))
    references.add_references(table, {rec['id'] for rec in records if rec[root_referer] in root_references})
