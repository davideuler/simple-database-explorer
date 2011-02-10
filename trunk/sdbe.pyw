#!/usr/bin/env python

#irc://irc.freenode.net/pyqt
from PyQt4 import QtGui, QtCore
import sys
from gui.mainwindow import Sdbe
import gui.resources
import ctypes


try:
    myappid = 'sdbecompany.sdbe.%s' # % __version__ # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except:
    print "Failed to set appusermodelID for icon to work on Windows 7"

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    app.setOrganizationName("sdbecompany")
    #app.setOrganizationDomain("sdbe.eu")
    app.setApplicationName("SDBE")
    app.setWindowIcon(QtGui.QIcon(QtGui.QPixmap(":icon/sdbe.png")))
    window = Sdbe()
    window.show()

    sys.exit(app.exec_())