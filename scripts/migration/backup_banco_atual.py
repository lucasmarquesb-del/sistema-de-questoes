#!/usr/bin/env python3
"""
Script para fazer backup do banco de dados atual

Este script:
1. Copia o banco de dados atual para um arquivo de backup
2. Exporta dados em formato JSON para segurança adicional
3. Verifica integridade do backup

Uso:
    python scripts/migration/backup_banco_atual.py
"""

import sys
import os
import shutil
import json
import sqlite3
from datetime import datetime
from pathlib import Path


def fazer_backup_arquivo(caminho_origem: str, diretorio_backup: str = 'backups') -> str:
    """
    Faz cópia do arquivo do banco de dados

    Args:
        caminho_origem: Caminho do banco original
        diretorio_backup: Diretório onde salvar o backup

    Returns:
        Caminho do arquivo de backup
    """
    # Criar diretório de backup se não existir
    os.makedirs(diretorio_backup, exist_ok=True)

    # Gerar nome do backup com timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    nome_arquivo = f"sistema_questoes_backup_{timestamp}.db"
    caminho_backup = os.path.join(diretorio_backup, nome_arquivo)

    print(f"\n📦 Copiando banco de dados...")
    print(f"   Origem: {caminho_origem}")
    print(f"   Destino: {caminho_backup}")

    # Copiar arquivo
    shutil.copy2(caminho_origem, caminho_backup)

    # Verificar tamanho
    tamanho_original = os.path.getsize(caminho_origem)
    tamanho_backup = os.path.getsize(caminho_backup)

    print(f"   Tamanho original: {tamanho_original:,} bytes")
    print(f"   Tamanho backup: {tamanho_backup:,} bytes")

    if tamanho_original != tamanho_backup:
        raise Exception("Tamanhos dos arquivos não conferem!")

    print("   ✓ Arquivo copiado com sucesso")

    return caminho_backup


def exportar_json(caminho_db: str, diretorio_backup: str = 'backups') -> str:
    """
    Exporta dados do banco para JSON

    Args:
        caminho_db: Caminho do banco de dados
        diretorio_backup: Diretório onde salvar o JSON

    Returns:
        Caminho do arquivo JSON
    """
    print(f"\n📄 Exportando dados para JSON...")

    # Conectar ao banco
    conn = sqlite3.connect(caminho_db)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Estrutura para armazenar dados
    dados_export = {
        'metadata': {
            'data_backup': datetime.now().isoformat(),
            'versao_schema': '1.x',
        },
        'tabelas': {}
    }

    # Listar todas as tabelas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tabelas = [row[0] for row in cursor.fetchall()]

    print(f"   Encontradas {len(tabelas)} tabelas")

    # Exportar cada tabela
    for tabela in tabelas:
        print(f"   Exportando {tabela}...")
        cursor.execute(f"SELECT * FROM {tabela}")

        # Obter nomes das colunas
        colunas = [description[0] for description in cursor.description]

        # Obter dados
        registros = []
        for row in cursor.fetchall():
            registro = {}
            for i, coluna in enumerate(colunas):
                valor = row[i]
                # Converter bytes para string se necessário
                if isinstance(valor, bytes):
                    valor = valor.decode('utf-8', errors='ignore')
                registro[coluna] = valor
            registros.append(registro)

        dados_export['tabelas'][tabela] = {
            'colunas': colunas,
            'registros': registros,
            'total': len(registros)
        }

        print(f"      ✓ {len(registros)} registros exportados")

    conn.close()

    # Salvar JSON
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    nome_json = f"sistema_questoes_backup_{timestamp}.json"
    caminho_json = os.path.join(diretorio_backup, nome_json)

    with open(caminho_json, 'w', encoding='utf-8') as f:
        json.dump(dados_export, f, ensure_ascii=False, indent=2)

    tamanho_json = os.path.getsize(caminho_json)
    print(f"   ✓ JSON salvo: {caminho_json}")
    print(f"   Tamanho: {tamanho_json:,} bytes")

    return caminho_json


