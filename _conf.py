#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys
import argparse
import ConfigParser


RECORD_CHANGES = 'RECORD_CHANGES'
MONITOR_FOLDER = 'MONITOR_FOLDER'
SAVE_PERIOD = 'SAVE_PERIOD'
LOG_FILE = 'LOG_FILE'
VERBOSITY_LEVEL = 'VERBOSITY_LEVEL'
COMMAND_PATH = 'COMMAND_PATH'

DEFAULTS = {
    LOG_FILE: None,
    VERBOSITY_LEVEL: '0',
    COMMAND_PATH: '/command/command.txt'
}
parser = argparse.ArgumentParser(description='Photo Sync Scope')
parser.add_argument('-c', '--config', required=True, type=str, help="Configuration file")
#parser.add_argument('action', choices=['save', 'hash', 'check'], help='Action')
args = parser.parse_args()
if not os.path.isfile(args.config):
    print('Can not load {}'.format(args.config))
    sys.exit(1)

__ini = ConfigParser.SafeConfigParser()
__ini.read(args.config)

log_file = DEFAULTS[LOG_FILE]
verbosity_level = DEFAULTS[VERBOSITY_LEVEL]
command_path = DEFAULTS[COMMAND_PATH]

# Not mandatory
try: log_file = __ini.get('DEFAULT', LOG_FILE)
except ConfigParser.NoOptionError: pass

try: verbosity_level = int(__ini.get('DEFAULT', VERBOSITY_LEVEL))
except ConfigParser.NoOptionError: pass

try: command_path = __ini.get('DEFAULT', COMMAND_PATH)
except ConfigParser.NoOptionError: pass

#  Mandatory
record_changes =  __ini.get('DEFAULT', RECORD_CHANGES)
monitor_folder =  __ini.get('DEFAULT', MONITOR_FOLDER)
save_period =     __ini.get('DEFAULT', SAVE_PERIOD)

if __name__ == "__main__":
    print('log_file = {}'.format(log_file))
    print('verbosity_level = {}'.format(verbosity_level))
    print('command_path = {}'.format(command_path))
    print('record_changes = {}'.format(record_changes))
    print('monitor_folder = {}'.format(monitor_folder))
    print('save_period = {}'.format(save_period))




