
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# This is the address of your database (like home address)
DATABASE_URL = os.getenv("DATABASE_URL")

# This creates a connection to the database
engine = create_engine(DATABASE_URL)

# This is how we open and close database sessions
SessionLocal = sessionmaker(bind=engine)

# This is the base class for all tables
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()