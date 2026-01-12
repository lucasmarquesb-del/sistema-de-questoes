"""
Sistema de Banco de Questões Educacionais
Módulo: Model Questão
Versão: 1.0.1

DESCRIÇÃO:
    Model responsável pela entidade Questão (núcleo do sistema).
    Gerencia questões OBJETIVAS (5 alternativas A-E) e DISCURSIVAS.

FUNCIONALIDADES:
    - Criar questão (objetiva ou discursiva)
    - Buscar questão por ID
    - Listar questões (com filtros)
    - Atualizar questão
    - Inativar/Reativar questão (soft delete)
    - Buscar questões por tags
    - Buscar questões por dificuldade
    - Buscar questões por ano/fonte
    - Vincular/desvincular tags
    - Obter versões alternativas de uma questão

RELACIONAMENTOS:
    - alternativa.py: Uma questão OBJETIVA tem 5 alternativas (1:N)
    - tag.py: Uma questão tem VÁRIAS tags (N:N via questao_tag)
    - dificuldade.py: Uma questão tem UMA dificuldade (N:1)
    - lista.py: Uma questão pode estar em VÁRIAS listas (N:N via lista_questao)
    - questao.py (self): Uma questão pode ter versões alternativas (N:N via questao_versao)
    - database.py: Utiliza a conexão com o banco de dados

TABELA NO BANCO:
    questao (
        id_questao INTEGER PRIMARY KEY,
        titulo VARCHAR(200),
        enunciado TEXT NOT NULL,
        tipo VARCHAR(20) CHECK(tipo IN ('OBJETIVA', 'DISCURSIVA')),
        ano INTEGER NOT NULL,
        fonte VARCHAR(100) NOT NULL,
        id_dificuldade INTEGER,
        imagem_enunciado VARCHAR(255),
        escala_imagem_enunciado DECIMAL(3,2) DEFAULT 0.7,
        resolucao TEXT,
        gabarito_discursiva TEXT,
        observacoes TEXT,
        data_criacao DATETIME,
        data_modificacao DATETIME,
        ativo BOOLEAN DEFAULT 1
    )

CAMPOS OBRIGATÓRIOS:
    - enunciado: Texto da questão (pode conter LaTeX)
    - tipo: 'OBJETIVA' ou 'DISCURSIVA'
    - ano: Ano da questão (ex: 2024)
    - fonte: Banca/Vestibular (ex: 'ENEM', 'FUVEST') ou 'AUTORAL'

CAMPOS OPCIONAIS:
    - titulo: Título curto para busca
    - id_dificuldade: FK para tabela dificuldade
    - imagem_enunciado: Caminho relativo para imagem
    - escala_imagem_enunciado: Escala da imagem no LaTeX (default: 0.7)
    - resolucao: Resolução detalhada (LaTeX)
    - gabarito_discursiva: Resposta esperada (apenas discursivas)
    - observacoes: Comentários internos

UTILIZADO POR:
    - AlternativaModel: Alternativas de questões objetivas
    - QuestaoController: Lógica de negócio e validações
    - QuestaoForm (view): Formulário de cadastro/edição
    - SearchPanel (view): Busca e filtros
    - ListaModel: Questões em listas/provas

EXEMPLO DE USO:
    >>> from src.models.questao import QuestaoModel
    >>> from src.models.alternativa import AlternativaModel
    >>>
    >>> # Criar questão objetiva
    >>> dados = {
    >>>     'titulo': 'Função Exponencial',
    >>>     'enunciado': 'Resolva $2^x = 8$',
    >>>     'tipo': 'OBJETIVA',
    >>>     'ano': 2024,
    >>>     'fonte': 'ENEM',
    >>>     'id_dificuldade': 1
    >>> }
    >>> id_questao = QuestaoModel.criar(**dados)
    >>>
    >>> # Adicionar alternativas
    >>> AlternativaModel.criar(id_questao, 'A', '$x = 2$', correta=False)
    >>> AlternativaModel.criar(id_questao, 'B', '$x = 3$', correta=True)
    >>> # ... etc
    >>>
    >>> # Vincular tags
    >>> QuestaoModel.vincular_tag(id_questao, id_tag_funcao_exp)
    >>>
    >>> # Buscar questões por filtros
    >>> questoes = QuestaoModel.buscar_por_filtros(
    >>>     ano=2024,
    >>>     fonte='ENEM',
    >>>     id_dificuldade=1,
    >>>     tags=[id_tag1, id_tag2]
    >>> )
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from src.models.database import db

logger = logging.getLogger(__name__)


class QuestaoModel:
    """
    Model para a entidade Questão.
    Implementa operações CRUD e gerenciamento de relacionamentos.
    """

    # Constantes
    TIPO_OBJETIVA = 'OBJETIVA'
    TIPO_DISCURSIVA = 'DISCURSIVA'

    @staticmethod
    def criar(enunciado: str, tipo: str, ano: int, fonte: str,
              titulo: str = None, id_dificuldade: int = None,
              imagem_enunciado: str = None, escala_imagem_enunciado: float = 0.7,
              resolucao: str = None, gabarito_discursiva: str = None,
              observacoes: str = None) -> Optional[int]:
        """
        Cria uma nova questão.

        Args:
            enunciado: Texto da questão (pode conter LaTeX)
            tipo: 'OBJETIVA' ou 'DISCURSIVA'
            ano: Ano da questão
            fonte: Banca/Vestibular ou 'AUTORAL'
            titulo: Título opcional para busca
            id_dificuldade: ID da dificuldade (1=Fácil, 2=Médio, 3=Difícil)
            imagem_enunciado: Caminho relativo da imagem
            escala_imagem_enunciado: Escala da imagem (default: 0.7)
            resolucao: Resolução detalhada (LaTeX)
            gabarito_discursiva: Resposta esperada (apenas discursivas)
            observacoes: Comentários internos

        Returns:
            int: ID da questão criada ou None se erro
        """
        try:
            # Validações básicas
            if tipo not in [QuestaoModel.TIPO_OBJETIVA, QuestaoModel.TIPO_DISCURSIVA]:
                logger.error(f"Tipo inválido: {tipo}")
                return None

            if not enunciado or not enunciado.strip():
                logger.error("Enunciado não pode ser vazio")
                return None

            query = """
                INSERT INTO questao (
                    titulo, enunciado, tipo, ano, fonte, id_dificuldade,
                    imagem_enunciado, escala_imagem_enunciado, resolucao,
                    gabarito_discursiva, observacoes, ativo
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """

            params = (
                titulo, enunciado, tipo, ano, fonte.upper(), id_dificuldade,
                imagem_enunciado, escala_imagem_enunciado, resolucao,
                gabarito_discursiva, observacoes
            )

            if db.execute_update(query, params):
                id_questao = db.get_last_insert_id()
                logger.info(f"Questão criada com sucesso. ID: {id_questao}")
                return id_questao
            return None

        except Exception as e:
            logger.error(f"Erro ao criar questão: {e}")
            return None

    @staticmethod
    def buscar_por_id(id_questao: int, incluir_inativas: bool = False) -> Optional[Dict]:
        """
        Busca uma questão pelo ID.

        Args:
            id_questao: ID da questão
            incluir_inativas: Se True, busca também questões inativas

        Returns:
            Dict: Dados da questão ou None se não encontrada
        """
        try:
            filtro_ativo = "" if incluir_inativas else "AND ativo = 1"
            query = f"""
                SELECT
                    q.*,
                    d.nome as dificuldade_nome
                FROM questao q
                LEFT JOIN dificuldade d ON q.id_dificuldade = d.id_dificuldade
                WHERE q.id_questao = ? {filtro_ativo}
            """
            results = db.execute_query(query, (id_questao,))

            if results and len(results) > 0:
                return dict(results[0])
            return None

        except Exception as e:
            logger.error(f"Erro ao buscar questão por ID: {e}")
            return None

    @staticmethod
    def listar_todas(apenas_ativas: bool = True, limite: int = None,
                     offset: int = 0, ordenar_por: str = "data_criacao DESC") -> List[Dict]:
        """
        Lista todas as questões com paginação.

        Args:
            apenas_ativas: Se True, retorna apenas questões ativas
            limite: Número máximo de resultados (None = sem limite)
            offset: Deslocamento para paginação
            ordenar_por: Campo para ordenação

        Returns:
            List[Dict]: Lista de questões
        """
        try:
            filtro_ativo = "WHERE q.ativo = 1" if apenas_ativas else ""
            limite_sql = f"LIMIT {limite}" if limite else ""
            offset_sql = f"OFFSET {offset}" if offset > 0 else ""

            query = f"""
                SELECT
                    q.*,
                    d.nome as dificuldade_nome
                FROM questao q
                LEFT JOIN dificuldade d ON q.id_dificuldade = d.id_dificuldade
                {filtro_ativo}
                ORDER BY {ordenar_por}
                {limite_sql} {offset_sql}
            """
            results = db.execute_query(query)

            if results:
                return [dict(row) for row in results]
            return []

        except Exception as e:
            logger.error(f"Erro ao listar questões: {e}")
            return []

    @staticmethod
    def buscar_por_filtros(titulo: str = None, tipo: str = None,
                          ano: int = None, fonte: str = None,
                          id_dificuldade: int = None, tags: List[int] = None,
                          apenas_ativas: bool = True,
                          limite: int = None, offset: int = 0) -> List[Dict]:
        """
        Busca questões aplicando múltiplos filtros (lógica AND).

        Args:
            titulo: Busca parcial no campo titulo (LIKE)
            tipo: 'OBJETIVA' ou 'DISCURSIVA'
            ano: Ano da questão
            fonte: Banca/Vestibular
            id_dificuldade: ID da dificuldade
            tags: Lista de IDs de tags (AND - questão deve ter TODAS)
            apenas_ativas: Se True, apenas questões ativas
            limite: Número máximo de resultados
            offset: Deslocamento para paginação

        Returns:
            List[Dict]: Lista de questões que atendem aos filtros
        """
        try:
            filtros = []
            params = []

            if apenas_ativas:
                filtros.append("q.ativo = 1")

            if titulo:
                filtros.append("q.titulo LIKE ?")
                params.append(f"%{titulo}%")

            if tipo:
                filtros.append("q.tipo = ?")
                params.append(tipo)

            if ano:
                filtros.append("q.ano = ?")
                params.append(ano)

            if fonte:
                filtros.append("q.fonte = ?")
                params.append(fonte.upper())

            if id_dificuldade:
                filtros.append("q.id_dificuldade = ?")
                params.append(id_dificuldade)

            # Filtro por tags (AND)
            if tags and len(tags) > 0:
                # Subquery para garantir que a questão tem TODAS as tags
                placeholders = ','.join(['?' for _ in tags])
                filtros.append(f"""
                    q.id_questao IN (
                        SELECT id_questao
                        FROM questao_tag
                        WHERE id_tag IN ({placeholders})
                        GROUP BY id_questao
                        HAVING COUNT(DISTINCT id_tag) = ?
                    )
                """)
                params.extend(tags)
                params.append(len(tags))

            where_clause = "WHERE " + " AND ".join(filtros) if filtros else ""
            limite_sql = f"LIMIT {limite}" if limite else ""
            offset_sql = f"OFFSET {offset}" if offset > 0 else ""

            query = f"""
                SELECT
                    q.*,
                    d.nome as dificuldade_nome
                FROM questao q
                LEFT JOIN dificuldade d ON q.id_dificuldade = d.id_dificuldade
                {where_clause}
                ORDER BY q.data_criacao DESC
                {limite_sql} {offset_sql}
            """

            results = db.execute_query(query, tuple(params))

            if results:
                return [dict(row) for row in results]
            return []

        except Exception as e:
            logger.error(f"Erro ao buscar questões por filtros: {e}")
            return []

    @staticmethod
    def atualizar(id_questao: int, **kwargs) -> bool:
        """
        Atualiza uma questão existente.
        Aceita qualquer campo da tabela questao como parâmetro nomeado.

        Args:
            id_questao: ID da questão
            **kwargs: Campos a serem atualizados

        Returns:
            bool: True se atualizado com sucesso
        """
        try:
            campos_permitidos = [
                'titulo', 'enunciado', 'tipo', 'ano', 'fonte', 'id_dificuldade',
                'imagem_enunciado', 'escala_imagem_enunciado', 'resolucao',
                'gabarito_discursiva', 'observacoes'
            ]

            campos = []
            valores = []

            for campo, valor in kwargs.items():
                if campo in campos_permitidos:
                    campos.append(f"{campo} = ?")
                    valores.append(valor)

            if not campos:
                logger.warning("Nenhum campo válido para atualizar")
                return False

            # Adicionar data de modificação
            campos.append("data_modificacao = CURRENT_TIMESTAMP")
            valores.append(id_questao)

            query = f"UPDATE questao SET {', '.join(campos)} WHERE id_questao = ?"

            return db.execute_update(query, tuple(valores))

        except Exception as e:
            logger.error(f"Erro ao atualizar questão: {e}")
            return False

    @staticmethod
    def inativar(id_questao: int) -> bool:
        """
        Inativa uma questão (soft delete).

        Args:
            id_questao: ID da questão

        Returns:
            bool: True se inativada com sucesso
        """
        try:
            query = "UPDATE questao SET ativo = 0 WHERE id_questao = ?"
            return db.execute_update(query, (id_questao,))

        except Exception as e:
            logger.error(f"Erro ao inativar questão: {e}")
            return False

    @staticmethod
    def reativar(id_questao: int) -> bool:
        """
        Reativa uma questão inativada.

        Args:
            id_questao: ID da questão

        Returns:
            bool: True se reativada com sucesso
        """
        try:
            query = "UPDATE questao SET ativo = 1 WHERE id_questao = ?"
            return db.execute_update(query, (id_questao,))

        except Exception as e:
            logger.error(f"Erro ao reativar questão: {e}")
            return False

    @staticmethod
    def vincular_tag(id_questao: int, id_tag: int) -> bool:
        """
        Vincula uma tag a uma questão.

        Args:
            id_questao: ID da questão
            id_tag: ID da tag

        Returns:
            bool: True se vinculada com sucesso
        """
        try:
            query = """
                INSERT OR IGNORE INTO questao_tag (id_questao, id_tag)
                VALUES (?, ?)
            """
            return db.execute_update(query, (id_questao, id_tag))

        except Exception as e:
            logger.error(f"Erro ao vincular tag: {e}")
            return False

    @staticmethod
    def desvincular_tag(id_questao: int, id_tag: int) -> bool:
        """
        Desvincula uma tag de uma questão.

        Args:
            id_questao: ID da questão
            id_tag: ID da tag

        Returns:
            bool: True se desvinculada com sucesso
        """
        try:
            query = "DELETE FROM questao_tag WHERE id_questao = ? AND id_tag = ?"
            return db.execute_update(query, (id_questao, id_tag))

        except Exception as e:
            logger.error(f"Erro ao desvincular tag: {e}")
            return False

    @staticmethod
    def listar_tags(id_questao: int) -> List[Dict]:
        """
        Lista todas as tags de uma questão.

        Args:
            id_questao: ID da questão

        Returns:
            List[Dict]: Lista de tags vinculadas
        """
        try:
            query = """
                SELECT t.*
                FROM tag t
                JOIN questao_tag qt ON t.id_tag = qt.id_tag
                WHERE qt.id_questao = ? AND t.ativo = 1
                ORDER BY t.ordem
            """
            results = db.execute_query(query, (id_questao,))

            if results:
                return [dict(row) for row in results]
            return []

        except Exception as e:
            logger.error(f"Erro ao listar tags da questão: {e}")
            return []

    @staticmethod
    def vincular_versao(id_questao_original: int, id_questao_versao: int,
                       observacao: str = None) -> bool:
        """
        Vincula uma questão como versão alternativa de outra.

        Args:
            id_questao_original: ID da questão original
            id_questao_versao: ID da questão que é versão
            observacao: Nota sobre a relação

        Returns:
            bool: True se vinculada com sucesso
        """
        try:
            query = """
                INSERT OR IGNORE INTO questao_versao
                (id_questao_original, id_questao_versao, observacao)
                VALUES (?, ?, ?)
            """
            return db.execute_update(query, (id_questao_original, id_questao_versao, observacao))

        except Exception as e:
            logger.error(f"Erro ao vincular versão: {e}")
            return False

    @staticmethod
    def listar_versoes(id_questao: int) -> List[Dict]:
        """
        Lista todas as versões alternativas de uma questão.

        Args:
            id_questao: ID da questão

        Returns:
            List[Dict]: Lista de questões que são versões
        """
        try:
            query = """
                SELECT q.*, qv.observacao
                FROM questao q
                JOIN questao_versao qv ON q.id_questao = qv.id_questao_versao
                WHERE qv.id_questao_original = ? AND q.ativo = 1
            """
            results = db.execute_query(query, (id_questao,))

            if results:
                return [dict(row) for row in results]
            return []

        except Exception as e:
            logger.error(f"Erro ao listar versões: {e}")
            return []

    @staticmethod
    def contar_total(apenas_ativas: bool = True) -> int:
        """
        Conta o total de questões no banco.

        Args:
            apenas_ativas: Se True, conta apenas questões ativas

        Returns:
            int: Total de questões
        """
        try:
            filtro = "WHERE ativo = 1" if apenas_ativas else ""
            query = f"SELECT COUNT(*) as total FROM questao {filtro}"
            result = db.execute_query(query)

            if result:
                return result[0]['total']
            return 0

        except Exception as e:
            logger.error(f"Erro ao contar questões: {e}")
            return 0


if __name__ == "__main__":
    """Testes do modelo"""
    print("=" * 60)
    print("TESTE DO MODEL QUESTÃO")
    print("=" * 60)

    # Contar questões
    print("\n1. Contando questões:")
    total = QuestaoModel.contar_total()
    print(f"   - Total de questões ativas: {total}")

    # Listar primeiras questões
    print("\n2. Listando primeiras questões:")
    questoes = QuestaoModel.listar_todas(limite=5)
    for q in questoes:
        print(f"   - ID {q['id_questao']}: {q.get('titulo', 'Sem título')}")

    print("\n" + "=" * 60)
    print("TESTE CONCLUÍDO")
    print("=" * 60)
