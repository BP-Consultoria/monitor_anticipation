from typing import List, Optional, Dict, Any
import pandas as pd
from database.connection import get_connection


class SecuritizacaoRepository:
    
    def __init__(self):
        self.connection = get_connection()
    
    def execute_query(self, query: str) -> pd.DataFrame:
        return pd.read_sql(query, self.connection)

    def close(self):
        if self.connection:
            self.connection.close()
            
    def get_done_bordero_today(self) -> pd.DataFrame:
        query = """
            SELECT bordero
            FROM SIGBORS
            WHERE CONVERT(date, DATA) = CONVERT(date, GETDATE())
              AND EstadoBordero = 'CONCLUIDO'
        """
        return pd.read_sql(query, self.connection)
    
    def get_bordero_info(self, bordero_id: int) -> pd.DataFrame:
        query = """
            SELECT CLIFOR, SACADO, DCTO, VALOR, VCTO_
            FROM SIGFLU
            WHERE BORDERO = ?
        """
        return pd.read_sql(query, self.connection, params=(bordero_id,))
    
    def check_sacado_in_group(self, group_number: int, sacado_id: int) -> pd.DataFrame:
        query = """
            SELECT *
            FROM GrupoEmpresa
            WHERE idgrupo = ? AND clifor = ?
        """
        return pd.read_sql(query, self.connection, params=(group_number, sacado_id))
    
    def get_sacado_info(self, codigo: int) -> pd.DataFrame:
        query = """
            SELECT NOME, CGC
            FROM SIGCAD
            WHERE CODIGO = ?
        """
        return pd.read_sql(query, self.connection, params=(codigo,))
    
    def get_cedente_name(self, cedente_id: int) -> pd.DataFrame:
        query = """
            SELECT NOME
            FROM SIGCAD
            WHERE CODIGO = ?
        """
        return pd.read_sql(query, self.connection, params=(cedente_id,))