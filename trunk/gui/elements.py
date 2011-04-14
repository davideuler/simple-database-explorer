from PyQt4 import QtCore, QtGui, Qsci
import yaml
from yaml.parser import ParserError
import pickle
#import time
import math
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
from cataloginfo import CatalogTree
from datetime import datetime

class QueryResult:
    """
        This class saves one query result, status, sql, time and possible errors
    """
    def __init__(self, query, status, sql="", rows=-1, starttime=datetime.now(), endtime=datetime.now(), error=""):
        self.query = query
        self.status = status
        self.rows = rows

        self.starttime = starttime
        self.endtime = endtime
        self.error = error
        self.sql = sql

    def gettime(self):
        self.executiontime = self.endtime - self.starttime
        return "%s.%s" % (self.executiontime.seconds, int(self.executiontime.microseconds / 100))

    def toarray(self):
        """ function to print the query result in the gui table with printMessage """
        return (self.status, self.rows, self.starttime.strftime('%H:%M:%S'), self.gettime(), self.error, self.sql)

class ExecuteManyThread(QtCore.QThread):
    """ runs a thread with multiple sql statements and stores the results in a list of QueryResults.
        - each time a sql is executed it emits a 'executed' signal that print the currently executed statements.
        - when all the sql statements are executed a 'finished' signal tells the gui to unlock the gui.

        We dont call the printMessage directly cuz of Qt limitation of creating childs in another thread.
        Signals are the adviced approch to work around this limitation.
    """
    def __init__(self, parent=None):
       QtCore.QThread.__init__(self, parent)
       self.script = parent
       self.results = []
       self.alive = 1

    def run(self):
        self.sqlparsed = self.script.editor.getparsedsql()

        for sql in self.sqlparsed:
            if self.alive == 1:
                try:
                    startime = datetime.now()
                    query = self.script.connection.cursor.execute(sql)
                    result = QueryResult(query, "OK", sql, query.rowcount, startime, datetime.now())
                    self.results.append(result)

                except Exception as exc:
                    result = QueryResult(None, "ERROR", sql, -1, startime, datetime.now(), str(exc))
                    self.results.append(result)
                finally:
                    self.emit(QtCore.SIGNAL('executed'))
            else:
                break

        self.emit(QtCore.SIGNAL('finished'))

    def stop(self):
       self.alive = 0

