#!/usr/bin/python3

from os import access, F_OK, R_OK, W_OK
from os.path import split
from tarfile import is_tarfile


def is_readable(filename, check_tar=False):
    path = split(filename)[0]
    if not access(path, F_OK):
        raise OSError(":: Path does not exist: {}".format(path))
    elif not access(path, R_OK):
        raise OSError(":: Path not readable by user: {}".format(path))

    if check_tar and not is_tarfile(filename):
        raise OSError(":: Not a tar file: {}".format(filename))

    return True

def is_writable(filename):
    path = split(filename)[0]
    if not access(path, F_OK):
        raise OSError(":: Path does not exist: {}".format(path))
    elif not access(path, W_OK):
        raise OSError(":: Path not writeable by user: {}".format(path))

    return True
