"""
QuestaoController - Nova versão usando ORM + Service Layer
Substitui questao_controller.py (legacy) e questao_controller_refactored.py
"""
from typing import Dict, List, Optional, Any
from services import services


class QuestaoControllerORM:
    """
    Controller para operações de questões usando ORM e Service Layer

    IMPORTANTE: Este controller usa a Service Facade com UUIDs e códigos legíveis (Q-2026-0001)
    """

    @staticmethod
    def criar_questao_completa(dados: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Cria uma questão completa com alternativas, tags e resposta

        Args:
            dados: Dict com dados da questão:
                - tipo: 'OBJETIVA' ou 'DISCURSIVA'
                - enunciado: Texto do enunciado (LaTeX)
                - titulo: Título opcional
                - fonte: Sigla da fonte (ENEM, FUVEST, etc)
                - ano: Ano de referência
                - dificuldade: 'FACIL', 'MEDIO', 'DIFICIL'
                - observacoes: Observações opcionais
                - tags: Lista de nomes de tags
                - alternativas: Lista de dicts (para OBJETIVA) com:
                    - letra: 'A', 'B', 'C', 'D', 'E'
                    - texto: Texto da alternativa
                    - uuid_imagem: UUID da imagem (opcional)
                    - escala_imagem: Escala da imagem (opcional)
                - resposta_objetiva: Dict com (para OBJETIVA):
                    - uuid_alternativa_correta: UUID da alternativa correta
                    - resolucao: Resolução opcional
                    - justificativa: Justificativa opcional
                - resposta_discursiva: Dict com (para DISCURSIVA):
                    - gabarito: Gabarito da questão
                    - resolucao: Resolução opcional
                    - justificativa: Justificativa opcional

        Returns:
            Dict com dados da questão criada ou None se erro

        Exemplo:
            dados = {
                'tipo': 'OBJETIVA',
                'enunciado': 'Qual é a capital do Brasil?',
                'titulo': 'Geografia - Capitais',
                'fonte': 'ENEM',
                'ano': 2024,
                'dificuldade': 'FACIL',
                'tags': ['Geografia', 'Brasil'],
                'alternativas': [
                    {'letra': 'A', 'texto': 'São Paulo'},
                    {'letra': 'B', 'texto': 'Rio de Janeiro'},
                    {'letra': 'C', 'texto': 'Brasília'},
                    {'letra': 'D', 'texto': 'Salvador'},
                    {'letra': 'E', 'texto': 'Belo Horizonte'}
                ],
                'resposta_objetiva': {
                    'uuid_alternativa_correta': 'uuid-da-alternativa-c',
                    'resolucao': 'Brasília é a capital federal desde 1960'
                }
            }

            questao = QuestaoControllerORM.criar_questao_completa(dados)
            print(f"Questão criada: {questao['codigo']}")  # Q-2024-0001
        """
        try:
            with services.transaction() as svc:
                # Criar questão usando QuestaoService
                questao = svc.questao.criar_questao(
                    tipo=dados.get('tipo'),
                    enunciado=dados.get('enunciado'),
                    titulo=dados.get('titulo'),
                    fonte=dados.get('fonte'),
                    ano=dados.get('ano'),
                    dificuldade=dados.get('dificuldade'),
                    observacoes=dados.get('observacoes'),
                    tags=dados.get('tags', []),
                    alternativas=dados.get('alternativas'),
                    resposta_objetiva=dados.get('resposta_objetiva'),
                    resposta_discursiva=dados.get('resposta_discursiva')
                )

                return questao

        except ValueError as e:
            print(f"Erro de validação: {e}")
            return None
        except Exception as e:
            print(f"Erro ao criar questão: {e}")
            return None

    @staticmethod
    def buscar_questao(codigo: str) -> Optional[Dict[str, Any]]:
        """
        Busca uma questão por código legível

        Args:
            codigo: Código da questão (Q-2024-0001)

        Returns:
            Dict com dados completos da questão ou None
        """
        try:
            return services.questao.buscar_questao(codigo)
        except Exception as e:
            print(f"Erro ao buscar questão: {e}")
            return None

    @staticmethod
    def listar_questoes(filtros: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Lista questões com filtros opcionais

        Args:
            filtros: Dict com filtros opcionais:
                - fonte: Sigla da fonte (ENEM, FUVEST, etc)
                - ano: Ano de referência
                - tags: Lista de nomes de tags
                - dificuldade: 'FACIL', 'MEDIO', 'DIFICIL'
                - tipo: 'OBJETIVA' ou 'DISCURSIVA'
                - titulo: Título parcial da questão

        Returns:
            Lista de dicts com dados resumidos das questões
        """
        try:
            return services.questao.listar_questoes(filtros)
        except Exception as e:
            print(f"Erro ao listar questões: {e}")
            return []

    @staticmethod
    def atualizar_questao(codigo: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Atualiza uma questão

        Args:
            codigo: Código da questão (Q-2024-0001)
            **kwargs: Campos a atualizar

        Returns:
            Dict com dados atualizados ou None
        """
        try:
            with services.transaction() as svc:
                return svc.questao.atualizar_questao(codigo, **kwargs)
        except Exception as e:
            print(f"Erro ao atualizar questão: {e}")
            return None

    @staticmethod
    def deletar_questao(codigo: str) -> bool:
        """
        Desativa uma questão (soft delete)

        Args:
            codigo: Código da questão (Q-2024-0001)

        Returns:
            True se desativada, False caso contrário
        """
        try:
            with services.transaction() as svc:
                return svc.questao.deletar_questao(codigo)
        except Exception as e:
            print(f"Erro ao deletar questão: {e}")
            return False

    @staticmethod
    def adicionar_tag(codigo_questao: str, nome_tag: str) -> bool:
        """Adiciona tag à questão"""
        try:
            with services.transaction() as svc:
                return svc.questao.adicionar_tag(codigo_questao, nome_tag)
        except Exception as e:
            print(f"Erro ao adicionar tag: {e}")
            return False

    @staticmethod
    def remover_tag(codigo_questao: str, nome_tag: str) -> bool:
        """Remove tag da questão"""
        try:
            with services.transaction() as svc:
                return svc.questao.remover_tag(codigo_questao, nome_tag)
        except Exception as e:
            print(f"Erro ao remover tag: {e}")
            return False

    @staticmethod
    def obter_estatisticas() -> Dict[str, Any]:
        """
        Retorna estatísticas sobre questões

        Returns:
            Dict com estatísticas (total, por tipo, por dificuldade, etc)
        """
        try:
            return services.questao.obter_estatisticas()
        except Exception as e:
            print(f"Erro ao obter estatísticas: {e}")
            return {}
