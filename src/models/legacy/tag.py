"""
Sistema de Banco de Questões Educacionais
Módulo: Model Tag
Versão: 1.0.1

DESCRIÇÃO:
    Model responsável pela entidade Tag (sistema hierárquico de categorização).
    Gerencia tags hierárquicas (ex: ÁLGEBRA > FUNÇÕES > FUNÇÃO EXPONENCIAL)
    e tags livres criadas pelo usuário.

FUNCIONALIDADES:
    - Listar tags (com ou sem hierarquia)
    - Buscar tag por ID
    - Criar nova tag (hierárquica ou livre)
    - Atualizar tag
    - Inativar/Reativar tag (soft delete)
    - Reorganizar hierarquia
    - Listar tags por nível
    - Buscar tags filhas de uma tag pai

RELACIONAMENTOS:
    - questao.py: Uma questão pode ter VÁRIAS tags (N:N via questao_tag)
    - tag.py (self): Uma tag pode ter uma tag pai (auto-relacionamento)
    - database.py: Utiliza a conexão com o banco de dados

TABELA NO BANCO:
    tag (
        id_tag INTEGER PRIMARY KEY,
        nome VARCHAR(100),
        numeracao VARCHAR(20) UNIQUE,
        nivel INTEGER,
        id_tag_pai INTEGER,
        ativo BOOLEAN,
        ordem INTEGER
    )

UTILIZADO POR:
    - QuestaoModel: Vinculação de tags às questões
    - TagController: Lógica de gerenciamento de tags
    - TagManager (view): Interface de gerenciamento
    - QuestaoForm (view): Seleção de tags ao criar questão
    - SearchPanel (view): Filtros por tags

HIERARQUIA DE TAGS:
    Nível 1: ÁLGEBRA (numeracao: "2", nivel: 1, id_tag_pai: NULL)
    Nível 2: ├── FUNÇÕES (numeracao: "2.1", nivel: 2, id_tag_pai: id_algebra)
    Nível 3:     └── FUNÇÃO EXPONENCIAL (numeracao: "2.1.3", nivel: 3, id_tag_pai: id_funcoes)

EXEMPLO DE USO:
    >>> from src.models.tag import TagModel
    >>>
    >>> # Listar todas as tags ativas
    >>> tags = TagModel.listar_todas(apenas_ativas=True)
    >>>
    >>> # Buscar tags de nível 1 (categorias principais)
    >>> principais = TagModel.listar_por_nivel(1)
    >>>
    >>> # Buscar tags filhas de "ÁLGEBRA"
    >>> algebra = TagModel.buscar_por_nome("ÁLGEBRA")
    >>> filhas = TagModel.listar_filhas(algebra['id_tag'])
    >>>
    >>> # Criar nova tag livre
    >>> id_nova = TagModel.criar("IMPORTANTE", nivel=1)
"""

import logging
from typing import Optional, List, Dict
from src.models.database import db
from src.models.queries import CommonQueries

logger = logging.getLogger(__name__)


