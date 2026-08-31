from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

DATABASE_URL = "sqlite:///cafe_management_system.db"
engine=create_engine(DATABASE_URL,connect_args={'check_same_thread': False})

Base = declarative_base()
Sessionlocal = sessionmaker(bind=engine,autocommit=False,expire_on_commit=False)

def get_db():
    db = Sessionlocal()
    try:
        yield db
    finally:
        db.close()