from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, Integer, Float, String, MetaData, ForeignKey, Text, DateTime, Unicode
from sqlalchemy.orm import relation, backref
import time
##import logging

Base = declarative_base()

#==== ==== ==== ====
# Connection
#==== ==== ==== ====
class Connection(Base):
    __tablename__  = "connection"

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(128))
    user = Column(Unicode(128))
    password = Column(Unicode(128))
    schema = Column(Unicode(128))
    #info = relation('ProcessLog', backref='process_log')

    def __init__(self, name, user, password, schema=''):
        self.name = name
        self.user = user
        self.password = password
        self.schema = schema

    def __repr__(self):
        return "<Connection('%s','%s')>" % (self.name, self.user)

##Level	Numeric value
##CRITICAL    50
##ERROR       40
##WARNING	  30
##INFO        20
##DEBUG       10
##NOTSET      0

##class SqlAlchemyHandler(logging.Handler):
##    def __init__(self, processStep):
##        logging.Handler.__init__(self)
##        self.processStep = processStep
##
##    def emit(self, record):
##        try:
##            #record.msg.levelname = record.levelname
##            self.processStep.info.append(record.msg)
##        except Exception, inst:
##            print inst
##
##    def close(self):
##        logging.Handler.close(self)
##
##class NullHandler(logging.Handler):
##    def emit(self, record):
##        pass
##
##Base = declarative_base()
##
###==== ==== ==== ====
### PROCESS STEP
###==== ==== ==== ====
##class ProcessStep(Base):
##    __tablename__  = "process_step"
##
##    process_step_id = Column(Integer, primary_key=True)
##    name = Column(Unicode(50))
##    info = relation('ProcessLog', backref='process_log')
##
##    def __init__(self, step, name, logLevel=None, logName=__name__):
##        self.step = step
##        self.name = name
##        self.logName = logName
##        self.logLevel = logLevel
##        self.setUpLogger()
##
##    def setUpLogger(self):
##        self.logger = logging.getLogger(self.logName) #process_name
##        if self.logLevel == None:
##            customHandler = NullHandler()
##        else:
##            customHandler = SqlAlchemyHandler(self)
##            self.logger.setLevel(self.logLevel)
##            customHandler.setLevel(self.logLevel)
##
##        self.logger.handlers = []
##        self.logger.addHandler(customHandler)
##
##    def getVariables(self, abstractRun):
##        for var in abstractRun.__dict__:
##            value = getattr(abstractRun, var)
##            self.logger.info(ProcessLog(self.process_step_id,  unicode(var), unicode(value)))
##
##    def callbackLogger(self, logLever, var, value):
##        self.logger.log(logLever, ProcessLog(self.process_step_id,  unicode(var), unicode(value)))
##
##    def start(self, abstractRun):
##        print "=== 1. START ===="
##        startTime = time.time()
##        self.logger.debug(ProcessLog(self.process_step_id,  u'START', u'START'))
##        print " == VARIABLES =="
##        #self.getVariables(abstractRun)
##
##        # START
##        try:
##            abstractRun.run()
##        except Exception, inst:
##            print "!!!! 2.ERROR !!!!"
##            self.logger.error(ProcessLog(self.process_step_id,  u'ERROR', unicode(inst)))
##
##        print "=== 3. END ===="
##        #self.getVariables(abstractRun)
##        self.logger.debug(ProcessLog(self.process_step_id,  u'END', u'END'))
##        print "=== 5. TIME ===="
##        endTime = time.time()
##        print endTime - startTime
##        return abstractRun.getReturnValue()
##
##    def __repr__(self):
##        return "<ProcessStep('%s','%s')>" % (self.process_step_id, self.name)
##
##
##
###==== ==== ==== ====
### PROCESS LOG
###==== ==== ==== ====
##class ProcessLog(Base):
##    __tablename__  = "process_log"
##
##    process_log_id = Column(Integer, primary_key=True)
##    process_step_id = Column(Integer, ForeignKey(ProcessStep.process_step_id))
##    time = Column(DateTime, default=datetime.now)
##    var = Column(Unicode(50))
##    value = Column(Unicode(10000))
##
##    def __init__(self, process_step_id, var, value):
##        self.process_step_id = process_step_id
##        self.var = var
##        self.value = value
##
##    def __repr__(self):
##        return "<ProcessLog('%s','%s','%s','%s')>" % (self.process_step_id, self.time, self.var, self.value)
##
###==== ==== ==== ====
### INFO (0: INFO, 1: VAR, -1: ERROR, 2: DEBUG)
###==== ==== ==== ====
##class Info:
##    def __init__(self, infoType, var, value):
##        self.infoType = infoType
##        self.var = unicode(var)
##        self.value = unicode(value)
##
##    def __repr__(self):
##        return "<Info('%s','%s','%s')>" % (self.infoType, self.var, self.value)
##
###==== ==== ==== ====
### ABSTRACT RUN
###==== ==== ==== ====
##class AbstractRun():
##    '''
##    - 1. obširen LOG (yield INFO, ERROR, WARNING, ki jih želiš) [OK]
##    - 1.1 dobiš vse variable znotraj AbstracRun [OK]
##    - 2. podaš razne argumente (za razliko od infe) [OK]
##    - 3. dobiš čas trajanja [OK]
##    - # 4. Connection pool: je difiniran na "serverju", ti sam vzames iz pula, ki naj bi bil dict...
##    - # 5. sproti lahko vidiš število vrstic, ki jih je že opravil (vmesnik ala demo collector)
##        za vsako povezavo posebej... (source in target)'''
##
##    def __init__(self, name, callbackLogger=None):
##        self.name = name
##        self.callbackLogger = callbackLogger
##        self.speed = 0
##        self.returnValue = None
##
##    def run(self):
##        self.callbackLogger(10, u'-', u'Inside AbstractRun')
##
##    def returnLifeInfo(self):
##        '''return live data about rows/second for each connection'''
##        pass
##
##    def getReturnValue(self):
##        return self.returnValue
##
### ************************************************************
### ************************************************************
### ************************************************************
###==== ==== ==== ====
### DUMMY
###==== ==== ==== ====
##class Dummy(AbstractRun):
##
##    def __init__(self, name, linkToRSS, n, callbackLogger=None):
##        AbstractRun.__init__(self, name, callbackLogger)
##        self.linkToRSS = linkToRSS
##        self.n = n
##
##    def run(self):
##        AbstractRun.run(self)
##        for i in xrange(self.n):
##            print i
##
##        print nebosdf
##
##        self.callbackLogger(10, u'-', u'Inside dummy 10')
##        self.callbackLogger(20, u'-', u'Inside dummy 20')
##        self.returnValue = "From Dummy: I did good!"
##
### ************************************************************
##def main():
##    """
##     - loggging lever should be in perent Process, name also
##     - there should be no name in process step, forein key to definition of step
##    """
##    p = ProcessStep(0, u"0 - Step get html.", logging.DEBUG, 'getHtml')
##    d = Dummy("Dummy 1", "http://....", 10, p.callbackLogger)
##
##    print "*** Return value = %s" % p.start(d)
##
##    db.add(p)
##    db.commit()
##
##if __name__ == '__main__':
##    main()