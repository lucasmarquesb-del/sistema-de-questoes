# -*- coding: utf-8 -*-
"""
Repository para operacoes com Disciplina.
"""

import logging
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.models.orm.disciplina import Disciplina

logger = logging.getLogger(__name__)


class DisciplinaRepository:
    """
    Repository para CRUD de disciplinas.
    
    Uso:
        repo = DisciplinaRepository(session)
        disciplinas = repo.listar_todas()
        disciplina = repo.buscar_por_codigo("MAT")
    """
    
    def __init__(self, session: Session):
        """
        Inicializa o repository.
        
        Args:
            session: Sessao do SQLAlchemy
        """
        self.session = session
    
    def listar_todas(self, apenas_ativas: bool = True) -> List[Disciplina]:
        """
        Lista todas as disciplinas.
        
        Args:
            apenas_ativas: Se True, retorna apenas disciplinas ativas
            
        Returns:
            Lista de Disciplina ordenada por 'ordem'
        """
        query = self.session.query(Disciplina)
        
        if apenas_ativas:
            query = query.filter(Disciplina.ativo == True)
        
        return query.order_by(Disciplina.ordem).all()
    
    def buscar_por_uuid(self, uuid_disciplina: str) -> Optional[Disciplina]:
        """
        Busca uma disciplina pelo UUID.
        
        Args:
            uuid_disciplina: UUID da disciplina
            
        Returns:
            Disciplina ou None se nao encontrar
        """
        return self.session.query(Disciplina).filter(
            Disciplina.uuid == uuid_disciplina
        ).first()
    
    def buscar_por_codigo(self, codigo: str) -> Optional[Disciplina]:
        """
        Busca uma disciplina pelo codigo (MAT, FIS, etc.).
        
        Args:
            codigo: Codigo da disciplina
            
        Returns:
            Disciplina ou None se nao encontrar
        """
        return self.session.query(Disciplina).filter(
            Disciplina.codigo == codigo.upper()
        ).first()
    
    def criar(self, dados: dict) -> Optional[Disciplina]:
        """
        Cria uma nova disciplina.
        
        Args:
            dados: Dicionario com os dados da disciplina
                   {codigo, nome, descricao?, cor?, ordem?, ativo?}
                   
        Returns:
            Disciplina criada ou None se falhar
        """
        try:
            disciplina = Disciplina(
                uuid=str(uuid.uuid4()),
                codigo=dados["codigo"].upper(),
                nome=dados["nome"],
                descricao=dados.get("descricao"),
                cor=dados.get("cor", "#3498db"),
                ordem=dados.get("ordem", 0),
                ativo=dados.get("ativo", True),
                data_criacao=datetime.now(),
            )
            
            self.session.add(disciplina)
            self.session.commit()
            
            logger.info(f"Disciplina criada: {disciplina.codigo}")
            return disciplina
            
        except IntegrityError as e:
            self.session.rollback()
            logger.error(f"Erro de integridade ao criar disciplina: {e}")
            return None
        except Exception as e:
            self.session.rollback()
            logger.error(f"Erro ao criar disciplina: {e}")
            return None
    
    def atualizar(self, uuid_disciplina: str, dados: dict) -> Optional[Disciplina]:
        """
        Atualiza uma disciplina.
        
        Args:
            uuid_disciplina: UUID da disciplina a atualizar
            dados: Dicionario com os campos a atualizar
            
        Returns:
            Disciplina atualizada ou None se falhar
        """
        try:
            disciplina = self.buscar_por_uuid(uuid_disciplina)
            if not disciplina:
                return None
            
            # Atualiza apenas os campos fornecidos
            if "codigo" in dados:
                disciplina.codigo = dados["codigo"].upper()
            if "nome" in dados:
                disciplina.nome = dados["nome"]
            if "descricao" in dados:
                disciplina.descricao = dados["descricao"]
            if "cor" in dados:
                disciplina.cor = dados["cor"]
            if "ordem" in dados:
                disciplina.ordem = dados["ordem"]
            if "ativo" in dados:
                disciplina.ativo = dados["ativo"]
            
            self.session.commit()
            
            logger.info(f"Disciplina atualizada: {disciplina.codigo}")
            return disciplina
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Erro ao atualizar disciplina: {e}")
            return None
    
    def inativar(self, uuid_disciplina: str) -> bool:
        """
        Inativa uma disciplina (soft delete).
        
        Args:
            uuid_disciplina: UUID da disciplina a inativar
            
        Returns:
            True se inativado com sucesso
        """
        try:
            disciplina = self.buscar_por_uuid(uuid_disciplina)
            if not disciplina:
                return False
            
            disciplina.ativo = False
            self.session.commit()
            
            logger.info(f"Disciplina inativada: {disciplina.codigo}")
            return True
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Erro ao inativar disciplina: {e}")
            return False
    
    def ativar(self, uuid_disciplina: str) -> bool:
        """
        Ativa uma disciplina.
        
        Args:
            uuid_disciplina: UUID da disciplina a ativar
            
        Returns:
            True se ativado com sucesso
        """
        try:
            disciplina = self.buscar_por_uuid(uuid_disciplina)
            if not disciplina:
                return False
            
            disciplina.ativo = True
            self.session.commit()
            
            logger.info(f"Disciplina ativada: {disciplina.codigo}")
            return True
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Erro ao ativar disciplina: {e}")
            return False
    
    def listar_para_select(self) -> List[tuple]:
        """
        Retorna lista formatada para uso em combobox/select.
        
        Returns:
            Lista de tuplas (uuid, "codigo - nome")
        """
        disciplinas = self.listar_todas(apenas_ativas=True)
        return [(d.uuid, f"{d.codigo} - {d.nome}") for d in disciplinas]
    
    def listar_para_select_com_cor(self) -> List[dict]:
        """
        Retorna lista formatada para uso em combobox com cor.
        
        Returns:
            Lista de dicts {uuid, codigo, nome, cor}
        """
        disciplinas = self.listar_todas(apenas_ativas=True)
        return [
            {
                "uuid": d.uuid,
                "codigo": d.codigo,
                "nome": d.nome,
                "cor": d.cor,
                "texto": f"{d.codigo} - {d.nome}",
            }
            for d in disciplinas
        ]
    
    def popular_padrao(self) -> int:
        """
        Popula com disciplinas padrao. 
        
        Retorna quantidade inserida.
        """
        padrao = Disciplina.get_disciplinas_padrao()
        inseridas = 0
        
        for dados in padrao:
            existente = self.buscar_por_codigo(dados["codigo"])
            if not existente:
                if self.criar(dados):
                    inseridas += 1
        
        logger.info(f"Disciplinas padrao inseridas: {inseridas}")
        return inseridas
    
    def contar_tags_por_disciplina(self, uuid_disciplina: str) -> int:
        """
        Conta quantas tags pertencem a uma disciplina.
        
        Args:
            uuid_disciplina: UUID da disciplina
            
        Returns:
            Quantidade de tags
        """
        disciplina = self.buscar_por_uuid(uuid_disciplina)
        if disciplina:
            return disciplina.total_conteudos
        return 0
