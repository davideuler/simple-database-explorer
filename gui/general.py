from PyQt4 import QtGui, QtCore
import pyodbc
from decimal import Decimal
import sqlite3

def getFont(size):
    font = QtGui.QFont()
    font.setFamily("Verdana")
    font.setPointSize(size)
    font.setWeight(50)
    font.setItalic(False)
    font.setBold(False)
    return font

def setClipboard(text):
    try:
##        import win32clipboard
##        win32clipboard.OpenClipboard()
##        win32clipboard.EmptyClipboard()
##        win32clipboard.SetClipboardText(text)
##        win32clipboard.CloseClipboard()
        clipboard = QtGui.QApplication.clipboard()
        clipboard.setText(text)
    except:
        print 'Could not copy clipboard data.'

def warningMessage(title, message):
    msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning, title, message,
            QtGui.QMessageBox.NoButton)
    msgBox.addButton("&Continue", QtGui.QMessageBox.RejectRole)
    msgBox.exec_()


def isnumber(x):
    """returns true it x is a number. So we can align them right"""
    if isinstance(x, (pyodbc.NUMBER, pyodbc.ROWID, Decimal, long)):
        return True

    return False


def convertforQt(x):
    """
        convert pyodbcs types for qt tableview

        pyodbc.Date is <type 'datetime.date'>
        pyodbc.DATETIME is <type 'datetime.datetime'>
        pyodbc.Time is <type 'datetime.time'>
        decimal.Decimal is <class 'decimal.Decimal'>
        pyodbc.NUMBER is <type 'float'>
    """
    if isinstance(x, pyodbc.ROWID) or isinstance(x, pyodbc.STRING):
        return x
    # TODO: not good :P
    elif isinstance(x, pyodbc.NUMBER): #float
        #print "float"
        return str(x) #str(x) QtCore.QVariant(x)
    elif isinstance(x, Decimal):
        # TODO: make it faster.. u know the types from cursor.desc...
        if int(x) == float(x):
            return int(x)
        else:
            return str(x) #unicode(float(x))
    elif isinstance(x, pyodbc.Date) or isinstance(x, pyodbc.DATETIME) or isinstance(x, pyodbc.Time):
        return unicode(x)
    elif isinstance(x, pyodbc.BINARY):
        return x
    else:
        return x

##def savetohistory(self, name, queryresult):
##    if not os.path.exists("files/history/%s.sqlite" % name):
##        conn = sqlite3.connect("files/history/%s.sqlite" % name)
##        foo.execute("Create table foo ( id integer, name varchar);")