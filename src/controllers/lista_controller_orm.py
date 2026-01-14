"""
ListaController - Nova versão usando ORM + Service Layer
Substitui lista_controller.py (legacy)
"""
from typing import Dict, List, Optional, Any
from src.services import services


class ListaControllerORM:
    """
    Controller para operações de listas de questões usando ORM e Service Layer

    IMPORTANTE: Este controller usa a Service Facade com UUIDs e códigos legíveis (LST-2026-0001)
    """

    @staticmethod
    def criar_lista(
        titulo: str,
        tipo: str = 'LISTA',
        cabecalho: Optional[str] = None,
        instrucoes: Optional[str] = None,
        codigos_questoes: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Cria uma lista de questões

        Args:
            titulo: Título da lista
            tipo: 'PROVA', 'LISTA' ou 'SIMULADO' (padrão: 'LISTA')
            cabecalho: Cabeçalho personalizado opcional
            instrucoes: Instruções gerais opcionais
            codigos_questoes: Lista de códigos de questões (Q-2024-0001) para adicionar

        Returns:
            Dict com dados da lista criada ou None se erro

        Exemplo:
            lista = ListaControllerORM.criar_lista(
                titulo='Prova de Geografia - 2024',
                tipo='PROVA',
                instrucoes='Responda todas as questões',
                codigos_questoes=['Q-2024-0001', 'Q-2024-0002']
            )
            print(f"Lista criada: {lista['codigo']}")  # LST-2026-0001
        """
        try:
            with services.transaction() as svc:
                return svc.lista.criar_lista(
                    titulo=titulo,
                    tipo=tipo,
                    cabecalho=cabecalho,
                    instrucoes=instrucoes,
                    codigos_questoes=codigos_questoes
                )
        except Exception as e:
            print(f"Erro ao criar lista: {e}")
            return None

    @staticmethod
    def buscar_lista(codigo: str) -> Optional[Dict[str, Any]]:
        """
        Busca uma lista por código

        Args:
            codigo: Código da lista (LST-2026-0001)

        Returns:
            Dict com dados completos da lista (incluindo questões) ou None
        """
        try:
            return services.lista.buscar_lista(codigo)
        except Exception as e:
            print(f"Erro ao buscar lista: {e}")
            return None

    @staticmethod
    def listar_listas(tipo: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Lista todas as listas, opcionalmente filtradas por tipo

        Args:
            tipo: Tipo opcional ('PROVA', 'LISTA', 'SIMULADO')

        Returns:
            Lista de dicts com dados resumidos das listas
        """
        try:
            return services.lista.listar_listas(tipo)
        except Exception as e:
            print(f"Erro ao listar listas: {e}")
            return []

    @staticmethod
    def adicionar_questao(
        codigo_lista: str,
        codigo_questao: str,
        ordem: Optional[int] = None
    ) -> bool:
        """
        Adiciona uma questão à lista

        Args:
            codigo_lista: Código da lista (LST-2026-0001)
            codigo_questao: Código da questão (Q-2024-0001)
            ordem: Ordem opcional (se não fornecida, adiciona ao final)

        Returns:
            True se adicionada com sucesso
        """
        try:
            with services.transaction() as svc:
                return svc.lista.adicionar_questao(codigo_lista, codigo_questao, ordem)
        except Exception as e:
            print(f"Erro ao adicionar questão à lista: {e}")
            return False

    @staticmethod
    def remover_questao(codigo_lista: str, codigo_questao: str) -> bool:
        """
        Remove uma questão da lista

        Args:
            codigo_lista: Código da lista (LST-2026-0001)
            codigo_questao: Código da questão (Q-2024-0001)

        Returns:
            True se removida com sucesso
        """
        try:
            with services.transaction() as svc:
                return svc.lista.remover_questao(codigo_lista, codigo_questao)
        except Exception as e:
            print(f"Erro ao remover questão da lista: {e}")
            return False

    @staticmethod
    def reordenar_questoes(
        codigo_lista: str,
        codigos_ordenados: List[str]
    ) -> bool:
        """
        Reordena as questões de uma lista

        Args:
            codigo_lista: Código da lista (LST-2026-0001)
            codigos_ordenados: Lista de códigos de questões na nova ordem

        Returns:
            True se reordenadas com sucesso
        """
        try:
            with services.transaction() as svc:
                return svc.lista.reordenar_questoes(codigo_lista, codigos_ordenados)
        except Exception as e:
            print(f"Erro ao reordenar questões: {e}")
            return False

    @staticmethod
    def atualizar_lista(
        codigo: str,
        titulo: str = None,
        tipo: str = None,
        cabecalho: str = None,
        instrucoes: str = None
    ):
        """
        Atualiza uma lista

        Args:
            codigo: Codigo da lista (LST-2026-0001)
            titulo: Novo titulo
            tipo: Novo tipo
            cabecalho: Novo cabecalho
            instrucoes: Novas instrucoes

        Returns:
            Dict com dados atualizados ou None
        """
        try:
            with services.transaction() as svc:
                return svc.lista.atualizar_lista(
                    codigo=codigo,
                    titulo=titulo,
                    tipo=tipo,
                    cabecalho=cabecalho,
                    instrucoes=instrucoes
                )
        except Exception as e:
            print(f"Erro ao atualizar lista: {e}")
            return None

    @staticmethod
    def deletar_lista(codigo: str) -> bool:
        """
        Desativa uma lista (soft delete)

        Args:
            codigo: Código da lista (LST-2026-0001)

        Returns:
            True se desativada com sucesso
        """
        try:
            with services.transaction() as svc:
                return svc.lista.deletar_lista(codigo)
        except Exception as e:
            print(f"Erro ao deletar lista: {e}")
            return False
