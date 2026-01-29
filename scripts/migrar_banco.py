# -*- coding: utf-8 -*-
"""
Script de Migracao do Banco de Dados
====================================

Adaptado para estrutura com UUIDs.

Este script executa a migracao completa:
1. Cria tabela disciplina
2. Adiciona coluna uuid_disciplina na tabela tag
3. Cria tabela nivel_escolar
4. Cria tabela questao_nivel
5. Expande tabela fonte_questao (se necessario)
6. Migra tags V* para fonte_questao
7. Migra tags N* para nivel_escolar/questao_nivel
8. Remove tags V* e N*

USO:
    python scripts/migrar_banco.py --dry-run    # Apenas mostra o que faria
    python scripts/migrar_banco.py              # Executa a migracao
"""

import sqlite3
import shutil
import argparse
import uuid
from datetime import datetime
from pathlib import Path

# ============================================================
# CONFIGURACAO
# ============================================================

DATABASE_PATH = "database/sistema_questoes_v2.db"
BACKUP_DIR = "database/backups"

# Disciplinas padrao
DISCIPLINAS_PADRAO = [
    ("MAT", "Matematica", "Matematica e Raciocinio Logico", "#3498db", 1),
    ("FIS", "Fisica", "Fisica Geral e Aplicada", "#e74c3c", 2),
    ("QUI", "Quimica", "Quimica Geral, Organica e Inorganica", "#9b59b6", 3),
    ("BIO", "Biologia", "Biologia Geral, Ecologia e Genetica", "#27ae60", 4),
    ("POR", "Portugues", "Lingua Portuguesa e Literatura", "#f39c12", 5),
    ("RED", "Redacao", "Producao Textual", "#e67e22", 6),
    ("HIS", "Historia", "Historia Geral e do Brasil", "#1abc9c", 7),
    ("GEO", "Geografia", "Geografia Geral e do Brasil", "#16a085", 8),
    ("FIL", "Filosofia", "Filosofia Geral", "#8e44ad", 9),
    ("SOC", "Sociologia", "Sociologia Geral", "#2c3e50", 10),
    ("ING", "Ingles", "Lingua Inglesa", "#c0392b", 11),
    ("ESP", "Espanhol", "Lingua Espanhola", "#d35400", 12),
]

# Niveis escolares padrao
NIVEIS_PADRAO = [
    ("EF1", "Ensino Fundamental I", "1 ao 5 ano", 1),
    ("EF2", "Ensino Fundamental II", "6 ao 9 ano", 2),
    ("EM", "Ensino Medio", "1 a 3 serie", 3),
    ("PRE", "Pre-Vestibular", "Cursinho preparatorio", 4),
    ("EJA", "Educacao de Jovens e Adultos", "EJA Fundamental e Medio", 5),
    ("TEC", "Ensino Tecnico", "Cursos tecnicos", 6),
    ("SUP", "Ensino Superior", "Graduacao", 7),
    ("POS", "Pos-Graduacao", "Especializacao, Mestrado, Doutorado", 8),
]

# Mapeamento de tags N* para niveis
# Baseado nos seus dados: N1=E.F.2, N2=E.M., N3=E.J.A.
MAPEAMENTO_NIVEIS = {
    'e.f.1': 'EF1',
    'e.f.2': 'EF2',
    'e.f.': 'EF2',
    'fundamental': 'EF2',
    'e.m.': 'EM',
    'medio': 'EM',
    'e.j.a.': 'EJA',
    'eja': 'EJA',
}


# ============================================================
# FUNCOES AUXILIARES
# ============================================================

def print_header(texto):
    print("\n" + "=" * 60)
    print(f" {texto}")
    print("=" * 60)


def print_ok(texto):
    print(f"   [OK] {texto}")


def print_erro(texto):
    print(f"   [ERRO] {texto}")


def print_aviso(texto):
    print(f"   [AVISO] {texto}")


def print_info(texto):
    print(f"   [INFO] {texto}")


def gerar_uuid():
    """Gera um novo UUID."""
    return str(uuid.uuid4())


def criar_backup(db_path):
    """Cria backup do banco de dados."""
    backup_dir = Path(BACKUP_DIR)
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"backup_pre_migracao_{timestamp}.db"

    shutil.copy2(db_path, backup_path)
    print_ok(f"Backup criado: {backup_path}")

    return str(backup_path)


def coluna_existe(cursor, tabela, coluna):
    """Verifica se uma coluna existe em uma tabela."""
    cursor.execute(f"PRAGMA table_info([{tabela}])")
    colunas = [col[1] for col in cursor.fetchall()]
    return coluna in colunas


