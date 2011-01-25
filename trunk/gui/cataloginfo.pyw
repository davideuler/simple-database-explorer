#!/usr/bin/env python
# Copyright (c) 2007-8 Qtrac Ltd. All rights reserved.
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later version. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.

import os
import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import treeoftable

class CatalogModel(treeoftable.TreeOfTableModel):

    def __init__(self, parent=None):
        super(CatalogModel, self).__init__(parent)


    def data(self, index, role):
        if role == Qt.DecorationRole:
            node = self.nodeFromIndex(index)

            if node is None:
                return QVariant()
            if isinstance(node, treeoftable.BranchNode):

                if index.column() != 0:
                    return QVariant()
                parent = node.parent.toString()
                if not parent:
                    filename = "db"
                else:
                    filename = "folder"
                filename = os.path.join("files/icons/milky", filename + ".png")

                pixmap = QPixmap(filename)
                if pixmap.isNull():
                    return QVariant()
                return QVariant(pixmap)
        return treeoftable.TreeOfTableModel.data(self, index, role)


class TreeOfTableWidget(QTreeView):

    def __init__(self, catalog, nesting=3, parent=None):
        super(TreeOfTableWidget, self).__init__(parent)
        self.setSelectionBehavior(QTreeView.SelectItems)
        self.setUniformRowHeights(True)
        model = CatalogModel(self)
        self.setModel(model)

        self.loadcatalog(catalog, nesting)

        self.connect(self, SIGNAL("activated(QModelIndex)"),
                     self.activated)
        self.connect(self, SIGNAL("expanded(QModelIndex)"),
                     self.expanded)
        self.expanded()

    def loadcatalog(self, catalog, nesting=3):
        try:
            self.model().load(catalog, nesting)
        except IOError, e:
            QMessageBox.warning(self, "DB Tree Info - Error",
                                unicode(e))
    def currentFields(self):
        return self.model().asRecord(self.currentIndex())


    def activated(self, index):
        self.emit(SIGNAL("activated"), self.model().asRecord(index))


    def expanded(self):
        for column in range(self.model().columnCount(QModelIndex())):
            self.resizeColumnToContents(column)


##class MainForm(QMainWindow):
##
##    def __init__(self, filename, nesting, separator, parent=None):
##        super(MainForm, self).__init__(parent)
##
##        headers = ["Server Tree"]
##        self.treeWidget = TreeOfTableWidget(catalog)
##        self.treeWidget.model().headers = headers
##
##
##        self.setCentralWidget(self.treeWidget)
##
####        QShortcut(QKeySequence("Escape"), self, self.close)
####        QShortcut(QKeySequence("Ctrl+Q"), self, self.close)
####
####        self.connect(self.treeWidget, SIGNAL("activated"),
####                     self.activated)
####
####        #self.setWindowTitle("Server Info")
####        #self.statusBar().showMessage("Ready...", 5000)
####
####
####    def picked(self):
####        return self.treeWidget.currentFields()
####
####    def activated(self, fields):
####        self.statusBar().showMessage("*".join(fields), 60000)
##
##
##app = QApplication(sys.argv)
##
##
##form = MainForm(os.path.join(os.path.dirname(__file__), "servers.txt"),
##                nesting, "*")
##form.resize(750, 550)
##form.show()
##app.exec_()
##print "*".join(form.picked())

