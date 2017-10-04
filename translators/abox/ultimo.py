#!/usr/bin/python3

from logging import getLogger

from rdf.metadata import add_metadata
from translators.abox.generic import translate as translate_generic
from translators.references.reference_manager import ReferenceManager


DATABASE = "ultimo"
PRIMARY_TABLE = "ProcessFunction"
SECONDARY_TABLES = []

DISK_BASE_PREFIX = "rws.disk"
DISK_SCHEMA_PREFIX = DISK_BASE_PREFIX + ".schema"
DISK_REFERENCE_TYPE = "Beheerobject"
DISK_REFERENCE_ATTR = "beheerobject_archiefcode"

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

    # load disk references if provided
    #scope = _retrieve_external_references(area)
    #logger.info("Found {} root references".format(len(scope)))

    # select relevant subset based on scope
    _retrieve_root_references(references, server, PRIMARY_TABLE, area)
    logger.info("Found {} matching root objects".format(len(set(references.references(table=PRIMARY_TABLE)))))

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

def _retrieve_external_references(graph):
    ns = dict(graph.namespaces())

    logger.info("Searching reference graph for root references...")
    reference_codes = set()
    for r in graph.subjects(predicate=ns['rdf']+"type", object=ns[DISK_SCHEMA_PREFIX]+DISK_REFERENCE_TYPE):
        ref_code = graph.value(subject=r, predicate=ns[DISK_SCHEMA_PREFIX]+DISK_REFERENCE_ATTR)
        if ref_code is not None:
            reference_codes.add(ref_code.toPython())

    return reference_codes

def _retrieve_root_references(references, server, table, area):
    # set condition
    condition = "PrfContext = '32768'"
    condition += """ AND CAST(REPLACE(_PrfRDGeocodeX, ',','.') AS DECIMAL) >= {}
                     AND CAST(REPLACE(_PrfRDGeocodeX, ',','.') AS DECIMAL) <= {}
                     AND CAST(REPLACE(_PrfRDGeocodeY, ',','.') AS DECIMAL) >= {}
                     AND CAST(REPLACE(_PrfRDGeocodeY, ',','.') AS DECIMAL) <= {}""".format(area.minimum.x,
                                                                                           area.maximum.x,
                                                                                           area.minimum.y,
                                                                                           area.maximum.y)
    records = server.records(table, select='prfid AS id, PrfCode AS archiefcode', where=condition)
    references.add_references(table, {rec['id'] for rec in records})

def _retrieve_root_references2(references, server, table, scope):
    # set condition
    condition = "PrfContext = '32768'"
    records = server.records(table, select='prfid AS id, PrfCode AS archiefcode', where=condition)

    if len(scope) > 0:
        references.add_references(table, {rec['id'] for rec in records if rec['archiefcode'] in scope})
    else:
        references.add_references(table, {rec['id'] for rec in records})

def _retrieve_secondary_references(g, references, server, table, visited):
    root_references = set(visited.references(table=PRIMARY_TABLE))
    root_referer = PRIMARY_TABLE[4:] + 'id'

    records = server.records(table, select='id, {}'.format(root_referer))
    references.add_references(table, {rec['id'] for rec in records if rec[root_referer] in root_references})
