#!/usr/bin/python3

from logging import getLogger
from statistics import mean, pstdev

from distance import levenshtein

from schema.auxiliarly import attributename_from_table,\
                              classname_from_table,\
                              relationname_from_table


logger = getLogger(__name__)

EXCL_ATTRS = ["TimeStamp"]

def generate(server, datatypes_map, uml=None):
    # selected database
    database = server.server.database

    # retrieve table list
    tables = server.list_tables(database)
    logger.info("Retrieved {} tables".format(len(tables)))

    # omit views and system tables
    if database == 'disk':
        tables = [table['TABLE_NAME'] for table in tables if table['TABLE_TYPE'] == 'BASE TABLE'
                  and (table['TABLE_NAME'].startswith('ktbl_') or
                       table['TABLE_NAME'].startswith('tbl_'))]
    if database == 'ultimo':
        tables = [table['TABLE_NAME'] for table in tables if table['TABLE_TYPE'] == 'BASE TABLE'
                  and not (table['TABLE_NAME'].startswith('_TMP')
                        or table['TABLE_NAME'].startswith('dba#'))]


    logger.info("After filtering: {} tables".format(len(tables)))

    # generate schema
    schema = {}

    # add meta data
    schema['metadata'] = {'database': database}

    # add content
    schema['schema'] = {}
    for table in tables:
        logger.info("Processing table {}".format(table))
        schema['schema'][table] = _table_to_schema(server, tables, table, datatypes_map, uml)

    return schema

def _table_to_schema(server, tables, table, datatypes_map, uml):
    subschema = {}

    subschema['link_table'] = True if table.lower().startswith('ktbl') else False
    subschema['classname'] = classname_from_table(server.server.database, table)
    subschema['subClassOf'] = None
    subschema['include'] = True

    columns = server.list_columns(table)
    primary_key = server.primary_key(table)
    if primary_key is not None:
        subschema['identifier'] = primary_key['COLUMN_NAME']
    elif 'id' in [column['column_name'] for column in columns]:
        subschema['identifier'] = 'id'
    else:
        subschema['identifier'] = None

    if uml is None:
        relations = server.foreign_keys(table)
        attributes = server.list_columns(table, include_keys=False)
    else:
        relations = uml.relations_of(table)
        attributes = uml.attributes_of(table)

    subschema['relations'] = _relations_from_table(server, table, columns, tables, relations, uml)
    subschema['attributes'] = _attributes_from_table(table, columns, datatypes_map, attributes)

    return subschema

def _attributes_from_table(table, columns, datatypes_map, schema_attributes):
    attributes = {}

    valid_entries = [attr['column_name'] for attr in schema_attributes if attr['column_name'] not in EXCL_ATTRS]
    for column in columns:
        entry = column['column_name']
        if entry in valid_entries:
            attributes[entry] = {'property': attributename_from_table(entry),
                                 'subPropertyOf': None,
                                 'datatype': datatypes_map.as_xsd(column['data_type']),
                                 'include': True}

    return attributes

def _relations_from_table(server, table, columns, tables, schema_relations, uml):
    relations = {}

    valid_entries = [rel['column_name'] for rel in schema_relations]
    valid_values = [rel['referenced_table'] for rel in schema_relations]
    for column in columns:
        # if this is likely a link
        entry = column['column_name']
        if entry in valid_entries:
            property_name = relationname_from_table(entry)
            if uml is None:
                referenced_table = valid_values[valid_entries.index(entry)]
                include = True
            else:
                referenced_table, unsure = _guess_table(server, property_name, tables)
                include = True if not unsure else False

            relations[entry] = {'property': property_name,
                                'subPropertyOf': None,
                                'targettable': referenced_table,
                                'targetclassname': classname_from_table(server.server.database, referenced_table),
                                'include': include}

    return relations

def _guess_table(server, name, tables):
    distances = []
    for table in tables:
        classname = classname_from_table(server.server.database, table)
        distances.append((levenshtein(name, classname.lower()), table))

    min_value = min(distances)[0]
    candidates = [k for v,k in distances if v == min_value]
    if len(candidates) > 1:
        return ("?" + "/".join(candidates) + "?", True)

    # question if value is less than 2.5 SDs from mean
    values = [v for v,_ in distances]
    if (mean(values)-min_value)/pstdev(values) < 2.5:
        return ("?" + candidates[0] + "?", True)

    return (candidates[0], False)
