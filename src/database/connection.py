import os
from typing import Optional
from dotenv import load_dotenv
import pyodbc

load_dotenv()

DB_ADRESS = os.getenv("DB_ADRESS")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME_SERVER_NAME = os.getenv("DB_NAME_SERVER_NAME")
DB_DRIVER = os.getenv("DB_DRIVER")


def get_connection(
) -> pyodbc.Connection:
    
    connection_string = (
        f"DRIVER={{{DB_DRIVER}}};"
        f"SERVER={DB_ADRESS}"
        f"DATABASE={DB_NAME_SERVER_NAME};"
        f"UID={DB_USER};"
        f"PWD={DB_PASSWORD};"
        "TrustServerCertificate=no;"
    )
    
    return pyodbc.connect(connection_string)