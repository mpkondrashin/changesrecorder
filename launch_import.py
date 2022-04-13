#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    This script is launched by launch_import() defined in darwin.py
    when camera flash is attached
"""

from os import system
from os.path import join
from sys import argv

say = 'say "Подключен флэш накопитель с фотографиями. Запускаю импорт"'
system(say)

root = '/Users/michael/PycharmProjects/photosync'
ps_py = join(root, 'im.sh')
#python = join(root, 'venv/bin/python3')

command = '"{ps_py}" "{cf_path}"'.format(
    ps_py=ps_py,
    cf_path=argv[1]
)
print(command)
system(command)
