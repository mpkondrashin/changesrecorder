#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import sys
import inspect
import importlib
import shutil
from subprocess import Popen, PIPE
import fnmatch
import time

#test_cases_list = []

ok = lambda flag: "Ok" if flag else "Fail"


def grep(file_name, pattern):
#    print('grep({},{})'.format(file_name, pattern))
    try:
        with open(file_name) as f:
            for line in f.readlines():
                if fnmatch.fnmatch(line, pattern):
                    return True
    except IOError:
        pass
    return False


def timeout_grep(file_name, pattern, timeout):
    start_time = time.time()
    while not grep(file_name, pattern):
#        print('{} not found - sleep'.format(pattern))
        time.sleep(1)
        if time.time() - start_time > timeout:
            try:
                print('======= BEGIN {} ======='.format(file_name))
                print(open(file_name).read())
                print('========= END {} ======='.format(file_name))
            except IOError as e:
                if e.errno != 2:
                    raise
                print(e.strerror)
            print("Wait for '{}' in '{}' timeout".format(pattern, file_name))
            return False
    return True

SCRIPT = '../../main.py'
CONF = ['-c', 'changesrecorder.ini']
def cr_monitor():
    command = [SCRIPT] + CONF + ['monitor']
#    print(' '.join(command))
    Popen(command)
    timeout_grep('changesrecorder.log', '*Monitoring started*', 3)



def cr_quit(p):
    command = [SCRIPT] + CONF + ['quit']
    Popen(command)
    timeout_grep('changesrecorder.log', '*Got quit command*', 3)


def cr_save(file_name):
    command = [SCRIPT] + CONF + ['save', file_name]
    Popen(command)
    timeout_grep('changesrecorder.log', '*Got save command*', 3)


def cr_peek(file_name):
    command = [SCRIPT] + CONF + ['peek', file_name]
    Popen(command)


def cr_download(file_name):
    command = [SCRIPT] + CONF + ['download', file_name]
    Popen(command)

CHANGES_RECORDER_INI = """\
[DEFAULT]
RECORD_CHANGES  : {0}/changes.txt
MONITOR_FOLDER  : {0}/folder
SAVE_PERIOD     : 900
LOG_FILE        : {0}/changesrecorder.log
VERBOSITY_LEVEL : 2
PORT            : 10021
"""


def prepare():
    d = 'folder'
    dd = os.path.join(d, 'subfolder')
    os.mkdir(d)
    os.mkdir(dd)
    df = os.path.join(d, 'some_file.txt')
    with open(df, 'w') as f:
        f.write('some data')
    ddf = os.path.join(dd, 'other_file.txt')
    with open(ddf, 'w') as f:
        f.write('some other data')
    with open('changesrecorder.ini', 'w') as f:
        cr_ini = CHANGES_RECORDER_INI.format(os.path.join(os.getcwd()))
        f.write(cr_ini)
    return d, df, dd, ddf


def test_case(test_function):
    def wrapper():
        name = test_function.__name__
        print('Start test: {}'.format(name))
        os.mkdir(name)
        os.chdir(name)
        objects = prepare()
        it = test_function(*objects)
        r1 = next(it)#.next()
        process = cr_monitor()
        rc = next(it) #.next()
        cr_quit(process)
        os.chdir('..')
        print('Done test: {} — {}'.format(name, ok(rc)))
        return rc
#        test_cases_list.append(test_function)
    return wrapper


@test_case
def __tdd_show_usage():
    #do nothing
    yield True
    yield timeout_grep('stderr.txt', '*changes is required*')


@test_case
def tdd_run_and_stop(*argv):
    yield True
    yield timeout_grep('changesrecorder.log', '*Loaded*', timeout=3)


@test_case
def tdd_new_file(d, df, dd, ddf):
    yield True
    if not timeout_grep('changesrecorder.log', '*Loaded*', timeout=3):
        yield False
        return
    with open(os.path.join(dd, 'new_file.txt'),'w') as f:
        f.write('some data')
    yield timeout_grep('changes.txt', '*/subfolder'.format(d), timeout=3)


@test_case
def tdd_delete_file(d, df, dd, ddf):
    yield True
    if not timeout_grep('changesrecorder.log', '*Loaded*', timeout=3):
        yield False
        return
    os.remove(df)
    expect = os.path.join(os.getcwd(), d)
    yield timeout_grep('changes.txt', expect, timeout=2)


@test_case
def tdd_update_file(d, df, dd, ddf):
    yield True
    if not timeout_grep('changesrecorder.log', '*started*', timeout=3):
        yield False
        return

    for __ in range(10):
        open(df,'w').close()
        if grep('changes.txt', '*{}'.format(d)):
            yield True
            return
        time.sleep(.1)
    yield False


@test_case
def tdd_peek(d, df, dd, ddf):
    yield True
    if not timeout_grep('changesrecorder.log', '*started*', timeout=3):
        yield False
        return
    with open(os.path.join(dd, 'new_file.txt'),'w') as f:
        f.write('some data')
    if not timeout_grep('changes.txt', '*/subfolder'.format(d), timeout=3):
        yield False
        return
    cr_peek('peek.txt')
    if not timeout_grep('changesrecorder.log', '*Sent*bytes*', 3):
        yield False
        return
    yield timeout_grep('peek.txt', '*/subfolder', 3)


@test_case
def tdd_download(d, df, dd, ddf):
    yield True
#    if not timeout_grep('changesrecorder.log', '*started*', timeout=3):
#        yield False
#         return
    with open(os.path.join(dd, 'new_file.txt'),'w') as f:
        f.write('some data')
    if not timeout_grep('changes.txt', '*/subfolder', timeout=3):
        yield False
        return
    cr_download('download.txt')
    if not timeout_grep('changesrecorder.log', '*Sent*bytes*', 3):
        yield False
        return
    if not timeout_grep('download.txt', '*/subfolder', 3):
        yield False
        return
    if os.path.getsize('changes.txt') != 0:
        print('changes.txt size != 0')
        yield False
        return
    cr_peek('peek.txt')
    if not timeout_grep('changesrecorder.log', '*Sent 0 bytes*', 3):
        yield False
        return
    if os.path.getsize('peek.txt') != 0:
        print('changes.txt size != 0')
        yield False
        return
    yield True

def iterate_test_cases():
    for name, entity in globals().items():
        if name.startswith('tdd'):
            yield name, entity


def main(mask):
    shutil.rmtree('tdd')
    os.mkdir('tdd')
    os.chdir('tdd')
    result = []
    for i, (name, test) in enumerate(iterate_test_cases()):
        if not fnmatch.fnmatch(name, mask):
            continue
        start_time = time.time()
        print('Test {: 2}: {}'.format(i, name))
        rc = test()
        duration = time.time() - start_time
        result.append('{: 2} [{: 6} ms] - {}: {}'.format(i+1, int(duration*1000), ok(rc), name))
#        print('{:02} - {}: {}'.format(i+1, ok(rc), name))
    print('\n'.join(result))


if __name__ == "__main__":
    main('*')