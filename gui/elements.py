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

def getFont(size):
    font = QtGui.QFont()
    font.setFamily("Verdana")
    font.setPointSize(size)
    font.setWeight(50)
    font.setItalic(False)
    font.setBold(False)
    return font

def warningMessage(title, message):
            msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning, title, message,
                    QtGui.QMessageBox.NoButton)
            msgBox.addButton("&Continue", QtGui.QMessageBox.RejectRole)
            msgBox.exec_()


class FindDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        super(FindDialog, self).__init__(parent)

        self.findLabel = QtGui.QLabel("Find &what:")
        self.findEdit = QtGui.QLineEdit()
        self.findLabel.setBuddy(self.findEdit)

        self.replaceLabel = QtGui.QLabel("Replace w&ith:")
        self.replaceEdit = QtGui.QLineEdit()
        self.replaceLabel.setBuddy(self.replaceEdit)

        caseCheckBox = QtGui.QCheckBox("Match &case")
        fromStartCheckBox = QtGui.QCheckBox("Search from &start")
        fromStartCheckBox.setChecked(True)

        findButton = QtGui.QPushButton("&Find")
        findButton.setDefault(True)
        QtCore.QObject.connect(findButton, QtCore.SIGNAL("clicked()"), self.findButtonClick)

        replaceButton = QtGui.QPushButton("&Replace")
        replaceButton.setDefault(True)

        replaceAllButton = QtGui.QPushButton("&Replace All")
        replaceAllButton.setDefault(True)

        moreButton = QtGui.QPushButton("&More")
        moreButton.setCheckable(True)
        moreButton.setAutoDefault(False)

        buttonBox = QtGui.QDialogButtonBox(QtCore.Qt.Vertical)
        buttonBox.addButton(findButton, QtGui.QDialogButtonBox.ActionRole)
        buttonBox.addButton(replaceButton, QtGui.QDialogButtonBox.ActionRole)
        buttonBox.addButton(replaceAllButton, QtGui.QDialogButtonBox.ActionRole)
        buttonBox.addButton(moreButton, QtGui.QDialogButtonBox.ActionRole)

        extension = QtGui.QWidget()

        wholeWordsCheckBox = QtGui.QCheckBox("&Whole words")
        backwardCheckBox = QtGui.QCheckBox("Search &backward")
        searchSelectionCheckBox = QtGui.QCheckBox("Search se&lection")

        moreButton.toggled.connect(extension.setVisible)

        extensionLayout = QtGui.QVBoxLayout()
        extensionLayout.setMargin(0)
        extensionLayout.addWidget(wholeWordsCheckBox)
        extensionLayout.addWidget(backwardCheckBox)
        extensionLayout.addWidget(searchSelectionCheckBox)
        extension.setLayout(extensionLayout)

        topLeftLayout = QtGui.QVBoxLayout()
        topLeftLayout.addWidget(self.findLabel)
        topLeftLayout.addWidget(self.findEdit)
        topLeftLayout.addWidget(self.replaceLabel)
        topLeftLayout.addWidget(self.replaceEdit)

        leftLayout = QtGui.QVBoxLayout()
        leftLayout.addLayout(topLeftLayout)
        leftLayout.addWidget(caseCheckBox)
        leftLayout.addWidget(fromStartCheckBox)
        leftLayout.addStretch(1)

        mainLayout = QtGui.QGridLayout()
        mainLayout.setSizeConstraint(QtGui.QLayout.SetFixedSize)
        mainLayout.addLayout(leftLayout, 0, 0)
        mainLayout.addWidget(buttonBox, 0, 1)
        mainLayout.addWidget(extension, 1, 0, 1, 2)
        self.setLayout(mainLayout)

        self.setWindowTitle("Find and replace")
        extension.hide()

        self.findFirst = False

    def findButtonClick(self):
        if self.findFirst == True:
            print "self.findFirst == True"
            self.parent().editor.findNext()
        else:

##            (	const QString & 	expr,
##bool 	re,
##bool 	cs,
##bool 	wo,
##bool 	wrap,
##bool 	forward = true,
##int 	line = -1,
##int 	index = -1,
##bool 	show = true
##)
            print self.findEdit.text()
            self.findEdit.text()
            self.parent().editor.findFirst(str(self.findEdit.text()),
                            False, False,
                            False, False,
                            True, -1, -1,
                            True)
            print "findButtonClick"
            self.findFirst = True

        print self.parent().editor.getCursorPosition()

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
        # Folding visual : we will use boxes
        self.editor.setFolding(Qsci.QsciScintilla.BoxedTreeFoldStyle)
        # Braces matching
        self.editor.setBraceMatching(Qsci.QsciScintilla.SloppyBraceMatch)
        ## Editing line color
        self.editor.setCaretLineVisible(True)
        self.editor.setCaretLineBackgroundColor(QtGui.QColor("#B2EC5D"))

        ## Margins colors
        # line numbers margin
        self.editor.setMarginsBackgroundColor(QtGui.QColor("#F8F4FF"))
        self.editor.setMarginsForegroundColor(QtGui.QColor("#663854"))

        # folding margin colors (foreground,background)
        self.editor.setFoldMarginColors(QtGui.QColor("#006B3C"),QtGui.QColor("#01796F"))

        self.editor.setAutoIndent(1)
        self.editor.setIndentationWidth(4)
        self.editor.setIndentationGuides(1)
        self.editor.setIndentationsUseTabs(0)
        self.editor.setAutoCompletionThreshold(2)
        self.editor.setCallTipsVisible(True)
        self.editor.setAutoCompletionReplaceWord(True)
        self.editor.setUtf8(True)

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

        self.setLayout(self.horizontalLayout)

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

        return re.sub("\-\-.*\n|\/\*.*\*\/", " ", unicode(sql).strip()) #.replace("\n\n", " ") \-\-.*\n

    def setSql(self, sql):
        if self.editor.hasSelectedText():
            print "setSql replace"
            print sql
            self.editor.replace(sql)
        else:
            self.editor.setText(sql)

    def formatSql(self):
        sql = sqlparse.format(self.getSql(), reindent=True, keyword_case='upper')
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
                        #print "\t", tehAlias

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

        if len(columns) > 0:
            self.editor.showUserList(1, sorted(columns))

    def showAutoComplete(self):
        self.editor.showUserList(1, sorted(self.connTab.catalog.keys()))

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
        self.connTab.showToolTip("executing " * 5)
        sql = self.getSql()
        sqlparsed = sqlparse.parse(sql)
        error = False
        #self.query.finish()
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
    def __init__(self, parent=None, connName='', connSettings=None):
        super(ConnTab, self).__init__(parent)

        # SQLITE
        self.connSettings = connSettings
        self.name = connName
        try:
            self.conn2 = pyodbc.connect('DSN=%s;PWD=%s' % (self.name, self.connSettings['password']))
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

        for table in self.catalog:
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