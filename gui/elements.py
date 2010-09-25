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
from sqlkeywords import keywords
from random import randint
from dialogs import *
from general import *

class QueryResult:
    def __init__(self, query, status, sql="", rows=-1, time=-1, errorcode="", error=""):
        self.query = query
        self.status = status
        self.rows = rows
        self.time = time
        self.errorcode = errorcode
        self.error = error
        self.sql = sql

    def toarray(self):
        return [self.status, self.rows, self.time, self.errorcode, self.error, self.sql]

class ExecuteThread(QtCore.QThread):
    def __init__(self, parent=None):
       QtCore.QThread.__init__(self, parent)
       self.script = parent
       self.result = None

    def run(self):
        try:
            sql = self.script.editor.getsql()
            startTime = time.time()
            query = self.script.connection.cursor.execute(sql)
            self.result = QueryResult(query, "OK", sql, query.rowcount, time.time() - startTime)

        except Exception as exc:
            self.result = QueryResult(None, "ERROR", sql, -1, -1, "", str(exc))
        finally:
            self.emit(QtCore.SIGNAL('finished'))

class ExecuteManyThread(QtCore.QThread):
    def __init__(self, parent=None):
       QtCore.QThread.__init__(self, parent)
       self.script = parent
       self.results = []
       self.alive = 1

    def run(self):
        sqlparsed = self.script.editor.getparsedsql()

        columns = ["S", "ROWS", "TIME (sec)", "ERROR_CODE", "ERROR", "SQL"]
        self.printTable = [columns]

        for sql in sqlparsed:
            if self.alive == 1:
                try:
                    startTime = time.time()
                    query = self.script.connection.cursor.execute(sql)
                    result = QueryResult(query, "OK", sql, query.rowcount, time.time() - startTime)
                    self.results.append(result.toarray())

                except Exception as exc:
                    result = QueryResult(None, "ERROR", sql, -1, -1, "", str(exc))
                    self.results.append(result.toarray())
                finally:
                    self.emit(QtCore.SIGNAL('executed'))
            else:
                break

        self.emit(QtCore.SIGNAL('finished'))

    def stop(self):
       self.alive = 0

    def toprint(self):
        return self.printTable + self.results

