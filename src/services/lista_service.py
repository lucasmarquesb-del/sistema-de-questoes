"""
Service para gerenciar Listas - usa apenas ORM
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from repositories import ListaRepository, QuestaoRepository


class ListaService:
    """Service para operações de negócio com listas"""

    def __init__(self, session: Session):
        self.session = session
        self.lista_repo = ListaRepository(session)
        self.questao_repo = QuestaoRepository(session)

    def criar_lista(
        self,
        titulo: str,
        tipo: str = 'LISTA',
        cabecalho: Optional[str] = None,
        instrucoes: Optional[str] = None,
        codigos_questoes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Cria uma lista de questões

        Args:
            titulo: Título da lista
            tipo: PROVA, LISTA ou SIMULADO
            cabecalho: Cabeçalho personalizado
            instrucoes: Instruções gerais
            codigos_questoes: Lista de códigos de questões para adicionar

        Returns:
            Dict com dados da lista criada
        """
        lista = self.lista_repo.criar_lista(titulo, tipo, cabecalho, instrucoes)

        # Adicionar questões se fornecidas
        if codigos_questoes:
            for ordem, codigo in enumerate(codigos_questoes, start=1):
                self.lista_repo.adicionar_questao(lista.codigo, codigo, ordem)

        self.session.flush()

        return {
            'codigo': lista.codigo,
            'uuid': lista.uuid,
            'titulo': lista.titulo,
            'tipo': lista.tipo,
            'total_questoes': len(codigos_questoes) if codigos_questoes else 0
        }

    def buscar_lista(self, codigo: str) -> Optional[Dict[str, Any]]:
        """
        Busca lista por código

        Args:
            codigo: Código da lista (LST-XXXX-YYYY)

        Returns:
            Dict com dados completos da lista
        """
        lista = self.lista_repo.buscar_por_codigo(codigo)
        if not lista:
            return None

        # Buscar tags relacionadas
        tags = self.lista_repo.buscar_tags_relacionadas(codigo)

        return {
            'codigo': lista.codigo,
            'uuid': lista.uuid,
            'titulo': lista.titulo,
            'tipo': lista.tipo,
            'cabecalho': lista.cabecalho,
            'instrucoes': lista.instrucoes,
            'questoes': [
                {
                    'codigo': q.codigo,
                    'titulo': q.titulo,
                    'tipo': q.tipo.codigo if q.tipo else None
                }
                for q in lista.questoes if q.ativo
            ],
            'tags_relacionadas': [tag.nome for tag in tags],
            'total_questoes': lista.contar_questoes()
        }

    def listar_listas(self, tipo: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Lista todas as listas, opcionalmente filtradas por tipo

        Args:
            tipo: Tipo opcional (PROVA, LISTA, SIMULADO)

        Returns:
            Lista de dicts
        """
        if tipo:
            listas = self.lista_repo.buscar_por_tipo(tipo)
        else:
            listas = self.lista_repo.listar_todos()

        return [
            {
                'codigo': l.codigo,
                'uuid': l.uuid,
                'titulo': l.titulo,
                'tipo': l.tipo,
                'total_questoes': l.contar_questoes()
            }
            for l in listas
        ]

    def adicionar_questao(
        self,
        codigo_lista: str,
        codigo_questao: str,
        ordem: Optional[int] = None
    ) -> bool:
        """Adiciona questão à lista"""
        return self.lista_repo.adicionar_questao(codigo_lista, codigo_questao, ordem)

    def remover_questao(self, codigo_lista: str, codigo_questao: str) -> bool:
        """Remove questão da lista"""
        return self.lista_repo.remover_questao(codigo_lista, codigo_questao)

    def reordenar_questoes(
        self,
        codigo_lista: str,
        codigos_ordenados: List[str]
    ) -> bool:
        """Reordena questões da lista"""
        return self.lista_repo.reordenar_questoes(codigo_lista, codigos_ordenados)

    def deletar_lista(self, codigo: str) -> bool:
        """Desativa lista (soft delete)"""
        lista = self.lista_repo.buscar_por_codigo(codigo)
        if lista:
            lista.ativo = False
            self.session.flush()
            return True
        return False