def tabela_existe(cursor, tabela):
    """Verifica se uma tabela existe."""
    cursor.execute("""
                   SELECT name
                   FROM sqlite_master
                   WHERE type = 'table'
                     AND name = ?
                   """, (tabela,))
    return cursor.fetchone() is not None


# ============================================================
# FUNCOES DE MIGRACAO
# ============================================================

def criar_tabela_disciplina(cursor, dry_run=False):
    """Cria a tabela disciplina."""
    print_header("ETAPA 1: Criar tabela DISCIPLINA")

    if tabela_existe(cursor, 'disciplina'):
        print_aviso("Tabela disciplina ja existe")
        return

    if dry_run:
        print_info("Criaria tabela disciplina com as colunas:")
        print_info("  codigo, nome, descricao, cor, ordem, uuid, data_criacao, ativo")
        print_info(f"Inseriria {len(DISCIPLINAS_PADRAO)} disciplinas padrao")
        return

    cursor.execute("""
                   CREATE TABLE disciplina
                   (
                       codigo       VARCHAR(10)  NOT NULL UNIQUE,
                       nome         VARCHAR(100) NOT NULL,
                       descricao    TEXT,
                       cor          VARCHAR(7)            DEFAULT '#3498db',
                       ordem        INTEGER      NOT NULL DEFAULT 0,
                       uuid         VARCHAR(36) PRIMARY KEY,
                       data_criacao DATETIME              DEFAULT CURRENT_TIMESTAMP,
                       ativo        BOOLEAN      NOT NULL DEFAULT 1
                   )
                   """)
    print_ok("Tabela disciplina criada")

    # Inserir disciplinas padrao
    for codigo, nome, descricao, cor, ordem in DISCIPLINAS_PADRAO:
        cursor.execute("""
                       INSERT INTO disciplina (codigo, nome, descricao, cor, ordem, uuid, ativo)
                       VALUES (?, ?, ?, ?, ?, ?, 1)
                       """, (codigo, nome, descricao, cor, ordem, gerar_uuid()))

    print_ok(f"{len(DISCIPLINAS_PADRAO)} disciplinas padrao inseridas")

    # Listar
    cursor.execute("SELECT codigo, nome FROM disciplina ORDER BY ordem")
    for codigo, nome in cursor.fetchall():
        print_info(f"  {codigo}: {nome}")


def adicionar_disciplina_na_tag(cursor, dry_run=False):
    """Adiciona coluna uuid_disciplina na tabela tag."""
    print_header("ETAPA 2: Adicionar uuid_disciplina na tabela TAG")

    if coluna_existe(cursor, 'tag', 'uuid_disciplina'):
        print_aviso("Coluna uuid_disciplina ja existe na tabela tag")
        return

    if dry_run:
        print_info("Adicionaria coluna uuid_disciplina na tabela tag")
        print_info("Associaria tags existentes a disciplina Matematica")
        return

    # Adiciona a coluna
    cursor.execute("""
                   ALTER TABLE tag
                       ADD COLUMN uuid_disciplina VARCHAR(36)
                           REFERENCES disciplina (uuid)
                   """)
    print_ok("Coluna uuid_disciplina adicionada")

    # Busca o UUID da disciplina Matematica
    cursor.execute("SELECT uuid FROM disciplina WHERE codigo = 'MAT'")
    resultado = cursor.fetchone()

    if resultado:
        uuid_matematica = resultado[0]

        # Associa todas as tags de conteudo (nao V* nem N*) a Matematica
        cursor.execute("""
                       UPDATE tag
                       SET uuid_disciplina = ?
                       WHERE numeracao NOT LIKE 'V%'
                         AND numeracao NOT LIKE 'N%'
                       """, (uuid_matematica,))

        qtd = cursor.rowcount
        print_ok(f"{qtd} tags de conteudo associadas a Matematica")
    else:
        print_erro("Disciplina Matematica nao encontrada!")