class Editor(Qsci.QsciScintilla):
    def __init__(self, parent=None):
        super(Editor, self).__init__(parent)

        self.setToolTip("SQL editor")
        self.setWhatsThis("")
        self.setObjectName("sqleditor")
        self.setInputMethodHints(QtCore.Qt.ImhUppercaseOnly)
        #self.setLexer(Qsci.QsciLexerSQL())
        #fm = QtGui.QFontMetrics(getFont(6))
        self.setFont(getFont(12))
        #self.setMarginsFont(getFont(7))
        # LINE NUMBERS
        #self.setMarginWidth(0, fm.width( "0000" ) + 2)
        #self.setMarginLineNumbers(2, True)
        self.setCaretLineVisible(False)
        # Folding visual : we will use boxes, Braces matching
        self.setFolding(Qsci.QsciScintilla.BoxedTreeFoldStyle)
        self.setBraceMatching(Qsci.QsciScintilla.SloppyBraceMatch)
        ## Editing line color
        self.setCaretLineVisible(True)
        self.setCaretLineBackgroundColor(QtGui.QColor("#B2EC5D"))
        ## Marker (bookmarks)
        self.setMarkerBackgroundColor(QtGui.QColor("#663854"))
        self.setMarkerForegroundColor(QtGui.QColor("#006B3C"))
        ## line numbers margin
        self.setMarginsBackgroundColor(QtGui.QColor("#F8F4FF"))
        self.setMarginsForegroundColor(QtGui.QColor("#663854"))

        # folding margin colors (foreground,background)
        self.setFoldMarginColors(QtGui.QColor("#006B3C"),QtGui.QColor("#01796F"))

        self.setAutoIndent(True)
        self.setIndentationWidth(4)
        self.setIndentationGuides(1)
        self.setIndentationsUseTabs(0)

        self.setCallTipsStyle(Qsci.QsciScintilla.CallTipsContext)
        self.setCallTipsVisible(False)
        self.setUtf8(True)
        self.setWrapMode(Qsci.QsciScintilla.WrapWord)

        self.setautocomplete()

        unindentshortcut = QtGui.QShortcut(QtGui.QKeySequence("Shift+Tab"), self, self.unindenttext)
        unindentshortcut.setContext(QtCore.Qt.WidgetShortcut)


    def getselection(self, linefrom, indexfrom, lineto, indexto):
        cursorPosition = self.getCursorPosition()

        self.setSelection(linefrom, indexfrom, lineto, indexto)
        text = unicode(self.selectedText())

        self.setCursorPosition(*cursorPosition)

        return text

    def formatsql(self):
        if self.hasSelectedText():
            sql = sqlparse.format(self.findselection(), reindent=True, keyword_case='upper')
            self.replace(sql)

    def unindenttext(self):
        if self.hasSelectedText():
            lines = xrange(self.getSelection()[0], self.getSelection()[2] + 1)
        else:
            lines = [self.getCursorPosition()[0]]

        for i in lines:
            self.unindent(i)

    def getsql(self):
        if self.hasSelectedText():
            sql = self.selectedText()
        else:
            sql = self.text()
        # remove sql comments
        return re.sub("\-\-.*\n|\/\*.*\*\/", " ", unicode(sql).strip())

    def getparsedsql(self):
        return [i.strip() for i in self.getsql().split(";") if i != '']

    def setsql(self, sql):
        if self.hasSelectedText():
            print "setsql replace"
            print sql
            self.replace(sql)
        else:
            self.setText(sql)

    def findselection(self):
        text = unicode(self.selectedText())
        s =  self.getSelection()
        self.findFirst(text, False, False, False, False, True, s[0], s[1], True)
        return text

    def comment(self):
        if self.hasSelectedText():
            text = self.findselection()

            if len([i for i in text.splitlines() if i.startswith("--")]) == len(text.splitlines()):
                self.replace("\n".join([i[2:] for i in text.splitlines()]))
            else:
                self.replace("--" + "\n--".join(text.splitlines()))

    def joinlines(self):
        if self.hasSelectedText():
            joiner, ok = QtGui.QInputDialog.getText(self, "Enter joiner...",
                "Joiner:", QtGui.QLineEdit.Normal,
                ", ")

        if ok: #  and text != ''
            text = self.findselection()
            text = re.split("\n|\r", text)
            text = unicode(joiner).join([i for i in text if i != ""])
            self.replace(text)

    def splitlines(self):
        if self.hasSelectedText():
            spliter, ok = QtGui.QInputDialog.getText(self, "Enter spliter...",
                "regex:", QtGui.QLineEdit.Normal,
                ",")

        if ok and spliter != '':
            try:
                spliter = re.compile(unicode(spliter))
                text = re.split(spliter, unicode(self.findselection()))
                self.replace("\n".join(text))
            except Exception as exc:
                warningMessage("Error splitting line!", unicode(exc.args))


    def setautocomplete(self, tables=[]):
        self.sqlLexer = Qsci.QsciLexerSQL(self)
        self.api = Qsci.QsciAPIs(self.sqlLexer)

        templates = {}

        for name in ["default.yaml", "user.yaml"]: #default-netezza.yaml, user-netezza.yaml
            if os.path.exists("files/templates/%s" % name):
                items = yaml.load(open("files/templates/%s" % name))

                if items != None:
                    for i in items:
                        templates[i] = items[i]

        for i in templates:
            self.api.add(templates[i])

        for i in tables:
            self.api.add(i)

        self.api.prepare()
        self.sqlLexer.setAPIs(self.api)
        self.setLexer(self.sqlLexer)

        self.setAutoCompletionThreshold(2)
        self.setAutoCompletionSource(Qsci.QsciScintilla.AcsAPIs)
        self.setAutoCompletionCaseSensitivity(False)
        self.setAutoCompletionReplaceWord(True)
        self.setAutoCompletionFillupsEnabled(True)
        #self.setAutoCompletionShowSingle(True)


    def wheelEvent(self, event):
        if event.modifiers() == QtCore.Qt.ControlModifier:
            if event.delta() > 0:
                self.zoomIn()
            else:
                self.zoomOut()
        else:
            vertical = self.verticalScrollBar()
            vertical.setValue(vertical.value() - int(event.delta() / 20))

