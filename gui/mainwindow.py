from PyQt4 import QtCore, QtGui, Qsci
import yaml
from yaml.parser import ParserError
import os
import time
from random import randint
from elements import *
import datetime
from pyodbc import dataSources
from subprocess import Popen

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(808, 600)
        # SETTINGS
        self.sett = self.loadsettings()

        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("files/icons/sdbe.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MainWindow.setWindowIcon(icon)

        self.centralWidget = QtGui.QWidget(MainWindow)
        self.centralWidget.setObjectName("centralWidget")
        self.vboxlayout = QtGui.QVBoxLayout(self.centralWidget)
        self.vboxlayout.setSpacing(0)
        self.vboxlayout.setContentsMargins(1, 1, 1, 2)
        self.vboxlayout.setObjectName("vboxlayout")
        # MAIN TABS
        self.conntabs = QtGui.QTabWidget(self.centralWidget)
        self.conntabs.setFont(getFont(12))
        self.conntabs.setContextMenuPolicy(QtCore.Qt.DefaultContextMenu)
        self.conntabs.setDocumentMode(False)
        self.conntabs.setTabsClosable(True)
        self.conntabs.setMovable(True)
        self.conntabs.setObjectName("conntabs")
        # conn tab
        self.vboxlayout.addWidget(self.conntabs)

        MainWindow.setCentralWidget(self.centralWidget)
        # MENUBAR
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 808, 20))
        self.menubar.setFont(getFont(7))
        self.fileMenu = QtGui.QMenu(self.menubar)
        self.editMenu = QtGui.QMenu(self.menubar)
        self.actionsMenu = QtGui.QMenu(self.menubar)
        self.navigateMenu = QtGui.QMenu(self.menubar)
        self.settingsMenu = QtGui.QMenu(self.menubar)
        MainWindow.setMenuBar(self.menubar)

        # #####################################
        # ACTIONS
        # #####################################
        def createAction(name, parent, parentName, shortcut, triggered, fontSize=10):
            new = QtGui.QAction(name, parent,
                shortcut=shortcut, triggered=triggered)
            new.setText(QtGui.QApplication.translate(parentName, name, None, QtGui.QApplication.UnicodeUTF8))
            new.setFont(getFont(fontSize))

            return new

        # ==== ==== ==== ==== ==== ==== ==== ====
        # FILE
        # ==== ==== ==== ==== ==== ==== ==== ====
        self.newConnAction = createAction("&New Connection", self, "MainWindow", "Ctrl+N", self.newconnection, 8)
        self.recentAction = createAction("Recent files", self, "MainWindow", "", self.recent, 8)

        self.newSqlAction = createAction("&New script", self, "MainWindow", "Ctrl+Shift+N", self.newscript, 8)
        self.openAction = createAction("&Open script", self, "MainWindow", "Ctrl+O", self.opendialog, 8)
        self.saveAction = createAction("&Save script", self, "MainWindow", "Ctrl+S", self.savedialog, 8)
        self.saveAsAction = createAction("&Save As script", self, "MainWindow", "Ctrl+Shift+S", self.saveasdialog, 8)

        self.fileMenu.addAction(self.newConnAction)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.recentAction)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.newSqlAction)
        self.fileMenu.addAction(self.openAction)
        self.fileMenu.addAction(self.saveAction)
        self.fileMenu.addAction(self.saveAsAction)

        # ==== ==== ==== ==== ==== ==== ==== ====
        # EDIT
        # ==== ==== ==== ==== ==== ==== ==== ====
        #self.copyAction = createAction("&Copy", self, "MainWindow", "Ctrl+C", self.copy, 8)
        self.searcheditorAction = createAction("&Find and Replace", self, "MainWindow", "Ctrl+F", self.searcheditor, 8)
        self.formatsqlAction = createAction("&Format SQL", self, "MainWindow", "Ctrl+Shift+F", self.formatsql, 8)
        self.commentAction = createAction("&Comment selection", self, "MainWindow", "Ctrl+B", self.comment, 8)
        self.joinlinesAction = createAction("&Join selected Lines", self, "MainWindow", "Ctrl+J", self.joinlines, 8)
        self.splitlinesAction = createAction("&Split selected Lines", self, "MainWindow", "Ctrl+I", self.splitlines, 8)

        #self.editMenu.addAction(self.copyAction)
        self.editMenu.addSeparator()
        self.editMenu.addAction(self.searcheditorAction)
        self.editMenu.addAction(self.formatsqlAction)
        #self.commentAction.setShortcutContext(QtCore.Qt.WidgetShortcut)
        self.editMenu.addAction(self.commentAction)
        self.editMenu.addSeparator()
        self.editMenu.addAction(self.joinlinesAction)
        self.editMenu.addAction(self.splitlinesAction)

        # ==== ==== ==== ==== ==== ==== ==== ====
        # ACTION
        # ==== ==== ==== ==== ==== ==== ==== ====
        self.executeAction = createAction("&Execute", self, "MainWindow", "Alt+X", self.execute, 8)
        self.stopexecuteAction = createAction("&Stop Execute", self, "MainWindow", "Ctrl+Q", self.stopexecute, 8)
        #self.stopexecuteAction = createAction("&Stop Execute", self, "MainWindow", "Esc", self.stopexecute, 8)
        self.executetofileAction = createAction("&Execute to file", self, "MainWindow", "Alt+Ctrl+X", self.executetofile, 8)
        #self.copytoclipbordAction = createAction("&Copy table to clipbord", self, "MainWindow", "Alt+C", self.copytoclipbord, 8)
        self.showautocompleteAction = createAction("&Auto Complete", self, "MainWindow", "Ctrl+Space", self.showautocomplete, 8)
        self.autoColumnCompleteAction = createAction("&Auto Column Complete", self, "MainWindow", "Alt+K", self.showcolumnautocomplete, 8)
        self.reloadCatalogAction = createAction("&Reload Catalog", self, "MainWindow", "Ctrl+R", self.reloadcatalog, 8)
        self.showCatalogAction = createAction("&Show Catalog", self, "MainWindow", "Ctrl+Shift+R", self.showcatalog, 8)

        self.actionsMenu.addAction(self.executeAction)
        self.actionsMenu.addAction(self.stopexecuteAction)
        #self.actionsMenu.addAction(self.stopexecuteAction)
        self.actionsMenu.addAction(self.executetofileAction)
        #self.actionsMenu.addAction(self.copytoclipbordAction)

        self.actionsMenu.addSeparator()
        self.actionsMenu.addAction(self.showautocompleteAction)
        #self.actionsMenu.addAction(self.autoColumnCompleteAction)
        self.actionsMenu.addSeparator()
        self.actionsMenu.addAction(self.reloadCatalogAction)
        self.actionsMenu.addAction(self.showCatalogAction)
        # ==== ==== ==== ==== ==== ==== ==== ====
        # NAVIGATE
        # ==== ==== ==== ==== ==== ==== ==== ====
        #self.toConsoleAction = createAction("&Console", self, "MainWindow", "Alt+I", self.newconnection, 8)
        self.toeditorAction = createAction("&SQL Editor", self, "MainWindow", "Alt+M", self.toeditor, 8)
        self.leftconnectionAction = createAction("&Left Connection", self, "MainWindow", "Alt+Down", self.leftconnection, 8)
        self.rightconnectionAction = createAction("&Right Connection", self, "MainWindow", "Alt+Up", self.rightconnection, 8)
        self.leftscriptAction = createAction("L&eft SQL script", self, "MainWindow", "Alt+Left", self.leftscript, 8)
        self.rightscriptAction = createAction("R&ight SQL script", self, "MainWindow", "Alt+Right", self.rightscript, 8)

        self.leftpantableAction = createAction("Le&ft pan Table", self, "MainWindow", "Alt+4", self.leftpantable, 8)
        self.rightpantableAction = createAction("Ri&ght pan Table", self, "MainWindow", "Alt+6", self.rightpantable, 8)
        self.downpantableAction = createAction("Down pan Table", self, "MainWindow", "Alt+2", self.downpantable, 8)
        self.uppantableAction = createAction("Up pan Table", self, "MainWindow", "Alt+8", self.uppantable, 8)

        self.defaultStretchAction = createAction("Default Stretch Table", self, "MainWindow", "Alt+*", self.defaultstretch, 8)
        self.expandTableAction = createAction("Expand Table", self, "MainWindow", "Alt++", self.expandtable, 8)
        self.shrinkTableAction = createAction("Shrink Table", self, "MainWindow", "Alt+-", self.shrinktable, 8)


        #self.navigateMenu.addAction(self.toConsoleAction)
        self.navigateMenu.addAction(self.toeditorAction)
        self.navigateMenu.addSeparator()
        self.navigateMenu.addAction(self.leftconnectionAction)
        self.navigateMenu.addAction(self.rightconnectionAction)
        self.navigateMenu.addSeparator()
        self.navigateMenu.addAction(self.leftscriptAction)
        self.navigateMenu.addAction(self.rightscriptAction)
        self.navigateMenu.addSeparator()
        self.navigateMenu.addAction(self.leftpantableAction)
        self.navigateMenu.addAction(self.rightpantableAction)
        self.navigateMenu.addAction(self.downpantableAction)
        self.navigateMenu.addAction(self.uppantableAction)
        self.navigateMenu.addSeparator()
        self.navigateMenu.addAction(self.defaultStretchAction)
        self.navigateMenu.addAction(self.expandTableAction)
        self.navigateMenu.addAction(self.shrinkTableAction)
        #self.navigateMenu.addAction(self.rightpantableAction)
        # ==== ==== ==== ==== ==== ==== ==== ====
        # SETTINGS
        # ==== ==== ==== ==== ==== ==== ==== ====
        self.opensettingsAction = createAction("Open settings", self, "MainWindow", "Ctrl+Alt+S", self.opensettings, 8)
        self.saveSettingsAction = createAction("Save/Reload settings", self, "MainWindow", "", self.saveSettings, 8)
        self.importODBCAction = createAction("Import ODBC connetions into settings", self, "MainWindow", "", self.importODBC, 8)
        self.openODBCmanagerAction = createAction("Open ODBC Manager", self, "MainWindow", "", self.openODBCmanager, 8)

        self.settingsMenu.addAction(self.opensettingsAction)
        self.settingsMenu.addAction(self.saveSettingsAction)
        self.settingsMenu.addSeparator()
        self.settingsMenu.addAction(self.openODBCmanagerAction)
        self.settingsMenu.addAction(self.importODBCAction)

        # MENU
        self.menubar.addAction(self.fileMenu.menuAction())
        self.menubar.addAction(self.editMenu.menuAction())
        self.menubar.addAction(self.actionsMenu.menuAction())
        self.menubar.addAction(self.navigateMenu.menuAction())
        self.menubar.addAction(self.settingsMenu.menuAction())

        self.retranslateUi(MainWindow)
        self.conntabs.setCurrentIndex(0)

        QtCore.QObject.connect(self.conntabs, QtCore.SIGNAL("tabCloseRequested(int)"), self.conntabs.removeTab)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        self.openworkspace()
        #self.statusBar().showMessage('Ready', 2000)
        #self.setToolTip(QtGui.QToolTip())

    def isConnectionFunc(self):
        return isinstance(self.conntabs.currentWidget(), Connection)

    class isConnection(object):
        def __init__(self, f):
            self.f = f

        def __call__(self, *args):
            print "Entering", self.f.__name__
            if self.isConnectionFunc():
                self.f(*args)
            print "Exited", self.f.__name__


    # ==== ==== ==== ==== ==== ==== ==== ====
    # NEW CONN, SQL
    # ==== ==== ==== ==== ==== ==== ==== ====
    def newconnection(self):
        self.sett = self.loadsettings()
        connections = sorted(self.sett.settings['connections'].keys())

        dialog = NewConnectionDialog(self, self.sett.settings['connections'])
        dialog.exec_()
        if dialog.result() == 1:
            connection = unicode(dialog.connectionsComboBox.currentText())
            password = unicode(dialog.passwordEdit.text())

            if dialog.savePassword.isChecked():
                self.sett = self.loadsettings()
                self.sett.settings['connections'].setdefault(connection, {}).setdefault("password", password)
                self.sett.settings['connections'][connection]["password"] = password
                yaml.dump(self.sett.settings, open("settings.yaml", "w"))
                self.sett = self.loadsettings()

            connection = self.opennewconnection(connection, password, False)
            connection.openworkspace()
            self.showtooltip("Connection has been opened.")

    def opennewconnection(self, connName, password="", openNewSql=True):
        connSettings = self.sett.settings['connections'].get(connName, {})
        connection = Connection(parent=self, connName=connName, password=password, connSettings=connSettings)
        self.conntabs.addTab(connection, "")
        self.conntabs.setTabText(self.conntabs.indexOf(connection), QtGui.QApplication.translate("MainWindow", connName, None, QtGui.QApplication.UnicodeUTF8))
        self.conntabs.setTabIcon(self.conntabs.indexOf(connection), connection.icon)

        self.conntabs.setCurrentWidget(connection)

        QtCore.QObject.connect(connection.scripttabs, QtCore.SIGNAL("tabCloseRequested(int)"), connection.scripttabs.removeTab)

        if openNewSql:
            self.newscript()

        return connection

    def recent(self):
        tab = self.conntabs.currentWidget()
        if isinstance(tab, Connection):

            if os.path.exists("files/recent/%s.pickle" % tab.name):
                recent = pickle.load(open("files/recent/%s.pickle" % tab.name))
                item, ok = QtGui.QInputDialog.getItem(self, "Select a recent file...",
                    "Recent:", sorted(recent, key=recent.get, reverse=True), 0, False)

                if ok and item:
                    self.conntabs.currentWidget().newscript(unicode(item))

    def newscript(self, path=None):
        if isinstance(self.conntabs.currentWidget(), Connection):
            self.conntabs.currentWidget().newscript()

    def showtooltip(self, text):
        p = self.pos()
        p.setX(p.x() + self.width() - (len(text) * 9) - 8)
        p.setY(p.y() + (self.height() - 8))
        t = QtGui.QToolTip
        t.setFont(getFont(10))
        t.showText(p, text)

    # ==== ==== ==== ==== ==== ==== ==== ====
    # FILE HANDLING
    # ==== ==== ==== ==== ==== ==== ==== ====
    #@isConnection
    def opendialog(self):
        if isinstance(self.conntabs.currentWidget(), Connection):
            o = QtGui.QFileDialog(self)
            QtCore.QObject.connect(o, QtCore.SIGNAL("fileSelected(QString)"), self.conntabs.currentWidget().newscript)
            o.setAcceptMode(0)
            o.setNameFilter("SQL files (*.sql)");
            o.open()

    def openfile(self, path):
        if isinstance(self.conntabs.currentWidget(), Connection):
            print path
            self.conntabs.currentWidget().openfile(path)

    def savedialog(self):
        if isinstance(self.conntabs.currentWidget(), Connection):
            script = self.conntabs.currentWidget().scripttabs.currentWidget()

            if script.saveTo == None:
                o = QtGui.QFileDialog(self)
                QtCore.QObject.connect(o, QtCore.SIGNAL("fileSelected(QString)"), self.savefile)
                o.setAcceptMode(1)
                o.setNameFilter("SQL files (*.sql)");
                o.open()
            else:
                self.savefile(script.saveTo)

    def savefile(self, s):
        if isinstance(self.conntabs.currentWidget(), Connection):
            scripttabs = self.conntabs.currentWidget().scripttabs
            #open(s, "w").write(unicode(scripttabs.currentWidget().editor.text()).encode("UTF-8"))
            scripttabs.currentWidget().savefile(s)

            scripttabs.currentWidget().saveTo = s
            scripttabs.setTabText(scripttabs.currentIndex(), QtGui.QApplication.translate("MainWindow", s.split("/")[-1], None, QtGui.QApplication.UnicodeUTF8))

            self.showtooltip("Saved.")

    def saveasdialog(self):
        if isinstance(self.conntabs.currentWidget(), Connection):
            o = QtGui.QFileDialog(self)
            o.setAcceptMode(1)
            o.setNameFilter("SQL files (*.sql)");
            QtCore.QObject.connect(o, QtCore.SIGNAL("fileSelected(QString)"), self.savefile)
            o.open()

    # ==== ==== ==== ==== ==== ==== ==== ====
    # EDIT
    # ==== ==== ==== ==== ==== ==== ==== ====
    def comment(self):
        if isinstance(self.conntabs.currentWidget(), Connection):
            print "main.comment"
            self.conntabs.currentWidget().scripttabs.currentWidget().editor.comment()

    def searcheditor(self):
        if isinstance(self.conntabs.currentWidget(), Connection):
            self.conntabs.currentWidget().scripttabs.currentWidget().searcheditor()

    def joinlines(self):
        if isinstance(self.conntabs.currentWidget(), Connection):
            self.conntabs.currentWidget().scripttabs.currentWidget().editor.joinlines()

    def splitlines(self):
        if isinstance(self.conntabs.currentWidget(), Connection):
            self.conntabs.currentWidget().scripttabs.currentWidget().editor.splitlines()

    # ==== ==== ==== ==== ==== ==== ==== ====
    # NAVIGATE
    # ==== ==== ==== ==== ==== ==== ==== ====
    def toeditor(self):
        if isinstance(self.conntabs.currentWidget(), Connection):
            self.conntabs.currentWidget().scripttabs.currentWidget().editor.setFocus()

     # CONN, SQL
    def leftconnection(self):
        if isinstance(self.conntabs.currentWidget(), Connection):
            self.conntabs.setCurrentIndex(self.conntabs.currentIndex() - 1)

    def rightconnection(self):
        self.conntabs.setCurrentIndex(self.conntabs.currentIndex() + 1)

    def leftscript(self):
        scripttabs = self.conntabs.currentWidget().scripttabs
        scripttabs.setCurrentIndex(scripttabs.currentIndex() - 1)

    def rightscript(self):
        scripttabs = self.conntabs.currentWidget().scripttabs
        scripttabs.setCurrentIndex(scripttabs.currentIndex() + 1)

    # TABLE
    def pantable(self, x, y):
        table = self.conntabs.currentWidget().scripttabs.currentWidget().table

        horizontal = table.horizontalScrollBar()
        vertical = table.verticalScrollBar()
        vertical.setFocus()
        horizontal.setValue(horizontal.value() + x)
        vertical.setValue(vertical.value() + y)

    def leftpantable(self):
        self.pantable(-1, 0)

    def rightpantable(self):
        self.pantable(1, 0)

    def uppantable(self):
        self.pantable(0, -1)

    def downpantable(self):
        self.pantable(0, 1)

    def defaultstretch(self):
        self.conntabs.currentWidget().scripttabs.currentWidget().defaultStretch()

    def expandtable(self):
        self.conntabs.currentWidget().scripttabs.currentWidget().expandTable()

    def shrinktable(self):
            self.conntabs.currentWidget().scripttabs.currentWidget().shrinkTable()
    # ==== ==== ==== ==== ==== ==== ==== ====
    # ACTIONS
    # ==== ==== ==== ==== ==== ==== ==== ====
    def execute(self):
        if isinstance(self.conntabs.currentWidget(), Connection):
            self.conntabs.currentWidget().saveworkspace()
            startTime = time.time()
            self.conntabs.currentWidget().scripttabs.currentWidget().execute()
            #self.showtooltip("Sql execute in %s seconds." % round(time.time() - startTime, 4))

    def stopexecute(self):
        if isinstance(self.conntabs.currentWidget(), Connection):
            self.conntabs.currentWidget().scripttabs.currentWidget().stopexecute()

    def executetofile(self):
        if isinstance(self.conntabs.currentWidget(), Connection):
            self.conntabs.currentWidget().saveworkspace()
            o = QtGui.QFileDialog(self)
            o.setAcceptMode(1)
            QtCore.QObject.connect(o, QtCore.SIGNAL("fileSelected(QString)"), self.conntabs.currentWidget().scripttabs.currentWidget().executetofile)
            o.open()

    def copytoclipbord(self):
        if isinstance(self.conntabs.currentWidget(), Connection):
            self.conntabs.currentWidget().scripttabs.currentWidget().copytoclipbord()
            self.showtooltip("Selection copied.")

    def showautocomplete(self):
        if isinstance(self.conntabs.currentWidget(), Connection):
            self.conntabs.currentWidget().scripttabs.currentWidget().showautocomplete()
    # deprecated
    def showcolumnautocomplete(self):
        if isinstance(self.conntabs.currentWidget(), Connection):
            self.conntabs.currentWidget().scripttabs.currentWidget().showcolumnautocomplete()

    def formatsql(self):
        if isinstance(self.conntabs.currentWidget(), Connection):
            self.conntabs.currentWidget().scripttabs.currentWidget().editor.formatsql()
            self.showtooltip("Sql has been formated.")

    def reloadcatalog(self):
        if isinstance(self.conntabs.currentWidget(), Connection):
            startTime = time.time()
            self.conntabs.currentWidget().reloadcatalog()
            self.showtooltip("Catalog has been reloadet in %s seconds for %s tables."
                                % (round(time.time() - startTime, 4),
                                len(self.conntabs.currentWidget().catalog)))

    def showcatalog(self):
        if isinstance(self.conntabs.currentWidget(), Connection):
            self.conntabs.currentWidget().showcatalog()
    # ==== ==== ==== ==== ==== ==== ==== ====
    # SETTINGS
    # ==== ==== ==== ==== ==== ==== ==== ====
    def loadsettings(self):
        sett = Settings("settings.yaml")
        message = sett.load()

        if message[0] == "Error":
            warningMessage("Settings load ERROR.", message[1])
        return sett

    def opensettings(self):
        settingsTab = SettingsTab(self, 'settings.yaml')
        self.conntabs.addTab(settingsTab, "")
        self.conntabs.setTabText(self.conntabs.indexOf(settingsTab), QtGui.QApplication.translate("MainWindow", "Settings", None, QtGui.QApplication.UnicodeUTF8))
        self.conntabs.setTabIcon(self.conntabs.indexOf(settingsTab), settingsTab.icon)
        self.conntabs.setCurrentWidget(settingsTab)

    def saveSettings(self):
        if isinstance(self.conntabs.currentWidget(), SettingsTab):
            print "saveSettings"
            self.conntabs.currentWidget().save()
            self.sett = self.loadsettings()
            self.showtooltip("Settings have been saved and reloadet.")

    # use decorator?
    def importODBC(self):
        if isinstance(self.conntabs.currentWidget(), SettingsTab):
            odbc = dataSources()

            for conn in odbc:
                if conn not in self.sett.settings['connections']:
                    settingsEditor = self.conntabs.currentWidget().editor
                    s = "  %s: {password: ENTER_IT}" % (conn)
                    settingsEditor.setText(settingsEditor.text() + "\n" + s)

    def openODBCmanager(self):
        try:
            Popen(["odbcad32.exe"])
        except:
            warningMessage("Error", "Could not open ODBC Manager.")

    # ==== ==== ==== ==== ==== ==== ==== ====
    # WORKSPACE
    # ==== ==== ==== ==== ==== ==== ==== ====
    def saveworkspace(self):
        print "saveworkspace"
        workspace = []
        for tabIndex in range(self.conntabs.count()):
            tab = self.conntabs.widget(tabIndex)
            if isinstance(tab, Connection):
                tab.saveworkspace()
                workspace.append(tab.name)

        yaml.dump(workspace, open("files/workspace.yaml", "w"))

    def openworkspace(self):
        print "#openworkspace"
        if os.path.exists("files/workspace.yaml"):
            try:
                workspace = yaml.load(open("files/workspace.yaml"))
            except Exception as exc:
                warningMessage("Error at loading workspace!", unicode(exc.args))
                workspace = list()

            if workspace != None:
                for connName in workspace:
                    print connName
                    try:
                        password = self.sett.settings['connections'].get(connName, {}).get("password", "")
                        connection = self.opennewconnection(connName, password,  False)
                        connection.openworkspace()

                    except Exception as exc:
                        warningMessage("Error loading workspace for conn: %s" % connName, unicode(exc.args))

    def closeevent(self, event):
        quit_msg = "Are you sure you want to exit the program?"
        reply = QtGui.QMessageBox.question(self, 'Quit?',
                         quit_msg, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)

        if reply == QtGui.QMessageBox.Yes:
            self.saveworkspace()
            event.accept()
        else:
            event.ignore()

    # ==== ==== ==== ==== ==== ==== ==== ====
    # OTHER
    # ==== ==== ==== ==== ==== ==== ==== ====
    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtGui.QApplication.translate("MainWindow", "Simple database explorer", None, QtGui.QApplication.UnicodeUTF8))

        self.fileMenu.setTitle(QtGui.QApplication.translate("MainWindow", "&File", None, QtGui.QApplication.UnicodeUTF8))
        self.editMenu.setTitle(QtGui.QApplication.translate("MainWindow", "&Edit", None, QtGui.QApplication.UnicodeUTF8))
        self.actionsMenu.setTitle(QtGui.QApplication.translate("MainWindow", "&Actions", None, QtGui.QApplication.UnicodeUTF8))
        self.navigateMenu.setTitle(QtGui.QApplication.translate("MainWindow", "&Navigate", None, QtGui.QApplication.UnicodeUTF8))
        self.settingsMenu.setTitle(QtGui.QApplication.translate("MainWindow", "&Settings", None, QtGui.QApplication.UnicodeUTF8))