class TagModel:
    """
    Model para a entidade Tag.
    Implementa operações CRUD e gerenciamento de hierarquia.
    """

    @staticmethod
    def listar_todas(apenas_ativas: bool = True, ordenar_por: str = "ordem") -> List[Dict]:
        """
        Lista todas as tags.
        CORRIGIDO: Whitelist de ordenação para prevenir SQL injection

        Args:
            apenas_ativas: Se True, retorna apenas tags ativas
            ordenar_por: Campo para ordenação (ordem, nome, numeracao)

        Returns:
            List[Dict]: Lista de dicionários com dados das tags
        """
        try:
            # SEGURANÇA: Validar ordenação com whitelist
            if ordenar_por not in CommonQueries.VALID_ORDER_BY_TAG:
                logger.warning(f"Campo de ordenação inválido: {ordenar_por}. Usando padrão.")
                ordenar_por = "ordem ASC"

            # CORRIGIDO: Usar queries distintas ao invés de concatenação
            if apenas_ativas:
                query = """
                    SELECT id_tag, nome, numeracao, nivel, id_tag_pai, ativo, ordem
                    FROM tag
                    WHERE ativo = 1
                    ORDER BY """ + ordenar_por
            else:
                query = """
                    SELECT id_tag, nome, numeracao, nivel, id_tag_pai, ativo, ordem
                    FROM tag
                    ORDER BY """ + ordenar_por

            results = db.execute_query(query)

            if results:
                return [dict(row) for row in results]
            return []

        except Exception as e:
            logger.error(f"Erro ao listar tags: {e}")
            return []

    @staticmethod
    def listar_por_nivel(nivel: int, apenas_ativas: bool = True) -> List[Dict]:
        """
        Lista tags de um nível específico da hierarquia.
        CORRIGIDO: Queries distintas ao invés de concatenação

        Args:
            nivel: Nível hierárquico (1=raiz, 2=filho, 3=neto, etc.)
            apenas_ativas: Se True, retorna apenas tags ativas

        Returns:
            List[Dict]: Lista de tags do nível especificado
        """
        try:
            # SEGURANÇA: Validar nivel como inteiro
            nivel = int(nivel)

            # CORRIGIDO: Usar queries distintas
            if apenas_ativas:
                query = """
                    SELECT id_tag, nome, numeracao, nivel, id_tag_pai, ativo, ordem
                    FROM tag
                    WHERE nivel = ? AND ativo = 1
                    ORDER BY ordem
                """
            else:
                query = """
                    SELECT id_tag, nome, numeracao, nivel, id_tag_pai, ativo, ordem
                    FROM tag
                    WHERE nivel = ?
                    ORDER BY ordem
                """

            results = db.execute_query(query, (nivel,))

            if results:
                return [dict(row) for row in results]
            return []

        except Exception as e:
            logger.error(f"Erro ao listar tags por nível: {e}")
            return []

    @staticmethod
    def listar_filhas(id_tag_pai: int, apenas_ativas: bool = True) -> List[Dict]:
        """
        Lista todas as tags filhas de uma tag pai.
        CORRIGIDO: Queries distintas ao invés de concatenação

        Args:
            id_tag_pai: ID da tag pai
            apenas_ativas: Se True, retorna apenas tags ativas

        Returns:
            List[Dict]: Lista de tags filhas
        """
        try:
            # SEGURANÇA: Validar id_tag_pai como inteiro
            id_tag_pai = int(id_tag_pai)

            # CORRIGIDO: Usar queries distintas
            if apenas_ativas:
                query = """
                    SELECT id_tag, nome, numeracao, nivel, id_tag_pai, ativo, ordem
                    FROM tag
                    WHERE id_tag_pai = ? AND ativo = 1
                    ORDER BY ordem
                """
            else:
                query = """
                    SELECT id_tag, nome, numeracao, nivel, id_tag_pai, ativo, ordem
                    FROM tag
                    WHERE id_tag_pai = ?
                    ORDER BY ordem
                """

            results = db.execute_query(query, (id_tag_pai,))

            if results:
                return [dict(row) for row in results]
            return []

        except Exception as e:
            logger.error(f"Erro ao listar tags filhas: {e}")
            return []

    @staticmethod
    def buscar_por_id(id_tag: int) -> Optional[Dict]:
        """
        Busca uma tag pelo ID.

        Args:
            id_tag: ID da tag

        Returns:
            Dict: Dados da tag ou None se não encontrada
        """
        try:
            query = """
                SELECT id_tag, nome, numeracao, nivel, id_tag_pai, ativo, ordem
                FROM tag
                WHERE id_tag = ?
            """
            results = db.execute_query(query, (id_tag,))

            if results and len(results) > 0:
                return dict(results[0])
            return None

        except Exception as e:
            logger.error(f"Erro ao buscar tag por ID: {e}")
            return None

    @staticmethod
    def buscar_por_nome(nome: str) -> Optional[Dict]:
        """
        Busca uma tag pelo nome exato.

        Args:
            nome: Nome da tag

        Returns:
            Dict: Dados da tag ou None se não encontrada
        """
        try:
            query = """
                SELECT id_tag, nome, numeracao, nivel, id_tag_pai, ativo, ordem
                FROM tag
                WHERE nome = ?
            """
            results = db.execute_query(query, (nome.upper(),))

            if results and len(results) > 0:
                return dict(results[0])
            return None

        except Exception as e:
            logger.error(f"Erro ao buscar tag por nome: {e}")
            return None

    @staticmethod
    def buscar_por_numeracao(numeracao: str) -> Optional[Dict]:
        """
        Busca uma tag pela numeração (ex: "2.1.3").

        Args:
            numeracao: Numeração hierárquica da tag

        Returns:
            Dict: Dados da tag ou None se não encontrada
        """
        try:
            query = """
                SELECT id_tag, nome, numeracao, nivel, id_tag_pai, ativo, ordem
                FROM tag
                WHERE numeracao = ?
            """
            results = db.execute_query(query, (numeracao,))

            if results and len(results) > 0:
                return dict(results[0])
            return None

        except Exception as e:
            logger.error(f"Erro ao buscar tag por numeração: {e}")
            return None

    @staticmethod
    def criar(nome: str, numeracao: str = None, nivel: int = 1,
              id_tag_pai: int = None, ordem: int = 0) -> Optional[int]:
        """
        Cria uma nova tag.

        Args:
            nome: Nome da tag
            numeracao: Numeração hierárquica (ex: "2.1.3")
            nivel: Nível na hierarquia (1=raiz)
            id_tag_pai: ID da tag pai (None para tags raiz)
            ordem: Ordem de exibição

        Returns:
            int: ID da tag criada ou None se erro
        """
        try:
            query = """
                INSERT INTO tag (nome, numeracao, nivel, id_tag_pai, ordem, ativo)
                VALUES (?, ?, ?, ?, ?, 1)
            """
            if db.execute_update(query, (nome.upper(), numeracao, nivel, id_tag_pai, ordem)):
                return db.get_last_insert_id()
            return None

        except Exception as e:
            logger.error(f"Erro ao criar tag: {e}")
            return None

    @staticmethod
    def atualizar(id_tag: int, nome: str = None, numeracao: str = None,
                  nivel: int = None, id_tag_pai: int = None, ordem: int = None) -> bool:
        """
        Atualiza uma tag existente.

        Args:
            id_tag: ID da tag
            nome: Novo nome (opcional)
            numeracao: Nova numeração (opcional)
            nivel: Novo nível (opcional)
            id_tag_pai: Novo ID pai (opcional)
            ordem: Nova ordem (opcional)

        Returns:
            bool: True se atualizado com sucesso
        """
        try:
            campos = []
            valores = []

            if nome is not None:
                campos.append("nome = ?")
                valores.append(nome.upper())

            if numeracao is not None:
                campos.append("numeracao = ?")
                valores.append(numeracao)

            if nivel is not None:
                campos.append("nivel = ?")
                valores.append(nivel)

            if id_tag_pai is not None:
                campos.append("id_tag_pai = ?")
                valores.append(id_tag_pai)

            if ordem is not None:
                campos.append("ordem = ?")
                valores.append(ordem)

            if not campos:
                logger.warning("Nenhum campo para atualizar")
                return False

            valores.append(id_tag)
            query = f"UPDATE tag SET {', '.join(campos)} WHERE id_tag = ?"

            return db.execute_update(query, tuple(valores))

        except Exception as e:
            logger.error(f"Erro ao atualizar tag: {e}")
            return False

    @staticmethod
    def inativar(id_tag: int) -> bool:
        """
        Inativa uma tag (soft delete).
        A tag permanece no banco mas não aparece nas buscas.

        Args:
            id_tag: ID da tag

        Returns:
            bool: True se inativada com sucesso
        """
        try:
            query = "UPDATE tag SET ativo = 0 WHERE id_tag = ?"
            return db.execute_update(query, (id_tag,))

        except Exception as e:
            logger.error(f"Erro ao inativar tag: {e}")
            return False

    @staticmethod
    def reativar(id_tag: int) -> bool:
        """
        Reativa uma tag inativada.

        Args:
            id_tag: ID da tag

        Returns:
            bool: True se reativada com sucesso
        """
        try:
            query = "UPDATE tag SET ativo = 1 WHERE id_tag = ?"
            return db.execute_update(query, (id_tag,))

        except Exception as e:
            logger.error(f"Erro ao reativar tag: {e}")
            return False

    @staticmethod
    def deletar(id_tag: int, forcar: bool = False) -> bool:
        """
        Deleta uma tag permanentemente.
        Por padrão, não permite deletar se houver questões vinculadas.

        Args:
            id_tag: ID da tag
            forcar: Se True, deleta mesmo com questões vinculadas

        Returns:
            bool: True se deletada com sucesso
        """
        try:
            if not forcar:
                # Verificar se há questões com esta tag
                query_check = """
                    SELECT COUNT(*) as total
                    FROM questao_tag
                    WHERE id_tag = ?
                """
                result = db.execute_query(query_check, (id_tag,))

                if result and result[0]['total'] > 0:
                    logger.warning(f"Tag {id_tag} possui questões vinculadas")
                    return False

            # Deletar tag
            query = "DELETE FROM tag WHERE id_tag = ?"
            return db.execute_update(query, (id_tag,))

        except Exception as e:
            logger.error(f"Erro ao deletar tag: {e}")
            return False

    @staticmethod
    def obter_caminho_completo(id_tag: int) -> List[Dict]:
        """
        Obtém o caminho completo de uma tag na hierarquia.
        Ex: ÁLGEBRA > FUNÇÕES > FUNÇÃO EXPONENCIAL

        Args:
            id_tag: ID da tag

        Returns:
            List[Dict]: Lista de tags do caminho (da raiz até a tag)
        """
        try:
            caminho = []
            tag_atual = TagModel.buscar_por_id(id_tag)

            while tag_atual:
                caminho.insert(0, tag_atual)  # Inserir no início
                if tag_atual['id_tag_pai']:
                    tag_atual = TagModel.buscar_por_id(tag_atual['id_tag_pai'])
                else:
                    break

            return caminho

        except Exception as e:
            logger.error(f"Erro ao obter caminho completo: {e}")
            return []

    @staticmethod
    def contar_questoes_por_tag() -> Dict[int, int]:
        """
        Retorna a quantidade de questões ativas por tag.
        Útil para exibir contadores na interface.

        Returns:
            Dict[int, int]: Dicionário {id_tag: quantidade}
        """
        try:
            query = """
                SELECT qt.id_tag, COUNT(q.id_questao) as total
                FROM questao_tag qt
                JOIN questao q ON qt.id_questao = q.id_questao
                WHERE q.ativo = 1
                GROUP BY qt.id_tag
            """
            results = db.execute_query(query)

            if results:
                return {row['id_tag']: row['total'] for row in results}
            return {}

        except Exception as e:
            logger.error(f"Erro ao contar questões por tag: {e}")
            return {}


