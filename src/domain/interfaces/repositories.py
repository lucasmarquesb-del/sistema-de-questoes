"""
Repository Interfaces
DESCRIÇÃO: Contratos para acesso a dados
PRINCÍPIO: Dependency Inversion - Controllers dependem de abstrações, não de Models concretos
BENEFÍCIOS:
    - Facilita testes (mock repositories)
    - Permite trocar implementação (SQLite -> PostgreSQL)
    - Desacopla lógica de negócio da persistência
"""

from typing import Protocol, Optional, Dict, List, Any
from datetime import datetime


class IQuestaoRepository(Protocol):
    """Interface para repositório de questões"""

    def criar(
        self,
        titulo: Optional[str],
        enunciado: str,
        tipo: str,
        ano: Optional[int],
        fonte: Optional[str],
        id_dificuldade: int,
        resolucao: Optional[str],
        gabarito_discursiva: Optional[str],
        observacoes: Optional[str],
        imagem_enunciado: Optional[str],
        escala_imagem_enunciado: Optional[float]
    ) -> Optional[int]:
        """Cria uma nova questão

        Args:
            titulo: Título da questão (opcional)
            enunciado: Texto do enunciado (obrigatório)
            tipo: Tipo da questão ('OBJETIVA' ou 'DISCURSIVA')
            ano: Ano da questão (opcional)
            fonte: Fonte/origem da questão (opcional)
            id_dificuldade: ID da dificuldade (1=FACIL, 2=MEDIO, 3=DIFICIL)
            resolucao: Resolução comentada (opcional)
            gabarito_discursiva: Gabarito para questões discursivas (opcional)
            observacoes: Comentários internos sobre a questão (opcional)
            imagem_enunciado: Caminho da imagem (opcional)
            escala_imagem_enunciado: Escala da imagem 0-1 (opcional)

        Returns:
            ID da questão criada ou None em caso de erro
        """
        ...

    def buscar_por_id(self, id_questao: int) -> Optional[Dict[str, Any]]:
        """Busca questão por ID

        Args:
            id_questao: ID da questão

        Returns:
            Dicionário com dados da questão ou None se não encontrada
        """
        ...

    def buscar_por_filtros(
        self,
        titulo: Optional[str] = None,
        tipo: Optional[str] = None,
        ano_inicio: Optional[int] = None,
        ano_fim: Optional[int] = None,
        fonte: Optional[str] = None,
        id_dificuldade: Optional[int] = None,
        tags: Optional[List[int]] = None,
        ativa: bool = True
    ) -> List[Dict[str, Any]]:
        """Busca questões aplicando filtros

        Args:
            titulo: Filtro por título (busca parcial)
            tipo: Filtro por tipo ('OBJETIVA' ou 'DISCURSIVA')
            ano_inicio: Ano inicial do intervalo de busca
            ano_fim: Ano final do intervalo de busca
            fonte: Filtro por fonte (busca parcial)
            id_dificuldade: Filtro por dificuldade
            tags: Lista de IDs de tags
            ativa: Se True, busca apenas questões ativas

        Returns:
            Lista de dicionários com questões encontradas
        """
        ...

    def atualizar(
        self,
        id_questao: int,
        titulo: Optional[str] = None,
        enunciado: Optional[str] = None,
        tipo: Optional[str] = None,
        ano: Optional[int] = None,
        fonte: Optional[str] = None,
        id_dificuldade: Optional[int] = None,
        resolucao: Optional[str] = None,
        gabarito_discursiva: Optional[str] = None,
        observacoes: Optional[str] = None,
        imagem_enunciado: Optional[str] = None,
        escala_imagem_enunciado: Optional[float] = None
    ) -> bool:
        """Atualiza dados de uma questão

        Args:
            id_questao: ID da questão a atualizar
            **kwargs: Campos a atualizar (apenas os fornecidos)

        Returns:
            True se atualização bem-sucedida, False caso contrário
        """
        ...

    def inativar(self, id_questao: int) -> bool:
        """Inativa uma questão (soft delete)

        Args:
            id_questao: ID da questão a inativar

        Returns:
            True se inativação bem-sucedida, False caso contrário
        """
        ...

    def reativar(self, id_questao: int) -> bool:
        """Reativa uma questão inativada

        Args:
            id_questao: ID da questão a reativar

        Returns:
            True se reativação bem-sucedida, False caso contrário
        """
        ...

    def vincular_tag(self, id_questao: int, id_tag: int) -> bool:
        """Vincula uma tag a uma questão

        Args:
            id_questao: ID da questão
            id_tag: ID da tag

        Returns:
            True se vinculação bem-sucedida, False caso contrário
        """
        ...

    def desvincular_tag(self, id_questao: int, id_tag: int) -> bool:
        """Desvincula uma tag de uma questão

        Args:
            id_questao: ID da questão
            id_tag: ID da tag

        Returns:
            True se desvinculação bem-sucedida, False caso contrário
        """
        ...

    def obter_tags(self, id_questao: int) -> List[Dict[str, Any]]:
        """Obtém todas as tags vinculadas a uma questão

        Args:
            id_questao: ID da questão

        Returns:
            Lista de dicionários com dados das tags
        """
        ...

    def contar_total(self, ativa: bool = True) -> int:
        """Conta total de questões

        Args:
            ativa: Se True, conta apenas questões ativas

        Returns:
            Número total de questões
        """
        ...

    def contar_por_tipo(self, ativa: bool = True) -> Dict[str, int]:
        """Conta questões por tipo

        Args:
            ativa: Se True, conta apenas questões ativas

        Returns:
            Dicionário com contagens por tipo {'OBJETIVA': 10, 'DISCURSIVA': 5}
        """
        ...


