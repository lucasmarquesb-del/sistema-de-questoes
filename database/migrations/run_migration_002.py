"""
Script para executar a migration 002 - Adicionar campos de imagem remota
Execute este script para atualizar o banco de dados.
"""
import os
import sys
import sqlite3

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def get_db_path():
    """Retorna o caminho do banco de dados"""
    # Tentar ler do config.ini
    import configparser
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config.ini')
    config.read(config_path, encoding='utf-8')
    return config.get('DATABASE', 'db_path', fallback='database/questoes.db')


def table_exists(cursor, table_name):
    """Verifica se uma tabela existe"""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return cursor.fetchone() is not None


def column_exists(cursor, table_name, column_name):
    """Verifica se uma coluna existe em uma tabela"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns


def create_imagem_table(cursor):
    """Cria a tabela imagem com todos os campos"""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS imagem (
            uuid TEXT PRIMARY KEY,
            data_criacao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            ativo BOOLEAN NOT NULL DEFAULT 1,
            nome_arquivo VARCHAR(255) UNIQUE NOT NULL,
            caminho_relativo VARCHAR(500) NOT NULL,
            hash_md5 VARCHAR(32) UNIQUE NOT NULL,
            tamanho_bytes INTEGER NOT NULL,
            largura INTEGER NOT NULL,
            altura INTEGER NOT NULL,
            formato VARCHAR(10) NOT NULL,
            mime_type VARCHAR(50) NOT NULL,
            data_upload DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            url_remota VARCHAR(1000),
            servico_hospedagem VARCHAR(50),
            id_remoto VARCHAR(255),
            url_thumbnail VARCHAR(1000),
            data_upload_remoto DATETIME
        )
    """)

    # Criar índices
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_imagem_hash ON imagem(hash_md5)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_imagem_nome ON imagem(nome_arquivo)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_imagem_url_remota ON imagem(url_remota)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_imagem_servico ON imagem(servico_hospedagem)")

    print("Tabela 'imagem' criada com sucesso!")


def add_remote_columns(cursor):
    """Adiciona as colunas de imagem remota se não existirem"""
    columns_to_add = [
        ('url_remota', 'VARCHAR(1000)'),
        ('servico_hospedagem', 'VARCHAR(50)'),
        ('id_remoto', 'VARCHAR(255)'),
        ('url_thumbnail', 'VARCHAR(1000)'),
        ('data_upload_remoto', 'DATETIME'),
    ]

    for column_name, column_type in columns_to_add:
        if not column_exists(cursor, 'imagem', column_name):
            cursor.execute(f"ALTER TABLE imagem ADD COLUMN {column_name} {column_type}")
            print(f"Coluna '{column_name}' adicionada!")
        else:
            print(f"Coluna '{column_name}' já existe, pulando...")

    # Criar índices se não existirem
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_imagem_url_remota ON imagem(url_remota)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_imagem_servico ON imagem(servico_hospedagem)")


def run_migration():
    """Executa a migration"""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    db_path = os.path.join(base_dir, get_db_path())

    print(f"Conectando ao banco: {db_path}")

    if not os.path.exists(db_path):
        print(f"ERRO: Banco de dados não encontrado em {db_path}")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        if not table_exists(cursor, 'imagem'):
            print("Tabela 'imagem' não existe. Criando...")
            create_imagem_table(cursor)
        else:
            print("Tabela 'imagem' já existe. Adicionando novas colunas...")
            add_remote_columns(cursor)

        conn.commit()
        print("\nMigration 002 executada com sucesso!")
        return True

    except Exception as e:
        conn.rollback()
        print(f"ERRO na migration: {e}")
        return False
    finally:
        conn.close()


if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)
