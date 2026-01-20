from sqlalchemy import create_engine, Column, Integer, String, Float, VARCHAR, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()

SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "database.db")


class Antecipacao(Base):
    __tablename__ = "antecipacao"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    bordero = Column(Integer, nullable=True)
    cedente = Column(String, nullable=False)
    sacado = Column(String, nullable=False)
    cnpj_sacado = Column(VARCHAR(14), nullable=True)
    titulo = Column(Integer, nullable=True)
    valor = Column(Float, nullable=True)
    vencimento = Column(VARCHAR(10), nullable=True)
    portal_email = Column(String, nullable=True)
    login = Column(VARCHAR(255), nullable=True)
    senha = Column(VARCHAR(255), nullable=True)
    is_inserted = Column(Boolean, default=False)


def get_sqlite_engine(db_path: str = None):
    if db_path is None:
        db_path = SQLITE_DB_PATH
    
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    return engine


def init_database(db_path: str = None):
    engine = get_sqlite_engine(db_path)
    Base.metadata.create_all(engine)
    return engine


def get_session(db_path: str = None):
    engine = get_sqlite_engine(db_path)
    Session = sessionmaker(bind=engine)
    return Session()