class Table(QtGui.QTableView):
    def __init__(self, parent=None):
        super(Table, self).__init__(parent)

        self.setSortingEnabled(True)
        self.setFont(getFont(8))
        self.horizontalHeader().setVisible(True)
        self.horizontalHeader().setCascadingSectionResizes(True)
        self.horizontalHeader().setDefaultSectionSize(90)
        self.horizontalHeader().setSortIndicatorShown(True)
        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(True)
        self.setWordWrap(True)
        self.verticalHeader().setDefaultSectionSize(20)
        self.verticalHeader().setMinimumSectionSize(16)
        #self.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers) #disable editing

        shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+C"), self, self.copytoclipbord)
        shortcut.setContext(QtCore.Qt.WidgetShortcut)


    def copytoclipbord(self):
        print "copytoclipbord"
        try:
            selection = self.selectionModel()
            indexes = selection.selectedIndexes()

            columns = indexes[-1].column() - indexes[0].column() + 1
            rows = len(indexes) / columns

            textTable = [[""] * columns for i in xrange(rows)]

            for i, index in enumerate(indexes):
                textTable[i % rows][i / rows] = unicode(self.model().data(index).toString())

            headerText = "\t".join((unicode(self.model().headerData(i, QtCore.Qt.Horizontal).toString()) for i in range(indexes[0].column(), indexes[-1].column() + 1)))
            text = "\n".join(("\t".join(i) for i in textTable))
            setClipboard(headerText + "\n" + text)

        except Exception as exc:
                warningMessage("Error copy to clipbord", unicode(exc.args))



