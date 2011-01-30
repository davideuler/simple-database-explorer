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

class CatalogTreeModel(treeoftable.TreeOfTableModel):

    def __init__(self, parent=None):
        super(CatalogTreeModel, self).__init__(parent)


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


class CatalogTree(QTreeView):

    def __init__(self, catalog, nesting=3, parent=None):
        super(CatalogTree, self).__init__(parent)
        self.setSelectionBehavior(QTreeView.SelectItems)
        self.setUniformRowHeights(True)
        model = CatalogTreeModel(self)
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



