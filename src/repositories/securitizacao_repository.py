from typing import List, Dict, Any
import pandas as pd
from database.connection import get_connection


class SecuritizacaoRepository:
    
    def __init__(self):
        self.connection = get_connection()
    
    def close(self):
        if self.connection:
            self.connection.close()

    def _fetch_as_dict(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Método auxiliar para converter resultados do cursor em lista de dicionários."""
        cursor = self.connection.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        # Pega o nome das colunas
        columns = [column[0] for column in cursor.description]
        # Faz o merge das colunas com os valores de cada linha
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        cursor.close()
        return results

    def get_done_bordero_today(self) -> List[Dict[str, Any]]:
        query = """
            SELECT bordero
            FROM SIGBORS
            WHERE CONVERT(date, DATA) = CONVERT(date, GETDATE())
            AND EstadoBordero = 'CONCLUIDO'
        """
        # Retornamos como dicionário para manter a consistência com o seu .to_dict('records')
        return self._fetch_as_dict(query)
    
    def get_bordero_info(self, bordero_id: int) -> List[Dict[str, Any]]:
        query = """
            SELECT CLIFOR, SACADO, DCTO, VALOR, VCTO_, EMISSAO
            FROM SIGFLU
            WHERE BORDERO = ?
        """
        return self._fetch_as_dict(query, (bordero_id,))
    
    def check_sacado_in_group(self, group_number: int, sacado_id: int) -> List[Dict[str, Any]]:
        query = """
            SELECT clifor
            FROM GrupoEmpresa
            WHERE idgrupo = ? AND clifor = ?
        """
        return self._fetch_as_dict(query, (group_number, sacado_id))
    
    def get_sacado_info(self, codigo: int) -> List[Dict[str, Any]]:
        query = """
            SELECT NOME, CGC
            FROM SIGCAD
            WHERE CODIGO = ?
        """
        return self._fetch_as_dict(query, (codigo,))
    
    def get_cedente_name(self, cedente_id: int) -> List[Dict[str, Any]]:
        query = """
            SELECT NOME
            FROM SIGCAD
            WHERE CODIGO = ?
        """
        return self._fetch_as_dict(query, (cedente_id,))