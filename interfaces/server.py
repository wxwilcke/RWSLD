#!/usr/bin/python3

import logging
from re import match

from pymssql import connect


class SQLServer():
    """ SQL Server Class
    """
    server = None

    def __init__(self, server=None):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initiating SQL Server instance")

        self._import_config(server)
        self.connect()
        self.select_database(self.server.database)

    def query(self, query, as_dict=True):
        self._cursor = self._connection.cursor(as_dict=as_dict)
        self._cursor.execute(query)

        return self._cursor

    def connect(self):
        self._connection = connect(server=self.server.servername,
                                   port=self.server.serverport,
                                   user=self.server.username,
                                   password=self.server.password,
                                   database=self.server.database)
    def disconnect(self):
        self._connection.close()

    def select_database(self, database):
        self.query("USE [{}]".format(database))

    def _import_config(self, config):
        m = match('([a-zA-Z][a-zA-Z0-9@$#_]*):(.*)@(.*):([0-9]*)/([a-zA-Z][a-zA-Z0-9@$#_]*)/([a-zA-Z][a-zA-Z0-9@$#_]*)', config)
        if m is None:
            raise Exception("Server login configuration fault")
        else:
            self.server = self.Config(m.group(3),  # servername
                                      m.group(4),  # serverport
                                      m.group(5),  # database
                                      m.group(6),  # schema
                                      m.group(1),  # username
                                      m.group(2))  # password

    ## Predefined Queries ##

    def list_table_info(self, table):
        q = """SELECT AC.name AS column_name,
                      TY.name AS data_type
                FROM sys.tables T
                INNER JOIN sys.all_columns AC ON T.object_id = AC.object_id
                INNER JOIN sys.types TY ON AC.system_type_id = TY.system_type_id AND AC.user_type_id = TY.user_type_id
                WHERE T.name = '{}'""".format(table)

        return [v for v in self.query(q)]

    def list_tables(self, database=None):
        if database is None:
            database = self.server.database

        q = """SELECT * FROM [{}].INFORMATION_SCHEMA.TABLES""".format(database)

        return [v for v in self.query(q)]

    def list_databases(self):
        q = """SELECT name FROM master.dbo.sysdatabases"""

        return [v for v in self.query(q)]

    def list_columns(self, table, include_keys=True):
        q = """SELECT COLUMN_NAME AS column_name, DATA_TYPE AS data_type
               FROM INFORMATION_SCHEMA.COLUMNS
               WHERE TABLE_NAME = '{}'""".format(table)

        columns = [c for c in self.query(q)]
        if not include_keys:
            pkey = self.primary_key(table)
            skeys = [key['column_name'] for key in self.foreign_keys(table)]

            discard_columns = [column for column in columns]
            for column in discard_columns:
                if column['column_name'] == pkey or column['column_name'] in skeys:
                    columns.remove(column)

        return columns

    def primary_key(self, table):
        q = """SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                WHERE OBJECTPROPERTY(OBJECT_ID(CONSTRAINT_SCHEMA + '.' + QUOTENAME(CONSTRAINT_NAME)), 'IsPrimaryKey') = 1
                AND TABLE_NAME = '{}' AND TABLE_CATALOG = '{}'""".format(table, self.server.database)

        keys = [k for k in self.query(q)]
        if len(keys) == 1:
            return keys[0]
        else:
            return None

    def foreign_keys(self, table):
        q = """SELECT  col1.name AS [column_name],
                       tab2.name AS [referenced_table],
                       col2.name AS [referenced_column]
                FROM sys.foreign_key_columns fkc
                INNER JOIN sys.tables tab1 ON tab1.object_id = fkc.parent_object_id
                INNER JOIN sys.columns col1 ON col1.column_id = parent_column_id AND col1.object_id = tab1.object_id
                INNER JOIN sys.tables tab2 ON tab2.object_id = fkc.referenced_object_id
                INNER JOIN sys.columns col2 ON col2.column_id = referenced_column_id AND col2.object_id = tab2.object_id
                WHERE tab1.name = '{}'""".format(table)

        return [k for k in self.query(q)]

    def inverse_foreign_keys(self, table):
        q = """SELECT CAST(f.name AS varchar(255)) AS key_name
                , CAST(c.name AS varchar(255)) AS foreign_table
                , CAST(fc.name AS varchar(255)) AS foreign_column
                , CAST(p.name AS varchar(255)) AS parent_table
                , CAST(rc.name AS varchar(255)) AS parent_column
                FROM  sysobjects f
                INNER JOIN sysobjects c ON f.parent_obj = c.id
                INNER JOIN sysreferences r ON f.id = r.constid
                INNER JOIN sysobjects p ON r.rkeyid = p.id
                INNER join syscolumns rc ON r.rkeyid = rc.id AND r.rkey1 = rc.colid
                INNER JOIN syscolumns fc ON r.fkeyid = fc.id AND r.fkey1 = fc.colid
                WHERE p.name = '{}' AND f.type = 'F'""".format(table)

        return [k for k in self.query(q)]

    ## Generators ##

    def records(self, table, select='*', where=None):
        q = """SELECT {} FROM {}""".format(select, self.server.absolute(table))

        if where is not None:
            q += " WHERE {}".format(where)

        for rec in self.query(q):
            yield rec

    ## Server Config ##

    class Config:
        servername = None
        serverport = None
        database = None
        schema= None
        username = None
        password = None

        def __init__(self, servername, serverport, database, schema, username, password):
            self.servername = servername
            self.serverport = serverport
            self.database = database
            self.schema = schema
            self.username = username
            self.password = password

        def absolute(self, table):
            return ".".join([self.database, self.schema, table])

if __name__ == "__main__":
    print("SQL Server")
