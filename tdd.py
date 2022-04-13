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
                line = line.strip()
                if fnmatch.fnmatch(line, pattern):
                    return True
#                print('|{}| does not match |{}|'.format(line, pattern))

    except IOError:
        pass
    return False


def timeout_grep(file_name, pattern, timeout):
    start_time = time.time()
    while not grep(file_name, pattern):
#        print('{} not found - sleep'.format(pattern))
        time.sleep(1)
        if time.time() - start_time > timeout:
            # missing file print separate
            if os.path.isfile(file_name):
                print('======= BEGIN {} ======='.format(file_name))
                print(open(file_name).read())
                print('========= END {} ======='.format(file_name))
            else:
                print("{}: missing".format(file_name))
            print("Wait for '{}' in '{}' timeout".format(pattern, file_name))
            return False
    return True

SCRIPT = '../../main.py'
CONF = ['-c', 'changesrecorder.ini']


def cr_exec(args, wait_for):
    command = [SCRIPT] + CONF + args
    print('Execute: {}'.format(' '.join(command)))
    Popen(command)
    return timeout_grep('changesrecorder.log', wait_for, 3)


def cr_monitor():
    return cr_exec(['monitor'], '*Monitoring started*')


def cr_quit():
    return cr_exec(['quit'], '*Got quit command*')


def cr_save(file_name):
    return cr_exec(['save', file_name], '*Got save command*')


def cr_peek(file_name):
    return cr_exec(CONF + ['peek', file_name], '*Got peek command*')


def cr_download(file_name):
    return cr_exec(['download', file_name], '*Got download command*')

CHANGES_RECORDER_INI = """\
[DEFAULT]
RECORD_CHANGES  : {0}/changes.txt
MONITOR_FOLDER  : {0}/folder
SAVE_PERIOD     : {1}
LOG_FILE        : {0}/changesrecorder.log
VERBOSITY_LEVEL : 2
PORT            : 10020
"""


def prepare(name):
    os.mkdir(name)
    os.chdir(name)
    files = ['folder/dir_{0}/file_{0}.txt'.format(c) for c in ['a', 'b', 'c']]
    files += ['folder/dir_a/subdir_a/file_a.txt']
    for file_name in files:
        os.makedirs(os.path.dirname(file_name))
        with open(file_name, 'w') as f:
            f.write('some data')
    with open('changesrecorder.ini', 'w') as f:
        cr_ini = CHANGES_RECORDER_INI.format(os.path.join(os.getcwd()), 900)
        f.write(cr_ini)
    return files


def test_case(test_function):
    def wrapper():
        name = test_function.__name__
        print('Start test: {}'.format(name))
        files = prepare(name)
        return_code = True
        for rc, name in test_function(files):
            print('Done test: {} — {}'.format(name, ok(rc)))
            if not rc:
                return_code = False
                break
        if not cr_quit():
            return False
        os.chdir('..')
        time.sleep(2.5)
        return return_code
    return wrapper


def new_file(folder):
    with open(os.path.join(folder, 'new_file.txt'),'w') as f:
        f.write('some data')
    return os.path.join(os.getcwd(), folder)


def remove_file(file_path):
    os.remove(file_path)
    d = os.path.dirname(file_path)
    return os.path.join(os.getcwd(), d)


def modify_file(file_path):
    with open(file_path, 'w') as f:
        f.write('some data')
    d = os.path.dirname(file_path)
    return os.path.join(os.getcwd(), d)


@test_case
def tdd01_test_changes(files):
    yield cr_monitor(), 'start monitor'

    expect0 = new_file(os.path.dirname(files[0]))
    yield timeout_grep('changes.txt', expect0, timeout=4), 'new_file'

    expect1 = remove_file(files[1])
    yield timeout_grep('changes.txt', expect1, timeout=3), 'delete_file'

    expect2 = modify_file(files[2])
    yield timeout_grep('changes.txt', expect2, timeout=3), 'modify_file'


