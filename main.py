#!/Users/michael/PycharmProjects/changesrecorder/venv/bin/python
# -*- coding: utf-8 -*-

"""
ChangesRecorder (c) 2018 by Mikhail Kondrashin
Version 0.1

TODO:
1. Ignore .DS_Store

use: socket.fileobject()

"""
from __future__ import print_function

try:
    import ConfigParser as cp
except ModuleNotFoundError:
    import configparser as cp

import errno
import argparse
import importlib
import logging
import logging.handlers
import os
import socket
import sys
from collections import namedtuple
from contextlib import contextmanager

import drives
import recorder
from common import error
from common import log
import common
from common import platform

DEFAULT_CONFIG_INI = 'changesrecorder.ini' # seek in same folder as main script
#DEFAULT_CONFIG_INI = '/etc/changesrecorder.ini'
#DEFAULT_CONFIG_INI = '~/.changesrecorder.ini'


def parse_args():
#    parser = argparse.ArgumentParser(prog='Changes Recorder')
    parser = argparse.ArgumentParser(prog=os.path.basename(sys.argv[0]))
#    parser.add_argument('-c', '--config', required=True, type=str, help="Configuration file")
    parser.add_argument('-c', '--config', type=str, help="Configuration file", required=True)
    subparsers = parser.add_subparsers(help='Action')

    parser_install = subparsers.add_parser('install', help='install daemon')
    parser_install.set_defaults(action='install')

    parser_uninstall = subparsers.add_parser('uninstall', help='uninstall daemon')
    parser_uninstall.set_defaults(action='uninstall')

    parser_monitor = subparsers.add_parser('monitor', help='Daemon mode. Monitor particular folder')
    parser_monitor.set_defaults(action='monitor')

    parser_save = subparsers.add_parser('save', help='Save to file')
    parser_save.add_argument('file', help='file to record changes')
    parser_save.set_defaults(action='save')

    parser_save = subparsers.add_parser('download', help='Download to file')
    parser_save.add_argument('file', help='file to record changes')
    parser_save.set_defaults(action='download')

    parser_save = subparsers.add_parser('peek', help='Peek for changes (do not reset them)')
    parser_save.add_argument('file', help='file to save changes')
    parser_save.set_defaults(action='peek')

    parser_quit = subparsers.add_parser('quit', help='quit daemon')
    parser_quit.set_defaults(action='quit')

    return parser.parse_args()


def unused_parse_config(args):
    RECORD_CHANGES = 'RECORD_CHANGES'
    MONITOR_FOLDER = 'MONITOR_FOLDER'
    SAVE_PERIOD = 'SAVE_PERIOD'
    LOG_FILE = 'LOG_FILE'
    IGNORE = 'IGNORE'
    VERBOSITY_LEVEL = 'VERBOSITY_LEVEL'
    PORT = 'PORT'

    DEFAULTS = {
        LOG_FILE: '',
        VERBOSITY_LEVEL: '0',
        PORT: '10022',
        SAVE_PERIOD: '900',
        IGNORE: ''
    }

    if os.path.isabs(DEFAULT_CONFIG_INI):
        config_ini = DEFAULT_CONFIG_INI
    elif DEFAULT_CONFIG_INI[0] == '~':
        config_ini = os.path.expanduser(DEFAULT_CONFIG_INI)
    else:
        script_folder = os.path.abspath(os.path.dirname(os.sys.argv[0]))
        config_ini = os.path.join(script_folder, DEFAULT_CONFIG_INI)

    if args.config is not None:
        config_ini = args.config

    if not os.path.isfile(config_ini):
        error(common.ERR_MISSING_CONFIG_INI,
              '{}: Not found'.format(config_ini))

    try:
        __ini = cp.ConfigParser(defaults=DEFAULTS)
        __ini.read(config_ini)
    except cp.Error as e:
        error(common.ERR_CONFIG_INI, "{}".format(e))

    try:
        # Not mandatory
        log_file = __ini.get('DEFAULT', LOG_FILE)
        verbosity_level = int(__ini.get('DEFAULT', VERBOSITY_LEVEL))
        port = int(__ini.get('DEFAULT', PORT))
        ignore_str = __ini.get('DEFAULT', IGNORE)
        ignore = [fname.strip() for fname in ignore_str.split(',')]
        #  Mandatory
        record_changes = __ini.get('DEFAULT', RECORD_CHANGES)
        monitor_folder = __ini.get('DEFAULT', MONITOR_FOLDER)
        save_period = int(__ini.get('DEFAULT', SAVE_PERIOD))
    except cp.NoOptionError as e:
        error(common.ERR_MISSING_OPTION,
              "{}: {}".format(config_ini, e))
    except ValueError as e:
        error(common.ERR_OPTION_VALUE,
              "{}: {}".format(config_ini, e))

    Configuration = namedtuple('Configuration', ['log_file',
                                                 'verbosity_level',
                                                 'record_changes',
                                                 'monitor_folder',
                                                 'ignore',
                                                 'save_period',
                                                 'port'])
    return Configuration(log_file=log_file,
                            verbosity_level=verbosity_level,
                            record_changes=record_changes,
                            monitor_folder=monitor_folder,
                            ignore=ignore,
                            save_period=save_period,
                            port=port)




