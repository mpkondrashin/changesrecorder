#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os


import sys
import plistlib
from common import log

# move logging and change.txt path here
user_plist_path = '~/Library/LaunchAgents/kondrashin.mikhail.changesrecorder.01.plist'
plist_path = os.path.abspath(os.path.expanduser(user_plist_path))

LAUNCH_SYNC = 'launch_sync.py'
LAUNCH_IMPORT = 'launch_import.py'

def install(args):
    print('Install on Darwin')
    plist_data = dict(
        Label='kondrashin.mikhail.changesrecorder.01',
        Program=os.path.abspath(sys.argv[0]),
        WorkingDirectory=os.path.abspath(os.path.dirname(sys.argv[0])),
        ProgramArguments=[
            os.path.abspath(sys.argv[0]),
            '--config',
            os.path.abspath(args.config),
            'monitor',
        ],
        KeepAlive=True,
        StandardErrorPath='/tmp/changesrecorder.err',
        StandardOutPath='/tmp/changesrecorder.out',
    )
    with open(plist_path, 'wb') as pl:
        plistlib.dump(plist_data, pl)
    print('Run "launchctl load {}"'.format(plist_path))
    os.system('launchctl load {}'.format(plist_path))


def uninstall(args):
    if not os.path.isfile(plist_path):
        print('{}: Not found. Not installed'.format(plist_path))
        return 3
    os.system('launchctl unload {}'.format(plist_path))
    os.remove(plist_path)


def notify(message, sound=False):
    pass


def add_path(file_name):
    # should be same with photosync
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), file_name)


def launch_sync(photo_path):
    launch_terminal_session(
        add_path(LAUNCH_SYNC),
        photo_path
    )


def launch_import(cf_path):
    launch_terminal_session(
        add_path(LAUNCH_IMPORT),
        cf_path
    )


def launch_terminal_session(script, *args):
    osascript = '''
osascript -e 'tell app \"Terminal\"
    do script \"{sync_py} {photo_path}\"
end tell'
    '''.format(
        sync_py=script,
        photo_path=' '.join(args)
    )
    sys.stderr.write("\n{}\n".format(osascript))
    log().debug('RUN: {}'.format(osascript))
    os.system(osascript)


"""
from Foundation import NSUserNotification
from Foundation import NSUserNotificationCenter
from Foundation import NSUserNotificationDefaultSoundName


def notify(message, sound=False):
    notification = NSUserNotification.alloc().init()
    notification.setTitle_("PhotoSync")
    notification.setInformativeText_(message)
    notification.setSubtitle_(u"по-русски")
    notification.setHasActionButton_(True)
    notification.setActionButtonTitle_("Ignore")
    #notification.setReplyButton_(1)
    #notification.setUserInfo_({"action": "open_url", "value": 'url'})
#    notification.setHasActionButton_(True)
#    notification.setActionButtonTitle_("View")
#    notification.setUserInfo_({"action": "open_url", "value": "aaa"})
    if sound:
        notification.setSoundName_(NSUserNotificationDefaultSoundName)
    center = NSUserNotificationCenter.defaultUserNotificationCenter()
    center.deliverNotification_(notification)


if __name__ == '__main__':
    notify("Drive connected - 100 folders to sync")
"""