class IAlternativaRepository(Protocol):
    """Interface para repositório de alternativas"""

    def criar(
        self,
        id_questao: int,
        letra: str,
        texto: str,
        correta: bool = False,
        imagem: Optional[str] = None,
        escala_imagem: Optional[float] = None
    ) -> Optional[int]:
        """Cria uma alternativa

        Args:
            id_questao: ID da questão
            letra: Letra da alternativa (A, B, C, D, E)
            texto: Texto da alternativa
            correta: Se é a alternativa correta
            imagem: Caminho da imagem (opcional)
            escala_imagem: Escala da imagem 0-1 (opcional)

        Returns:
            ID da alternativa criada ou None em caso de erro
        """
        ...

    def criar_conjunto_completo(
        self,
        id_questao: int,
        alternativas_dados: List[Dict[str, Any]]
    ) -> bool:
        """Cria conjunto completo de 5 alternativas

        Args:
            id_questao: ID da questão
            alternativas_dados: Lista com dados de cada alternativa

        Returns:
            True se criação bem-sucedida, False caso contrário
        """
        ...

    def buscar_por_questao(self, id_questao: int) -> List[Dict[str, Any]]:
        """Busca todas alternativas de uma questão

        Args:
            id_questao: ID da questão

        Returns:
            Lista de dicionários com alternativas ordenadas por letra
        """
        ...

    def atualizar(
        self,
        id_alternativa: int,
        texto: Optional[str] = None,
        correta: Optional[bool] = None,
        imagem: Optional[str] = None,
        escala_imagem: Optional[float] = None
    ) -> bool:
        """Atualiza uma alternativa

        Args:
            id_alternativa: ID da alternativa
            **kwargs: Campos a atualizar

        Returns:
            True se atualização bem-sucedida, False caso contrário
        """
        ...

    def validar_alternativas(self, id_questao: int) -> Dict[str, Any]:
        """Valida estrutura de alternativas de uma questão

        Args:
            id_questao: ID da questão

        Returns:
            Dicionário com resultado da validação:
            {
                'valido': bool,
                'total': int,
                'tem_correta': bool,
                'erros': List[str]
            }
        """
        ...

    def deletar_por_questao(self, id_questao: int) -> bool:
        """Deleta todas as alternativas de uma questão

        Args:
            id_questao: ID da questão

        Returns:
            True se a deleção for bem-sucedida, False caso contrário.
        """
        ...