class ExecuteManyModel(QtGui.QStandardItemModel):
    def data(self, index, role=0):
        value = super(ExecuteManyModel, self).data(index, role)
        cellvalue = super(ExecuteManyModel, self).data(index)

        if role == QtCore.Qt.TextColorRole and index.column() == 0:
            if cellvalue == "OK":
                return QtGui.QColor(QtCore.Qt.black)
            else:
                return QtGui.QColor(QtCore.Qt.white)

        if role == QtCore.Qt.BackgroundColorRole and index.column() == 0:
            if cellvalue == "OK":
                return QtGui.QColor("#B2EC5D")
            else:
                return QtGui.QColor("#FF3300")

        return value


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

        # catalog tree
        headers = ["DB Tree"]
        self.catalogtree = CatalogTree([["", "", "", "", ""]])
        self.catalogtree.model().headers = headers

        # sql editor
        self.editor = Editor(self)
        self.editor.setautocomplete(self.connection.catalog)
        self.findDialog = FindDialog(self)
        QtCore.QObject.connect(self.editor, QtCore.SIGNAL("userListActivated(int,QString)"), self.userlistselected)

        # table
        self.table = Table(self)
        QtCore.QObject.connect(self.table.verticalScrollBar(), QtCore.SIGNAL("valueChanged(int)"), self.maybefetchmore)

        #script = self.scripttabs.currentWidget()
        #script.splitter.addWidget(self.treeWidget)
        # layout
        self.splitter = QtGui.QSplitter(self)
        #self.splitter.addWidget(self.catalogtree)
        self.splitter.addWidget(self.editor)
        self.splitter.addWidget(self.table)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 3)
        #self.splitter.setStretchFactor(2, 4)
        #self.splitter.re
        self.horizontalLayout.addWidget(self.splitter)

        self.setLayout(self.horizontalLayout)


    def showfinddialog(self):
        self.findDialog.show()

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
        self.alias = dict([(i[2].upper(), i[2].upper()) for i in self.connection.catalog])

        # create a set of tables that appear in sql (for regex)
        sql = self.editor.getsql().upper()
        words = set(re.split("\s", sql))
        searchFor = words & set([i[2].upper() for i in self.connection.catalog])
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

    def executemany(self):
        sqlparsed = self.editor.getparsedsql()

        if not self.connection.conn:
            self.connection.openconnection()

        if len(sqlparsed) > 0:
            header = ["S", "ROWS", "START", "TIME", "ERROR", "SQL"]

            self.fetchedall = True
            self.locktab()
            self.executemanythread = ExecuteManyThread(self)
            self.connect(self.executemanythread, QtCore.SIGNAL('executed'), self.executed)
            self.connect(self.executemanythread, QtCore.SIGNAL('finished()'), self.postexecutemany)

            # define model
            self.fetchednum = 0
            self.executemanymodel = ExecuteManyModel(0, len(header), self)
            for i, name in enumerate(header):
                self.executemanymodel.setHeaderData(i, QtCore.Qt.Horizontal, name)

            self.table.setModel(self.executemanymodel)
            self.table.setWordWrap(True)
            self.table.resizeColumnsToContents()

            self.executemanythread.start()

    def executed(self):
        result = self.executemanythread.results[self.fetchednum].toarray()
        self.executemanymodel.insertRow(self.fetchednum, QtCore.QModelIndex())

        for j, column in enumerate(result):
            self.executemanymodel.setData(self.executemanymodel.index(self.fetchednum, j, QtCore.QModelIndex()), column, role=0)

        # scrool table
        vertical = self.table.verticalScrollBar()
        vertical.setFocus()
        vertical.setValue(vertical.value() + 5)

        #print self.fetchednum, type(self.fetchednum), math.log(self.fetchednum + 1, 2)
        if math.log(self.fetchednum + 1, 2).is_integer():
            self.table.resizeColumnsToContents()

        self.fetchednum += 1

    def stopexecute(self):
        print "stopexecute"
        self.executemanythread.stop()

    def is_singleselect(self):
        try:
            sqlparsed = self.executemanythread.sqlparsed
            if len(sqlparsed) == 1 and sqlparsed[0].upper().strip().startswith('SELECT'):
                if self.executemanythread.results[0].status == "OK":
                    return True
        except:
            return False

    def postexecutemany(self):
        print "postexecutemany"
        self.unlocktab()
        self.table.resizeColumnsToContents()

        if self.is_singleselect():
            self.postexecute()


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
        palette = QtGui.QPalette()


        brush = QtGui.QBrush(QtGui.QColor("#E3F6CE"))
        brush.setStyle(QtCore.Qt.SolidPattern)

        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Base, brush)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Window, brush)
        self.table.setPalette(palette)
        #self.connTab.seticon("files/icons/DeletedIcon.ico")

    def showworking(self):
        print "Pixmap"
        pixmap = QtGui.QPixmap("files/icons/working.gif");
        s = QtGui.QSplashScreen(self, pixmap)
        print "SHOW"
        s.show()
        s.showMessage("Working")

    def postexecute(self):
        self.query = self.executemanythread.results[0].query
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

    def unlocktab(self):

        self.connection.setDisabled(False)
        self.editor.setFocus()


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


