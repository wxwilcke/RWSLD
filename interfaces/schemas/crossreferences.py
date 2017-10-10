#!/usr/bin/python3

from re import match

from interfaces.schema import Schema


class SchemaXR(Schema):
    """
    {
     'uri_1': ['datatype_1', 'datatype_2', ...],
     ...
     }"""

    def __init__(self, path):
         super().__init__(path)

    def database_pairs(self):
        pairs = set()

        for database, links in self.schema.items():
            for link in links:
                target = self._decode(link['target'])

                if target is not None and target.group('database') is not "":
                    pairs.add((database, target.group('database')))

        return pairs

    def from_database(self, database):
        if database not in self.schema.keys():
            return None

        schema = self.schema[database]
        for link in schema:
            source = self._decode(link['source'])
            target = self._decode(link['target'])

            if source is None or target is None:
                continue

            yield { 'source': { 'database': source.group('database'),
                                'table': source.group('table'),
                                'property': source.group('property') },
                    'target': { 'database': target.group('database'),
                                'table': target.group('table'),
                                'property': target.group('property') }
                  }

    def _decode(self, rule):
        return match('(?P<database>[a-z]*).(?P<table>[A-Za-z_]*)(?:/)?(?P<property>[A-Za-z]*)?', rule)
