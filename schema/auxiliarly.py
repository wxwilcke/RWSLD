#!/usr/bin/python3

from logging import getLogger


logger = getLogger(__name__)

def classname_from_table(database, name, delimiter='_'):
    if name.startswith("?") and name.endswith("?"):
        name = name[1:-1]

        if "/" in name:
            names = name.split("/")

            classnames = "?"
            for i in range(len(names)):
                classnames += classname_from_table(database, names[i])
                if i < len(names) - 1:
                    classnames += "/"

            return classnames + "?"

    if name.startswith("_"):
        name = name[1:]

    splitted = name.split(delimiter)
    if splitted[0] == "":
        splitted = splitted[1:]
    if database == 'disk':
        if splitted[0] == "ktbl" or splitted[0] == "tbl":
            splitted = splitted[1:]

    classname = ""
    for w in splitted:
        classname += w[0].upper() + w[1:]

    return classname

def attributename_from_table(name):
    return name.lower()

def relationname_from_table(name):
    name = name.lower()
    if name.endswith("_id"):
        name = name[:-3]
    elif name.endswith("id"):
        name = name[:-2]

    return name