class Script(QtGui.QWidget):
    def __init__(self, parent=None, conn=None):
        super(Script, self).__init__(parent)
        #   sql tab
        self.connection = parent
        self.alias = {}

        self.saveTo = None
        self.query = []
        self.fetchedall = True
        self.fetchednum = 0
        self.fetchto = 0
        self.model = QtGui.QStandardItemModel(0, 0)

        self.horizontalLayout = QtGui.QHBoxLayout(self)
        self.horizontalLayout.setSpacing(1)
        self.horizontalLayout.setMargin(1)
        #       text
        self.editor = Editor(self)
        self.editor.setautocomplete(self.connection.catalog.keys())
        QtCore.QObject.connect(self.editor, QtCore.SIGNAL("userListActivated(int,QString)"), self.userlistselected)

        # ===============================================
        self.table = Table(self)
        QtCore.QObject.connect(self.table.verticalScrollBar(), QtCore.SIGNAL("valueChanged(int)"), self.maybefetchmore)

        # layout
        self.splitter = QtGui.QSplitter(self)
        self.splitter.addWidget(self.editor)
        self.splitter.addWidget(self.table)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 2)
        self.horizontalLayout.addWidget(self.splitter)

        self.setLayout(self.horizontalLayout)


    def searcheditor(self):
        dialog = FindDialog(self)
        dialog.exec_()

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


    def getalias(self):
        self.alias = dict([(i.upper(),i.upper()) for i in self.connection.catalog])

        # create a set of tables that appear in sql (for regex)
        sql = self.editor.getsql().upper()
        words = set(re.split("\s", sql))
        searchFor = words & set([i.upper() for i in self.connection.catalog])
        regex = re.compile("|".join(("%s\s+a?s?\s?[\w\_]+" % re.escape(i) for i in searchFor)), re.IGNORECASE)

        for line in sql.splitlines():
            for newAlias in re.findall(regex, line):
                name, alias = re.split("\s|as", newAlias)
                if alias not in keywords:
                    self.alias[alias] = name

    def showcolumnautocomplete(self):
        columns = []
        self.getalias()

        # get string till the first space or newline
        x, y = self.editor.getCursorPosition()
        self.editor.findFirst("[\s\n]", True, False, False, False, False, x, y, False)
        x2, y2 = self.editor.getCursorPosition()

        tempAlias, tempColumn = self.editor.getselection(x, y2, x, y).upper().split(".")

        if tempAlias in self.alias:
            tableName = unicode(self.alias[tempAlias])
            columns = self.connection.catalog[tableName]["COLUMNS"].keys()

            if len(columns) == 0:
                print "GET columns catalog from DB!"
                self.connection.catalog[tableName]["COLUMNS"] = {}
                for c in self.connection.cursor.columns(table=tableName):
                    self.connection.catalog[tableName]["COLUMNS"][c[3]] = (c[6], c[7])
                # workaround.. cuz of casesensitivity..
                for c in self.connection.cursor.columns(table=tableName.lower()):
                    self.connection.catalog[tableName]["COLUMNS"][c[3]] = (c[6], c[7])

                self.connection.savecatalog()

                columns = self.connection.catalog[tableName]["COLUMNS"].keys()

        self.editor.setCursorPosition(x, y)

        if len(columns) > 0:
            self.editor.showUserList(1, sorted(columns))

    def showautocomplete(self):
        # check if user want colomn help. if he typed "." before.
        line, index = self.editor.getCursorPosition()

        if self.editor.getselection(line, index - 1, line, index) == ".":
            self.showcolumnautocomplete()
        else:
            self.editor.showUserList(4, sorted(self.connection.catalog.keys()))

    def userlistselected(self, i, s):
        print i, s

        x, y = self.editor.getCursorPosition()
        self.editor.findFirst("[\.\s\n]", True, False, False, False, False, x, y, False)
        x2, y2 = self.editor.getCursorPosition()

        self.editor.setSelection(x, y2, x, y)
        self.editor.replace(s)
        self.editor.setCursorPosition(x, y + (len(s) - (y - y2)))

    def open(self, path):
        self.editor.setText(open(path).read())
        self.saveTo = path

    def savefile(self, path):
        open(path, "w").write(unicode(self.editor.text()).encode("UTF-8"))
        self.saveTo = path

    def printmessage(self, table):
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
        sqlparsed = self.editor.getparsedsql()
        # Reconnect
        if not self.connection.conn:
            self.connection.openconnection()

        if len(sqlparsed) > 0:
            if len(sqlparsed) == 1 and sqlparsed[0].startswith('SELECT'):
                self.locktab()
                self.executeThread = ExecuteThread(self)
                self.connect(self.executeThread, QtCore.SIGNAL('finished()'), self.postexecute)
                self.executeThread.start()
            else:
                self.executemany()


    def executemany(self):
        sqlparsed = self.editor.getparsedsql()

        self.fetchedall = True
        self.locktab()
        self.executemanythread = ExecuteManyThread(self)
        self.connect(self.executemanythread, QtCore.SIGNAL('executed'), self.executed)
        self.connect(self.executemanythread, QtCore.SIGNAL('finished()'), self.postexecutemany)
        self.executemanythread.start()

    def executed(self):
        self.printmessage(self.executemanythread.toprint())

    def stopexecute(self):
        print "stopexecute"
        self.executemanythread.stop()

    def postexecutemany(self):
        print "postexecutemany"
        self.unlocktab()

    def executetofile(self, path):
        try:
            self.query = self.connection.cursor.execute(self.editor.getsql())
            o = open(path, "w", 5000)

            if self.query:
                # HEADER
                bazz = u";".join([i[0] for i in self.query.description])
                o.write(bazz.encode('UTF-8') + u";\n")

                for row in self.query:
                    #print row
                    line = u"%s;\n" % u";".join(map(unicode, row))
                    o.write(line.encode('UTF-8'))
            o.close()
        except Exception as exc:
                warningMessage("Error executing to file!", unicode(exc.args))

    def locktab(self):
        self.connection.setDisabled(True)
        #self.connTab.seticon("files/icons/DeletedIcon.ico")

    def showworking(self):
        print "Pixmap"
        pixmap = QtGui.QPixmap("files/icons/working.gif");
        s = QtGui.QSplashScreen(self, pixmap)
        print "SHOW"
        s.show()
        s.showMessage("Working")

    def postexecute(self):
        self.unlocktab()

        if self.executeThread.result.status == "OK":
            self.query = self.executeThread.result.query
            self.columnsLen = len(self.query.description)
            # print types
            for i in self.query.description:
                print "%s: '%s'" % (i[0], i[1])
            # New model
            self.model = QtGui.QStandardItemModel(0, self.columnsLen)
            # Header
            for index, column in enumerate(self.query.description):
                self.model.setHeaderData(index, QtCore.Qt.Horizontal, column[0], role=0)

            self.fetchednum = 0
            self.fetchto = 0
            self.fetchedall = False

            self.table.setModel(self.model)
            self.fetchMore()
        else:
            columns = ["S", "ROWS", "TIME (sec)", "ERROR_CODE", "ERROR", "SQL"]
            printTable = [columns]
            printTable.append(self.executeThread.result.toarray())
            self.printmessage(printTable)

    def unlocktab(self):
        self.connection.setDisabled(False)

    def maybefetchmore(self, value):
        if self.fetchedall == False:
            vertical = self.table.verticalScrollBar()
            if vertical.value() +  vertical.pageStep() > vertical.maximum() and vertical.maximum() != 0:
                self.fetchMore()

    def fetchMore(self):
        self.fetchto += 256
        self.model.insertRows(self.fetchednum, 256, QtCore.QModelIndex())

        # PYODBC
        for row in self.query:
            for j in xrange(self.columnsLen):
                self.model.setData(self.model.index(self.fetchednum, j, QtCore.QModelIndex()), convertforQt(row[j]), role=0)
                if isnumber(row[j]):
                    self.model.setData(self.model.index(self.fetchednum, j, QtCore.QModelIndex()), QtCore.QVariant(QtCore.Qt.AlignRight + QtCore.Qt.AlignVCenter) , QtCore.Qt.TextAlignmentRole)

            self.fetchednum += 1

            if self.fetchednum >= self.fetchto:
                break
        else:
            self.fetchedall = True

        self.model.removeRows(self.fetchednum, self.model.rowCount() - (self.fetchednum), QtCore.QModelIndex())
        self.table.resizeColumnsToContents()

        self.connection.showtooltip("Rows: %s" % self.model.rowCount())


