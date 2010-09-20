import sys
from PyQt4 import uic

uic.compileUi(open("mainwindow.ui"), open("mainwindow_pallete.py", "w"))
