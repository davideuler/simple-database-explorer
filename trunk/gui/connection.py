from PyQt4 import QtCore, QtGui, Qsci
import yaml
from yaml.parser import ParserError
from elements import *
import pyodbc
#from pyodbc import dataSources

class Connection(QtGui.QWidget):
    """
        Implement all the logic for one single connection
        - connect, reconnect
        - catalog load and save
        - workspace per connection...
        - managing scripts
    """
    def __init__(self, parent=None, connName='', password="", connSettings=None):
        super(Connection, self).__init__(parent)

        # SQLITE
        self.connSettings = connSettings
        self.name = connName
        self.password = password

        self.openconnection()
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

        # AUTO COMPLETE
        self.loadcatalog()
        self.seticon()

    def openconnection(self):
        try:
            self.conn = pyodbc.connect('DSN=%s;PWD=%s' % (self.name, self.password))
            self.conn.autocommit = True
            self.cursor = self.conn.cursor()
        except Exception as exc:
            self.conn = None
            warningMessage("Error opening connection: %s" % self.name, unicode(exc.args))

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
        #print  self.cursor.tables(schema=self.connSettings.get('schema', '%'))
        for i in self.cursor.tables(schema=self.connSettings.get('schema', '%')):
            #print i
            if i.table_name != None:
                catalog[i.table_name.upper()] = dict([("TYPE", i.table_type), ("COLUMNS", dict())])

        print "END CATALOG LOAD: %s" % time.ctime()

        return catalog

    def reloadcatalog(self):
        self.catalog = self.getcatalog()
        self.savecatalog()
        # rebuild editor API for autocomplete
        for scriptIndex in range(0, self.scripttabs.count()):
            self.scripttabs.widget(scriptIndex).editor.setautocomplete(self.catalog.keys())

    def savecatalog(self):
        pickle.dump(self.catalog, open("files/cache/%s.pickle" % self.name, "w"))

    def loadcatalog(self):
        if os.path.exists("files/cache/%s.pickle" % self.name):
            self.catalog = pickle.load(open("files/cache/%s.pickle" % self.name))
        else:
            self.reloadcatalog()

    def showcatalog(self):
        print "showcatalog"
        headers = ["DB Tree"]
        catalog = self.cursor.tables(schema=self.connSettings.get('schema', '%'))

        #treeWidget = CatalogTree(catalog)
        #treeWidget.model().headers = headers

        script = self.scripttabs.currentWidget()
        script.catalogtree.loadcatalog(catalog)
        #script.splitter.addWidget(self.treeWidget)
        #script.table = self.treeWidget
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