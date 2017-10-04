#!/usr/bin/python3

from json import dump
from logging import getLogger


logger = getLogger(__name__)

def write(json_object, filename):
    """ Write JSON
    """
    logger.info("Writing JSON object to {}".format(filename))
    with open(filename, 'w') as f:
        dump(json_object, f, indent=4, sort_keys=True)
