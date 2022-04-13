#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ChangesRecorder (c) 2018 by Mikhail Kondrashin
Version 0.1
"""
import os
from os.path import join
import threading
import time

from watchdog.events import DirCreatedEvent
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from common import log
from common import platform

VOLUMES = '/Volumes'
ARCHIVE_ROOT = 'photo'
CAMERA_FLASH = 'EOS_DIGITAL'
CAMERA_FLASH_FOLDER = 'DCIM'

class MonitorDrives(FileSystemEventHandler):
    def __init__(self, monitored_folder, port):
        super(MonitorDrives, self).__init__()
        self.archive_folder = os.path.basename(monitored_folder)
        self.monitored_folder = VOLUMES
        self.port = port

    def on_created(self, event):
        log().debug("MonitorDrives:on_created: {}".format(event))
        if not isinstance(event, DirCreatedEvent):
            return
        photo_path = join(event.src_path, ARCHIVE_ROOT)
        if os.path.isdir(photo_path):
            self.photo_attached(photo_path)
            return
        dcim_path = join(event.src_path, CAMERA_FLASH_FOLDER)
        if os.path.basename(event.src_path) == CAMERA_FLASH and \
           os.path.isdir(dcim_path):
            self.eos_attached(dcim_path)
            return
        log().debug("on_created: SKIP {}".format(event.src_path))

    def photo_attached(self, photo_path):
        log().debug('launch sync with {}'.format(photo_path))
        #platform.notify('Please run sync {}'.format(photo_path))
        #log().debug('notify')
        platform.launch_sync(photo_path)
        #log().debug('after lauch_sync')

    def eos_attached(self, dcim_path):
        # platform.launch_import ?
        log().debug('launch import from {}'.format(dcim_path))
        #platform.notify('import? {}'.format(dcim_path))
        platform.launch_import(dcim_path)

    def create_observer(self):
        observer = Observer()
        observer.schedule(self, '/Volumes', recursive=False)
        observer.start()
#        log().info('Monitoring started')
        return observer

    def run(self):
        observer = self.create_observer()
        try:
            while 1:
                time.sleep(3)
        finally:
            observer.stop()
            observer.join()


def monitor(monitored_folder, port):
    m = MonitorDrives(monitored_folder, port)
    monitor_thread = threading.Thread(target=m.run, name='MonitorDrives', daemon=True)
    monitor_thread.start()
