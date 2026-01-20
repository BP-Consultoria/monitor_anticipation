import os
from typing import Optional
from dotenv import load_dotenv
import pyodbc

load_dotenv()

DB_ADRESS = os.getenv("DB_ADRESS")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_DRIVER = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
DB_PORT = os.getenv("DB_PORT")


def get_connection(
    timeout: int = 120
) -> pyodbc.Connection:
    
    server = DB_ADRESS
    if DB_PORT:
        server = f"{DB_ADRESS},{DB_PORT}"
    
    connection_string = (
        f"DRIVER={{{DB_DRIVER}}};"
        f"SERVER={server};"
        f"DATABASE={DB_NAME};"
        f"UID={DB_USER};"
        f"PWD={DB_PASSWORD};"
        f"Connection Timeout={timeout};"
        "TrustServerCertificate=yes;"
        "Encrypt=no;"
        "MultipleActiveResultSets=False;"
    )
    
    return pyodbc.connect(connection_string, timeout=timeout)