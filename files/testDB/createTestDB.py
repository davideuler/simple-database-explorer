import sqlite3
import datetime
import random
import time

connString = ["BigTypes.sqlite", ""][0]

foo = sqlite3.connect(connString)

foo.execute('''CREATE TABLE "TYPES" (
                "ID" INTEGER NOT NULL ,
                "BOOL" BOOL,
                "DATE" DATE,
                "TIMESTAMP" TIMESTAMP,
                "DOUBLE" DOUBLE,
                "FLOAT" FLOAT,
                "REAL" REAL,
                "CHAR" CHAR,
                "TEXT" TEXT,
                "VARCHAR" VARCHAR,
                "BLOB" BLOB,
                "NUMERIC" NUMERIC
                )''')

c = foo.cursor()
times = 2000000

# INSERT
startTime = time.time()

today = datetime.date.today()

for i in xrange(times):
    c.execute("""insert into TYPES values (%s ,
                %s,
                '%s',
                '%s',
                %s,
                %s,
                %s,
                '%s',
                '%s',
                '%s',
                '%s',
                %s);""" % (
                    i,
                    random.randint(0, 1),
                    today,
                    datetime.datetime.now(),
                    random.random(),
                    random.random(),
                    random.random(),
                    "A", "TEXT: Našud Timš ", "Našud Timš", "BLOB: Našud Timš",
                    1111111111111111      ))

foo.commit()
endTime = time.time()
totalTime = endTime - startTime

print "INSERT/sekundo: %s" % int(times / totalTime)


# SELECT
startTime = time.time()
select = c.execute("SELECT * FROM TYPES").fetchall()
endTime = time.time()
totalTime = endTime - startTime

print "SELECT/sekundo: %s" % int(len(select) / totalTime)

# MEMORY
##INSERT/sekundo: 10537
##SELECT/sekundo: 43478
# DB
##INSERT/sekundo: 6653
##SELECT/sekundo: 29411


