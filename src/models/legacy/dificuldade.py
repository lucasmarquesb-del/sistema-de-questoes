"""
Sistema de Banco de Questões Educacionais
Módulo: Model Dificuldade
Versão: 1.0.1

DESCRIÇÃO:
    Model responsável pela entidade Dificuldade (FÁCIL, MÉDIO, DIFÍCIL).
    Gerencia os níveis de dificuldade das questões.

FUNCIONALIDADES:
    - Listar todas as dificuldades
    - Buscar dificuldade por ID
    - Buscar dificuldade por nome
    - Criar nova dificuldade (admin)
    - Atualizar dificuldade (admin)
    - Deletar dificuldade (admin)

RELACIONAMENTOS:
    - questao.py: Uma questão possui UMA dificuldade (N:1)
    - database.py: Utiliza a conexão com o banco de dados

TABELA NO BANCO:
    dificuldade (
        id_dificuldade INTEGER PRIMARY KEY,
        nome VARCHAR(50) UNIQUE,
        descricao TEXT,
        ordem INTEGER
    )

UTILIZADO POR:
    - QuestaoModel: Para definir a dificuldade de uma questão
    - QuestaoController: Validação e seleção de dificuldade
    - QuestaoForm (view): ComboBox de seleção de dificuldade
    - SearchPanel (view): Filtro por dificuldade

EXEMPLO DE USO:
    >>> from src.models.dificuldade import DificuldadeModel
    >>>
    >>> # Listar todas as dificuldades
    >>> dificuldades = DificuldadeModel.listar_todas()
    >>> for d in dificuldades:
    >>>     print(f"{d['nome']} - {d['descricao']}")
    >>>
    >>> # Buscar por ID
    >>> facil = DificuldadeModel.buscar_por_id(1)
    >>> print(facil['nome'])  # "FÁCIL"
"""

import logging
from typing import Optional, List, Dict
from src.models.database import db
from src.models.queries import DificuldadeQueries

logger = logging.getLogger(__name__)


