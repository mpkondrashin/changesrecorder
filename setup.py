from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

ext_modules = [ Extension("changesrecorder",       ["changesrecorder.py"]),
                Extension("syncscope",     ["changes.py"]),
                ]


setup(
    name='ChangesRecorder',
    cmdclass={'build_ext': build_ext},
    ext_modules=ext_modules
)
