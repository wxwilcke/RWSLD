#!/usr/bin/python3

import logging
from ast import literal_eval
from ui.terminal import clear_term
from ui.font import Font


FONT = None
logger = logging.getLogger(__name__)

def cli(schema, excluded_only=True):
    logger.info("Initiating CLI")
    global FONT
    FONT = Font()

    clear_term()
    for table in schema['schema'].keys():
        mapping = schema['schema'][table]
        #if excluded_only and mapping['include']:
        #    continue

        skip = _inspect_table(table, mapping, excluded_only)
        if skip:
            return

def _inspect_table(table, mapping, excluded_only):
    for attr in mapping['attributes'].keys():
        if excluded_only and mapping['attributes'][attr]['include']:
            continue
        skip = _inspect_property(attr, table,  mapping['attributes'][attr])

        if skip:
            return True
    for rel in mapping['relations'].keys():
        if excluded_only and mapping['relations'][rel]['include']:
            continue
        skip = _inspect_property(rel, table, mapping['relations'][rel])

        if skip:
            return True

    return False

def _inspect_property(prop, table, mapping):
    skip = False
    while True:
        clear_term()
        print("{} / {}".format(table, prop))
        print()
        keymap = _print_properties(mapping)
        print()
        answer = _ask_action()

        if answer.startswith("s"):
            skip = True
            break
        if answer.startswith("e"):
            key = _ask_edit_action(mapping, keymap.keys())
            if _guess_data_type(key) == int:
                _edit_property(mapping, keymap[int(key)])
        else:
            break

    return skip

def _edit_property(mapping, keyname):
    value = mapping[keyname]

    addional_options = ""
    is_bool = False
    is_guess = False
    if type(value) == bool:
        addional_options = " / {}".format(FONT.bold_first_char("invert"))
        is_bool = True
    if type(value) == str and value.startswith("?") and value.endswith("?"):
        addional_options = " / {}".format(FONT.bold_first_char("confirm"))
        is_guess = True

    print("[NEW VALUE] ([{}]{}): ".format(FONT.bold_first_char("abort"),
                                          addional_options),
          end="")
    answer = input()

    if answer == "" or answer == "a" or answer == "abort":
        return

    if is_bool:
        if answer == "i" or answer == "invert":
            mapping[keyname] = not value
            return
    if is_guess:
        if answer == "c" or answer == "confirm":
            mapping[keyname] = value[1:-1]
            return

    datatype = _guess_data_type(answer)
    if datatype is not type(value):
        raise TypeError()

    # set new value
    mapping[keyname] = datatype(answer)

def _guess_data_type(input_data):
    try:
        return type(literal_eval(input_data))
    except (ValueError, SyntaxError):
        # A string, so return str
        return str

def _ask_action():
    print("[ACTION] ([{}] / {} / {}): ".format(FONT.bold_first_char("continue"),
                                               FONT.bold_first_char("edit"),
                                               FONT.bold_first_char("skip to end")),
          end="")
    return input()

def _ask_edit_action(mapping, keys):
    numbers = " / ".join([str(i) for i in list(keys)])
    print("[EDIT] ([{}] / {}): ".format(FONT.bold_first_char("abort"),
                                        numbers),
          end="")
    return input()

def _print_properties(mapping):
    keymap = {}

    max_length = 0
    for k,_ in mapping.items():
        if len(k) > max_length:
            max_length = len(k)

    max_length += 4  # include numbering

    i = 0
    for k,v in mapping.items():
        i += 1

        print(" {}) {:<{}}\t{}".format(i,k,max_length+2,v))
        keymap[i] = k

    return keymap