class DificuldadeModel:
    """
    Model para a entidade Dificuldade.
    Implementa operações CRUD básicas.
    """

    @staticmethod
    def listar_todas() -> List[Dict]:
        """
        Lista todas as dificuldades ordenadas por ordem.

        Returns:
            List[Dict]: Lista de dicionários com dados das dificuldades
                       Cada dict contém: id_dificuldade, nome, descricao, ordem
        """
        try:
            # ATUALIZADO: Usar query centralizada
            query = DificuldadeQueries.SELECT_ALL
            results = db.execute_query(query)

            if results:
                return [dict(row) for row in results]
            return []

        except Exception as e:
            logger.error(f"Erro ao listar dificuldades: {e}")
            return []

    @staticmethod
    def buscar_por_id(id_dificuldade: int) -> Optional[Dict]:
        """
        Busca uma dificuldade pelo ID.

        Args:
            id_dificuldade: ID da dificuldade

        Returns:
            Dict: Dados da dificuldade ou None se não encontrada
        """
        try:
            # ATUALIZADO: Usar query centralizada
            query = DificuldadeQueries.SELECT_BY_ID
            results = db.execute_query(query, (id_dificuldade,))

            if results and len(results) > 0:
                return dict(results[0])
            return None

        except Exception as e:
            logger.error(f"Erro ao buscar dificuldade por ID: {e}")
            return None

    @staticmethod
    def buscar_por_nome(nome: str) -> Optional[Dict]:
        """
        Busca uma dificuldade pelo nome.

        Args:
            nome: Nome da dificuldade (ex: "FÁCIL", "MÉDIO", "DIFÍCIL")

        Returns:
            Dict: Dados da dificuldade ou None se não encontrada
        """
        try:
            # ATUALIZADO: Usar query centralizada
            query = DificuldadeQueries.SELECT_BY_NOME
            results = db.execute_query(query, (nome.upper(),))

            if results and len(results) > 0:
                return dict(results[0])
            return None

        except Exception as e:
            logger.error(f"Erro ao buscar dificuldade por nome: {e}")
            return None

    @staticmethod
    def criar(nome: str, descricao: str = "", ordem: int = 0) -> Optional[int]:
        """
        Cria uma nova dificuldade.
        NOTA: Normalmente não será usado, pois as dificuldades já vêm pré-cadastradas.

        Args:
            nome: Nome da dificuldade
            descricao: Descrição opcional
            ordem: Ordem de exibição

        Returns:
            int: ID da dificuldade criada ou None se erro
        """
        try:
            query = """
                INSERT INTO dificuldade (nome, descricao, ordem)
                VALUES (?, ?, ?)
            """
            if db.execute_update(query, (nome.upper(), descricao, ordem)):
                return db.get_last_insert_id()
            return None

        except Exception as e:
            logger.error(f"Erro ao criar dificuldade: {e}")
            return None

    @staticmethod
    def atualizar(id_dificuldade: int, nome: str = None,
                  descricao: str = None, ordem: int = None) -> bool:
        """
        Atualiza uma dificuldade existente.

        Args:
            id_dificuldade: ID da dificuldade
            nome: Novo nome (opcional)
            descricao: Nova descrição (opcional)
            ordem: Nova ordem (opcional)

        Returns:
            bool: True se atualizado com sucesso
        """
        try:
            # Montar query dinamicamente baseado nos campos fornecidos
            campos = []
            valores = []

            if nome is not None:
                campos.append("nome = ?")
                valores.append(nome.upper())

            if descricao is not None:
                campos.append("descricao = ?")
                valores.append(descricao)

            if ordem is not None:
                campos.append("ordem = ?")
                valores.append(ordem)

            if not campos:
                logger.warning("Nenhum campo para atualizar")
                return False

            valores.append(id_dificuldade)
            query = f"UPDATE dificuldade SET {', '.join(campos)} WHERE id_dificuldade = ?"

            return db.execute_update(query, tuple(valores))

        except Exception as e:
            logger.error(f"Erro ao atualizar dificuldade: {e}")
            return False

    @staticmethod
    def deletar(id_dificuldade: int) -> bool:
        """
        Deleta uma dificuldade.
        CUIDADO: Verifica se não há questões vinculadas antes de deletar.

        Args:
            id_dificuldade: ID da dificuldade

        Returns:
            bool: True se deletado com sucesso
        """
        try:
            # Verificar se há questões com esta dificuldade
            query_check = """
                SELECT COUNT(*) as total
                FROM questao
                WHERE id_dificuldade = ?
            """
            result = db.execute_query(query_check, (id_dificuldade,))

            if result and result[0]['total'] > 0:
                logger.warning(f"Dificuldade {id_dificuldade} possui questões vinculadas")
                return False

            # Deletar dificuldade
            query = "DELETE FROM dificuldade WHERE id_dificuldade = ?"
            return db.execute_update(query, (id_dificuldade,))

        except Exception as e:
            logger.error(f"Erro ao deletar dificuldade: {e}")
            return False

    @staticmethod
    def contar_questoes_por_dificuldade() -> Dict[str, int]:
        """
        Retorna a quantidade de questões por dificuldade.
        Útil para estatísticas.

        Returns:
            Dict[str, int]: Dicionário {nome_dificuldade: quantidade}
        """
        try:
            query = """
                SELECT d.nome, COUNT(q.id_questao) as total
                FROM dificuldade d
                LEFT JOIN questao q ON d.id_dificuldade = q.id_dificuldade
                WHERE q.ativo = 1
                GROUP BY d.id_dificuldade, d.nome
                ORDER BY d.ordem
            """
            results = db.execute_query(query)

            if results:
                return {row['nome']: row['total'] for row in results}
            return {}

        except Exception as e:
            logger.error(f"Erro ao contar questões por dificuldade: {e}")
            return {}


if __name__ == "__main__":
    """Testes do modelo"""
    print("=" * 60)
    print("TESTE DO MODEL DIFICULDADE")
    print("=" * 60)

    # Listar todas
    print("\n1. Listando todas as dificuldades:")
    dificuldades = DificuldadeModel.listar_todas()
    for d in dificuldades:
        print(f"   - {d['nome']}: {d['descricao']} (ordem: {d['ordem']})")

    # Buscar por ID
    print("\n2. Buscando dificuldade por ID (1):")
    diff = DificuldadeModel.buscar_por_id(1)
    if diff:
        print(f"   - {diff['nome']}: {diff['descricao']}")

    # Buscar por nome
    print("\n3. Buscando dificuldade por nome ('MÉDIO'):")
    diff = DificuldadeModel.buscar_por_nome("MÉDIO")
    if diff:
        print(f"   - ID {diff['id_dificuldade']}: {diff['descricao']}")

    # Contar questões
    print("\n4. Contando questões por dificuldade:")
    contagem = DificuldadeModel.contar_questoes_por_dificuldade()
    for nome, total in contagem.items():
        print(f"   - {nome}: {total} questões")

    print("\n" + "=" * 60)
    print("TESTE CONCLUÍDO")
    print("=" * 60)
