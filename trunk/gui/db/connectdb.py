import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
#from mynews.db.classDB2 import *

# ==== CONNECT ====
def getdbconnection():
    path = os.path.join(os.path.split(__file__)[0], 'sdbe.sqlite')
    #print path
    engine = create_engine('sqlite:///%s' % path, echo=True, encoding='utf-8')
    #engine = create_engine('postgresql://postgres:******@localhost:5432/postgres', echo=False, encoding='utf-8')
    # 0.6 +pg8000 +psycopg2
    #engine = create_engine('postgresql+psycopg2://postgres:******@localhost:5432/postgres', echo=False, encoding='utf-8')

    Session = sessionmaker(bind=engine)
    return Session()

db = getdbconnection()