from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from classdb import *
from connectdb import getdbconnection

# ==== CREATE TABLE ====
#Base = declarative_base()
db = getdbconnection()
metadata = Base.metadata
metadata.create_all(db.bind.engine)
db.close()