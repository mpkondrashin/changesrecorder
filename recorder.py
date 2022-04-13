#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ChangesRecorder (c) 2018 by Mikhail Kondrashin
Version 0.1

"""
import os
import socket
import time
import errno

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

import changes
from common import log


def send(conn, data):
    sent = 0
    while sent < len(data):
        sent += conn.send(data[sent:].encode('utf-8'))
    return sent


class Quit(Exception):
    pass


class ChangesRecorder(FileSystemEventHandler):
    def __init__(self, changes_file_name, monitored_folder, port=9090, save_period=15 * 60, ignore = None):
        super(ChangesRecorder, self).__init__()
        self.ignore = ignore
        self.changes_file_name = changes_file_name
        self.monitored_folder = monitored_folder
        self.save_period = save_period
        self.port = port
        self.last_save = None
        log().debug("{}: changes_file_name = {}".format(
            self.__class__.__name__, self.changes_file_name))
        log().debug("{}: monitored_folder = {}".format(
            self.__class__.__name__, self.monitored_folder))
        log().debug("{}: save_period = {}".format(
            self.__class__.__name__, self.save_period))
        log().debug("{}: port = {}".format(
            self.__class__.__name__, self.port))
        log().debug("{}: ignore = {}".format(
            self.__class__.__name__, self.ignore))
        try:
            self.scope = changes.read_from_file(self.changes_file_name)
            log().debug("Paths loaded:\n{}".format(changes.paths(self.scope)))
        except IOError as e:
            if e.errno != 2:
                raise
            self.scope = changes.Scope()
        log().info("Loaded {} paths".format(
            changes.count_paths(self.scope)))

    def on_any_event(self, event):
        if hasattr(event, 'src_path'):
            self.add(event.src_path)
        if hasattr(event, 'dst_path'):
            self.add(event.dst_path)

    def clear_period(self, had_change):
        if self.last_save is None:
            if had_change:
                self.last_save = time.time()
            return False
        if time.time() - self.last_save > self.save_period:
            self.last_save = None
            return True
        return False

    def add(self, path):
        log().debug('Modification {}'.format(path))

        if not os.path.isdir(path):
            if os.path.basename(path) in self.ignore:
                return
            path = os.path.dirname(path)

        had_change = changes.add(self.scope, path)
        if had_change:
            log().info('New path {}'.format(path))
            with open(self.changes_file_name, 'a') as f:
                f.write("\n{}".format(path))
        if self.clear_period(had_change):
            self.save()

        return False

    def save(self):
        changes.write_to_file(self.scope, self.changes_file_name)
        log().debug('Save to {}'.format(self.changes_file_name))

    def create_observer(self):
        observer = Observer()
        observer.schedule(self, self.monitored_folder, recursive=True)
        observer.start()
        log().info('Monitoring started')
        return observer

    def create_server_socket(self):
        sock = socket.socket()
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('127.0.0.1', self.port))
        sock.listen(1)
        log().debug('Listen for commands on 127.0.0.1:{}'.format(self.port))
        return sock

    def action_quit(self, conn):
        log().info("Got quit command. Exiting")
        raise Quit

    def action_peek(self, conn):
        log().info('Got peek command')
        size = send(conn, changes.to_text(self.scope))
        log().info('Sent {} bytes'.format(size))

    def action_download(self, conn):
        log().info('Got download command')
        save_scope, self.scope = self.scope.copy(), changes.Scope()
        open(self.changes_file_name, 'w').close()
        size = send(conn, changes.to_text(save_scope))
        log().info('Sent {} bytes'.format(size))

    def process_commands(self, sock):
        actions = {
            'quit': self.action_quit,
            'peek': self.action_peek,
            'download': self.action_download,
        }
        while True:
            conn, __ = sock.accept()
            log().debug('Connected')
            data = conn.recv(1024).decode('utf-8')
            log().debug("Received: '{}'".format(data))
            try:
                actions[data](conn)
                #actions[data.strip().lower()](conn)
            except KeyError:
                log().error('Wrong command "{}"'.format(data))
            conn.close()

    def run(self):
        observer = self.create_observer()
        try:
            sock = self.create_server_socket()
            self.process_commands(sock)
        except Quit:
            pass
        except KeyboardInterrupt:
            log().info("Keyboard interrupt")
        except socket.error as e:
            if e.errno == errno.EADDRINUSE:
                log().error('Can not bind to 127.0.0.1:{}'.format(self.port))
            else:
                raise
        finally:
            observer.stop()
            observer.join()
