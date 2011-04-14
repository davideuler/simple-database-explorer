from PyQt4 import QtCore, QtGui, Qsci
import pyodbc
import os
import time
import pickle
import subprocess
#import keyring
from general import *

class NewConnectionDialog(QtGui.QDialog):
    def __init__(self, parent=None, settings=None):
        super(NewConnectionDialog, self).__init__(parent)
        self.connections = pyodbc.dataSources()
        self.settings = settings

        #self.connectionsComboBox = QtGui.QListWidget(self)
        self.connectionsComboBox = self.createcombobox()
        self.connectionsComboBox.setAutoCompletion(True)
        self.connectionsComboBox.setAutoCompletionCaseSensitivity(True)
        self.connectionsComboBox.setFont(getFont(14))
        self.fillcombobox()
        self.connectionsComboBox.setFocus()

        #
        self.usernameEdit = QtGui.QLineEdit()
        self.schemaEdit = QtGui.QLineEdit()

        self.passwordEdit = QtGui.QLineEdit()
        self.passwordEdit.setEchoMode(QtGui.QLineEdit.Password)
        self.savePassword = QtGui.QCheckBox("Save password")
        self.savePassword.setChecked(True)
        self.odbcManagerButton = self.createbutton("&ODBC Manager", self.openODBCmanager)

        self.buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.connectionsComboBox.activated.connect(self.setpassword)

        self.mainLayout = QtGui.QGridLayout()

        self.mainLayout.addWidget(QtGui.QLabel("ODBC connection:"), 0, 0)
        self.mainLayout.addWidget(self.connectionsComboBox, 0, 1)
        self.mainLayout.addWidget(QtGui.QLabel("Username:"), 1, 0)
        self.mainLayout.addWidget(self.usernameEdit, 1, 1)
        self.mainLayout.addWidget(QtGui.QLabel("Password:"), 2, 0)
        self.mainLayout.addWidget(self.passwordEdit, 2, 1)
        self.mainLayout.addWidget(self.savePassword, 3, 1)

        self.mainLayout.addWidget(QtGui.QLabel("Shema:"), 4, 0)
        self.mainLayout.addWidget(self.schemaEdit, 4, 1)


        self.mainLayout.addWidget(QtGui.QLabel("Open ODBC manager:"), 5, 0)
        self.mainLayout.addWidget(self.odbcManagerButton, 5, 1)
        self.mainLayout.addWidget(self.buttonBox, 6, 1)
        self.setLayout(self.mainLayout)

        self.setWindowTitle("Open new odbc connection")
        self.setpassword()

    def setpassword(self):
        password = self.settings.get(unicode(self.connectionsComboBox.currentText()), {}).get("password", "")
##        db = unicode(self.connectionsComboBox.currentText())
##        user = 'sdbeuser'
##        password = keyring.get_password(db, user)
        if password == None:
            password = ''

        self.passwordEdit.setText(password)

    def openODBCmanager(self):
        try:
            subprocess.call(["odbcad32.exe"])
            self.connections = pyodbc.dataSources()
            self.connectionsComboBox.clear()
            self.fillcombobox()
            self.setpassword()
        except Exception as exc:
            warningMessage("Could not open ODBC Manager", unicode(exc.args))

    def createcombobox(self):
            comboBox = QtGui.QComboBox()
            #comboBox.setEditable(False)
            comboBox.setSizePolicy(QtGui.QSizePolicy.Expanding,
                    QtGui.QSizePolicy.Preferred)
            return comboBox

    def fillcombobox(self):
        for i in sorted(self.connections.keys()):
            self.connectionsComboBox.addItem(i)

    def createbutton(self, text, member):
        button = QtGui.QPushButton(text)
        button.clicked.connect(member)
        return button

class FindDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        super(FindDialog, self).__init__(parent)

        self.findLabel = QtGui.QLabel("Find &what:")
        self.findEdit = self.createcombobox()
        self.findLabel.setBuddy(self.findEdit)
        self.findEdit.setFocus()

        self.replaceLabel = QtGui.QLabel("Replace w&ith:")
        self.replaceEdit = self.createcombobox()
        self.replaceLabel.setBuddy(self.replaceEdit)

        self.caseCheckBox = QtGui.QCheckBox("Match &case")
        self.fromStartCheckBox = QtGui.QCheckBox("Search from &start")
        self.fromStartCheckBox.setChecked(True)

        self.findButton = QtGui.QPushButton("&Find")
        self.findButton.setDefault(True)
        QtCore.QObject.connect(self.findButton, QtCore.SIGNAL("clicked()"), self.findbuttonclick)

        self.countButton = QtGui.QPushButton("&Count")
        QtCore.QObject.connect(self.countButton, QtCore.SIGNAL("clicked()"), self.countbuttonclick)

        self.replaceButton = QtGui.QPushButton("&Replace")
        QtCore.QObject.connect(self.replaceButton, QtCore.SIGNAL("clicked()"), self.replacebuttonclick)

        self.replaceAllButton = QtGui.QPushButton("&Replace All")
        QtCore.QObject.connect(self.replaceAllButton, QtCore.SIGNAL("clicked()"), self.replaceallclick)

        self.moreButton = QtGui.QPushButton("&More")
        self.moreButton.setCheckable(True)
        self.moreButton.setAutoDefault(False)

        # NoFocus
        self.caseCheckBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.fromStartCheckBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.countButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.replaceButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.replaceAllButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.moreButton.setFocusPolicy(QtCore.Qt.NoFocus)


        self.buttonBox = QtGui.QDialogButtonBox(QtCore.Qt.Vertical)
        self.buttonBox.addButton(self.findButton, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.countButton, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.replaceButton, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.replaceAllButton, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.moreButton, QtGui.QDialogButtonBox.ActionRole)

        self.extension = QtGui.QWidget()

        self.regexCheckBox = QtGui.QCheckBox("&Regular expression")
        self.wholeWordsCheckBox = QtGui.QCheckBox("&Whole words")
        self.backwardCheckBox = QtGui.QCheckBox("Search &backward")
        self.searchSelectionCheckBox = QtGui.QCheckBox("Search se&lection")

        self.moreButton.toggled.connect(self.extension.setVisible)

        self.extensionLayout = QtGui.QVBoxLayout()
        self.extensionLayout.setMargin(0)
        self.extensionLayout.addWidget(self.regexCheckBox)
        self.extensionLayout.addWidget(self.wholeWordsCheckBox)
        self.extensionLayout.addWidget(self.backwardCheckBox)
        self.extensionLayout.addWidget(self.searchSelectionCheckBox)
        self.extension.setLayout(self.extensionLayout)

        self.topLeftLayout = QtGui.QVBoxLayout()
        self.topLeftLayout.addWidget(self.findLabel)
        self.topLeftLayout.addWidget(self.findEdit)
        self.topLeftLayout.addWidget(self.replaceLabel)
        self.topLeftLayout.addWidget(self.replaceEdit)

        self.leftLayout = QtGui.QVBoxLayout()
        self.leftLayout.addLayout(self.topLeftLayout)
        self.leftLayout.addWidget(self.caseCheckBox)
        self.leftLayout.addWidget(self.fromStartCheckBox)
        self.leftLayout.addStretch(1)

        self.mainLayout = QtGui.QGridLayout()
        self.mainLayout.setSizeConstraint(QtGui.QLayout.SetFixedSize)
        self.mainLayout.addLayout(self.leftLayout, 0, 0)
        self.mainLayout.addWidget(self.buttonBox, 0, 1)
        self.mainLayout.addWidget(self.extension, 1, 0, 1, 2)
        self.setLayout(self.mainLayout)

        self.setWindowTitle("Find and replace")
        self.extension.show()

        self.findFirst = False
        self.openhistory()

    def createcombobox(self):
            comboBox = QtGui.QComboBox()
            comboBox.setEditable(True)
            comboBox.setSizePolicy(QtGui.QSizePolicy.Expanding,
                    QtGui.QSizePolicy.Preferred)
            comboBox.setMinimumWidth(300)
            return comboBox

    def openhistory(self):
        self.findEdit.clear()

        if self.parent().editor.hasSelectedText():
            self.findEdit.addItem(self.parent().editor.selectedText())

        #self.findEdit.selectAll()

        # FIND
        if os.path.exists("files/search/find.pickle"):
            find = pickle.load(open("files/search/find.pickle"))
            self.findEdit.addItems(sorted(find, key=find.get, reverse=True))
        # REPLACE
        if os.path.exists("files/search/replace.pickle"):
            replace = pickle.load(open("files/search/replace.pickle"))
            self.replaceEdit.addItems(sorted(replace, key=replace.get, reverse=True))

    def savehistory(self):
        # FIND
        if os.path.exists("files/search/find.pickle"):
            find = pickle.load(open("files/search/find.pickle"))
        else:
            find = {}

        find[unicode(self.findEdit.currentText())[:512]] = int(time.time())
        pickle.dump(find, open("files/search/find.pickle", "w"))

        # REPLACE
        if os.path.exists("files/search/replace.pickle"):
            replace = pickle.load(open("files/search/replace.pickle"))
        else:
            replace = {}

        replace[unicode(self.replaceEdit.currentText())[:512]] = int(time.time())
        pickle.dump(replace, open("files/search/replace.pickle", "w"))

        self.openhistory()

    def findbuttonclick(self):
        #self.savehistory()
        ##(const QString & 	expr,
        ##bool 	re,
        ##bool 	cs is true then the search is case sensitive.
        ##bool 	wo is true then the search looks for whole word matches only,
        ##bool 	wrap is true then the search wraps around the end of the text.
        ##bool 	forward = true,
        ##int 	line = -1,
        ##int 	index = -1,
        ##bool 	show is true (the default) then any text found is made visible
        ##)
        return self.parent().editor.findFirst(unicode(self.findEdit.currentText()),
                        self.regexCheckBox.isChecked(), # re
                        self.caseCheckBox.isChecked(),
                        self.wholeWordsCheckBox.isChecked(),
                        False,
                        (not self.backwardCheckBox.isChecked()),
                        -1, -1,
                        True)

    def countbuttonclick(self):
        self.parent().editor.setCursorPosition(0, 0)
        i = 0
        while self.findbuttonclick():
            i += 1

        QtGui.QMessageBox.information(self, "Count", str(i))

    def replacebuttonclick(self):
        #self.savehistory()
        self.parent().editor.replace(unicode(self.replaceEdit.currentText()))
        return self.findbuttonclick()


    def replaceallclick(self):
        self.parent().editor.setCursorPosition(0, 0)
        i = 0
        while self.replacebuttonclick():
            i += 1

        QtGui.QMessageBox.information(self, "Replaced items:", str(i))

    def showEvent(self, event):
        print "showEvent"
        self.openhistory()

    def hideEvent(self, event):
        print "hideEvent"
        self.savehistory()