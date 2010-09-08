class SdbeTableView(QtGui.QTableView):
    def __init__(self, parent):
        super(SdbeTableView, self).__init__(parent)
        self.sqlTab = parent


    def verticalScrollbarAction(self, action):
        #print "verticalScrollbarAction:", action
        vertical = self.sqlTab.table.verticalScrollBar()
        #print "value:", vertical.value()
        #print "pageStep:", vertical.pageStep()
        #print "maximum:", vertical.maximum()
        if vertical.value() +  vertical.pageStep() > vertical.maximum():
            #print "fetchMore", vertical.value() +  vertical.pageStep()
            self.sqlTab.fetchMore()

    def changed(value):
        print value





class ExecuteThread(QtCore.QThread):
    def __init__(self, parent = None, db=None, sql='', sqlTab=None):
       QtCore.QThread.__init__(self, parent)
       self.alive = 1
       self.running = 0
       self.n = 0
       self.db = db
       self.sql = sql
       self.sqlTab= sqlTab
       #self.printMessage = printMessage

    def run(self):
        print "FOO"

        query = QtSql.QSqlQuery(db=self.db)
        query.setForwardOnly(True)
        query.exec_(self.sql)

        record = query.record()

        self.sqlTab.table.setModel(QtGui.QStandardItemModel(0, 0))

        # ==== ERROR ====
        if len(query.lastError().databaseText().toUtf8()) > 0:
            dbError = query.lastError().databaseText()
            driverError = query.lastError().driverText()

            self.printMessage([ ["Driver Error", "Database error"],
                                [driverError, dbError]
                                ])
        # ==== NOT SELECT ====
        elif record.isEmpty():
            self.printMessage([ ["STATUS", "Affected"],
                                ["OK", "Rows Affected: %s" % query.numRowsAffected()]
                                ])

        # ==== SELECT ====
        if query.isSelect():
            model = QtGui.QStandardItemModel(0, record.count())
            modelCopy = QtGui.QStandardItemModel(0, record.count())

            for i in range(record.count()):
                model.setHeaderData(i, QtCore.Qt.Horizontal, record.fieldName(i), role=0)
                modelCopy.setHeaderData(i, QtCore.Qt.Horizontal, record.fieldName(i), role=0)

            i = 0
            fetchRowsNum = 256
            devider = 1
            columnsLen = record.count()

##            print "start while"
##            while query.next() and self.alive == 1 and i < 100:
##            	model.insertRow(i, QtCore.QModelIndex())
##            	modelCopy.insertRow(i, QtCore.QModelIndex())
##
##                for j in xrange(columnsLen):
##                    model.setData(model.index(i, j, QtCore.QModelIndex()), query.value(j))
##                    modelCopy.setData(modelCopy.index(i, j, QtCore.QModelIndex()), query.value(j))
##                i += 1
##
##            print "set modelCopy"
##            self.sqlTab.table.setModel(modelCopy)

            # BIND ON START
            self.sqlTab.table.setModel(model)

            # FETCH MORE... ON SCHOOL TO BOTTOM ;p
            print "start while"
            while query.next() and self.alive == 1:
            	model.insertRow(i, QtCore.QModelIndex())

                for j in xrange(columnsLen):
                    model.setData(model.index(i, j, QtCore.QModelIndex()), query.value(j), role=0)
                i += 1

                while i > fetchRowsNum and self.alive == 1:
                    print "while -> fetchRowsNum:", fetchRowsNum
                    self.msleep(200)
##                if i == 50:
##                    print "setModel, i: %s, devider: %s" % (i, devider)
##                    #modelCopy = copy.copy(model)
##                    #print model, modelCopy
##                    #self.sqlTab.table.setModel(modelCopy)
##                    self.msleep(1000)
##                    devider *= 100
##

            print "set model"

            self.sqlTab.table.resizeColumnsToContents()
            #self.selectionModel = QtGui.QItemSelectionModel(model)
            #self.sqlTab.table.setSelectionModel(self.selectionModel)


    def printMessage(self, table):
        model = QtGui.QStandardItemModel(0, len(table[0]), self)

        for i, name in enumerate(table[0]):
            model.setHeaderData(i, QtCore.Qt.Horizontal, name)

        for i, row in enumerate(table[1:]):
            model.insertRow(i, QtCore.QModelIndex())

            for j, column in enumerate(row):
                model.setData(model.index(i, j, QtCore.QModelIndex()), column)

        self.sqlTab.table.setModel(model)
        self.sqlTab.table.resizeColumnsToContents()


    def toggle(self):
       if self.running:
           self.running = 0
       else:
           self.running = 1

    def stop(self):
       self.alive = 0




