import os
from dotenv import load_dotenv
from database.connection import get_connection

load_dotenv()

print("Testando conexão com o banco de dados...")
print(f"DB_ADRESS: {os.getenv('DB_ADRESS')}")
print(f"DB_NAME: {os.getenv('DB_NAME')}")
print(f"DB_USER: {os.getenv('DB_USER')}")
print(f"DB_DRIVER: {os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server')}")
print(f"DB_PORT: {os.getenv('DB_PORT', 'não configurado (usando padrão 1433)')}")
print("-" * 50)

try:
    print("Tentando conectar...")
    conn = get_connection(timeout=120)
    print("✓ Conexão estabelecida com sucesso!")
    
    cursor = conn.cursor()
    cursor.execute("SELECT @@VERSION")
    version = cursor.fetchone()
    print(f"✓ Versão do SQL Server: {version[0][:50]}...")
    
    cursor.close()
    conn.close()
    print("✓ Conexão fechada com sucesso!")
    
except Exception as e:
    print(f"✗ Erro ao conectar: {e}")
    import traceback
    traceback.print_exc()

