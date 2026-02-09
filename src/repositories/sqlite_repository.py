from typing import List, Optional, Dict, Any
import pandas as pd
from sqlalchemy.orm import Session
from models.models import Antecipacao, get_session


class SQLiteRepository:
    
    def __init__(self, session: Optional[Session] = None):
        self.session = session or get_session()
    
    def save(self, antecipacao: Antecipacao) -> Antecipacao:
        self.session.add(antecipacao)
        self.session.commit()
        self.session.refresh(antecipacao)
        return antecipacao
    
    def update(self, antecipacao: Antecipacao) -> Antecipacao:
        self.session.commit()
        self.session.refresh(antecipacao)
        return antecipacao
    
    def get_by_id(self, antecipacao_id: int) -> Optional[Antecipacao]:
        return self.session.query(Antecipacao).filter(Antecipacao.id == antecipacao_id).first()
    
    def mark_as_inserted(self, antecipacao_id: int) -> bool:
        antecipacao = self.get_by_id(antecipacao_id)
        if antecipacao:
            antecipacao.is_inserted = True
            self.session.commit()
            return True
        return False
    
    def insert_antecipacao(
        self,
        cedente: str,
        sacado: str,
        bordero: int,
        cnpj_sacado: Optional[str] = None,
        titulo: Optional[int] = None,
        valor: Optional[float] = None,
        emissao: Optional[str] = None,
        vencimento: Optional[str] = None,
        portal_email: Optional[str] = None,
        login: Optional[str] = None,
        senha: Optional[str] = None,
        is_inserted: bool = False
    ) -> Antecipacao:
        
        antecipacao = Antecipacao(
            bordero=bordero,
            cedente=cedente,
            sacado=sacado,
            cnpj_sacado=cnpj_sacado,
            titulo=titulo,
            valor=valor,
            emissao=emissao,
            vencimento=vencimento,
            portal_email=portal_email,
            login=login,
            senha=senha,
            is_inserted=is_inserted
        )
        return self.save(antecipacao)
    
    def get_all_antecipations_as_dataframe(self) -> pd.DataFrame:
        query = self.session.query(Antecipacao)
        df = pd.read_sql(query.statement, self.session.bind)
        return df
    
    def antecipations_exists(self, bordero: int, titulo: int, cnpj_sacado: str | None) -> bool:
        
        return (
            self.session.query(Antecipacao)
            .filter(
                Antecipacao.bordero == bordero,
                Antecipacao.titulo == titulo,
                Antecipacao.cnpj_sacado == cnpj_sacado
            ).first()
            is not None
        )