# ConnTab

        # SQLMODEL -> VIEW
##        query = QSqlForwardQuery(db=self.conn) #QtSql.QSqlQuery
##        #query.setForwardOnly(True)
##        print query.isForwardOnly()
##        query.exec_(sqlTab.getSql())
##        #query.setForwardOnly(False)
##        print query.isForwardOnly()
##
##        model = QtSql.QSqlQueryModel() # *model = new QSqlQueryModel;
##        model.setQuery(query);
##        sqlTab.table.setModel(model)

        # TABLEVIEW
        #query = QtSql.QSqlQuery(sqlTab.getSql(), db=self.conn)
        #record = query.record()
##        sqlTab.table.setModel(QtGui.QStandardItemModel(0, 0, self))
##        time.sleep(0.5)
##        try:
##            print "self.executeThread.stop()"
##            self.executeThread.stop()
##            del self.executeThread
##            print "Thread was stopped!!!"
##        except:
##            print "none running thread"
##        self.executeThread = ExecuteThread(self, db=self.conn, sql=sqlTab.getSql(), sqlTab=sqlTab)
##        self.executeThread.start()

        #sqlTab.table.setRowCount(0)
        #sqlTab.table.setColumnCount(0)

        # 1. IF ERROR
##        if len(query.lastError().databaseText().toUtf8()) > 0:
##            dbError = query.lastError().databaseText()
##            driverError = query.lastError().driverText()
##
##            self.printMessage([[dbError], [driverError]])
##        # NOT select?
##        elif record.isEmpty():
##            self.printMessage([["OK", "Rows Affected: %s" % query.numRowsAffected()]])
##
##        if query.isSelect():
##            pass

            # ==== NEW ====
##            model = QtGui.QStandardItemModel(0, record.count(), self) # QtSql.QSqlQueryModel(self) #10, record.count(),
##            gc.collect()
##            for i in range(record.count()):
##                model.setHeaderData(i, QtCore.Qt.Horizontal, record.fieldName(i))
##
##            i = 0
##            columnsLen = record.count()
##
##            while query.next():
##            	model.insertRow(i, QtCore.QModelIndex())
##
##                for j in xrange(columnsLen):
##                    model.setData(model.index(i, j, QtCore.QModelIndex()), query.value(j))
##                i += 1
##
##            sqlTab.table.setModel(model)
##            sqlTab.table.resizeColumnsToContents()
            #self.selectionModel = QtGui.QItemSelectionModel(model)
            #sqlTab.table.setSelectionModel(self.selectionModel)


################################
class testit(Thread):
    def __init__ (self,db, table, tableType):
        Thread.__init__(self)
        self.db = db
        self.tableName = table
        self.table = {}
        self.tableType = tableType
    def run(self):
        self.tableName
        t = self.db.record(self.tableName)
        self.table = {
            "TYPE": self.tableType,
            "COLUMNS": [(unicode(t.field(c).name()), t.field(c).type(), t.field(c).length()) for c in range(len(t))]
            }

class qtestit(QtCore.QThread):
    def __init__ (self, parent = None, db=None, table='', tableType=0):
        QtCore.QThread.__init__(self, parent)
        self.db = db
        self.tableName = table
        self.table = {}
        self.tableType = tableType
    def run(self):
        self.tableName
        t = self.db.record(self.tableName)
        self.table = {
            "TYPE": self.tableType,
            "COLUMNS": [(unicode(t.field(c).name()), t.field(c).type(), t.field(c).length()) for c in range(len(t))]
            }
        print "END of: %s" % self.tableName