class Connection(QtGui.QWidget):
    def __init__(self, parent=None, connName='', password="", connSettings=None):
        super(Connection, self).__init__(parent)

        # SQLITE
        self.connSettings = connSettings
        self.name = connName
        self.password = password

        self.openconnection()
        # AUTO COMPLETE
        self.loadcatalog()
        self.seticon()

        # conn tab
        self.verticalLayout_3 = QtGui.QVBoxLayout()
        self.verticalLayout_3.setSpacing(2)
        self.verticalLayout_3.setContentsMargins(1, 4, 1, 2)
        #   CHILD TABS
        self.scripttabs = QtGui.QTabWidget()
        self.scripttabs.setFont(getFont(11))
        self.scripttabs.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.scripttabs.setTabPosition(QtGui.QTabWidget.South)
        self.scripttabs.setTabShape(QtGui.QTabWidget.Triangular)
        self.scripttabs.setTabsClosable(True)
        self.scripttabs.setMovable(True)
        # layout
        self.verticalLayout_3.addWidget(self.scripttabs)
        self.setLayout(self.verticalLayout_3)

    def openconnection(self):
        try:
            self.conn = pyodbc.connect('DSN=%s;PWD=%s' % (self.name, self.password))
            self.conn.autocommit = True
            self.cursor = self.conn.cursor()
        except Exception as exc:
            self.conn = None
            warningMessage("Error opening connection: %s" % connName, unicode(exc.args))

    def seticon(self, path=None):
        if path == None:
            if self.conn:
                self.icon = QtGui.QIcon("files/icons/NormalIcon.ico") #files/icons/working.gif
            else:
                self.icon = QtGui.QIcon("files/icons/ModifiedIcon.ico")
        else:
            print "path != None"
            self.icon = QtGui.QIcon(path)

    def getcatalog(self):
        catalog = {}