class Editor(Qsci.QsciScintilla):
    """
        Class thats add extra functions to the Qt Scintilla implementation.
         - some extra fuctions to make editing easier
         - some user friendly functionalyt: comment, join split lines, ctrl+whell mouse zoom
         - we set autocomplete from templates and tables names
    """
    def __init__(self, parent=None):
        super(Editor, self).__init__(parent)

        #self.setToolTip("SQL editor")
        #self.setWhatsThis("")
        self.setObjectName("sqleditor")
        self.setInputMethodHints(QtCore.Qt.ImhUppercaseOnly)
        self.setFont(getFont(12))
        self.setUtf8(True)
        self.setWrapMode(Qsci.QsciScintilla.WrapWord)
        #self.setMarginsFont(getFont(7))
        ## line numbers
        #self.setMarginWidth(0, fm.width( "0000" ) + 2)
        #self.setMarginLineNumbers(2, True)
        self.setCaretLineVisible(False)
        ## Folding visual : we will use boxes, Braces matching
        self.setFolding(Qsci.QsciScintilla.BoxedTreeFoldStyle)
        self.setFoldMarginColors(QtGui.QColor("#006B3C"),QtGui.QColor("#01796F"))
        self.setBraceMatching(Qsci.QsciScintilla.SloppyBraceMatch)
        ## Editing line color
        self.setCaretLineVisible(True)
        self.setCaretLineBackgroundColor(QtGui.QColor("#B2EC5D"))
        ## Marker (bookmarks)
        self.setMarkerBackgroundColor(QtGui.QColor("#663854"))
        self.setMarkerForegroundColor(QtGui.QColor("#006B3C"))
        ## Line numbers margin
        self.setMarginsBackgroundColor(QtGui.QColor("#F8F4FF"))
        self.setMarginsForegroundColor(QtGui.QColor("#663854"))
        ## Indentation
        self.setAutoIndent(True)
        self.setIndentationWidth(4)
        self.setIndentationGuides(1)
        self.setIndentationsUseTabs(0)
        unindentshortcut = QtGui.QShortcut(QtGui.QKeySequence("Shift+Tab"), self, self.unindenttext)
        unindentshortcut.setContext(QtCore.Qt.WidgetShortcut)

        self.setCallTipsStyle(Qsci.QsciScintilla.CallTipsContext)
        #self.setCallTipsStyle(QsciScintilla.CallTipsNoContext)
        self.setCallTipsVisible(False)
        self.setautocomplete()

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
        return [i.strip() for i in sqlparse.split(self.getsql()) if i != '']

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

    def tabletoapi(self, tableline):
        typemapping = {  'ALIAS': 1,
                         'GLOBAL TEMPORARY': 2,
                         'LOCAL TEMPORARY': 3,
                         'SYNONYM': 4,
                         'SYSTEM TABLE': 5,
                         'TABLE': 6,
                         'VIEW': 7}

        table = ".".join([i.upper() for i in tableline[:-2] if i != 'None'])
        return table + "?%s" % typemapping.get(tableline[-2], 0)

    def setautocomplete(self, tables=[]):
        self.sqlLexer = Qsci.QsciLexerSQL(self) #QsciLexerPython
        self.api = Qsci.QsciAPIs(self.sqlLexer)

        templates = {}

        for name in ["default.yaml", "user.yaml"]: #default-netezza.yaml, user-netezza.yaml
            if os.path.exists("files/templates/%s" % name):
                items = yaml.load(open("files/templates/%s" % name))

                if items != None:
                    for i in items:
                        templates[i] = items[i]
                        templates[i.lower()] = items[i].lower()
            else:
                open("files/templates/%s" % name, "w").write('')

        for i in templates:
            self.api.add(templates[i])

        for i in tables:
            #self.api.add(self.tabletoapi(i))
            self.api.add(i[2])

        #self.api.add("STG_CRM.INFORMAT.STG_PARTY?10")
        #self.api.add("STG_CRM.INFORMAT.STG_PARTY?10")
        #self.api.add("MAX?4() -> int")

        self.api.prepare()
        self.sqlLexer.setAPIs(self.api)
        self.setLexer(self.sqlLexer)

        self.setAutoCompletionThreshold(2)
        self.setAutoCompletionSource(Qsci.QsciScintilla.AcsAPIs)
        self.setAutoCompletionCaseSensitivity(False)
        self.setAutoCompletionReplaceWord(True)
        self.setAutoCompletionFillupsEnabled(False)
        self.setAutoCompletionShowSingle(False)


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
    """  QTableView with default settings and copytoclipbord function """
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
        self.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers) #disable editing

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