class Configuration(object):
    RECORD_CHANGES = 'RECORD_CHANGES'
    MONITOR_FOLDER = 'MONITOR_FOLDER'
    SAVE_PERIOD = 'SAVE_PERIOD'
    LOG_FILE = 'LOG_FILE'
    IGNORE = 'IGNORE'
    VERBOSITY_LEVEL = 'VERBOSITY_LEVEL'
    PORT = 'PORT'

    DEFAULTS = {
        LOG_FILE: '',
        VERBOSITY_LEVEL: '0',
        PORT: '10022',
        SAVE_PERIOD: '900',
        IGNORE: ''
    }

    def __init__(self):
        self.ini = cp.ConfigParser(defaults=self.DEFAULTS)
        self.ini.read(self.config_ini())
        # check mandatory variables:
        _ = self.record_changes
        _ = self.monitor_folder

    def config_ini(self):
        if args.config is not None:
            return args.config
        if os.path.isabs(DEFAULT_CONFIG_INI):
            return DEFAULT_CONFIG_INI
        if DEFAULT_CONFIG_INI[0] == '~':
            return os.path.expanduser(DEFAULT_CONFIG_INI)

        script_folder = os.path.abspath(os.path.dirname(sys.argv[0]))
        return os.path.join(script_folder, DEFAULT_CONFIG_INI)

    @property
    def log_file(self):
        return self.ini.get('DEFAULT', self.LOG_FILE)

    @property
    def verbosity_level(self):
        return self.ini.getint('DEFAULT', self.VERBOSITY_LEVEL)

    @property
    def port(self):
        return self.ini.getint('DEFAULT', self.PORT)

    @property
    def ignore(self):
        ignore_str = self.ini.get('DEFAULT', self.IGNORE)
        return [fname.strip() for fname in ignore_str.split(',')]

    @property
    def record_changes(self):
        return self.ini.get('DEFAULT', self.RECORD_CHANGES)

    @property
    def monitor_folder(self):
        return self.ini.get('DEFAULT', self.MONITOR_FOLDER)

    @property
    def save_period(self):
        return self.ini.getint('DEFAULT', self.SAVE_PERIOD)


def parse_config(args):
    try:
        return Configuration()
    except cp.NoOptionError as e:
        error(common.ERR_MISSING_OPTION, "{}".format(e))
    except cp.Error as e:
        error(common.ERR_CONFIG_INI, "{}".format(e))
    except ValueError as e:
        error(common.ERR_OPTION_VALUE, "{}".format(e))


def config_logging(conf):
    formatter = logging.Formatter("%(asctime)s [%(process)d/%(threadName)s] %(levelname)s: %(message)s")
    if conf.log_file != '':
        log_file = os.path.abspath(os.path.expanduser(conf.log_file))
        #        handler = logging.FileHandler(conf.log_file())
        try: #  move this to darwin.py
            os.makedirs(os.path.dirname(log_file))
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
        handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=10)
    else:
        handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    log().addHandler(handler)

    log().setLevel(logging.WARNING)
    if conf.verbosity_level == 1:
        log().setLevel(logging.INFO)
        log().info("LogLevel: info")
    elif conf.verbosity_level == 2:
        log().setLevel(logging.DEBUG)
        log().debug("LogLevel: debug")


def action_monitor(conf):
    config_logging(conf)

    drives.monitor(monitored_folder=conf.monitor_folder,
                   port=conf.port)


    record_changes = os.path.abspath(os.path.expanduser(conf.record_changes.rstrip('/')))
    # this also should go to plafrom specific module:
    try:  # move  this to darwin.py
        os.makedirs(os.path.dirname(record_changes))
    except OSError as e:
        if e.errno != 17:
            raise
    monitor_folder = os.path.abspath(os.path.expanduser(conf.monitor_folder.rstrip('/')))

    #  platform dependent demonization goes here. Nothing for macOS
    rec = recorder.ChangesRecorder(record_changes,
            monitor_folder,
            save_period=conf.save_period,
            port=conf.port,
            ignore=conf.ignore)
    rec.run()
    return 0


def send_command(command, conf, operation):
    sock = socket.socket()
    try:
        sock.connect(('localhost', conf.port))
        sock.send(command.encode('utf-8'))
        return operation(sock)
    except socket.error as e:
        if e.errno == 61:
            print('Can not connect to {}:{}'.format('localhost', conf.port))
        return common.ERR_CANNOT_CONNECT
    finally:
        sock.close()


def action_quit(conf):
#    return send_command('quit', conf, lambda sock: sock.recv(1024))
    return send_command('quit', conf, lambda __: 0)


@contextmanager
def open_dash(file_name):
    if file_name == '-':
        yield sys.stdout
    else:
        with open(file_name, 'w') as f:
            yield f


def receive_to_stream(sock, stream):
    result = list()
    while True:
        data = sock.recv(1024*2)
        if data == b'':
            break
        result.append(data)
    resulting_data = b''.join(result)
    stream.write(resulting_data.decode('utf-8'))
    return len(resulting_data)


def action_download(command, args):
    def operation(sock):
        with open_dash(args.file) as f:
            size = receive_to_stream(sock, f)
#            print('Downloaded {} bytes'.format(size))
    return send_command(command, conf, operation)


if __name__ == "__main__":
    args = parse_args()
    #print(args)
    conf = parse_config(args)
    if args.action == 'monitor':
        sys.exit(action_monitor(conf))
    elif args.action == 'install':
        sys.exit(platform.install(args))
    elif args.action == 'uninstall':
        sys.exit(platform.uninstall(args))
    elif args.action == 'peek':
        sys.exit(action_download('peek', args))
    elif args.action == 'download':
        sys.exit(action_download('download', args))
    elif args.action == 'quit':
        sys.exit(action_quit(conf))
    else:
        error(common.ERR_UNKNOWN_ACTION, 'Unknown action: "{}"'.format(args.action))
