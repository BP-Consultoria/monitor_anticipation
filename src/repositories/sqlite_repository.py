from typing import List, Optional
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
    
    def save_bulk(self, antecipacoes: List[Antecipacao]) -> List[Antecipacao]:
        self.session.add_all(antecipacoes)
        self.session.commit()
        for antecipacao in antecipacoes:
            self.session.refresh(antecipacao)
        return antecipacoes
    
    def get_by_id(self, antecipacao_id: int) -> Optional[Antecipacao]:
        return self.session.query(Antecipacao).filter(Antecipacao.id == antecipacao_id).first()
    
    def get_all(self) -> List[Antecipacao]:
        return self.session.query(Antecipacao).all()
    
    def get_not_inserted(self) -> List[Antecipacao]:
        return self.session.query(Antecipacao).filter(Antecipacao.is_inserted == False).all()
    
    def get_by_cedente(self, cedente: str) -> List[Antecipacao]:
        return self.session.query(Antecipacao).filter(Antecipacao.cedente == cedente).all()
    
    def get_by_sacado(self, sacado: str) -> List[Antecipacao]:
        return self.session.query(Antecipacao).filter(Antecipacao.sacado == sacado).all()
    
    def update(self, antecipacao: Antecipacao) -> Antecipacao:
        self.session.commit()
        self.session.refresh(antecipacao)
        return antecipacao
    
    def mark_as_inserted(self, antecipacao_id: int) -> bool:
        antecipacao = self.get_by_id(antecipacao_id)
        if antecipacao:
            antecipacao.is_inserted = True
            self.session.commit()
            return True
        return False
