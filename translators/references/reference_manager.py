#!/usr/bin/python3

import logging
from copy import deepcopy


class ReferenceManager:
    """ Reference Manager Class
    """

    _references = None

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initiating Reference Manager instance")

        self.clear()

    def add_reference(self, table, record_id):
        if table in self._references.keys():
            self._references[table].add(record_id)
        else:
            self._references[table] = {record_id,}

    def add_references(self, table, record_ids):
        if table in self._references.keys():
            self._references[table].update(record_ids)
        else:
            self._references[table] = record_ids

    def rmv_reference(self, table, record_id, trim=True):
        if table in self._references.keys():
            self._references[table].discard(record_id)

        if trim:
            self.trim()

    def rmv_references(self, table, record_ids, trim=True):
        if table in self._references.keys():
            self._references[table].difference_update(record_ids)

        if trim:
            self.trim()

    def union_update(self, reference_manager):
        if type(reference_manager) is not type(self):
            raise TypeError("Wrong type: {}".format(type(reference_manager)))

        for referenced_table, referenced_records in reference_manager._references.items():
            self.add_references(referenced_table, referenced_records)

    def difference_update(self, reference_manager, trim=True):
        if type(reference_manager) is not type(self):
            raise TypeError("Wrong type: {}".format(type(reference_manager)))

        for referenced_table, referenced_records in reference_manager._references.items():
            self.rmv_references(referenced_table, referenced_records, trim=False)

        if trim:
            self.trim()

    def references(self, table=None, sync=False):
        references_dict = deepcopy(self._references) if sync else self._references

        if table is not None:
            if table not in references_dict.keys():
                raise KeyError("Table not found: {}".format(table))

            for referenced_record in references_dict[table]:
                yield referenced_record
        else:
            for referenced_table, referenced_records in references_dict.items():
                yield (referenced_table, referenced_records)

    def trim(self):
        empty_tables = []
        for referenced_table, referenced_records in self._references.items():
            if len(referenced_records) <= 0:
                empty_tables.append(referenced_table)

        for empty_table in empty_tables:
            del self._references[empty_table]

    def clear(self):
        self._references = {}

    def is_empty(self):
        self.trim()
        if len(self._references) > 0:
            return False

        return True

    def __str__(self):
        string = ""
        for referenced_table, referenced_records in self._references.items():
            string += referenced_table + ": " + ", ".join([str(i) for i in referenced_records]) + "\n"

        return string
