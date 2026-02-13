"""
Service para gerenciar Listas - usa apenas ORM
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from src.repositories import ListaRepository, QuestaoRepository


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
        formulas: Optional[str] = None,
        codigos_questoes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Cria uma lista de questões

        Args:
            titulo: Título da lista
            tipo: PROVA, LISTA ou SIMULADO
            formulas: Caixa de fórmulas (LaTeX)
            codigos_questoes: Lista de códigos de questões para adicionar

        Returns:
            Dict com dados da lista criada
        """
        lista = self.lista_repo.criar_lista(titulo, tipo, formulas)

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

        # Buscar questoes com dados completos
        questoes_data = []
        for q in lista.questoes:
            if not q.ativo:
                continue

            # Buscar fonte: primeiro tenta o campo fonte, depois nas tags (numeracao começa com V)
            fonte_nome = None
            if q.fonte:
                fonte_nome = q.fonte.sigla
            else:
                # Buscar nas tags de vestibular
                for tag in q.tags:
                    if tag.ativo and tag.numeracao and tag.numeracao.startswith('V'):
                        fonte_nome = tag.nome
                        break

            questao_dict = {
                'codigo': q.codigo,
                'titulo': q.titulo,
                'tipo': q.tipo.codigo if q.tipo else None,
                'enunciado': q.enunciado,
                'fonte': fonte_nome,
                'ano': q.ano.ano if q.ano else None,
                'alternativas': sorted([
                    {
                        'uuid': alt.uuid,
                        'letra': alt.letra,
                        'texto': alt.texto
                    }
                    for alt in q.alternativas
                ], key=lambda x: x['letra']) if hasattr(q, 'alternativas') and q.alternativas else [],
                'resposta': None
            }
            # Buscar resposta se existir
            if hasattr(q, 'resposta') and q.resposta:
                if hasattr(q.resposta, 'alternativa_correta') and q.resposta.alternativa_correta:
                    questao_dict['resposta'] = q.resposta.alternativa_correta.letra
                elif hasattr(q.resposta, 'gabarito_discursivo'):
                    questao_dict['resposta'] = q.resposta.gabarito_discursivo
            questoes_data.append(questao_dict)

        return {
            'codigo': lista.codigo,
            'uuid': lista.uuid,
            'titulo': lista.titulo,
            'tipo': lista.tipo,
            'formulas': lista.formulas,
            'questoes': questoes_data,
            'tags_relacionadas': [tag.nome for tag in tags],
            'total_questoes': lista.contar_questoes()
        }

    def listar_listas(self, tipo: Optional[str] = None, apenas_ativos: bool = True) -> List[Dict[str, Any]]:
        """
        Lista todas as listas, opcionalmente filtradas por tipo

        Args:
            tipo: Tipo opcional (PROVA, LISTA, SIMULADO)
            apenas_ativos: Se True, retorna apenas listas ativas

        Returns:
            Lista de dicts
        """
        if tipo:
            listas = self.lista_repo.buscar_por_tipo(tipo)
        else:
            listas = self.lista_repo.listar_todos(apenas_ativos=apenas_ativos)

        return [
            {
                'id': hash(l.uuid) % 2147483647,  # Converter uuid para int positivo
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

    def atualizar_lista(
        self,
        codigo: str,
        titulo: Optional[str] = None,
        tipo: Optional[str] = None,
        formulas: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Atualiza uma lista

        Args:
            codigo: Codigo da lista
            titulo: Novo titulo
            tipo: Novo tipo
            formulas: Nova caixa de formulas (LaTeX)

        Returns:
            Dict com dados atualizados ou None
        """
        lista = self.lista_repo.buscar_por_codigo(codigo)
        if not lista:
            return None

        if titulo is not None:
            lista.titulo = titulo
        if tipo is not None:
            lista.tipo = tipo
        if formulas is not None:
            lista.formulas = formulas

        self.session.flush()

        return {
            'codigo': lista.codigo,
            'titulo': lista.titulo,
            'tipo': lista.tipo,
            'formulas': lista.formulas
        }

    def deletar_lista(self, codigo: str) -> bool:
        """Desativa lista (soft delete)"""
        lista = self.lista_repo.buscar_por_codigo(codigo)
        if lista:
            lista.ativo = False
            self.session.flush()
            return True
        return False

    def reativar_lista(self, codigo: str) -> bool:
        """Reativa lista previamente inativada"""
        # Buscar sem filtro de ativo
        listas = self.lista_repo.listar_todos(apenas_ativos=False)
        lista = next((l for l in listas if l.codigo == codigo), None)
        if lista and not lista.ativo:
            lista.ativo = True
            self.session.flush()
            return True
        return False
