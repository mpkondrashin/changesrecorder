from __future__ import print_function

import logging
import importlib
import sys

ERR_PLATFORM_NOT_SUPPORTED = 3
ERR_UNKNOWN_ACTION = 4
ERR_MISSING_CONFIG_INI = 5
ERR_CONFIG_INI = 6
ERR_MISSING_OPTION = 7
ERR_OPTION_VALUE = 8
ERR_CANNOT_CONNECT = 9


def error(code, *args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)
    sys.exit(code)


def log():
    return logging.getLogger()

import darwin

try:
    platform = importlib.import_module(sys.platform, package=None)
except ImportError:
    error(ERR_PLATFORM_NOT_SUPPORTED,
          '{}: platform is not supported'.format(sys.platform))