def criar_tabela_nivel_escolar(cursor, dry_run=False):
    """Cria a tabela nivel_escolar."""
    print_header("ETAPA 3: Criar tabela NIVEL_ESCOLAR")

    if tabela_existe(cursor, 'nivel_escolar'):
        print_aviso("Tabela nivel_escolar ja existe")
        return

    if dry_run:
        print_info("Criaria tabela nivel_escolar")
        print_info(f"Inseriria {len(NIVEIS_PADRAO)} niveis padrao")
        return

    cursor.execute("""
                   CREATE TABLE nivel_escolar
                   (
                       codigo       VARCHAR(10)  NOT NULL UNIQUE,
                       nome         VARCHAR(100) NOT NULL,
                       descricao    TEXT,
                       ordem        INTEGER      NOT NULL DEFAULT 0,
                       uuid         VARCHAR(36) PRIMARY KEY,
                       data_criacao DATETIME              DEFAULT CURRENT_TIMESTAMP,
                       ativo        BOOLEAN      NOT NULL DEFAULT 1
                   )
                   """)
    print_ok("Tabela nivel_escolar criada")

    # Inserir niveis padrao
    for codigo, nome, descricao, ordem in NIVEIS_PADRAO:
        cursor.execute("""
                       INSERT INTO nivel_escolar (codigo, nome, descricao, ordem, uuid, ativo)
                       VALUES (?, ?, ?, ?, ?, 1)
                       """, (codigo, nome, descricao, ordem, gerar_uuid()))

    print_ok(f"{len(NIVEIS_PADRAO)} niveis escolares inseridos")

    cursor.execute("SELECT codigo, nome FROM nivel_escolar ORDER BY ordem")
    for codigo, nome in cursor.fetchall():
        print_info(f"  {codigo}: {nome}")


