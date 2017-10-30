#!/usr/bin/python3

from re import compile, fullmatch

from interfaces.schema import Schema


class SchemaER(Schema):
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

        schema = self.schema[database]
        for link in schema:
            source = [self._decode_source(e) for e in link['source']]
            target = link['target']

            if source is [] or target is None:
                continue

            yield { 'source': [ { 'model': e.group('model'),
                                  'database': e.group('database'),
                                  'table': e.group('table'),
                                  'property': e.group('property') } for e in source ],
                    'target': target
                  }

    def compile_value(self, tail, values):
        if type(tail) is not dict:
            return tail

        regex = compile('(?P<var>\[\w*\])')
        regit = regex.finditer(tail['tail'])

        new_tail=tail['tail']
        for i, match in enumerate(regit):
            if i >= len(values):
                raise Exception("Number of variables and values does not match")

            var_value = values[match.group('var')]
            if i == 0 and tail['head'].rsplit("#")[1] not in ['ID', 'string', 'time', 'wktLiteral']:
                # not a string literal
                new_tail = var_value
            else:
                new_tail = new_tail.replace(match.group('var'), str(var_value))

        return new_tail

    def _decode_source(self, rule):
        return fullmatch('(?P<model>[a-z]*):(?P<database>[a-z]*).(?P<table>[\?]?[A-Za-z_]*)(?:/)?(?P<property>[A-Za-z]*)?', rule)
