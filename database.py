from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from config import load_config

config = load_config()
engine = create_engine(config["db_url"])
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

class Student(Base):
    __tablename__ = "students"
    student_id = Column(Integer, primary_key=True)
    tg_id = Column(Integer, unique=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    exam_type = Column(String, nullable=False)
    scores = relationship("Score", back_populates="student")

class Score(Base):
    __tablename__ = "scores"
    score_id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.student_id"), nullable=False, index=True)
    subject = Column(String, nullable=False)
    score = Column(Integer, nullable=False)
    student = relationship("Student", back_populates="scores")


def init_db():
    Base.metadata.create_all(engine)
