from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
print(os.path.abspath("autogpt.db"))

db = SQLAlchemy()

DATABASE_URL = "sqlite:///autogpt.db"  # Update this with your actual database URL

engine = create_engine(DATABASE_URL, convert_unicode=True)
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()
print("dbMANUAL")
print(Base.query)
def init_db():
    import autogpt.models
    Base.metadata.create_all(bind=engine)