@test_case
def tdd02_test_peek_download(files):
    yield cr_monitor(), 'start monitor'

    expect0 = new_file(os.path.dirname(files[0]))
    expect1 = remove_file(files[1])
    expect2 = modify_file(files[2])

    yield cr_peek('peek.txt'), 'peek_action'
    yield timeout_grep('changesrecorder.log', '*Sent*bytes*', timeout=3), 'expect_sent_bytes'
    yield timeout_grep('peek.txt', expect0, 4), 'expect_in_peek_0_txt'
    yield timeout_grep('peek.txt', expect1, 4), 'expect_in_peek_1_txt'
    yield timeout_grep('peek.txt', expect2, 4), 'expect_in_peek_2_txt'
    yield cr_download('download.txt'), 'download_action'
    yield timeout_grep('download.txt', expect0, 4), 'expect_in_download_0_txt'
    yield timeout_grep('download.txt', expect1, 4), 'expect_in_download_1_txt'
    yield timeout_grep('download.txt', expect2, 4), 'expect_in_download_2_txt'
    yield os.path.getsize('changes.txt') == 0, 'changes_empty'
    yield cr_peek('peek.txt'), 'peek_empty'
    yield timeout_grep('changesrecorder.log', '*Sent 0 bytes*', 3), 'peek_sent_0_bytes'
    yield os.path.getsize('peek.txt') == 0, 'second_peek_empty'


@test_case
def tdd03_test_folder_subfolder(files):
    yield cr_monitor(), 'start monitor'
    expect0 = new_file(os.path.dirname(files[0]))
    expect3 = new_file(os.path.dirname(files[3]))
    yield cr_peek('peek.txt'), 'peek_only_one'
    yield timeout_grep('peek.txt', expect0, 4), 'folder_subfolder'


@test_case
def tdd04_test_subfolder_folder(files):
    yield cr_monitor(), 'start monitor'
    expect3 = new_file(os.path.dirname(files[3]))
    expect0 = new_file(os.path.dirname(files[0]))
    yield cr_peek('peek.txt'), 'peek_only_one'
    yield timeout_grep('peek.txt', expect0, 4), 'subfolder_folder'


@test_case
def tdd05_test_loaded(files):
    yield cr_monitor(), 'start monitor'
    expect0 = new_file(os.path.dirname(files[0]))
    yield timeout_grep('changes.txt', expect0, timeout=4), 'new_file'
    yield cr_quit(), 'quit'
    yield cr_monitor(), 'second start monitor'
    yield timeout_grep('changesrecorder.log', '*Loaded 1 paths', 4), 'loaded_one_path'


@test_case
def tdd06_test_changes_compact(files):
    with open('changesrecorder.ini', 'w') as f:
        cr_ini = CHANGES_RECORDER_INI.format(os.path.join(os.getcwd()), 2)
        f.write(cr_ini)
    yield cr_monitor(), 'start monitor'
    expect0 = new_file(os.path.dirname(files[0]))
    yield timeout_grep('changes.txt', expect0, timeout=4), 'new_file_in_subdir'
    start_time = time.time()
    expect1 = new_file(os.path.dirname(os.path.dirname(files[0])))
    yield timeout_grep('changes.txt', expect0, timeout=4), 'new_file_in_dir'
    for i in range(4):
        expect2 = new_file(os.path.dirname(files[0]))
        if open('changes.txt').read() == expect1:
            yield True, 'changes_compact'
            return
        if time.time() - start_time > 3:
            print('Timeout')
            break
        time.sleep(1)
    else:
        print('For is over')
    yield False, 'changes_compact'


def iterate_test_cases():
    for name, entity in globals().items():
        if name.startswith('tdd'):
            yield name, entity


def main(mask):
    shutil.rmtree('tdd')
    os.mkdir('tdd')
    os.chdir('tdd')

    result = []
    for i, (name, test) in enumerate(sorted(iterate_test_cases())):
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
    sys.exit(main('*'))