##        if os.path.exists("files/cache/%s.sqlite" % self.name):
##            catalog2 = sqlite3.connect("files/cache/%s.sqlite" % self.name)
##        else:
##            catalog2 = sqlite3.connect("files/cache/%s.sqlite" % self.name)
##

        print "START CATALOG LOAD: %s" % time.ctime()

        for i in self.cursor.tables(schema=self.connSettings.get('schema', '%')):
            #print i
            if i.table_name != None:
                catalog[i.table_name.upper()] = dict([("TYPE", i.table_type), ("COLUMNS", dict())])

        print "END CATALOG LOAD: %s" % time.ctime()

        return catalog

    def reloadcatalog(self):
        self.catalog = self.getcatalog()
        self.savecatalog()

    def savecatalog(self):
        pickle.dump(self.catalog, open("files/cache/%s.pickle" % self.name, "w"))

    def loadcatalog(self):
        if os.path.exists("files/cache/%s.pickle" % self.name):
            self.catalog = pickle.load(open("files/cache/%s.pickle" % self.name))
        else:
            self.reloadcatalog()

    def showcatalog(self):
        script = self.scripttabs.currentWidget()
        columns = ["TABLE/COLUMN", "TYPE", "LENGTH"]
        printTable = [columns]

        for table in sorted(self.catalog):
            printTable.append([table, self.catalog[table]["TYPE"], ""])
            columns = self.catalog[table]["COLUMNS"]
            for column in columns:
                printTable.append(["\t%s" % column, 0, 0])

            printTable.append(["", "", ""])
        script.printmessage(printTable)

    def showtooltip(self, text):
        p = self.pos()
        p.setX(p.x() + (self.width() / 2))
        p.setY(p.y() + (self.height() - 10))
        QtGui.QToolTip.showText(p, text)

    def openfile(self, path):
        self.scripttabs.currentWidget().editor.setText(open(path).read().decode("UTF-8"))
        self.scripttabs.currentWidget().saveTo = path
        self.scripttabs.setTabText(self.scripttabs.currentIndex(), QtGui.QApplication.translate("MainWindow", path.split("/")[-1], None, QtGui.QApplication.UnicodeUTF8))

    def newscript(self, path=None):
        path = unicode(path)
        script = Script(self)
        self.scripttabs.addTab(script, "")
        self.scripttabs.setTabText(self.scripttabs.indexOf(script), QtGui.QApplication.translate("MainWindow", "Sql script", None, QtGui.QApplication.UnicodeUTF8))
        self.scripttabs.setCurrentWidget(script)

        if path != None:
            try:
                self.openfile(path)
                self.scripttabs.setTabText(self.scripttabs.indexOf(script), QtGui.QApplication.translate("MainWindow", path.split("/")[-1], None, QtGui.QApplication.UnicodeUTF8))
                # Save for recent
                if os.path.exists("files/recent/%s.pickle" % self.name):
                    recent = pickle.load(open("files/recent/%s.pickle" % self.name))
                else:
                    recent = {}

                recent[path] = int(time.time())
                pickle.dump(recent, open("files/recent/%s.pickle" % self.name, "w"))

            except Exception as exc:
                print "Error opening file: %s" % path, unicode(exc.args)

        if self.scripttabs.count() < 2:
            self.scripttabs.tabBar().hide()
        else:
            self.scripttabs.tabBar().show()

    def saveworkspace(self):
        workspace = []
        # If conn dir is in sql folder
        if not os.path.exists(u"files/sql/%s" % (self.name)):
            os.mkdir(u"files/sql/%s" % (self.name))
        # save
        for scriptIndex in range(0, self.scripttabs.count()):
            script = self.scripttabs.widget(scriptIndex)
            if script.saveTo == None:
                path = u"files/sql/%s/%s_%s.sql" % (self.name, "".join(map(str, time.localtime()[:3])), randint(0, 1000000))
            else:
                path = unicode(script.saveTo)

            script.savefile(path)
            workspace.append(path)

        yaml.dump(workspace, open("files/workspace/%s.yaml" % self.name, "w"))

    def openworkspace(self):
        if os.path.exists("files/workspace/%s.yaml" % self.name):
            try:
                workspace = yaml.load(open("files/workspace/%s.yaml" % self.name))
            except Exception as exc:
                warningMessage("Error at loading workspace!", unicode(exc.args))
                workspace = list()

            if workspace != None:
                for path in workspace:
                    print "\t", path
                    self.newscript(path)
        else:
            self.newscript()



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