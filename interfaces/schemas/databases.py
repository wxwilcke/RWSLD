#!/usr/bin/python3

from interfaces.schema import Schema


class SchemaDB(Schema):
    """
    {
     'table_1': {
         'link_table': 'true or not',
         'class': 'class name of table',
         'subClassOf': 'class name of superclass',
         'attributes': {
             'attr_1':  {
                 'datatype': 'type of attribute',
                 'property': 'name of attribute link'
                 'subPropertyOf': 'intance of rdf:Property'
                        }
                       },
         'relations': {
             'rel_1':  {
                 'property': 'name of relation link',
                 'subPropertyOf': 'instance of rdf:Property',
                 'targetclassname'   : 'table'
                       }
                      }
                    },
    }"""

    def __init__(self, path):
         super().__init__(path)

    def database_name(self):
        return self.schema['metadata']['database']

    def classes(self, link_table=False, include_excluded=False):
        for k in self.schema['schema'].keys():
            if not include_excluded and not self.is_included(k):
                continue
            if not link_table and self.is_link_table(k):
                continue
            yield k

    def is_included(self, table):
        return self.schema['schema'][table]['include']

    def is_link_table(self, table):
        return self.schema['schema'][table]['link_table']

    def subClassOf(self, table):
        return self.schema['schema'][table]['subClassOf']

    def attributes(self, of_class, include_excluded=False):
        if of_class in self.schema['schema'].keys():
            for k in self.schema['schema'][of_class]['attributes']:
                if not include_excluded and\
                   not self.schema['schema'][of_class]['attributes'][k]['include']:
                    continue
                yield k

    def relations(self, of_class, include_excluded=False):
        if of_class in self.schema['schema'].keys():
            for k in self.schema['schema'][of_class]['relations']:
                if not include_excluded and\
                   not self.schema['schema'][of_class]['relations'][k]['include']:
                    continue
                yield k
