# -*- coding: utf-8 -*-
"""
Script de correcao para popular disciplinas e associar tags.

Execute apos a migracao principal.
"""

import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

DATABASE_PATH = "database/sistema_questoes_v2.db"

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


def gerar_uuid():
    return str(uuid.uuid4())


def main():
    print("=" * 60)
    print(" CORRECAO: Popular Disciplinas e Associar Tags")
    print("=" * 60)

    if not Path(DATABASE_PATH).exists():
        print(f"[ERRO] Banco nao encontrado: {DATABASE_PATH}")
        return

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # 1. Verificar se disciplinas ja existem
    cursor.execute("SELECT COUNT(*) FROM disciplina")
    qtd_disciplinas = cursor.fetchone()[0]
    print(f"\n[INFO] Disciplinas existentes: {qtd_disciplinas}")

    # 2. Popular disciplinas se estiver vazia
    if qtd_disciplinas == 0:
        print("\n[ETAPA 1] Inserindo disciplinas padrao...")

        data_agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for codigo, nome, descricao, cor, ordem in DISCIPLINAS_PADRAO:
            cursor.execute("""
                           INSERT INTO disciplina (codigo, nome, descricao, cor, ordem, uuid, data_criacao, ativo)
                           VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                           """, (codigo, nome, descricao, cor, ordem, gerar_uuid(), data_agora))
            print(f"   [OK] {codigo}: {nome}")

        print(f"\n   [OK] {len(DISCIPLINAS_PADRAO)} disciplinas inseridas")
    else:
        print("\n[ETAPA 1] Disciplinas ja existem, pulando...")

    # 3. Buscar UUID da Matematica
    cursor.execute("SELECT uuid FROM disciplina WHERE codigo = 'MAT'")
    resultado = cursor.fetchone()

    if not resultado:
        print("[ERRO] Disciplina MAT nao encontrada!")
        conn.close()
        return

    uuid_matematica = resultado[0]
    print(f"\n[INFO] UUID da Matematica: {uuid_matematica}")

    # 4. Associar tags de conteudo a Matematica
    cursor.execute("""
                   SELECT COUNT(*)
                   FROM tag
                   WHERE uuid_disciplina IS NULL
                     AND numeracao NOT LIKE 'V%'
                     AND numeracao NOT LIKE 'N%'
                   """)
    tags_sem_disciplina = cursor.fetchone()[0]

    print(f"\n[ETAPA 2] Tags sem disciplina: {tags_sem_disciplina}")

    if tags_sem_disciplina > 0:
        cursor.execute("""
                       UPDATE tag
                       SET uuid_disciplina = ?
                       WHERE uuid_disciplina IS NULL
                         AND numeracao NOT LIKE 'V%'
                         AND numeracao NOT LIKE 'N%'
                       """, (uuid_matematica,))

        print(f"   [OK] {cursor.rowcount} tags associadas a Matematica")
    else:
        print("   [INFO] Todas as tags ja tem disciplina")

    # 5. Commit
    conn.commit()
    print("\n[OK] Alteracoes salvas!")

    # 6. Verificacao final
    print("\n" + "=" * 60)
    print(" VERIFICACAO FINAL")
    print("=" * 60)

    cursor.execute("SELECT COUNT(*) FROM disciplina")
    print(f"\n   Disciplinas: {cursor.fetchone()[0]}")

    cursor.execute("SELECT codigo, nome FROM disciplina ORDER BY ordem")
    for codigo, nome in cursor.fetchall():
        print(f"      - {codigo}: {nome}")

    cursor.execute("SELECT COUNT(*) FROM tag WHERE uuid_disciplina IS NOT NULL")
    print(f"\n   Tags com disciplina: {cursor.fetchone()[0]}")

    cursor.execute("SELECT COUNT(*) FROM tag WHERE uuid_disciplina IS NULL")
    sem_disc = cursor.fetchone()[0]
    if sem_disc > 0:
        print(f"   [AVISO] Tags sem disciplina: {sem_disc}")
    else:
        print(f"   Tags sem disciplina: 0")

    conn.close()

    print("\n" + "=" * 60)
    print(" CORRECAO CONCLUIDA!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()