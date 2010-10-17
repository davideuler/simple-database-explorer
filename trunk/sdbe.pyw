#!/usr/bin/env python

#irc://irc.freenode.net/pyqt
from PyQt4 import QtGui, QtCore
import sys
from gui.mainwindow import Sdbe

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = Sdbe()
    window.show()

    sys.exit(app.exec_())