#!/usr/bin/python3

from xml.etree import ElementTree


class UML:
    _xml = None
    _relation_hl = None
    uml = None

    def __init__(self, relation_highlight='Cr:255,255,0,255'):
        self._relation_hl = relation_highlight

    def parse(self, filename):
     self._xml = ElementTree.parse(filename)
     self.uml = self._xml.find("./Models/*[@modelType='Package']/ChildModels")

     if self.uml is None:
         raise Exception("Unable to find UML Database node.")

    def relations_of(self, table):
        table_node = self.uml.find("./*[@name='{}']/ChildModels".format(table))
        if table_node is None:
            return []

        relation_nodes = self._xml.findall("./Diagrams/*[@diagramType='ClassDiagram']"
                                           + "/Shapes/*[@name='{}']/".format(table)
                                           + "CompartmentColorModels/*[@background="
                                           + "'{}']".format(self._relation_hl))

        return [{'column_name':node.get('name'), 'referenced_table':None, 'referenced_column':None}
                for node in table_node.getchildren()
                if node.get('id') in [node.get('proxy') for node in relation_nodes]]

    def attributes_of(self, table):
        table_node = self.uml.find("./*[@name='{}']/ChildModels".format(table))
        if table_node is None:
            return []

        relation_nodes = self._xml.findall("./Diagrams/*[@diagramType='ClassDiagram']"
                                           + "/Shapes/*[@name='{}']/".format(table)
                                           + "CompartmentColorModels/*[@background="
                                           + "'{}']".format(self._relation_hl))

        return [{'column_name':node.get('name'), 'data_type':None} for node in table_node.getchildren()
                if node.get('id') not in [node.get('proxy') for node in relation_nodes]]