class ITagRepository(Protocol):
    """Interface para repositório de tags"""

    def criar(
        self,
        nome: str,
        numeracao: str,
        nivel: int,
        id_pai: Optional[int],
        ordem: int
    ) -> Optional[int]:
        """Cria uma tag

        Args:
            nome: Nome da tag
            numeracao: Numeração hierárquica (ex: "2.1")
            nivel: Nível hierárquico (1, 2, 3)
            id_pai: ID da tag pai (None para nível 1)
            ordem: Ordem de exibição entre tags do mesmo nível

        Returns:
            ID da tag criada ou None em caso de erro
        """
        ...

    def buscar_por_id(self, id_tag: int) -> Optional[Dict[str, Any]]:
        """Busca tag por ID

        Args:
            id_tag: ID da tag

        Returns:
            Dicionário com dados da tag ou None se não encontrada
        """
        ...

    def buscar_todas(self, nivel: Optional[int] = None, apenas_ativas: bool = True) -> List[Dict[str, Any]]:
        """Busca todas as tags

        Args:
            nivel: Filtro opcional por nível (1, 2 ou 3)
            apenas_ativas: Se True, retorna apenas tags ativas

        Returns:
            Lista de dicionários com tags
        """
        ...

    def buscar_filhas(self, id_tag: int) -> List[Dict[str, Any]]:
        """Busca tags filhas de uma tag pai

        Args:
            id_tag: ID da tag pai

        Returns:
            Lista de dicionários com tags filhas
        """
        ...

    def buscar_hierarquia_completa(self) -> List[Dict[str, Any]]:
        """Busca toda hierarquia de tags

        Returns:
            Lista hierárquica de tags com estrutura aninhada
        """
        ...

    def atualizar(
        self,
        id_tag: int,
        nome: Optional[str] = None,
        nivel: Optional[int] = None,
        id_pai: Optional[int] = None,
        ordem: Optional[int] = None,
        numeracao: Optional[str] = None
    ) -> bool:
        """Atualiza uma tag

        Args:
            id_tag: ID da tag
            **kwargs: Campos a atualizar (nome, nivel, id_pai, ordem, numeracao)

        Returns:
            True se atualização bem-sucedida, False caso contrário
        """
        ...

    def deletar(self, id_tag: int) -> bool:
        """Deleta uma tag

        Args:
            id_tag: ID da tag

        Returns:
            True se deleção bem-sucedida, False caso contrário
        """
        ...


class IListaRepository(Protocol):
    """Interface para repositório de listas"""

    def criar(
        self,
        titulo: str,
        tipo: Optional[str] = None,
        cabecalho: Optional[str] = None,
        instrucoes: Optional[str] = None
    ) -> Optional[int]:
        """Cria uma lista

        Args:
            titulo: Título da lista
            tipo: Tipo da lista (Prova, Lista, Simulado, etc)
            cabecalho: Cabeçalho personalizado
            instrucoes: Instruções gerais

        Returns:
            ID da lista criada ou None em caso de erro
        """
        ...

    def buscar_por_id(self, id_lista: int) -> Optional[Dict[str, Any]]:
        """Busca lista por ID

        Args:
            id_lista: ID da lista

        Returns:
            Dicionário com dados da lista ou None se não encontrada
        """
        ...

    def buscar_todas(self) -> List[Dict[str, Any]]:
        """Busca todas as listas

        Returns:
            Lista de dicionários com listas
        """
        ...

    def atualizar(
        self,
        id_lista: int,
        titulo: Optional[str] = None,
        tipo: Optional[str] = None,
        cabecalho: Optional[str] = None,
        instrucoes: Optional[str] = None
    ) -> bool:
        """Atualiza uma lista

        Args:
            id_lista: ID da lista
            **kwargs: Campos a atualizar

        Returns:
            True se atualização bem-sucedida, False caso contrário
        """
        ...

    def deletar(self, id_lista: int) -> bool:
        """Deleta uma lista

        Args:
            id_lista: ID da lista

        Returns:
            True se deleção bem-sucedida, False caso contrário
        """
        ...

    def adicionar_questao(
        self,
        id_lista: int,
        id_questao: int,
        ordem: int
    ) -> bool:
        """Adiciona questão a uma lista

        Args:
            id_lista: ID da lista
            id_questao: ID da questão
            ordem: Ordem da questão na lista

        Returns:
            True se adição bem-sucedida, False caso contrário
        """
        ...

    def remover_questao(self, id_lista: int, id_questao: int) -> bool:
        """Remove questão de uma lista

        Args:
            id_lista: ID da lista
            id_questao: ID da questão

        Returns:
            True se remoção bem-sucedida, False caso contrário
        """
        ...

    def obter_questoes(self, id_lista: int) -> List[Dict[str, Any]]:
        """Obtém questões de uma lista

        Args:
            id_lista: ID da lista

        Returns:
            Lista de questões ordenadas
        """
        ...
    
    def obter_lista_completa(self, id_lista: int) -> Optional[Dict[str, Any]]:
        """Obtém os dados completos de uma lista, incluindo suas questões."""
        ...

    def reordenar_questoes(
        self,
        id_lista: int,
        questoes_ordem: List[tuple[int, int]]
    ) -> bool:
        """Reordena questões de uma lista

        Args:
            id_lista: ID da lista
            questoes_ordem: Lista de tuplas (id_questao, nova_ordem)

        Returns:
            True se reordenação bem-sucedida, False caso contrário
        """
        ...
