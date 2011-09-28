from PyQt4 import QtCore, QtGui, Qsci
import yaml
from yaml.parser import ParserError
import os
import time
from random import randint
from connection import *
import datetime
from pyodbc import dataSources
from subprocess import Popen
import resources
import platform
#import keyring

__version__ = "0.2.0"

class Sdbe(QtGui.QMainWindow):
    """ Sets up the main window of SDBE. It sets a :
         - menu bar
         - a tabs widget (for connections)

        Almost all action go thru the Menu bar. It a centralized action base :)
    """

    #Qt.FramelessWindowHint	0x00000800	Produces a borderless window.
    # The user cannot move or resize a borderless window via the window system.
    # On X11, the result of the flag is dependent on the window manager and its
    # ability to understand Motif and/or NETWM hints. Most existing modern window managers can handle this.
    def __init__(self, parent=None, application=None):
        super(QtGui.QMainWindow, self).__init__(parent)
        self.setObjectName("SDBE")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":icon/sdbe.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(icon)
        self.application = application

        # SETTINGS
        settings = QtCore.QSettings()
        self.restoreGeometry(settings.value("Geometry").toByteArray())
        self.sett = self.loadsettings()

        self.centralWidget = QtGui.QWidget(self)
        self.centralWidget.setObjectName("centralWidget")
        self.vboxlayout = QtGui.QVBoxLayout(self.centralWidget)
        self.vboxlayout.setSpacing(0)
        self.vboxlayout.setContentsMargins(0, 0, 0, 0)
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

        self.setCentralWidget(self.centralWidget)
        # MENUBAR
        self.menubar = QtGui.QMenuBar(self)
        #self.menubar.setGeometry(QtCore.QRect(0, 0, 808, 20))
        self.menubar.setFont(getFont(7))
        self.fileMenu = QtGui.QMenu(self.menubar)
        self.editMenu = QtGui.QMenu(self.menubar)
        self.actionsMenu = QtGui.QMenu(self.menubar)
        self.navigateMenu = QtGui.QMenu(self.menubar)
        self.settingsMenu = QtGui.QMenu(self.menubar)
        self.helpMenu = QtGui.QMenu(self.menubar)
        self.setMenuBar(self.menubar)

        # ==== ==== ==== ==== ==== ==== ==== ====
        # FILE
        # ==== ==== ==== ==== ==== ==== ==== ====
        # QtGui.QKeySequence.New
        self.newconn_action = self.createAction("&New Connection", self.newconnection, QtGui.QKeySequence.New, "130")
        self.recent_action = self.createAction("Recent files", self.recent, "", "44")
        self.newsql_action = self.createAction("&New script", self.newscript, "Ctrl+Shift+N", "8")
        self.open_action = self.createAction("&Open script", self.opendialog, QtGui.QKeySequence.Open, "119")
        self.save_action = self.createAction("&Save script", self.savedialog, QtGui.QKeySequence.Save, "7")
        self.saveas_action = self.createAction("&Save As script", self.saveasdialog, "Ctrl+Shift+S", "131")

        self.addActions(self.fileMenu, ( self.newconn_action, None, self.recent_action, None,
                                        self.newsql_action, self.open_action, self.save_action,
                                        self.saveas_action ))

        # ==== ==== ==== ==== ==== ==== ==== ====
        # EDIT
        # ==== ==== ==== ==== ==== ==== ==== ====
        self.showfinddialog_action = self.createAction("&Find and Replace", self.showfinddialog, QtGui.QKeySequence.Find, "16")
        self.findnext_action = self.createAction("Find Next", self.findnext, QtGui.QKeySequence.FindNext, "16")
        self.formatsql_action = self.createAction("&Format SQL", self.formatsql, "Ctrl+Shift+F", "27")
        self.comment_action = self.createAction("&Comment selection", self.comment, QtGui.QKeySequence.Bold, "38")
        self.joinlines_action = self.createAction("&Join selected Lines",
                self.joinlines, "Ctrl+Shift+J", "82")
        self.splitlines_action = self.createAction("&Split selected Lines", self.splitlines, "Ctrl+I", "83")

        self.addActions(self.editMenu, ( self.showfinddialog_action, self.findnext_action, None, self.formatsql_action,
                        self.comment_action, None, self.joinlines_action, self.splitlines_action ))

        # ==== ==== ==== ==== ==== ==== ==== ====
        # ACTION
        # ==== ==== ==== ==== ==== ==== ==== ====
        self.execute_action = self.createAction("&Execute", self.executemany, "Alt+X", "98")
        self.stopexecute_action = self.createAction("&Stop Execute", self.stopexecute, "Ctrl+Q", "116")
        self.executetofile_action = self.createAction("&Execute to file", self.executetofile, "Alt+Ctrl+X", "104")
        self.showautocomplete_action = self.createAction("&Auto Complete", self.showautocomplete, "Ctrl+Space", "13")
        #self.autocolumncomplete_action = self.createAction("&Auto Column Complete", self.showcolumnautocomplete, "Alt+K")
        self.reloadcatalog_action = self.createAction("&Reload Catalog", self.reloadcatalog, "Ctrl+R", "48")
        self.showcatalog_action = self.createAction("&Show Catalog", self.showcatalog, "Ctrl+Shift+R", "123")

        self.addActions(self.actionsMenu, ( self.execute_action, self.stopexecute_action,
                        self.executetofile_action, None, self.showautocomplete_action,
                        None, self.reloadcatalog_action, self.showcatalog_action ))

        # ==== ==== ==== ==== ==== ==== ==== ====
        # NAVIGATE
        # ==== ==== ==== ==== ==== ==== ==== ====
        # TODO: create a txt file as a settings for all the actions
        self.toeditor_action = self.createAction("&SQL Editor", self.toeditor, "Alt+M", "1")
        self.toconsole_action = self.createAction("&Console", self.toconsole, "", "1")
        self.leftconnection_action = self.createAction("&Left Connection",
                self.leftconnection, "Ctrl+H", "105")
        self.rightconnection_action = self.createAction("&Right Connection",
                self.rightconnection, "Ctrl+L", "103")
        self.leftscript_action = self.createAction("L&eft SQL script",
                self.leftscript, "Ctrl+J", "102")
        self.rightscript_action = self.createAction("R&ight SQL script",
                self.rightscript, "Ctrl+K", "104")

        self.leftpantable_action = self.createAction("Le&ft pan Table", self.leftpantable, "Alt+H", "28")
        self.rightpantable_action = self.createAction("Ri&ght pan Table", self.rightpantable, "Alt+L", "23")
        self.downpantable_action = self.createAction("Down pan Table", self.downpantable, "Alt+J", "24")
        self.uppantable_action = self.createAction("Up pan Table", self.uppantable, "Alt+K", "19")

        self.defaultstretch_action = self.createAction("Default Stretch Table", self.defaultstretch, "Alt+*", "111")
        self.expandtable_action = self.createAction("Expand Table", self.expandtable, "Alt+I", "112")
        self.shrinktable_action = self.createAction("Shrink Table", self.shrinktable, "Alt+O", "117")

        self.addActions(self.navigateMenu, ( self.toeditor_action, self.toconsole_action, None, self.leftconnection_action,
                    self.rightconnection_action, None, self.leftscript_action, self.rightscript_action,
                    None, self.leftpantable_action, self.rightpantable_action, self.downpantable_action,
                    self.uppantable_action, None, self.defaultstretch_action, self.expandtable_action,
                    self.shrinktable_action, ))

        # ==== ==== ==== ==== ==== ==== ==== ====
        # SETTINGS
        # ==== ==== ==== ==== ==== ==== ==== ====
        #self.opensettings_action = self.createAction("Open settings", self.opensettings, "Ctrl+Alt+S")
        #self.savesettings_action = self.createAction("Save/Reload settings", self.saveSettings, "")
        self.openodbcmanager_action = self.createAction("Open ODBC Manager", self.openODBCmanager, "", "odbcmanager")
        self.addActions(self.settingsMenu, ( self.openodbcmanager_action, ))

        # ==== ==== ==== ==== ==== ==== ==== ====
        # HELP
        # ==== ==== ==== ==== ==== ==== ==== ====
        self.helpabout_action = self.createAction("About", self.helpabout, "", "65")
        self.helphelp_action = self.createAction("Help", self.helphelp, "", "6")

        self.addActions(self.helpMenu, ( self.helpabout_action, self.helphelp_action, ))

        # MENU
        self.menubar.addAction(self.fileMenu.menuAction())
        self.menubar.addAction(self.editMenu.menuAction())
        self.menubar.addAction(self.actionsMenu.menuAction())
        self.menubar.addAction(self.navigateMenu.menuAction())
        self.menubar.addAction(self.settingsMenu.menuAction())
        self.menubar.addAction(self.helpMenu.menuAction())

        self.retranslateUi()
        self.conntabs.setCurrentIndex(0)

        QtCore.QObject.connect(self.conntabs, QtCore.SIGNAL("tabCloseRequested(int)"), self.conntabs.removeTab)
        QtCore.QMetaObject.connectSlotsByName(self)

        QtCore.QTimer.singleShot(0, self.openworkspace)
        #self.statusBar().showMessage('Ready', 2000)
        #self.setToolTip(QtGui.QToolTip())

    def createAction(self, text, slot=None, shortcut=None, icon=None,
                        tip=None, checkable=False, signal="triggered()"):
        action = QtGui.QAction(text, self)
        action.setFont(getFont(8))
        if icon is not None:
            action.setIcon(QtGui.QIcon("files/icons/milky/%s.png" % icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            self.connect(action, QtCore.SIGNAL(signal), slot)
        if checkable:
            action.setCheckable(True)
        return action

    def addActions(self, target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)

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
                # --
                #keyring.set_password(connection, 'sdbeuser', password)

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
            self.showcatalog()

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

    def savefile(self, path):
        if isinstance(self.conntabs.currentWidget(), Connection):
            path = unicode(path)
            if not path.lower().endswith(".sql"):
                path = path + ".sql"

            scripttabs = self.conntabs.currentWidget().scripttabs
            #open(s, "w").write(unicode(scripttabs.currentWidget().editor.text()).encode("UTF-8"))
            scripttabs.currentWidget().savefile(path)

            scripttabs.currentWidget().saveTo = path
            scripttabs.setTabText(scripttabs.currentIndex(), QtGui.QApplication.translate("MainWindow", path.split("/")[-1], None, QtGui.QApplication.UnicodeUTF8))

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
        print "main.comment"
        c = self.conntabs.currentWidget().scripttabs.currentWidget()
        #getattr(w, nameAction)()
        self.conntabs.currentWidget().scripttabs.currentWidget().editor.comment()


    def showfinddialog(self):
        self.conntabs.currentWidget().scripttabs.currentWidget().showfinddialog()

    def findnext(self):
        self.conntabs.currentWidget().scripttabs.currentWidget().findDialog.findbuttonclick()

    def joinlines(self):
        self.conntabs.currentWidget().scripttabs.currentWidget().editor.joinlines()

    def splitlines(self):
        self.conntabs.currentWidget().scripttabs.currentWidget().editor.splitlines()

    # ==== ==== ==== ==== ==== ==== ==== ====
    # NAVIGATE
    # ==== ==== ==== ==== ==== ==== ==== ====
    def toeditor(self):
        self.conntabs.currentWidget().scripttabs.currentWidget().editor.setFocus()

    def toconsole(self):
        self.conntabs.currentWidget().scripttabs.currentWidget().console.setFocus()
     # CONN, SQL
    def leftconnection(self):
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
    def executemany(self):
        if self.conntabs.currentWidget().isEnabled():
            self.conntabs.currentWidget().saveworkspace()
            startTime = time.time()
            self.conntabs.currentWidget().scripttabs.currentWidget().executemany()
            #self.showtooltip("Sql execute in %s seconds." % round(time.time() - startTime, 4))

    def stopexecute(self):
        self.conntabs.currentWidget().scripttabs.currentWidget().stopexecute()

    def executetofile(self):
        if self.conntabs.currentWidget().isEnabled():
            self.conntabs.currentWidget().saveworkspace()
            o = QtGui.QFileDialog(self)
            o.setAcceptMode(1)
            QtCore.QObject.connect(o, QtCore.SIGNAL("fileSelected(QString)"), self.conntabs.currentWidget().scripttabs.currentWidget().executetofile)
            o.open()

    def copytoclipbord(self):
        self.conntabs.currentWidget().scripttabs.currentWidget().copytoclipbord()
        self.showtooltip("Selection copied.")

    def showautocomplete(self):
        self.conntabs.currentWidget().scripttabs.currentWidget().showautocomplete()

    def formatsql(self):
        self.conntabs.currentWidget().scripttabs.currentWidget().editor.formatsql()
        self.showtooltip("Sql has been formated.")

    def reloadcatalog(self):
        if self.conntabs.currentWidget().isEnabled():
            startTime = time.time()
            self.conntabs.currentWidget().reloadcatalog()
            self.showtooltip("Catalog has been reloadet in %s seconds for %s tables."
                                % (round(time.time() - startTime, 4),
                                len(self.conntabs.currentWidget().catalog)))

    def showcatalog(self):
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

    # ==== ==== ==== ==== ==== ==== ==== ====
    # HELP
    # ==== ==== ==== ==== ==== ==== ==== ====
    def helpabout(self):
        QtGui.QMessageBox.about(self, "About simple database explorer",
                """<b>Simple database explorer</b> v %s
                <p>Open source &copy; 2011 sdbecompany.

                <p>This application can be used to perform
                simple database exploration.
                <p>Python %s - Qt %s - PyQt %s on %s""" % (
                __version__, platform.python_version(),
                QtCore.QT_VERSION_STR, QtCore.PYQT_VERSION_STR, platform.system()))

    def helphelp(self):
        #form = helpform.HelpForm("index.html", self)
        #form.show()
        QtGui.QMessageBox.about(self, "Help for simple database explorer",
                """<a href="http://code.google.com/p/simple-database-explorer/">Homepage</a>""")

##    def opensettings(self):
##        settingsTab = SettingsTab(self, 'settings.yaml')
##        self.conntabs.addTab(settingsTab, "")
##        self.conntabs.setTabText(self.conntabs.indexOf(settingsTab), QtGui.QApplication.translate("MainWindow", "Settings", None, QtGui.QApplication.UnicodeUTF8))
##        self.conntabs.setTabIcon(self.conntabs.indexOf(settingsTab), settingsTab.icon)
##        self.conntabs.setCurrentWidget(settingsTab)
##
##    def saveSettings(self):
##        if isinstance(self.conntabs.currentWidget(), SettingsTab):
##            print "saveSettings"
##            self.conntabs.currentWidget().save()
##            self.sett = self.loadsettings()
##            self.showtooltip("Settings have been saved and reloadet.")
##
##    # use decorator?
##    def importODBC(self):
##        if isinstance(self.conntabs.currentWidget(), SettingsTab):
##            odbc = dataSources()
##
##            for conn in odbc:
##                if conn not in self.sett.settings['connections']:
##                    settingsEditor = self.conntabs.currentWidget().editor
##                    s = "  %s: {password: ENTER_IT}" % (conn)
##                    settingsEditor.setText(settingsEditor.text() + "\n" + s)

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
                self.newconnection()

            if workspace != None:
                for connName in workspace:
                    print connName
                    try:
                        password = self.sett.settings['connections'].get(connName, {}).get("password", "")
                        connection = self.opennewconnection(connName, password,  False)
                        connection.openworkspace()
                        #QtCore.QTimer.singleShot(1, connection.openworkspace)

                    except Exception as exc:
                        warningMessage("Error loading workspace for conn: %s" % connName, unicode(exc.args))
                if len(workspace) == 0:
                    self.newconnection()

    def closeEvent(self, event):
        quit_msg = "Are you sure you want to exit the program?"
        reply = QtGui.QMessageBox.question(self, 'Quit?',
                         quit_msg, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)

        if reply == QtGui.QMessageBox.Yes:
            self.saveworkspace()
            settings = QtCore.QSettings()
            settings.setValue("Geometry", QtCore.QVariant(self.saveGeometry()))
            event.accept()
        else:
            event.ignore()

    # ==== ==== ==== ==== ==== ==== ==== ====
    # OTHER
    # ==== ==== ==== ==== ==== ==== ==== ====
    def retranslateUi(self):
        self.setWindowTitle(QtGui.QApplication.translate("MainWindow", "Simple database explorer", None, QtGui.QApplication.UnicodeUTF8))

        self.fileMenu.setTitle(QtGui.QApplication.translate("MainWindow", "&File", None, QtGui.QApplication.UnicodeUTF8))
        self.editMenu.setTitle(QtGui.QApplication.translate("MainWindow", "&Edit", None, QtGui.QApplication.UnicodeUTF8))
        self.actionsMenu.setTitle(QtGui.QApplication.translate("MainWindow", "&Actions", None, QtGui.QApplication.UnicodeUTF8))
        self.navigateMenu.setTitle(QtGui.QApplication.translate("MainWindow", "&Navigate", None, QtGui.QApplication.UnicodeUTF8))
        self.settingsMenu.setTitle(QtGui.QApplication.translate("MainWindow", "&Settings", None, QtGui.QApplication.UnicodeUTF8))
        self.helpMenu.setTitle(QtGui.QApplication.translate("MainWindow", "Help", None, QtGui.QApplication.UnicodeUTF8))


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
