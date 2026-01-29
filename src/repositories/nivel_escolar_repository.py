# -*- coding: utf-8 -*-
"""
Repository para operacoes com NivelEscolar.
"""

import logging
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from src.models.orm.nivel_escolar import NivelEscolar

logger = logging.getLogger(__name__)


class NivelEscolarRepository:
    """
    Repository para CRUD de niveis escolares.
    
    Uso:
        repo = NivelEscolarRepository(session)
        niveis = repo.listar_todos()
        nivel = repo.buscar_por_codigo("EM")
    """
    
    def __init__(self, session: Session):
        """
        Inicializa o repository.
        
        Args:
            session: Sessao do SQLAlchemy
        """
        self.session = session
    
    def listar_todos(self, apenas_ativos: bool = True) -> List[NivelEscolar]:
        """
        Lista todos os niveis escolares.
        
        Args:
            apenas_ativos: Se True, retorna apenas niveis ativos
            
        Returns:
            Lista de NivelEscolar ordenada por 'ordem'
        """
        query = self.session.query(NivelEscolar)
        
        if apenas_ativos:
            query = query.filter(NivelEscolar.ativo == True)
        
        return query.order_by(NivelEscolar.ordem).all()
    
    def buscar_por_uuid(self, uuid_nivel: str) -> Optional[NivelEscolar]:
        """
        Busca um nivel pelo UUID.
        
        Args:
            uuid_nivel: UUID do nivel
            
        Returns:
            NivelEscolar ou None se nao encontrar
        """
        return self.session.query(NivelEscolar).filter(
            NivelEscolar.uuid == uuid_nivel
        ).first()
    
    def buscar_por_codigo(self, codigo: str) -> Optional[NivelEscolar]:
        """
        Busca um nivel pelo codigo (EF1, EM, etc.).
        
        Args:
            codigo: Codigo do nivel
            
        Returns:
            NivelEscolar ou None se nao encontrar
        """
        return self.session.query(NivelEscolar).filter(
            NivelEscolar.codigo == codigo.upper()
        ).first()
    
    def criar(self, dados: dict) -> Optional[NivelEscolar]:
        """
        Cria um novo nivel escolar.
        
        Args:
            dados: Dicionario com os dados do nivel
                   {codigo, nome, descricao?, ordem?, ativo?}
                   
        Returns:
            NivelEscolar criado ou None se falhar
        """
        try:
            nivel = NivelEscolar(
                uuid=str(uuid.uuid4()),
                codigo=dados["codigo"].upper(),
                nome=dados["nome"],
                descricao=dados.get("descricao"),
                ordem=dados.get("ordem", 0),
                ativo=dados.get("ativo", True),
                data_criacao=datetime.now(),
            )
            
            self.session.add(nivel)
            self.session.commit()
            
            logger.info(f"Nivel escolar criado: {nivel.codigo}")
            return nivel
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Erro ao criar nivel: {e}")
            return None
    
    def atualizar(self, uuid_nivel: str, dados: dict) -> Optional[NivelEscolar]:
        """
        Atualiza um nivel escolar.
        
        Args:
            uuid_nivel: UUID do nivel a atualizar
            dados: Dicionario com os campos a atualizar
            
        Returns:
            NivelEscolar atualizado ou None se falhar
        """
        try:
            nivel = self.buscar_por_uuid(uuid_nivel)
            if not nivel:
                return None
            
            if "codigo" in dados:
                nivel.codigo = dados["codigo"].upper()
            if "nome" in dados:
                nivel.nome = dados["nome"]
            if "descricao" in dados:
                nivel.descricao = dados["descricao"]
            if "ordem" in dados:
                nivel.ordem = dados["ordem"]
            if "ativo" in dados:
                nivel.ativo = dados["ativo"]
            
            self.session.commit()
            
            logger.info(f"Nivel escolar atualizado: {nivel.codigo}")
            return nivel
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Erro ao atualizar nivel: {e}")
            return None
    
    def inativar(self, uuid_nivel: str) -> bool:
        """
        Inativa um nivel escolar (soft delete).
        
        Args:
            uuid_nivel: UUID do nivel a inativar
            
        Returns:
            True se inativado com sucesso
        """
        try:
            nivel = self.buscar_por_uuid(uuid_nivel)
            if not nivel:
                return False
            
            nivel.ativo = False
            self.session.commit()
            
            logger.info(f"Nivel escolar inativado: {nivel.codigo}")
            return True
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Erro ao inativar nivel: {e}")
            return False
    
    def listar_para_select(self) -> List[tuple]:
        """
        Retorna lista formatada para uso em combobox/select.
        
        Returns:
            Lista de tuplas (uuid, "codigo - nome")
        """
        niveis = self.listar_todos(apenas_ativos=True)
        return [(n.uuid, f"{n.codigo} - {n.nome}") for n in niveis]
    
    def popular_padrao(self) -> int:
        """
        Popula com niveis padrao.
        
        Retorna quantidade inserida.
        """
        padrao = NivelEscolar.get_niveis_padrao()
        inseridos = 0
        
        for dados in padrao:
            existente = self.buscar_por_codigo(dados["codigo"])
            if not existente:
                if self.criar(dados):
                    inseridos += 1
        
        logger.info(f"Niveis escolares padrao inseridos: {inseridos}")
        return inseridos
    
    def buscar_por_uuids(self, uuids: List[str]) -> List[NivelEscolar]:
        """
        Busca multiplos niveis por uma lista de UUIDs.
        
        Args:
            uuids: Lista de UUIDs
            
        Returns:
            Lista de NivelEscolar encontrados
        """
        if not uuids:
            return []
        
        return self.session.query(NivelEscolar).filter(
            NivelEscolar.uuid.in_(uuids)
        ).all()
