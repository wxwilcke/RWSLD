#!/usr/bin/python3

from logging import getLogger

from rdf.metadata import add_metadata
from translators.abox.generic_gdb import translate as translate_gdb


logger = getLogger(__name__)

def translate(gdb, mapper, area, time):
    """ Translate
    """
    # determine database
    database = mapper.database_name()

    g = translate_gdb(gdb, mapper, area, time)

    # add meta data
    add_metadata(g, "rws.{}".format(database), time, database)

    return g