def criar_tabela_questao_nivel(cursor, dry_run=False):
    """Cria a tabela de relacionamento questao_nivel."""
    print_header("ETAPA 4: Criar tabela QUESTAO_NIVEL")

    if tabela_existe(cursor, 'questao_nivel'):
        print_aviso("Tabela questao_nivel ja existe")
        return

    if dry_run:
        print_info("Criaria tabela questao_nivel (relacionamento N:N)")
        return

    cursor.execute("""
                   CREATE TABLE questao_nivel
                   (
                       uuid_questao VARCHAR(36) NOT NULL,
                       uuid_nivel   VARCHAR(36) NOT NULL,
                       data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
                       PRIMARY KEY (uuid_questao, uuid_nivel),
                       FOREIGN KEY (uuid_questao) REFERENCES questao (uuid) ON DELETE CASCADE,
                       FOREIGN KEY (uuid_nivel) REFERENCES nivel_escolar (uuid) ON DELETE CASCADE
                   )
                   """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_qn_questao ON questao_nivel(uuid_questao)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_qn_nivel ON questao_nivel(uuid_nivel)")

    print_ok("Tabela questao_nivel criada com indices")


def expandir_fonte_questao(cursor, dry_run=False):
    """Expande a tabela fonte_questao com novas colunas."""
    print_header("ETAPA 5: Expandir tabela FONTE_QUESTAO")

    if not tabela_existe(cursor, 'fonte_questao'):
        print_erro("Tabela fonte_questao nao existe!")
        return

    # Adiciona colunas que nao existem
    novas_colunas = [
        ("estado", "VARCHAR(2)"),
        ("ano_inicio", "INTEGER"),
        ("ano_fim", "INTEGER"),
        ("url_oficial", "VARCHAR(500)"),
    ]

    for nome_col, tipo in novas_colunas:
        if not coluna_existe(cursor, 'fonte_questao', nome_col):
            if dry_run:
                print_info(f"Adicionaria coluna {nome_col}")
            else:
                try:
                    cursor.execute(f"ALTER TABLE fonte_questao ADD COLUMN {nome_col} {tipo}")
                    print_ok(f"Coluna {nome_col} adicionada")
                except Exception as e:
                    print_aviso(f"Coluna {nome_col}: {e}")
        else:
            print_info(f"Coluna {nome_col} ja existe")


def migrar_tags_vestibular(cursor, dry_run=False):
    """Migra tags V* para fonte_questao."""
    print_header("ETAPA 6: Migrar tags de VESTIBULAR (V*)")

    cursor.execute("""
                   SELECT uuid, numeracao, nome
                   FROM tag
                   WHERE numeracao LIKE 'V%'
                   ORDER BY numeracao
                   """)
    tags_vest = cursor.fetchall()

    if not tags_vest:
        print_info("Nenhuma tag de vestibular encontrada")
        return

    print_info(f"{len(tags_vest)} tags de vestibular encontradas")

    for uuid_tag, numeracao, nome in tags_vest:
        print_info(f"  {numeracao}: {nome}")

        if dry_run:
            continue

        # Verifica se ja existe na fonte_questao
        cursor.execute("SELECT uuid FROM fonte_questao WHERE nome_completo = ? OR sigla = ?",
                       (nome, nome))
        existente = cursor.fetchone()

        if existente:
            uuid_fonte = existente[0]
            print_info(f"    -> Ja existe em fonte_questao")
        else:
            # Insere nova fonte
            uuid_fonte = gerar_uuid()
            data_agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                           INSERT INTO fonte_questao (sigla, nome_completo, tipo_instituicao, uuid, ativo, data_criacao)
                           VALUES (?, ?, 'VESTIBULAR', ?, 1, ?)
                           """, (nome, nome, uuid_fonte, data_agora))
            print_ok(f"    -> Inserido em fonte_questao")

        # Atualiza questoes que usavam essa tag para usar a fonte
        # Primeiro, pega as questoes que tem essa tag
        cursor.execute("""
                       SELECT uuid_questao
                       FROM questao_tag
                       WHERE uuid_tag = ?
                       """, (uuid_tag,))
        questoes_com_tag = cursor.fetchall()

        for (uuid_questao,) in questoes_com_tag:
            # Verifica se a questao ja tem fonte definida
            cursor.execute("SELECT uuid_fonte FROM questao WHERE uuid = ?", (uuid_questao,))
            resultado = cursor.fetchone()
            if resultado and resultado[0] is None:
                cursor.execute("""
                               UPDATE questao
                               SET uuid_fonte = ?
                               WHERE uuid = ?
                               """, (uuid_fonte, uuid_questao))

        if questoes_com_tag:
            print_info(f"    -> {len(questoes_com_tag)} questoes verificadas")

        # Remove relacionamentos questao_tag
        cursor.execute("DELETE FROM questao_tag WHERE uuid_tag = ?", (uuid_tag,))

        # Remove a tag
        cursor.execute("DELETE FROM tag WHERE uuid = ?", (uuid_tag,))

    if not dry_run:
        print_ok("Tags de vestibular migradas e removidas")


def migrar_tags_nivel(cursor, dry_run=False):
    """Migra tags N* para nivel_escolar."""
    print_header("ETAPA 7: Migrar tags de NIVEL (N*)")

    cursor.execute("""
                   SELECT uuid, numeracao, nome
                   FROM tag
                   WHERE numeracao LIKE 'N%'
                   ORDER BY numeracao
                   """)
    tags_nivel = cursor.fetchall()

    if not tags_nivel:
        print_info("Nenhuma tag de nivel encontrada")
        return

    print_info(f"{len(tags_nivel)} tags de nivel encontradas")

    for uuid_tag, numeracao, nome in tags_nivel:
        print_info(f"  {numeracao}: {nome}")

        # Encontra o codigo do nivel correspondente
        codigo_nivel = None
        nome_lower = nome.lower().strip()

        for chave, codigo in MAPEAMENTO_NIVEIS.items():
            if chave in nome_lower:
                codigo_nivel = codigo
                break

        if not codigo_nivel:
            print_aviso(f"    -> Nao foi possivel mapear para nivel escolar")
            continue

        if dry_run:
            print_info(f"    -> Seria mapeado para {codigo_nivel}")
            continue

        # Busca o uuid do nivel
        cursor.execute("SELECT uuid FROM nivel_escolar WHERE codigo = ?", (codigo_nivel,))
        resultado = cursor.fetchone()

        if not resultado:
            print_aviso(f"    -> Nivel {codigo_nivel} nao encontrado")
            continue

        uuid_nivel = resultado[0]
        print_ok(f"    -> Mapeado para {codigo_nivel}")

        # Migra relacionamentos para questao_nivel
        cursor.execute("""
                       SELECT uuid_questao
                       FROM questao_tag
                       WHERE uuid_tag = ?
                       """, (uuid_tag,))
        questoes = cursor.fetchall()

        for (uuid_questao,) in questoes:
            try:
                cursor.execute("""
                               INSERT
                               OR IGNORE INTO questao_nivel (uuid_questao, uuid_nivel)
                    VALUES (?, ?)
                               """, (uuid_questao, uuid_nivel))
            except Exception as e:
                print_aviso(f"    Erro ao inserir relacao: {e}")

        if questoes:
            print_info(f"    -> {len(questoes)} questoes associadas ao nivel")

        # Remove relacionamentos questao_tag
        cursor.execute("DELETE FROM questao_tag WHERE uuid_tag = ?", (uuid_tag,))

        # Remove a tag
        cursor.execute("DELETE FROM tag WHERE uuid = ?", (uuid_tag,))

    if not dry_run:
        print_ok("Tags de nivel migradas e removidas")


def criar_indices(cursor, dry_run=False):
    """Cria indices para melhor performance."""
    print_header("ETAPA 8: Criar INDICES")

    indices = [
        ("idx_tag_disciplina", "tag", "uuid_disciplina"),
        ("idx_disciplina_codigo", "disciplina", "codigo"),
        ("idx_disciplina_ativo", "disciplina", "ativo"),
        ("idx_nivel_codigo", "nivel_escolar", "codigo"),
        ("idx_nivel_ativo", "nivel_escolar", "ativo"),
        ("idx_fonte_tipo", "fonte_questao", "tipo_instituicao"),
        ("idx_fonte_ativo", "fonte_questao", "ativo"),
    ]

    for nome_idx, tabela, coluna in indices:
        if dry_run:
            print_info(f"Criaria indice {nome_idx} em {tabela}({coluna})")
        else:
            try:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS {nome_idx} ON {tabela}({coluna})")
                print_ok(f"Indice {nome_idx} criado")
            except Exception as e:
                print_aviso(f"Indice {nome_idx}: {e}")


def verificar_resultado(cursor):
    """Verifica o resultado da migracao."""
    print_header("VERIFICACAO FINAL")

    # Disciplinas
    if tabela_existe(cursor, 'disciplina'):
        cursor.execute("SELECT COUNT(*) FROM disciplina")
        print_info(f"Disciplinas: {cursor.fetchone()[0]}")

    # Niveis
    if tabela_existe(cursor, 'nivel_escolar'):
        cursor.execute("SELECT COUNT(*) FROM nivel_escolar")
        print_info(f"Niveis escolares: {cursor.fetchone()[0]}")

    # Fontes
    cursor.execute("SELECT COUNT(*) FROM fonte_questao")
    print_info(f"Fontes de questao: {cursor.fetchone()[0]}")

    # Tags restantes
    cursor.execute("SELECT COUNT(*) FROM tag WHERE numeracao LIKE 'V%' OR numeracao LIKE 'N%'")
    tags_resto = cursor.fetchone()[0]
    if tags_resto == 0:
        print_ok("Nenhuma tag V*/N* restante")
    else:
        print_erro(f"{tags_resto} tags V*/N* ainda existem!")

    # Tags com disciplina
    if coluna_existe(cursor, 'tag', 'uuid_disciplina'):
        cursor.execute("SELECT COUNT(*) FROM tag WHERE uuid_disciplina IS NOT NULL")
        print_info(f"Tags com disciplina definida: {cursor.fetchone()[0]}")

    # Relacionamentos questao_nivel
    if tabela_existe(cursor, 'questao_nivel'):
        cursor.execute("SELECT COUNT(*) FROM questao_nivel")
        print_info(f"Relacionamentos questao-nivel: {cursor.fetchone()[0]}")


# ============================================================
# FUNCAO PRINCIPAL
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Migracao do banco de dados")
    parser.add_argument("--dry-run", action="store_true", help="Apenas mostra o que seria feito")
    parser.add_argument("--no-backup", action="store_true", help="Nao criar backup")
    args = parser.parse_args()

    print("=" * 60)
    print(" MIGRACAO DO BANCO DE DADOS")
    print(" Disciplinas, Niveis e Fontes")
    print("=" * 60)

    if args.dry_run:
        print("\n[AVISO] MODO DRY-RUN: Nenhuma alteracao sera feita\n")

    # Verifica se o banco existe
    if not Path(DATABASE_PATH).exists():
        print_erro(f"Banco nao encontrado: {DATABASE_PATH}")
        return 1

    # Backup
    if not args.no_backup and not args.dry_run:
        criar_backup(DATABASE_PATH)

    # Conecta ao banco
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")

    try:
        # Executa etapas
        criar_tabela_disciplina(cursor, args.dry_run)
        adicionar_disciplina_na_tag(cursor, args.dry_run)
        criar_tabela_nivel_escolar(cursor, args.dry_run)
        criar_tabela_questao_nivel(cursor, args.dry_run)
        expandir_fonte_questao(cursor, args.dry_run)
        migrar_tags_vestibular(cursor, args.dry_run)
        migrar_tags_nivel(cursor, args.dry_run)
        criar_indices(cursor, args.dry_run)

        if not args.dry_run:
            conn.commit()
            print_ok("\nAlteracoes salvas no banco de dados")

        verificar_resultado(cursor)

    except Exception as e:
        conn.rollback()
        print_erro(f"\nERRO: {e}")
        print_info("Alteracoes foram revertidas")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        conn.close()

    print("\n" + "=" * 60)
    if args.dry_run:
        print(" DRY-RUN CONCLUIDO")
        print(" Execute sem --dry-run para aplicar as alteracoes")
    else:
        print(" MIGRACAO CONCLUIDA COM SUCESSO!")
    print("=" * 60 + "\n")

    return 0


if __name__ == "__main__":
    exit(main())