from PyQt4 import QtCore, QtGui, Qsci
import yaml
from yaml.parser import ParserError
import pickle
import gc
import time
import sqlparse
import re
from threading import Thread
import pyodbc
from decimal import Decimal
import sqlite3
import os
from subprocess import Popen
import subprocess

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
        import win32clipboard
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(text)
        win32clipboard.CloseClipboard()
    except:
        print 'Could not copy clipboard data.'

def warningMessage(title, message):
            msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning, title, message,
                    QtGui.QMessageBox.NoButton)
            msgBox.addButton("&Continue", QtGui.QMessageBox.RejectRole)
            msgBox.exec_()

class NewConnectionDialog(QtGui.QDialog):
    def __init__(self, parent=None, settings=None):
        super(NewConnectionDialog, self).__init__(parent)
        self.connections = pyodbc.dataSources()
        self.settings = settings

        self.connectionsComboBox = self.createComboBox()
        self.connectionsComboBox.setAutoCompletion(True)
        self.connectionsComboBox.setAutoCompletionCaseSensitivity(True)
        self.connectionsComboBox.setFont(getFont(14))
        self.fillComboBox()
        self.connectionsComboBox.setFocus()
        self.passwordEdit = QtGui.QLineEdit()
        self.passwordEdit.setEchoMode(QtGui.QLineEdit.Password)
        self.savePassword = QtGui.QCheckBox("Save password")
        self.savePassword.setChecked(True)
        self.odbcManagerButton = self.createButton("&ODBC Manager", self.openODBCManager)

        self.buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.connectionsComboBox.activated.connect(self.setPassword)

        self.mainLayout = QtGui.QGridLayout()

        self.mainLayout.addWidget(QtGui.QLabel("ODBC connection:"), 0, 0)
        self.mainLayout.addWidget(self.connectionsComboBox, 0, 1)
        self.mainLayout.addWidget(QtGui.QLabel("Password:"), 1, 0)
        self.mainLayout.addWidget(self.passwordEdit, 1, 1)
        self.mainLayout.addWidget(self.savePassword, 2, 1)

        self.mainLayout.addWidget(QtGui.QLabel("Open ODBC manager:"), 3, 0)
        self.mainLayout.addWidget(self.odbcManagerButton, 3, 1)
        self.mainLayout.addWidget(self.buttonBox, 4, 1)
        self.setLayout(self.mainLayout)

        self.setWindowTitle("Open new odbc connection")
        self.setPassword()

    def setPassword(self):
        password = self.settings.get(str(self.connectionsComboBox.currentText()), {}).get("password", "")
        self.passwordEdit.setText(password)

    def openODBCManager(self):
        try:
            subprocess.call(["odbcad32.exe"])
            self.connections = pyodbc.dataSources()
            self.connectionsComboBox.clear()
            self.fillComboBox()
            self.setPassword()
        except Exception as exc:
            warningMessage("Could not open ODBC Manager", unicode(exc.args))

    def createComboBox(self):
            comboBox = QtGui.QComboBox()
            #comboBox.setEditable(False)
            comboBox.setSizePolicy(QtGui.QSizePolicy.Expanding,
                    QtGui.QSizePolicy.Preferred)
            return comboBox

    def fillComboBox(self):
        for i in sorted(self.connections.keys()):
            #self.connectionsComboBox.insertSeparator(1000)
            self.connectionsComboBox.addItem(i)

    def createButton(self, text, member):
        button = QtGui.QPushButton(text)
        button.clicked.connect(member)
        return button

class FindDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        super(FindDialog, self).__init__(parent)

        self.findLabel = QtGui.QLabel("Find &what:")
        self.findEdit = QtGui.QLineEdit()
        self.findLabel.setBuddy(self.findEdit)

        self.replaceLabel = QtGui.QLabel("Replace w&ith:")
        self.replaceEdit = QtGui.QLineEdit()
        self.replaceLabel.setBuddy(self.replaceEdit)

        self.caseCheckBox = QtGui.QCheckBox("Match &case")
        self.fromStartCheckBox = QtGui.QCheckBox("Search from &start")
        self.fromStartCheckBox.setChecked(True)

        self.findButton = QtGui.QPushButton("&Find")
        self.findButton.setDefault(True)
        QtCore.QObject.connect(self.findButton, QtCore.SIGNAL("clicked()"), self.findButtonClick)

        self.countButton = QtGui.QPushButton("&Count")
        QtCore.QObject.connect(self.countButton, QtCore.SIGNAL("clicked()"), self.countbuttonclick)

        self.replaceButton = QtGui.QPushButton("&Replace")
        QtCore.QObject.connect(self.replaceButton, QtCore.SIGNAL("clicked()"), self.replaceButtonClick)

        self.replaceAllButton = QtGui.QPushButton("&Replace All")
        QtCore.QObject.connect(self.replaceAllButton, QtCore.SIGNAL("clicked()"), self.replaceallclick)

        self.moreButton = QtGui.QPushButton("&More")
        self.moreButton.setCheckable(True)
        self.moreButton.setAutoDefault(False)

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
        self.extension.hide()

        self.findFirst = False

    def findButtonClick(self):
        #print "*" * 10
        #print "forward = %s" % (not self.backwardCheckBox.isChecked())
        #print self.findEdit.text()

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
        return self.parent().editor.findFirst(unicode(self.findEdit.text()),
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

        while self.findButtonClick():
            i += 1

        print i
        QtGui.QMessageBox.information(self, "Count", str(i))


    def replaceButtonClick(self):
        #print "*" * 5
        #print "replaceButtonClick: %s" % unicode(self.replaceEdit.text())
        self.parent().editor.replace(unicode(self.replaceEdit.text()))
        return self.findButtonClick()


    def replaceallclick(self):
        print "*" * 5
        print "replaceallclick: %s" % unicode(self.replaceEdit.text())

        while self.replaceButtonClick():
            pass
            #print "replaced..."


class SqlTab(QtGui.QWidget):
    def __init__(self, parent=None, conn=None):
        super(SqlTab, self).__init__(parent)
        #   sql tab
        self.connTab = parent
        self.alias = {}

        self.saveTo = None
        self.query2 = []
        self.rownum = 0
        self.fetchRowsNum = 0
        self.model = QtGui.QStandardItemModel(0, 0)

        self.horizontalLayout = QtGui.QHBoxLayout(self)
        self.horizontalLayout.setSpacing(1)
        self.horizontalLayout.setMargin(1)
        #       text
        font = getFont(12)
        self.editor = Qsci.QsciScintilla(self)
        self.editor.setToolTip("QsciScintilla")
        self.editor.setWhatsThis("")
        self.editor.setObjectName("textEdit")
        self.editor.setInputMethodHints(QtCore.Qt.ImhUppercaseOnly)
        self.editor.setLexer(Qsci.QsciLexerSQL())
        fm = QtGui.QFontMetrics(getFont(6))
        self.editor.setFont(font)
        #self.editor.setMarginsFont(getFont(7))
        # LINE NUMBERS
        #self.editor.setMarginWidth(0, fm.width( "0000" ) + 2)
        #self.editor.setMarginLineNumbers(2, True)
        self.editor.setCaretLineVisible(False)
        # Folding visual : we will use boxes
        self.editor.setFolding(Qsci.QsciScintilla.BoxedTreeFoldStyle)
        # Braces matching
        self.editor.setBraceMatching(Qsci.QsciScintilla.SloppyBraceMatch)
        ## Editing line color
        self.editor.setCaretLineVisible(True)
        self.editor.setCaretLineBackgroundColor(QtGui.QColor("#B2EC5D"))

        ## Marker (bookmarks)
        self.editor.setMarkerBackgroundColor(QtGui.QColor("#663854"))
        self.editor.setMarkerForegroundColor(QtGui.QColor("#006B3C"))

        ## Margins colors
        # line numbers margin
        self.editor.setMarginsBackgroundColor(QtGui.QColor("#F8F4FF"))
        self.editor.setMarginsForegroundColor(QtGui.QColor("#663854"))

        # folding margin colors (foreground,background)
        self.editor.setFoldMarginColors(QtGui.QColor("#006B3C"),QtGui.QColor("#01796F"))

        self.editor.setAutoIndent(True)
        self.editor.setIndentationWidth(4)
        self.editor.setIndentationGuides(1)
        self.editor.setIndentationsUseTabs(0)

        self.editor.setCallTipsStyle(Qsci.QsciScintilla.CallTipsContext)
        self.editor.setCallTipsVisible(False)
        self.editor.setUtf8(True)
        self.editor.setWrapMode(Qsci.QsciScintilla.WrapWord)

        self.sqlLexer = Qsci.QsciLexerSQL(self.editor)
        self.api = Qsci.QsciAPIs(self.sqlLexer)
        self.api.add(QtCore.QString("SELECT\t*\nFROM\t"))
        self.api.add(QtCore.QString("UPDATE\t_\nSET\t\t"))
        self.api.add(QtCore.QString("INSERT\tINTO\t_\nVALUES\t"))
        self.api.add(QtCore.QString("CREATE\tTABLE\t"))
        self.api.add(QtCore.QString("CREATE\tVIEW\t"))
        self.api.add("www simple database explore")
        self.api.prepare()
        self.sqlLexer.setAPIs(self.api)
        self.editor.setLexer(self.sqlLexer)

        self.editor.setAutoCompletionThreshold(2)
        self.editor.setAutoCompletionSource(Qsci.QsciScintilla.AcsAPIs)
        self.editor.setAutoCompletionCaseSensitivity(False)
        #self.editor.setAutoCompletionReplaceWord(True)
        #self.editor.setAutoCompletionShowSingle(True)

        # ===============================================
        self.table = QtGui.QTableView(self)
        self.table.setSortingEnabled(True)
        self.table.setFont(getFont(8))
        self.table.horizontalHeader().setVisible(True)
        self.table.horizontalHeader().setCascadingSectionResizes(True)
        self.table.horizontalHeader().setDefaultSectionSize(90)
        self.table.horizontalHeader().setSortIndicatorShown(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setWordWrap(True)
        self.table.verticalHeader().setDefaultSectionSize(20)
        self.table.verticalHeader().setMinimumSectionSize(16)
        # layout
        self.splitter = QtGui.QSplitter(self)
        self.splitter.addWidget(self.editor)
        self.splitter.addWidget(self.table)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 2)
        self.horizontalLayout.addWidget(self.splitter)

        QtCore.QObject.connect(self.editor, QtCore.SIGNAL("userListActivated(int,QString)"), self.userListSelected)
        vertical = self.table.verticalScrollBar()
        QtCore.QObject.connect(vertical, QtCore.SIGNAL("valueChanged(int)"), self.maybeFetchMore)
        shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+C"), self.table, self.copytoclipbord)
        self.setLayout(self.horizontalLayout)

        self.newAction = QtGui.QAction("Copy table selection", self,
                shortcut="Ctrl+W", triggered=self.copyTable)

    def copyTable(self):
        print "dflkj"

    def defaultStretch(self):
        self.splitter.setSizes([200, 200])

    def expandTable(self):
        s = self.splitter.sizes()
        s[1] *= 2
        self.splitter.setSizes(s)

    def shrinkTable(self):
        s = self.splitter.sizes()
        s[1] /= 2
        self.splitter.setSizes(s)

    def getSql(self):
        if self.editor.hasSelectedText():
            sql = self.editor.selectedText()
        else:
            sql = self.editor.text()
        # remove sql comments
        return re.sub("\-\-.*\n|\/\*.*\*\/", " ", unicode(sql).strip())

    def setSql(self, sql):
        if self.editor.hasSelectedText():
            print "setSql replace"
            print sql
            self.editor.replace(sql)
        else:
            self.editor.setText(sql)

    def formatSql(self):
        if self.editor.hasSelectedText():
            text = self.findSelection()
            sql = sqlparse.format(text, reindent=True, keyword_case='upper')
            self.editor.replace(sql)


        print sql

        self.setSql(sql)

    def showColumnAutoComplete(self):
        startTime = time.time()
        sqlparsed = sqlparse.parse(self.getSql().upper())
        print len(self.connTab.catalog.keys())
        words = set(re.split("\s", self.getSql().upper()))
        searchFor = words & set([i.upper() for i in self.connTab.catalog])
        print searchFor
        regex = re.compile("|".join(("%s\s+a?s?\s?[\w\_]+" % re.escape(i) for i in searchFor)), re.IGNORECASE)

        for sql in sqlparsed:
            if sql.token_first().value == 'SELECT':
                sqlFrom = " ".join(sql.to_unicode().split("FROM")[1:])
                for line in sqlFrom.splitlines():
                    #print "*" * 5
                    for tehAlias in re.findall(regex, line):
                        tehAlias = re.split("\s|as", tehAlias)
                        self.alias[tehAlias[-1]] = tehAlias[0]

        print "COLUMN AUTOCOMPLETE:", time.time() - startTime


        x, y = self.editor.getCursorPosition()
        self.editor.findFirst("[\.\s\n]", True, False, False, False, False, x, y - 1, False)
        x2, y2 = self.editor.getCursorPosition()

        if x2 < x:
            y2 = 0
        self.editor.setSelection(x, y2, x, y)
        aliasTemp = unicode(self.editor.selectedText()).replace(".", "").upper()
        print aliasTemp

        try:
            print "ALIAS:", self.alias
            tableName = unicode(self.alias[aliasTemp])
            columns = self.connTab.catalog[tableName]["COLUMNS"].keys()

            if len(columns) == 0:
                print "GET columns catalog from DB!"
                #t = self.conn.record(tableName)
                self.connTab.catalog[tableName]["COLUMNS"] = {}
                for c in self.connTab.cursor.columns(table=tableName):
                    self.connTab.catalog[tableName]["COLUMNS"][c[3]] = (c[6], c[7])

                for c in self.connTab.cursor.columns(table=tableName.lower()):
                    self.connTab.catalog[tableName]["COLUMNS"][c[3]] = (c[6], c[7])

                self.connTab.saveCatalog()

                columns = self.connTab.catalog[tableName]["COLUMNS"].keys()
        except Exception as exc:
            print exc.args
            print "Error at getting alias"
            print "aliasTemp: '%s'" % aliasTemp, " not found in:"
            for i in self.alias:
                print "%s: '%s'" % (i, self.alias[i])
            columns = []

        self.editor.setSelection(x, y, x, y)
        if len(columns) > 0:
            self.editor.showUserList(1, sorted(columns))

    def showAutoComplete(self):
        # check if user want colomn help. if he typed "." before.
        line, index = self.editor.getCursorPosition()
        self.editor.setSelection(line, index - 1, line, index)
        if self.editor.hasSelectedText():
            text = unicode(self.editor.selectedText())
            if text == ".":
                self.editor.setCursorPosition(line, index)
                self.showColumnAutoComplete()
                return

        self.editor.setCursorPosition(line, index)
        self.editor.showUserList(4, sorted(self.connTab.catalog.keys()))

    def userListSelected(self, i, s):
        print i, s
        s = str(s)

        # TABLE
        if s.startswith("."):
            s = s.replace(".", "")
            self.editor.insert(s)
            x, y = self.editor.getCursorPosition()
            self.editor.setCursorPosition(x, y + len(s))
        else:
            x, y = self.editor.getCursorPosition()
            self.editor.findFirst("[\.\s\n]", True, False, False, False, False, x, y, False)
            x2, y2 = self.editor.getCursorPosition()
            if x2 < x:
                y2 = 0
            self.editor.setSelection(x, y2, x, y)
            self.editor.replace(s)
            self.editor.setCursorPosition(x, y + len(s))

    def open(self, path):
        self.editor.setText(open(path).read())
        self.saveTo = path

    def saveFile(self, path):
        open(path, "w").write(self.editor.text())
        self.saveTo = path

    def printMessage(self, table):
        model = QtGui.QStandardItemModel(0, len(table[0]), self)

        for i, name in enumerate(table[0]):
            model.setHeaderData(i, QtCore.Qt.Horizontal, name)

        for i, row in enumerate(table[1:]):
            model.insertRow(i, QtCore.QModelIndex())

            for j, column in enumerate(row):
                model.setData(model.index(i, j, QtCore.QModelIndex()), column)

        self.table.setModel(model)
        self.table.setWordWrap(True)
        self.table.resizeColumnsToContents()


    def execute(self):
        sqlparsed = sqlparse.parse(self.getSql())
        error = False
        self.printMessage([["STATUS"], [""]])

        if len(sqlparsed) > 0:
            # is select
            if len(sqlparsed) == 1 and sqlparsed[0].token_first().value.upper() == 'SELECT':
                try:

                    self.query2 = self.connTab.cursor.execute(self.getSql())
                except:
                    error = True

                # ==== SELECT ====
                if error == False:
                    self.columnsLen = len(self.query2.description)
                    self.model = QtGui.QStandardItemModel(0, self.columnsLen)

                    for index, column in enumerate(self.query2.description):
                        self.model.setHeaderData(index, QtCore.Qt.Horizontal, column[0], role=0)

                    self.rownum = 0
                    self.fetchRowsNum = 0

                    # BIND ON START
                    self.table.setModel(self.model)
                    self.fetchMore()

            if not (len(sqlparsed) == 1 and sqlparsed[0].token_first().value.upper() == 'SELECT') or error:
                columns = ["S", "ROWS", "TIME (sec)", "DB_ERROR", "DRIVER_ERROR", "SQL"]
                printTable = [columns]
                self.fetchRowsNum = -1

                for sql in sqlparsed:
                    if len(sql.tokens) > 2:
                        startTime = time.time()
                        try:

                            query = self.connTab.cursor.execute(sql.to_unicode()) #QtSql.QSqlQuery(query=sql.to_unicode(), db=self.conn)
                            driverError = dbError = ""
                            status = "OK"
                            rows = query.rowcount
                        except Exception as exc:
                            dbError = exc.args[0]
                            driverError = exc.args[1]
                            status = "ERROR"
                            rows = -1

                        totalTime = time.time() - startTime
                        printTable.append([status, rows, totalTime, dbError, driverError, sql.to_unicode().replace("\n", " ").strip()])

                self.printMessage(printTable)

    def executeToFile(self, path):
        try:
            self.query2 = self.connTab.cursor.execute(self.getSql())
            o = open(path, "w", 5000)

            if self.query2:
                # HEADER
                bazz = u";".join([i[0] for i in self.query2.description])
                o.write(bazz.encode('UTF-8') + u";\n")

                for row in self.query2:
                    #print row
                    line = u"%s;\n" % u";".join(map(unicode, row))
                    o.write(line.encode('UTF-8'))
            o.close()
        except Exception as exc:
                warningMessage("Error executing to file!", unicode(exc.args))

    def findSelection(self):
        text = unicode(self.editor.selectedText())
        s =  self.editor.getSelection()
        self.editor.findFirst(text, False, False, False, False, True, s[0], s[1], True)
        return text

    def comment(self):
        if self.editor.hasSelectedText():
            text = self.findSelection()

            if len([i for i in text.splitlines() if i.startswith("--")]) == len(text.splitlines()):
                self.editor.replace("\n".join([i[2:] for i in text.splitlines()]))
            else:
                self.editor.replace("--" + "\n--".join(text.splitlines()))

    def joinlines(self):
        if self.editor.hasSelectedText():
            text = self.findSelection()
            self.editor.replace(re.sub("\n|\r", " ", text))

    def copytoclipbord(self):
        print "copytoclipbord"
        try:
            if self.table.hasFocus():
                selection = self.table.selectionModel()
                indexes = selection.selectedIndexes()

                columns = indexes[-1].column() - indexes[0].column() + 1
                rows = len(indexes) / columns

                textTable = [[""] * columns for i in xrange(rows)]

                for i, index in enumerate(indexes):
                    #print index.row(), index.column()
                    #print "i:", i, ", row():", index.row(), ", row:", i % rows, ", column:", i / rows
                    #print " =", unicode(self.model.data(index).toString())
                    textTable[i % rows][i / rows] = unicode(self.model.data(index).toString())
                    #print textTable

                headerText = "\t".join((unicode(self.model.headerData(i, QtCore.Qt.Horizontal).toString()) for i in range(indexes[0].column(), indexes[-1].column() + 1)))
                text = "\n".join(("\t".join(i) for i in textTable))
                setClipboard(headerText + "\n" + text)
            else:
                self.editor.copy()

        except Exception as exc:
                warningMessage("Error copy to clipbord", unicode(exc.args))

    def maybeFetchMore(self, value):
        vertical = self.table.verticalScrollBar()
        #print "value:", vertical.value(), "pageStep:", vertical.pageStep(), "maximum:", vertical.maximum()
        if vertical.value() +  vertical.pageStep() > vertical.maximum() and vertical.maximum() != 0:
            #print "fetchMore", vertical.value() +  vertical.pageStep()
            self.fetchMore()

    ##>>> pyodbc.Date
    ##<type 'datetime.date'>
    ##>>> pyodbc.DATETIME
    ##<type 'datetime.datetime'>
    ##>>> pyodbc.Time
    ##<type 'datetime.time'>
    ##>>> decimal.Decimal
    ##<class 'decimal.Decimal'>
    def convertForQt(self, x):
        if isinstance(x, pyodbc.NUMBER) or isinstance(x, pyodbc.ROWID) or isinstance(x, pyodbc.STRING):
            return x
        elif isinstance(x, Decimal):
            return int(x)
        elif isinstance(x, pyodbc.Date) or isinstance(x, pyodbc.DATETIME) or isinstance(x, pyodbc.Time):
            return unicode(x)
        elif isinstance(x, pyodbc.BINARY):
            return x #None #unicode(x)
        else:
            return x

    def fetchMore(self):
        if self.fetchRowsNum != -1:
            self.fetchRowsNum += 256
            self.model.insertRows(self.rownum, 256, QtCore.QModelIndex())

            # PYODBC
            for row in self.query2:
                #print row
                for j in xrange(self.columnsLen):
                    self.model.setData(self.model.index(self.rownum, j, QtCore.QModelIndex()), self.convertForQt(row[j]), role=0)
                self.rownum += 1

                if self.rownum >= self.fetchRowsNum:
                    break

            self.model.removeRows(self.rownum, self.model.rowCount() - (self.rownum), QtCore.QModelIndex())
            self.table.resizeColumnsToContents()

            self.connTab.showToolTip("Rows: %s" % self.model.rowCount())
    # ###########################
    def searchEditor(self):
        dialog = FindDialog(self)
        dialog.exec_()

    #def findText(self, )

class ConnTab(QtGui.QWidget):
    def __init__(self, parent=None, connName='', password="", connSettings=None):
        super(ConnTab, self).__init__(parent)

        # SQLITE
        self.connSettings = connSettings
        self.name = connName

        try:
            self.conn2 = pyodbc.connect('DSN=%s;PWD=%s' % (self.name, password))
            self.conn2.autocommit = True
            self.cursor = self.conn2.cursor()
        except Exception as exc:
            self.conn2 = None
            warningMessage("Error opening connection: %s" % connName, unicode(exc.args))
        # AUTO COMPLETE
        self.loadCatalog()
        self.setIcon()

        # conn tab
        self.verticalLayout_3 = QtGui.QVBoxLayout()
        self.verticalLayout_3.setSpacing(2)
        self.verticalLayout_3.setContentsMargins(1, 4, 1, 2)
        #   CHILD TABS
        self.childTabs = QtGui.QTabWidget()
        self.childTabs.setFont(getFont(11))
        self.childTabs.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.childTabs.setTabPosition(QtGui.QTabWidget.South)
        self.childTabs.setTabShape(QtGui.QTabWidget.Triangular)
        self.childTabs.setTabsClosable(True)
        self.childTabs.setMovable(True)
        # layout
        self.verticalLayout_3.addWidget(self.childTabs)
        self.setLayout(self.verticalLayout_3)

##    def getConnection(self, connName, driver='QODBC', host='localhost', database='', schema='', port=0, user='', password=''):
##        conn = QtSql.QSqlDatabase.addDatabase(driver, connName)
##        conn.setHostName(host)
##        conn.setDatabaseName(database)
##        conn.setPort(port)
##        conn.setUserName(user)
##        conn.setPassword(password)

##        return conn

    def setIcon(self):
        if self.conn2:
            self.icon = QtGui.QIcon("files/icons/NormalIcon.ico")
        else:
            self.icon = QtGui.QIcon("files/icons/ModifiedIcon.ico")

    def getCatalog(self):
        catalog = {}
        if os.path.exists("files/cache/%s.sqlite" % self.name):
            catalog2 = sqlite3.connect("files/cache/%s.sqlite" % self.name)
        else:
            catalog2 = sqlite3.connect("files/cache/%s.sqlite" % self.name)
        print "START CATALOG LOAD: %s" % time.ctime()

        for i in self.cursor.tables(schema=self.connSettings.get('schema', '%')):
            #print i
            if i.table_name != None:
                catalog[i.table_name.upper()] = dict([("TYPE", i.table_type), ("COLUMNS", dict())])


        print "END CATALOG LOAD: %s" % time.ctime()

        return catalog

    def reloadCatalog(self):
        self.catalog = self.getCatalog()
        self.saveCatalog()

    def saveCatalog(self):
        pickle.dump(self.catalog, open("files/cache/%s.pickle" % self.name, "w"))

    def loadCatalog(self):
        try:
            self.catalog = pickle.load(open("files/cache/%s.pickle" % self.name))
        except:
            self.reloadCatalog()


    def showCatalog(self):
        sqlTab = self.childTabs.currentWidget()
        columns = ["TABLE/COLUMN", "TYPE", "LENGTH"]
        printTable = [columns]

        for table in sorted(self.catalog):
            printTable.append([table, self.catalog[table]["TYPE"], ""])
            columns = self.catalog[table]["COLUMNS"]
            for column in columns:
                printTable.append(["\t%s" % column, 0, 0])

            printTable.append(["", "", ""])
        sqlTab.printMessage(printTable)

    def showToolTip(self, text):
        p = self.pos()
        p.setX(p.x() + (self.width() / 2))
        p.setY(p.y() + (self.height() - 10))
        QtGui.QToolTip.showText(p, text)


class SettingsTab(QtGui.QWidget):
    def __init__(self, parent=None, path=None):
        super(SettingsTab, self).__init__(parent)
        #   sql tab
        self.horizontalLayout = QtGui.QHBoxLayout(self)
        self.horizontalLayout.setSpacing(1)
        self.horizontalLayout.setMargin(1)
        #       text
        font = getFont(12)
        self.editor = Qsci.QsciScintilla(self)
        self.editor.setToolTip("QsciScintilla")
        self.editor.setWhatsThis("")
        self.editor.setObjectName("textEdit")
        self.editor.setInputMethodHints(QtCore.Qt.ImhUppercaseOnly)
        self.editor.setLexer(Qsci.QsciLexerYAML())
        fm = QtGui.QFontMetrics(getFont(6))
        self.editor.setFont(font)
        self.editor.setMarginsFont(getFont(7))
        # LINE NUMBERS
        self.editor.setMarginWidth(0, fm.width( "0000" ) + 2)
        self.editor.setMarginLineNumbers(2, True)
        # Folding visual : we will use boxes
        self.editor.setFolding(Qsci.QsciScintilla.BoxedTreeFoldStyle)
        # Braces matching
        self.editor.setBraceMatching(Qsci.QsciScintilla.SloppyBraceMatch)
        ## Editing line color
        self.editor.setCaretLineVisible(True)
        self.editor.setCaretLineBackgroundColor(QtGui.QColor("#BCD4E6"))

        ## Margins colors
        # line numbers margin
        self.editor.setMarginsBackgroundColor(QtGui.QColor("#F8F4FF"))
        self.editor.setMarginsForegroundColor(QtGui.QColor("#663854"))

        # folding margin colors (foreground,background)
        self.editor.setFoldMarginColors(QtGui.QColor("#006B3C"),QtGui.QColor("#89CFF0"))

        self.editor.setAutoIndent(1)
        self.editor.setIndentationWidth(4)
        self.editor.setIndentationGuides(1)
        self.editor.setIndentationsUseTabs(0)
        self.editor.setAutoCompletionThreshold(2)
        self.editor.setCallTipsVisible(True)
        self.editor.setAutoCompletionReplaceWord(True)
        self.editor.setUtf8(True)
        self.editor.setWrapMode(Qsci.QsciScintilla.WrapWord)
        self.editor.setAnnotationDisplay(Qsci.QsciScintilla.AnnotationHidden)

        self.horizontalLayout.addWidget(self.editor)
        self.setLayout(self.horizontalLayout)

        self.open(path)
        self.icon = QtGui.QIcon("files/icons/AddedIcon.ico")

    def open(self, path):
        self.editor.setText(open(path).read())
        self.saveTo = path

    def save(self):
        open(self.saveTo, "w").write(self.editor.text())


class Settings:
    def __init__(self, settingsFile):
        self.settingsFile = settingsFile
    # ==== LOAD SETTINGS ====
    def load(self):
        self.settings = {}

        try:
            self.settings = yaml.load(open(self.settingsFile))
            return ("OK", "Settings loadet successfully")
        except IOError, e:
            open(self.settingsFile, "w").write(open("files/%s.%s" % (self.settingsFile, "example")).read())
            self.settings = yaml.load(open(self.settingsFile))
            return ("Info", "Settings file not found! I have created a settings.yml file in files directory. \nGo edit it or just click Settings button!")
        except ParserError, e:
            return ("Error", "Settings load ERROR. YAML setting file is corrupt!\n %s" % str(e))