# -*- coding: utf-8 -*-
"""
Script para verificar a estrutura atual do banco de dados.
Execute ANTES de iniciar a migracao.

Versao compativel com Windows (sem emojis).
Versao robusta que detecta nomes de colunas automaticamente.
"""

import sqlite3
from pathlib import Path

DATABASE_PATH = "database/sistema_questoes_v2.db"


def get_colunas_tabela(cursor, tabela):
    """Retorna lista de nomes de colunas de uma tabela."""
    cursor.execute(f"PRAGMA table_info([{tabela}])")
    return [col[1] for col in cursor.fetchall()]


def get_coluna_id(cursor, tabela):
    """Tenta descobrir qual e a coluna de ID da tabela."""
    colunas = get_colunas_tabela(cursor, tabela)

    # Tenta encontrar a coluna de ID em ordem de prioridade
    possiveis = [
        f"id_{tabela}",  # id_tag, id_questao
        "id",  # id
        f"{tabela}_id",  # tag_id, questao_id
        "codigo",  # codigo
    ]

    for possivel in possiveis:
        if possivel in colunas:
            return possivel

    # Se nao encontrar, retorna a primeira coluna (geralmente e o ID)
    return colunas[0] if colunas else None


def main():
    if not Path(DATABASE_PATH).exists():
        print(f"[ERRO] Banco nao encontrado: {DATABASE_PATH}")
        print(f"       Caminho procurado: {Path(DATABASE_PATH).absolute()}")
        return

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    print("=" * 70)
    print(" VERIFICACAO DA ESTRUTURA DO BANCO DE DADOS")
    print("=" * 70)

    # 1. Listar tabelas
    print("\n[1] TABELAS EXISTENTES:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tabelas = [t[0] for t in cursor.fetchall()]
    for tabela in tabelas:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM [{tabela}]")
            qtd = cursor.fetchone()[0]
            print(f"    - {tabela}: {qtd} registros")
        except Exception as e:
            print(f"    - {tabela}: (erro ao contar: {e})")

    # 2. Verificar se tabela disciplina existe
    print("\n[2] TABELA 'disciplina':")
    if 'disciplina' in tabelas:
        print("    [OK] Ja existe")
        cursor.execute("SELECT * FROM disciplina LIMIT 5")
        for row in cursor.fetchall():
            print(f"         {row}")
    else:
        print("    [AVISO] NAO existe (sera criada na migracao)")

    # 3. Verificar estrutura da tabela tag
    print("\n[3] ESTRUTURA DA TABELA 'tag':")
    if 'tag' in tabelas:
        colunas_tag = get_colunas_tabela(cursor, 'tag')
        print(f"    Colunas encontradas: {colunas_tag}")

        for col in colunas_tag:
            print(f"    - {col}")

        # Verificar se tem coluna id_disciplina
        if 'id_disciplina' in colunas_tag:
            print("    [OK] Coluna id_disciplina existe")
        else:
            print("    [AVISO] Coluna id_disciplina NAO existe (sera criada)")

        # Descobrir coluna de ID
        col_id = get_coluna_id(cursor, 'tag')
        print(f"    Coluna de ID detectada: {col_id}")

        # Descobrir coluna de numeracao/codigo
        col_num = None
        for possivel in ['numeracao', 'codigo', 'code', 'numero']:
            if possivel in colunas_tag:
                col_num = possivel
                break

        # Descobrir coluna de nome
        col_nome = None
        for possivel in ['nome', 'name', 'titulo', 'descricao']:
            if possivel in colunas_tag:
                col_nome = possivel
                break

        print(f"    Coluna de numeracao detectada: {col_num}")
        print(f"    Coluna de nome detectada: {col_nome}")

    else:
        print("    [AVISO] Tabela 'tag' nao encontrada")
        colunas_tag = []
        col_id = None
        col_num = None
        col_nome = None

    # 4. Contar tags por tipo
    print("\n[4] TAGS POR TIPO:")
    qtd_vestibular = 0
    qtd_nivel = 0

    if 'tag' in tabelas and col_num:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM tag WHERE [{col_num}] NOT LIKE 'V%' AND [{col_num}] NOT LIKE 'N%'")
            qtd_conteudo = cursor.fetchone()[0]
            print(f"    - Tags de Conteudo: {qtd_conteudo}")

            cursor.execute(f"SELECT COUNT(*) FROM tag WHERE [{col_num}] LIKE 'V%'")
            qtd_vestibular = cursor.fetchone()[0]
            print(f"    - Tags de Vestibular (V*): {qtd_vestibular}")

            cursor.execute(f"SELECT COUNT(*) FROM tag WHERE [{col_num}] LIKE 'N%'")
            qtd_nivel = cursor.fetchone()[0]
            print(f"    - Tags de Nivel (N*): {qtd_nivel}")
        except Exception as e:
            print(f"    [ERRO] {e}")
    else:
        print("    [AVISO] Nao foi possivel analisar tags (tabela ou coluna nao encontrada)")

    # 5. Listar tags V*
    print("\n[5] TAGS DE VESTIBULAR (V*):")
    if qtd_vestibular > 0 and col_id and col_num and col_nome:
        try:
            cursor.execute(
                f"SELECT [{col_id}], [{col_num}], [{col_nome}] FROM tag WHERE [{col_num}] LIKE 'V%' ORDER BY [{col_num}]")
            for row in cursor.fetchall():
                print(f"    - {row[1]}: {row[2]}")
        except Exception as e:
            print(f"    [ERRO] {e}")
    elif qtd_vestibular > 0:
        print("    [AVISO] Encontradas mas nao foi possivel listar (colunas nao detectadas)")
    else:
        print("    Nenhuma encontrada")

    # 6. Listar tags N*
    print("\n[6] TAGS DE NIVEL (N*):")
    if qtd_nivel > 0 and col_id and col_num and col_nome:
        try:
            cursor.execute(
                f"SELECT [{col_id}], [{col_num}], [{col_nome}] FROM tag WHERE [{col_num}] LIKE 'N%' ORDER BY [{col_num}]")
            for row in cursor.fetchall():
                print(f"    - {row[1]}: {row[2]}")
        except Exception as e:
            print(f"    [ERRO] {e}")
    elif qtd_nivel > 0:
        print("    [AVISO] Encontradas mas nao foi possivel listar (colunas nao detectadas)")
    else:
        print("    Nenhuma encontrada")

    # 7. Verificar tabela fonte_questao
    print("\n[7] TABELA 'fonte_questao':")
    if 'fonte_questao' in tabelas:
        print("    [OK] Existe")
        colunas = get_colunas_tabela(cursor, 'fonte_questao')
        for col in colunas:
            print(f"         - {col}")

        cursor.execute("SELECT COUNT(*) FROM fonte_questao")
        qtd = cursor.fetchone()[0]
        print(f"    Registros: {qtd}")
    else:
        print("    [AVISO] NAO existe (sera criada na migracao)")

    # 8. Verificar tabela nivel_escolar
    print("\n[8] TABELA 'nivel_escolar':")
    if 'nivel_escolar' in tabelas:
        print("    [OK] Existe")
        cursor.execute("SELECT COUNT(*) FROM nivel_escolar")
        qtd = cursor.fetchone()[0]
        print(f"    Registros: {qtd}")
    else:
        print("    [AVISO] NAO existe (sera criada na migracao)")

    # 9. Verificar tabela questao_nivel
    print("\n[9] TABELA 'questao_nivel':")
    if 'questao_nivel' in tabelas:
        print("    [OK] Existe")
        cursor.execute("SELECT COUNT(*) FROM questao_nivel")
        qtd = cursor.fetchone()[0]
        print(f"    Registros: {qtd}")
    else:
        print("    [AVISO] NAO existe (sera criada na migracao)")

    # 10. Verificar tabela questao
    print("\n[10] TABELA 'questao':")
    if 'questao' in tabelas:
        print("    [OK] Existe")
        colunas_questao = get_colunas_tabela(cursor, 'questao')
        print(f"    Colunas: {colunas_questao}")

        if 'id_fonte' in colunas_questao:
            print("    [OK] Coluna id_fonte existe")
        else:
            print("    [AVISO] Coluna id_fonte NAO existe")

        cursor.execute("SELECT COUNT(*) FROM questao")
        qtd = cursor.fetchone()[0]
        print(f"    Total de questoes: {qtd}")
    else:
        print("    [AVISO] Tabela 'questao' nao encontrada")

    # 11. Mostrar algumas amostras de dados
    print("\n[11] AMOSTRA DE DADOS DA TABELA 'tag':")
    if 'tag' in tabelas:
        try:
            cursor.execute("SELECT * FROM tag LIMIT 5")
            rows = cursor.fetchall()
            if rows:
                for row in rows:
                    print(f"    {row}")
            else:
                print("    (tabela vazia)")
        except Exception as e:
            print(f"    [ERRO] {e}")

    print("\n" + "=" * 70)
    print(" VERIFICACAO CONCLUIDA")
    print("=" * 70)
    print("\n[IMPORTANTE] Anote os nomes das colunas da tabela 'tag' mostrados acima.")
    print("             O script de migracao precisara ser ajustado conforme sua estrutura.")
    print("\n[DICA] Para salvar esta saida:")
    print("       python scripts/verificar_estrutura.py > estrutura_antes.txt\n")

    conn.close()


if __name__ == "__main__":
    main()