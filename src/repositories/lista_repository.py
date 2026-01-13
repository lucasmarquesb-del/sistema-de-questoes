"""Repository para Listas"""
from typing import List, Optional
from sqlalchemy.orm import Session
from models.orm import Lista, Questao, Tag, CodigoGenerator
from .base_repository import BaseRepository

class ListaRepository(BaseRepository[Lista]):
    def __init__(self, session: Session):
        super().__init__(Lista, session)
    
    def buscar_por_codigo(self, codigo: str) -> Optional[Lista]:
        return self.session.query(Lista).filter_by(codigo=codigo, ativo=True).first()
    
    def buscar_por_titulo(self, titulo: str) -> List[Lista]:
        return self.session.query(Lista).filter(Lista.titulo.ilike(f"%{titulo}%"), Lista.ativo == True).all()
    
    def buscar_por_tipo(self, tipo: str) -> List[Lista]:
        return self.session.query(Lista).filter_by(tipo=tipo, ativo=True).order_by(Lista.data_criacao.desc()).all()
    
    def criar_lista(self, titulo: str, tipo: str = 'LISTA', cabecalho: str = None, instrucoes: str = None) -> Lista:
        codigo = CodigoGenerator.gerar_codigo_lista(self.session)
        lista = Lista(codigo=codigo, titulo=titulo, tipo=tipo, cabecalho=cabecalho, instrucoes=instrucoes)
        self.session.add(lista)
        self.session.flush()
        return lista
    
    def adicionar_questao(self, codigo_lista: str, codigo_questao: str, ordem: int = None) -> bool:
        lista = self.buscar_por_codigo(codigo_lista)
        questao = self.session.query(Questao).filter_by(codigo=codigo_questao, ativo=True).first()
        if lista and questao:
            lista.adicionar_questao(self.session, questao, ordem)
            return True
        return False
    
    def remover_questao(self, codigo_lista: str, codigo_questao: str) -> bool:
        lista = self.buscar_por_codigo(codigo_lista)
        questao = self.session.query(Questao).filter_by(codigo=codigo_questao).first()
        if lista and questao:
            lista.remover_questao(self.session, questao)
            return True
        return False
    
    def reordenar_questoes(self, codigo_lista: str, codigos_questoes_ordenados: List[str]) -> bool:
        lista = self.buscar_por_codigo(codigo_lista)
        if lista:
            lista.reordenar_questoes(self.session, codigos_questoes_ordenados)
            return True
        return False
    
    def buscar_tags_relacionadas(self, codigo_lista: str) -> List[Tag]:
        lista = self.buscar_por_codigo(codigo_lista)
        return lista.buscar_tags_relacionadas(self.session) if lista else []
    
    def contar_questoes(self, codigo_lista: str) -> int:
        lista = self.buscar_por_codigo(codigo_lista)
        return lista.contar_questoes() if lista else 0