if __name__ == "__main__":
    """Testes do modelo"""
    print("=" * 60)
    print("TESTE DO MODEL TAG")
    print("=" * 60)

    # Listar tags de nível 1
    print("\n1. Listando tags de nível 1:")
    tags = TagModel.listar_por_nivel(1)
    for t in tags[:5]:  # Mostrar apenas primeiras 5
        print(f"   - {t['numeracao']}: {t['nome']}")

    # Buscar ÁLGEBRA e suas filhas
    print("\n2. Buscando ÁLGEBRA e suas subáreas:")
    algebra = TagModel.buscar_por_nome("ÁLGEBRA")
    if algebra:
        print(f"   - {algebra['nome']} (ID: {algebra['id_tag']})")
        filhas = TagModel.listar_filhas(algebra['id_tag'])
        for f in filhas:
            print(f"     └── {f['numeracao']}: {f['nome']}")

    # Buscar por numeração
    print("\n3. Buscando tag por numeração (2.1):")
    tag = TagModel.buscar_por_numeracao("2.1")
    if tag:
        print(f"   - {tag['nome']}")

    # Caminho completo
    print("\n4. Caminho completo de uma tag:")
    if tag:
        caminho = TagModel.obter_caminho_completo(tag['id_tag'])
        nomes = [t['nome'] for t in caminho]
        print(f"   - {' > '.join(nomes)}")

    print("\n" + "=" * 60)
    print("TESTE CONCLUÍDO")
    print("=" * 60)
