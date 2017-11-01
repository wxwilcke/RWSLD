#!/usr/bin/python3

from re import fullmatch

from interfaces.schema import Schema


class SchemaOTL(Schema):
    """
    {
     'database': [ { 'source', 'target' }, ...],
     ...
     }"""

    def __init__(self, path):
         super().__init__(path)

    def from_database(self, database):
        if database not in self.schema.keys():
            return None

        for key in self.schema[database].keys():
            yield key

    def from_db_table(self, database, table):
        if database not in self.schema.keys():
            return None
        schema = self.schema[database]
        if table not in schema.keys():
            return None

        for entry in schema[table]:
            p = self._decode_property(entry['property'], database, table.lower())
            if p is None:
                continue
            p = p.group('property')

            yield { 'concept': entry['otl_concept'],
                    'property': p,
                    'subtypes': [ { 'name': e['name'],
                                    'referenced_table': self._decode_subtype(e['type_id'], database).group('table'),
                                    'referenced_id' : self._decode_subtype(e['type_id'], database).group('id') }
                                 for e in entry['subtypes'] ]
                  }

    def _decode_property(self, p, database, table):
        m = None
        if database == 'disk':
            m = fullmatch('disk-\d\.\d+-{}-(?P<property>\w*)'.format(table), p)
        if database == 'ultimo':
            m = fullmatch('ultimo-niv\d---{}-(?P<property>\w*)--code-'.format(table), p)

        if m is not None:
            return m

    def _decode_subtype(self, stype, database):
        if database == 'disk':
            m = fullmatch('disk-\d\.\d+-(?P<table>\w*)-(?P<id>\d+)', stype)
        if database == 'ultimo':
            m = fullmatch('ultimo-(?P<table>\w*)-(?P<id>\d+)', stype)

        if m is not None:
            return m