def verificar_integridade(caminho_backup: str, caminho_original: str):
    """
    Verifica integridade do backup

    Args:
        caminho_backup: Caminho do backup
        caminho_original: Caminho do banco original
    """
    print(f"\n🔍 Verificando integridade do backup...")

    # Conectar aos dois bancos
    conn_original = sqlite3.connect(caminho_original)
    conn_backup = sqlite3.connect(caminho_backup)

    cursor_original = conn_original.cursor()
    cursor_backup = conn_backup.cursor()

    # Listar tabelas
    cursor_original.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tabelas_original = set(row[0] for row in cursor_original.fetchall())

    cursor_backup.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tabelas_backup = set(row[0] for row in cursor_backup.fetchall())

    # Verificar se tem as mesmas tabelas
    if tabelas_original != tabelas_backup:
        raise Exception("Tabelas diferentes entre original e backup!")

    print(f"   ✓ Todas as {len(tabelas_original)} tabelas estão presentes")

    # Verificar contagem de registros em cada tabela
    total_original = 0
    total_backup = 0

    for tabela in tabelas_original:
        cursor_original.execute(f"SELECT COUNT(*) FROM {tabela}")
        count_original = cursor_original.fetchone()[0]

        cursor_backup.execute(f"SELECT COUNT(*) FROM {tabela}")
        count_backup = cursor_backup.fetchone()[0]

        if count_original != count_backup:
            raise Exception(f"Contagem diferente na tabela {tabela}: {count_original} vs {count_backup}")

        total_original += count_original
        total_backup += count_backup

        print(f"   ✓ {tabela}: {count_original} registros")

    conn_original.close()
    conn_backup.close()

    print(f"\n   ✅ Total de registros: {total_original}")
    print(f"   ✅ Backup verificado com sucesso!")


def main():
    """Função principal"""
    print("\n" + "="*80)
    print("BACKUP DO BANCO DE DADOS ATUAL")
    print("Versão 1.x → Preparação para migração")
    print("="*80)

    try:
        # Perguntar caminho do banco atual
        caminho_default = 'data/sistema_questoes.db'
        print(f"\n📂 Caminho do banco atual: {caminho_default}")

        if not os.path.exists(caminho_default):
            print(f"\n❌ Banco de dados não encontrado: {caminho_default}")
            caminho_db = input("Digite o caminho correto: ").strip()
            if not os.path.exists(caminho_db):
                print(f"\n❌ Arquivo não encontrado: {caminho_db}")
                sys.exit(1)
        else:
            resposta = input("Deseja usar este caminho? (S/n): ").strip().lower()
            if resposta and resposta != 's':
                caminho_db = input("Digite o caminho desejado: ").strip()
            else:
                caminho_db = caminho_default

        # Verificar se banco existe e não está vazio
        tamanho = os.path.getsize(caminho_db)
        if tamanho == 0:
            print(f"\n❌ O banco de dados está vazio!")
            sys.exit(1)

        print(f"\n📊 Tamanho do banco: {tamanho:,} bytes")

        # Confirmar operação
        print(f"\n⚠️  Esta operação irá:")
        print(f"   1. Copiar o banco de dados para a pasta 'backups'")
        print(f"   2. Exportar dados para JSON")
        print(f"   3. Verificar integridade do backup")
        resposta = input("\nDeseja continuar? (S/n): ").strip().lower()

        if resposta and resposta != 's':
            print("\n❌ Operação cancelada pelo usuário.")
            return

        # Executar backup
        caminho_backup = fazer_backup_arquivo(caminho_db)
        caminho_json = exportar_json(caminho_db)
        verificar_integridade(caminho_backup, caminho_db)

        print("\n" + "="*80)
        print("✅ BACKUP CONCLUÍDO COM SUCESSO!")
        print("="*80)
        print(f"\n📁 Arquivos de backup:")
        print(f"   • Banco de dados: {os.path.abspath(caminho_backup)}")
        print(f"   • JSON: {os.path.abspath(caminho_json)}")
        print("\n📋 Próximos passos:")
        print("   1. Verifique os arquivos de backup")
        print("   2. Execute o script de criação do novo schema")
        print("   3. Execute o script de migração de dados")

    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
