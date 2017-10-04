#!/usr/bin/python3

class PersistentNamespaceManager():
    default_prefix_abox = ""
    default_prefix_tbox = ""

    def __init__(self, namespace_manager):
        self._namespace_manager = namespace_manager
