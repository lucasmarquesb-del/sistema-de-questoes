"""
Sistema de Banco de Questões Educacionais
Módulo: Database
Descrição: Gerenciamento de conexão e inicialização do banco de dados SQLite
Versão: 1.0.1
Data: Janeiro 2026
"""

import sqlite3
import os
from pathlib import Path
from typing import Optional
import logging

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Database:
    """
    Classe responsável pelo gerenciamento da conexão com o banco de dados SQLite.
    Implementa o padrão Singleton para garantir uma única instância de conexão.
    """

    _instance: Optional['Database'] = None
    _connection: Optional[sqlite3.Connection] = None

    def __new__(cls):
        """Implementa o padrão Singleton"""
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Inicializa a classe Database"""
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.db_path = None
            self.project_root = None

    def get_project_root(self) -> Path:
        """
        Retorna o diretório raiz do projeto.

        Returns:
            Path: Caminho absoluto para o diretório raiz
        """
        if self.project_root is None:
            # Assume que database.py está em src/models/
            current_file = Path(__file__)
            self.project_root = current_file.parent.parent.parent
        return self.project_root

    def get_db_path(self) -> Path:
        """
        Retorna o caminho completo para o arquivo do banco de dados.

        Returns:
            Path: Caminho absoluto para questoes.db
        """
        if self.db_path is None:
            root = self.get_project_root()
            db_dir = root / 'database'
            db_dir.mkdir(exist_ok=True)
            self.db_path = db_dir / 'questoes.db'
        return self.db_path

    def connect(self) -> sqlite3.Connection:
        """
        Estabelece conexão com o banco de dados.
        Se o banco não existir, será criado.

        Returns:
            sqlite3.Connection: Objeto de conexão com o banco

        Raises:
            sqlite3.Error: Se houver erro ao conectar
        """
        try:
            if self._connection is None:
                db_path = self.get_db_path()
                db_exists = db_path.exists()

                # Configurações da conexão
                self._connection = sqlite3.connect(
                    str(db_path),
                    check_same_thread=False,
                    timeout=10.0
                )

                # Habilitar foreign keys
                self._connection.execute("PRAGMA foreign_keys = ON")

                # Configurar row factory para retornar dicionários
                self._connection.row_factory = sqlite3.Row

                if db_exists:
                    logger.info(f"Conectado ao banco de dados: {db_path}")
                else:
                    logger.info(f"Banco de dados criado: {db_path}")

            return self._connection

        except sqlite3.Error as e:
            logger.error(f"Erro ao conectar ao banco de dados: {e}")
            raise

    def disconnect(self):
        """
        Fecha a conexão com o banco de dados.
        """
        if self._connection is not None:
            try:
                self._connection.close()
                self._connection = None
                logger.info("Conexão com banco de dados fechada")
            except sqlite3.Error as e:
                logger.error(f"Erro ao fechar conexão: {e}")

    def initialize_database(self) -> bool:
        """
        Inicializa o banco de dados executando o script SQL.
        Cria todas as tabelas, índices, triggers e dados iniciais.

        Returns:
            bool: True se inicialização foi bem sucedida, False caso contrário
        """
        try:
            # Conectar ao banco
            conn = self.connect()
            cursor = conn.cursor()

            # Localizar arquivo SQL
            root = self.get_project_root()
            sql_file = root / 'database' / 'init_db.sql'

            if not sql_file.exists():
                logger.error(f"Arquivo SQL não encontrado: {sql_file}")
                return False

            # Ler e executar script SQL
            logger.info("Iniciando criação das tabelas...")
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_script = f.read()

            # Executar script (pode conter múltiplos comandos)
            cursor.executescript(sql_script)
            conn.commit()

            logger.info("Banco de dados inicializado com sucesso!")
            logger.info("Tabelas criadas: tag, dificuldade, questao, alternativa, " +
                       "questao_tag, lista, lista_questao, questao_versao, configuracao")

            return True

        except sqlite3.Error as e:
            logger.error(f"Erro ao inicializar banco de dados: {e}")
            if conn:
                conn.rollback()
            return False

        except FileNotFoundError as e:
            logger.error(f"Arquivo não encontrado: {e}")
            return False

        except Exception as e:
            logger.error(f"Erro inesperado: {e}")
            return False

    def verify_database_integrity(self) -> bool:
        """
        Verifica a integridade do banco de dados.
        Checa se todas as tabelas essenciais existem.

        Returns:
            bool: True se o banco está íntegro, False caso contrário
        """
        try:
            conn = self.connect()
            cursor = conn.cursor()

            # Lista de tabelas obrigatórias
            required_tables = [
                'tag',
                'dificuldade',
                'questao',
                'alternativa',
                'questao_tag',
                'lista',
                'lista_questao',
                'questao_versao',
                'configuracao'
            ]

            # Verificar cada tabela
            for table in required_tables:
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (table,)
                )
                if cursor.fetchone() is None:
                    logger.error(f"Tabela '{table}' não encontrada no banco de dados")
                    return False

            logger.info("Integridade do banco de dados verificada com sucesso")
            return True

        except sqlite3.Error as e:
            logger.error(f"Erro ao verificar integridade: {e}")
            return False

    def execute_query(self, query: str, params: tuple = None) -> Optional[list]:
        """
        Executa uma query SELECT no banco de dados.

        Args:
            query: SQL query a ser executada
            params: Parâmetros para prepared statement

        Returns:
            list: Lista de resultados (sqlite3.Row) ou None se erro
        """
        try:
            conn = self.connect()
            cursor = conn.cursor()

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            results = cursor.fetchall()
            return results

        except sqlite3.Error as e:
            logger.error(f"Erro ao executar query: {e}")
            return None

    def execute_update(self, query: str, params: tuple = None) -> bool:
        """
        Executa uma query de modificação (INSERT, UPDATE, DELETE).

        Args:
            query: SQL query a ser executada
            params: Parâmetros para prepared statement

        Returns:
            bool: True se bem sucedido, False caso contrário
        """
        try:
            conn = self.connect()
            cursor = conn.cursor()

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            conn.commit()

            # Armazenar lastrowid para ser recuperado depois
            self._last_insert_id = cursor.lastrowid

            return True

        except sqlite3.Error as e:
            logger.error(f"Erro ao executar update: {e}")
            if conn:
                conn.rollback()
            return False

    def get_last_insert_id(self) -> Optional[int]:
        """
        Retorna o ID do último registro inserido.

        Returns:
            int: ID do último insert ou None se erro
        """
        try:
            return getattr(self, '_last_insert_id', None)
        except Exception as e:
            logger.error(f"Erro ao obter último ID: {e}")
            return None

    def backup_database(self, backup_path: str) -> bool:
        """
        Cria um backup do banco de dados.

        Args:
            backup_path: Caminho completo para o arquivo de backup

        Returns:
            bool: True se backup foi criado com sucesso
        """
        try:
            conn = self.connect()
            backup_conn = sqlite3.connect(backup_path)

            with backup_conn:
                conn.backup(backup_conn)

            backup_conn.close()
            logger.info(f"Backup criado com sucesso: {backup_path}")
            return True

        except sqlite3.Error as e:
            logger.error(f"Erro ao criar backup: {e}")
            return False


# Instância global do banco de dados
db = Database()


# Funções auxiliares para facilitar o uso
def get_connection() -> sqlite3.Connection:
    """Retorna a conexão ativa com o banco de dados"""
    return db.connect()


def initialize_db() -> bool:
    """Inicializa o banco de dados"""
    return db.initialize_database()


def verify_db() -> bool:
    """Verifica integridade do banco de dados"""
    return db.verify_database_integrity()


def close_db():
    """Fecha a conexão com o banco de dados"""
    db.disconnect()


if __name__ == "__main__":
    """
    Teste do módulo database.
    Executa quando o arquivo é rodado diretamente.
    """
    print("=" * 60)
    print("TESTE DO MÓDULO DATABASE")
    print("=" * 60)

    # Inicializar banco
    print("\n1. Inicializando banco de dados...")
    if initialize_db():
        print("✓ Banco inicializado com sucesso!")
    else:
        print("✗ Erro ao inicializar banco")
        exit(1)

    # Verificar integridade
    print("\n2. Verificando integridade...")
    if verify_db():
        print("✓ Integridade verificada!")
    else:
        print("✗ Problemas de integridade detectados")
        exit(1)

    # Testar queries básicas
    print("\n3. Testando queries básicas...")

    # Contar dificuldades
    result = db.execute_query("SELECT COUNT(*) as total FROM dificuldade")
    if result:
        print(f"   - Dificuldades cadastradas: {result[0]['total']}")

    # Contar tags
    result = db.execute_query("SELECT COUNT(*) as total FROM tag")
    if result:
        print(f"   - Tags cadastradas: {result[0]['total']}")

    # Contar configurações
    result = db.execute_query("SELECT COUNT(*) as total FROM configuracao")
    if result:
        print(f"   - Configurações: {result[0]['total']}")

    # Listar dificuldades
    print("\n4. Listando dificuldades:")
    dificuldades = db.execute_query(
        "SELECT nome, descricao FROM dificuldade ORDER BY ordem"
    )
    if dificuldades:
        for diff in dificuldades:
            print(f"   - {diff['nome']}: {diff['descricao']}")

    print("\n" + "=" * 60)
    print("TESTE CONCLUÍDO COM SUCESSO!")
    print("=" * 60)

    # Fechar conexão
    close_db()
