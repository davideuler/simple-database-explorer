from PyQt4 import QtCore, QtGui, QtSql, Qsci
import yaml
from yaml.parser import ParserError
import os
import time
from random import randint
from elements import *

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(808, 600)
        # SETTINGS
        self.sett = self.loadSettings()

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
        self.mainTabs = QtGui.QTabWidget(self.centralWidget)
        self.mainTabs.setFont(getFont(12))
        self.mainTabs.setContextMenuPolicy(QtCore.Qt.DefaultContextMenu)
        self.mainTabs.setDocumentMode(False)
        self.mainTabs.setTabsClosable(True)
        self.mainTabs.setMovable(True)
        self.mainTabs.setObjectName("mainTabs")
        # conn tab
        self.vboxlayout.addWidget(self.mainTabs)
        # CONSOLE
        self.console = QtGui.QLineEdit(self.centralWidget)
        self.console.setFont(getFont(10))
        self.console.setObjectName("console")


        self.console.setCompleter(self.getConnCompleter())

        self.vboxlayout.addWidget(self.console)
        MainWindow.setCentralWidget(self.centralWidget)
        # MENUBAR
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 808, 20))
        self.menubar.setFont(getFont(7))
        self.fileMenu = QtGui.QMenu(self.menubar)
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
        self.newConnAction = createAction("&New Connection", self, "MainWindow", "Ctrl+N", self.toConsole, 8)
        self.newSqlAction = createAction("&New &Sql script", self, "MainWindow", "Ctrl+Shift+N", self.newSqlScript, 8)

        self.openAction = createAction("&Open Sql script", self, "MainWindow", "Ctrl+O", self.openDialog, 8)
        self.saveAction = createAction("&Save Sql script", self, "MainWindow", "Ctrl+S", self.saveDialog, 8)
        self.saveAsAction = createAction("&Save As Sql script", self, "MainWindow", "Ctrl+Shift+S", self.saveAsDialog, 8)

        self.fileMenu.addAction(self.newConnAction)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.newSqlAction)
        self.fileMenu.addAction(self.openAction)
        self.fileMenu.addAction(self.saveAction)
        self.fileMenu.addAction(self.saveAsAction)

        # ==== ==== ==== ==== ==== ==== ==== ====
        # ACTION
        # ==== ==== ==== ==== ==== ==== ==== ====
        self.executeAction = createAction("&Execute", self, "MainWindow", "Alt+X", self.executeSql, 8)
        #self.stopExecuteSqlAction = createAction("&Stop Execute", self, "MainWindow", "Esc", self.stopExecuteSql, 8)
        self.executeToFileAction = createAction("&Execute to file", self, "MainWindow", "Alt+Ctrl+X", self.executeToFileSql, 8)
        self.autoCompleteAction = createAction("&Auto Complete", self, "MainWindow", "Alt+J", self.autoComplete, 8)
        self.autoColumnCompleteAction = createAction("&Auto Column Complete", self, "MainWindow", "Alt+K", self.showColumnAutoComplete, 8)
        self.formatSqlAction = createAction("&Format Sql", self, "MainWindow", "Ctrl+Q", self.formatSql, 8)
        self.reloadCatalogAction = createAction("&Reload Catalog", self, "MainWindow", "Ctrl+R", self.reloadCatalogCall, 8)
        self.showCatalogAction = createAction("&Show Catalog", self, "MainWindow", "Ctrl+Shift+R", self.showCatalogCall, 8)

        self.actionsMenu.addAction(self.executeAction)
        #self.actionsMenu.addAction(self.stopExecuteSqlAction)
        self.actionsMenu.addAction(self.executeToFileAction)
        self.actionsMenu.addSeparator()
        self.actionsMenu.addAction(self.autoCompleteAction)
        self.actionsMenu.addAction(self.autoColumnCompleteAction)
        self.actionsMenu.addAction(self.formatSqlAction)
        self.actionsMenu.addSeparator()
        self.actionsMenu.addAction(self.reloadCatalogAction)
        self.actionsMenu.addAction(self.showCatalogAction)
        # ==== ==== ==== ==== ==== ==== ==== ====
        # NAVIGATE
        # ==== ==== ==== ==== ==== ==== ==== ====
        self.toConsoleAction = createAction("&Console", self, "MainWindow", "Alt+I", self.toConsole, 8)
        self.toSqlEditorAction = createAction("&Sql Edit", self, "MainWindow", "Alt+M", self.toSqlEditor, 8)
        self.leftConnectionAction = createAction("&Left Connection", self, "MainWindow", "Alt+Down", self.leftConnection, 8)
        self.rightConnectionAction = createAction("&Right Connection", self, "MainWindow", "Alt+Up", self.rightConnection, 8)
        self.leftSqlEditAction = createAction("L&eft Sql Edit", self, "MainWindow", "Alt+Left", self.leftSqlEdit, 8)
        self.rightSqlEditAction = createAction("R&ight Sql Edit", self, "MainWindow", "Alt+Right", self.rightSqlEdit, 8)

        self.leftPanTableAction = createAction("Le&ft pan Table", self, "MainWindow", "Alt+4", self.leftPanTable, 8)
        self.rightPanTableAction = createAction("Ri&ght pan Table", self, "MainWindow", "Alt+6", self.rightPanTable, 8)
        self.downPanTableAction = createAction("Down pan Table", self, "MainWindow", "Alt+2", self.downPanTable, 8)
        self.upPanTableAction = createAction("Up pan Table", self, "MainWindow", "Alt+8", self.upPanTable, 8)

        self.defaultStretchAction = createAction("Default Stretch Table", self, "MainWindow", "Alt+*", self.defaultStretchCall, 8)
        self.expandTableAction = createAction("Expand Table", self, "MainWindow", "Alt++", self.expandTableCall, 8)
        self.shrinkTableAction = createAction("Shrink Table", self, "MainWindow", "Alt+-", self.shrinkTableCall, 8)


        self.navigateMenu.addAction(self.toConsoleAction)
        self.navigateMenu.addAction(self.toSqlEditorAction)
        self.navigateMenu.addSeparator()
        self.navigateMenu.addAction(self.leftConnectionAction)
        self.navigateMenu.addAction(self.rightConnectionAction)
        self.navigateMenu.addSeparator()
        self.navigateMenu.addAction(self.leftSqlEditAction)
        self.navigateMenu.addAction(self.rightSqlEditAction)
        self.navigateMenu.addSeparator()
        self.navigateMenu.addAction(self.leftPanTableAction)
        self.navigateMenu.addAction(self.rightPanTableAction)
        self.navigateMenu.addAction(self.downPanTableAction)
        self.navigateMenu.addAction(self.upPanTableAction)
        self.navigateMenu.addSeparator()
        self.navigateMenu.addAction(self.defaultStretchAction)
        self.navigateMenu.addAction(self.expandTableAction)
        self.navigateMenu.addAction(self.shrinkTableAction)
        #self.navigateMenu.addAction(self.rightPanTableAction)
        # ==== ==== ==== ==== ==== ==== ==== ====
        # SETTINGS
        # ==== ==== ==== ==== ==== ==== ==== ====
        self.openSettingsAction = createAction("Open settings", self, "MainWindow", "Ctrl+Alt+S", self.openSettings, 8)
        self.saveSettingsAction = createAction("Save/Reload settings", self, "MainWindow", "", self.saveSettings, 8)

        self.settingsMenu.addAction(self.openSettingsAction)
        self.settingsMenu.addAction(self.saveSettingsAction)

        # MENU
        self.menubar.addAction(self.fileMenu.menuAction())
        self.menubar.addAction(self.actionsMenu.menuAction())
        self.menubar.addAction(self.navigateMenu.menuAction())
        self.menubar.addAction(self.settingsMenu.menuAction())

        self.retranslateUi(MainWindow)
        self.mainTabs.setCurrentIndex(0)

        QtCore.QObject.connect(self.console, QtCore.SIGNAL("returnPressed()"), self.newConnection)
        QtCore.QObject.connect(self.mainTabs, QtCore.SIGNAL("tabCloseRequested(int)"), self.mainTabs.removeTab)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        self.openWorkspace()

    # ==== ==== ==== ==== ==== ==== ==== ====
    # NEW CONN, SQL
    # ==== ==== ==== ==== ==== ==== ==== ====
    def getConnCompleter(self):
        connectionList = self.sett.settings['connections'].keys()
        completer = QtGui.QCompleter(connectionList)
        completer.setCaseSensitivity(0)
        completer.setCompletionMode(1)
        completer.setModelSorting(2)
        return completer

    def newConnection(self):
        connName = str(self.console.text())
        self.console.setText('')
        self.openNewConnection(connName)

    def openNewConnection(self, connName, openNewSql=True):
        connSettings = self.sett.settings['connections'][connName]
        connTab = ConnTab(connName=connName, connSettings=connSettings)
        self.mainTabs.addTab(connTab, "")
        self.mainTabs.setTabText(self.mainTabs.indexOf(connTab), QtGui.QApplication.translate("MainWindow", connName, None, QtGui.QApplication.UnicodeUTF8))
        self.mainTabs.setTabIcon(self.mainTabs.indexOf(connTab), connTab.icon)

        self.mainTabs.setCurrentWidget(connTab)

        QtCore.QObject.connect(connTab.childTabs, QtCore.SIGNAL("tabCloseRequested(int)"), connTab.childTabs.removeTab)

        if openNewSql:
            self.newSqlScript()

    def newSqlScript(self, path=None):

        connTab = self.mainTabs.currentWidget()
        sqlTab = SqlTab(connTab)
        #childTabs = .childTabs
        connTab.childTabs.addTab(sqlTab, "")
        connTab.childTabs.setTabText(connTab.childTabs.indexOf(sqlTab), QtGui.QApplication.translate("MainWindow", "Sql script", None, QtGui.QApplication.UnicodeUTF8))
        connTab.childTabs.setCurrentWidget(sqlTab)
        self.toSqlEditor()

        if path != None:
            try:
                self.openFile(path)
            except:
                print "error at opening file"

    # ==== ==== ==== ==== ==== ==== ==== ====
    # FILE HANDLING
    # ==== ==== ==== ==== ==== ==== ==== ====
    def openDialog(self):
        o = QtGui.QFileDialog(self)
        QtCore.QObject.connect(o, QtCore.SIGNAL("fileSelected(QString)"), self.newSqlScript)
        o.setAcceptMode(0)
        o.open()

    def openFile(self, path):
        print path
        childTabs = self.mainTabs.currentWidget().childTabs
        childTabs.currentWidget().editor.setText(open(path).read())
        childTabs.currentWidget().saveTo = path
        childTabs.setTabText(childTabs.currentIndex(), QtGui.QApplication.translate("MainWindow", path.split("/")[-1], None, QtGui.QApplication.UnicodeUTF8))

    def saveDialog(self):
        sqlTab = self.mainTabs.currentWidget().childTabs.currentWidget()

        if sqlTab.saveTo == None:
            o = QtGui.QFileDialog(self)
            QtCore.QObject.connect(o, QtCore.SIGNAL("fileSelected(QString)"), self.saveFile)
            o.setAcceptMode(1)
            o.open()
        else:
            self.saveFile(sqlTab.saveTo)

    def saveFile(self, s):
        childTabs = self.mainTabs.currentWidget().childTabs
        open(s, "w").write(childTabs.currentWidget().editor.text())

        childTabs.currentWidget().saveTo = s
        childTabs.setTabText(childTabs.currentIndex(), QtGui.QApplication.translate("MainWindow", s.split("/")[-1], None, QtGui.QApplication.UnicodeUTF8))

    def saveAsDialog(self):
        o = QtGui.QFileDialog(self)
        o.setAcceptMode(1)
        QtCore.QObject.connect(o, QtCore.SIGNAL("fileSelected(QString)"), self.saveFile)
        o.open()


    # ==== ==== ==== ==== ==== ==== ==== ====
    # NAVIGATE
    # ==== ==== ==== ==== ==== ==== ==== ====
    def toConsole(self):
        self.console.setFocus()

    def toSqlEditor(self):
        self.mainTabs.currentWidget().childTabs.currentWidget().editor.setFocus()

     # CONN, SQL
    def leftConnection(self):
        self.mainTabs.setCurrentIndex(self.mainTabs.currentIndex() - 1)

    def rightConnection(self):
        self.mainTabs.setCurrentIndex(self.mainTabs.currentIndex() + 1)

    def leftSqlEdit(self):
        childTabs = self.mainTabs.currentWidget().childTabs
        childTabs.setCurrentIndex(childTabs.currentIndex() - 1)

    def rightSqlEdit(self):
        childTabs = self.mainTabs.currentWidget().childTabs
        childTabs.setCurrentIndex(childTabs.currentIndex() + 1)

    # TABLE
    def panTable(self, x, y):
        table = self.mainTabs.currentWidget().childTabs.currentWidget().table

        horizontal = table.horizontalScrollBar()
        vertical = table.verticalScrollBar()
        vertical.setFocus()
        horizontal.setValue(horizontal.value() + x)
        vertical.setValue(vertical.value() + y)

    def leftPanTable(self):
        self.panTable(-1, 0)

    def rightPanTable(self):
        self.panTable(1, 0)

    def upPanTable(self):
        self.panTable(0, -1)

    def downPanTable(self):
        self.panTable(0, 1)

    def defaultStretchCall(self):
        self.mainTabs.currentWidget().childTabs.currentWidget().defaultStretch()

    def expandTableCall(self):
        self.mainTabs.currentWidget().childTabs.currentWidget().expandTable()

    def shrinkTableCall(self):
            self.mainTabs.currentWidget().childTabs.currentWidget().shrinkTable()
    # ==== ==== ==== ==== ==== ==== ==== ====
    # ACTIONS
    # ==== ==== ==== ==== ==== ==== ==== ====
    def executeSql(self):
        self.mainTabs.currentWidget().childTabs.currentWidget().execute()

    def stopExecuteSql(self):
        self.mainTabs.currentWidget().executeThread.stop()

    def executeToFileSql(self):
        o = QtGui.QFileDialog(self)
        o.setAcceptMode(1)
        QtCore.QObject.connect(o, QtCore.SIGNAL("fileSelected(QString)"), self.mainTabs.currentWidget().childTabs.currentWidget().executeToFile)
        o.open()

    def autoComplete(self):
        #editor = self.mainTabs.currentWidget().childTabs.currentWidget().editor
        #editor.showUserList(1, sorted(self.mainTabs.currentWidget().catalog.keys()))
        self.mainTabs.currentWidget().childTabs.currentWidget().showAutoComplete()

    def showColumnAutoComplete(self):
        self.mainTabs.currentWidget().childTabs.currentWidget().showColumnAutoComplete()

    def formatSql(self):
        self.mainTabs.currentWidget().childTabs.currentWidget().formatSql()

    def reloadCatalogCall(self):
        self.mainTabs.currentWidget().reloadCatalog()

    def showCatalogCall(self):
        self.mainTabs.currentWidget().showCatalog()
    # ==== ==== ==== ==== ==== ==== ==== ====
    # SETTINGS
    # ==== ==== ==== ==== ==== ==== ==== ====
    def loadSettings(self):
        sett = Settings("settings.yaml")
        sett.load()
        return sett

    def openSettings(self):
        settingsTab = SettingsTab(self, 'settings.yaml')
        self.mainTabs.addTab(settingsTab, "")
        self.mainTabs.setTabText(self.mainTabs.indexOf(settingsTab), QtGui.QApplication.translate("MainWindow", "Settings", None, QtGui.QApplication.UnicodeUTF8))
        self.mainTabs.setTabIcon(self.mainTabs.indexOf(settingsTab), settingsTab.icon)
        self.mainTabs.setCurrentWidget(settingsTab)

    def saveSettings(self):
        print "saveSettings"
        self.mainTabs.currentWidget().save()
        self.sett = self.loadSettings()
        self.console.setCompleter(self.getConnCompleter())

    # ==== ==== ==== ==== ==== ==== ==== ====
    # WORKSPACE
    # ==== ==== ==== ==== ==== ==== ==== ====
    def saveWorkspace(self):
        print "saveWorkspace"
        workspace = {}
        for tabIndex in range(self.mainTabs.count()):
            mainTab = self.mainTabs.widget(tabIndex)
            childTabs = mainTab.childTabs
            workspace[mainTab.name] = list()
            # SqlTabs
            for sqlTabIndex in range(0, childTabs.count()):
                sqlTab = childTabs.widget(sqlTabIndex)
                if sqlTab.saveTo == None:
                    path = u"files/sql/%s_%s_%s.sql" % (mainTab.name, "".join(map(str, time.localtime()[:3])), randint(0, 100000))
                else:
                    path = unicode(sqlTab.saveTo)

                sqlTab.saveFile(path)
                workspace[mainTab.name].append(path)

        yaml.dump(workspace, open("files/workspace.yaml", "w"))

    def openWorkspace(self):
        print "openWorkspace"
        if os.path.exists("files/workspace.yaml"):
            try:
                workspace = yaml.load(open("files/workspace.yaml"))
            except:
                workspace = list()
                #os.remove("files/workspace.yaml")

            for connName in workspace:
                try:
                    self.openNewConnection(connName, False)

                    # SqlTabs
                    for sqlScript in workspace[connName]:
                        self.newSqlScript(sqlScript)
                except:
                    print "Error loading workspace for conn: %s" % connName

    def closeEvent(self, event):
        quit_msg = "Are you sure you want to exit the program?"
        reply = QtGui.QMessageBox.question(self, 'Message',
                         quit_msg, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)

        if reply == QtGui.QMessageBox.Yes:
            self.saveWorkspace()
            event.accept()
        else:
            event.ignore()

    # ==== ==== ==== ==== ==== ==== ==== ====
    # OTHER
    # ==== ==== ==== ==== ==== ==== ==== ====
    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtGui.QApplication.translate("MainWindow", "Simple database explorer", None, QtGui.QApplication.UnicodeUTF8))

        self.fileMenu.setTitle(QtGui.QApplication.translate("MainWindow", "&File", None, QtGui.QApplication.UnicodeUTF8))
        self.actionsMenu.setTitle(QtGui.QApplication.translate("MainWindow", "&Actions", None, QtGui.QApplication.UnicodeUTF8))
        self.navigateMenu.setTitle(QtGui.QApplication.translate("MainWindow", "&Navigate", None, QtGui.QApplication.UnicodeUTF8))
        self.settingsMenu.setTitle(QtGui.QApplication.translate("MainWindow", "&Settings", None, QtGui.QApplication.UnicodeUTF8))
