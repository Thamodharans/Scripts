import datetime
from sqlalchemy import BigInteger, Column, Integer, String, Text, DateTime
from app.db import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    job_id = Column(String(50), unique=True, index=True)
    query_url = Column(Text, nullable=False)
    interval = Column(Integer)
    filenames = Column(Text)
    keywords = Column(Text)
    words_count = Column(Integer)
    status = Column(String(20), default="queued")
    last_run = Column(DateTime)
    output_links = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Run(Base):
    __tablename__ = "runs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(50), index=True)
    state = Column(String(20))
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    error = Column(Text)


class Artifact(Base):
    __tablename__ = "artifacts"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, index=True)
    type = Column(String(20))
    path = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
