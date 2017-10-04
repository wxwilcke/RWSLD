#!/usr/bin/python3

import logging
import json

from data.auxiliarly import is_readable


class Schema():
    """
    """
    schema = None

    def __init__(self, path):
         self.logger = logging.getLogger(__name__)

         if is_readable(path):
             self.load_schema(path)

    def load_schema(self, path):
        """ Load Schema
        """
        self.logger.info("Loading Schema")
        with open(path, 'r') as f:
            self.schema = json.load(f)
