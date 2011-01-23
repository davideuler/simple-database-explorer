#!/usr/bin/env python

#irc://irc.freenode.net/pyqt
from PyQt4 import QtGui, QtCore
import sys
from gui.mainwindow import Sdbe

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    app.setOrganizationName("SDBE Ltd.")
    app.setOrganizationDomain("sdbe.eu")
    app.setApplicationName("SDBE")
    app.setWindowIcon(QtGui.QIcon(QtGui.QPixmap("files/icons/sdbe.ico")))
    window = Sdbe()
    window.show()

    sys.exit(app.exec_())