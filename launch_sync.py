#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    This script is launched by launch_sync() defined in darwin.py
    when external hard driver that has photo folder in root is attached
"""

from os import system
from os.path import join
from sys import argv

say = 'say "Запускаю синхронизацию"'
system(say)

root = '/Users/michael/PycharmProjects/photosync'
ps_py = join(root, 'ps.py')
python = join(root, 'venv/bin/python3')

command = '{python} "{ps_py}" "{photo_path}" -p'.format(
    python=python,
    ps_py=ps_py,
    photo_path=argv[1]
)
print(command)
rc = system(command) // 256
#print('launch_sync. RC: {}'.format(rc))
if rc == 0:
    say = 'say "Синхронизация завершена успешно"'
else:
    say = 'say "Ошибка синхронизации {}"'.format(rc)

system(say)
