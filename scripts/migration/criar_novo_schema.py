#!/usr/bin/env python3
"""
Script para criar o novo schema do banco de dados com UUID e ORM

Este script:
1. Cria todas as tabelas do novo schema
2. Popula dados iniciais (dificuldades, tipos de questão)
3. Não toca no banco antigo

Uso:
    python scripts/migration/criar_novo_schema.py
"""

import sys
import os
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.orm import (
    Base,
    TipoQuestao,
    FonteQuestao,
    Dificuldade,
    CodigoGenerator
)


def criar_engine_novo_banco(caminho_db: str = 'data/sistema_questoes_v2.db'):
    """
    Cria engine para o novo banco de dados

    Args:
        caminho_db: Caminho para o arquivo do banco novo

    Returns:
        Engine do SQLAlchemy
    """
    # Garantir que o diretório data existe
    os.makedirs(os.path.dirname(caminho_db), exist_ok=True)

    # Criar engine
    engine = create_engine(f'sqlite:///{caminho_db}', echo=True)
    return engine


def criar_todas_tabelas(engine):
    """
    Cria todas as tabelas do novo schema

    Args:
        engine: Engine do SQLAlchemy
    """
    print("\n" + "="*80)
    print("CRIANDO TABELAS DO NOVO SCHEMA")
    print("="*80 + "\n")

    Base.metadata.create_all(engine)

    print("\n✅ Todas as tabelas foram criadas com sucesso!")


def popular_dados_iniciais(session):
    """
    Popula dados iniciais no banco

    Args:
        session: Sessão do SQLAlchemy
    """
    print("\n" + "="*80)
    print("POPULANDO DADOS INICIAIS")
    print("="*80 + "\n")

    # 1. Criar tipos de questão
    print("📝 Criando tipos de questão...")
    tipos = [
        TipoQuestao(codigo='OBJETIVA', nome='Questão Objetiva'),
        TipoQuestao(codigo='DISCURSIVA', nome='Questão Discursiva'),
    ]

    for tipo in tipos:
        existing = session.query(TipoQuestao).filter_by(codigo=tipo.codigo).first()
        if not existing:
            session.add(tipo)
            print(f"   ✓ {tipo.codigo}: {tipo.nome}")
        else:
            print(f"   - {tipo.codigo} já existe")

    session.commit()

    # 2. Criar dificuldades
    print("\n📊 Criando dificuldades...")
    dificuldades = [
        Dificuldade(codigo='FACIL'),
        Dificuldade(codigo='MEDIO'),
        Dificuldade(codigo='DIFICIL'),
    ]

    for dif in dificuldades:
        existing = session.query(Dificuldade).filter_by(codigo=dif.codigo).first()
        if not existing:
            session.add(dif)
            print(f"   ✓ {dif.codigo}")
        else:
            print(f"   - {dif.codigo} já existe")

    session.commit()

    # 3. Criar algumas fontes comuns
    print("\n🏫 Criando fontes de questões...")
    fontes = [
        FonteQuestao(
            sigla='AUTORAL',
            nome_completo='Questão Autoral',
            tipo_instituicao='AUTORAL'
        ),
        FonteQuestao(
            sigla='ENEM',
            nome_completo='Exame Nacional do Ensino Médio',
            tipo_instituicao='VESTIBULAR'
        ),
        FonteQuestao(
            sigla='FUVEST',
            nome_completo='Fundação Universitária para o Vestibular',
            tipo_instituicao='VESTIBULAR'
        ),
    ]

    for fonte in fontes:
        existing = session.query(FonteQuestao).filter_by(sigla=fonte.sigla).first()
        if not existing:
            session.add(fonte)
            print(f"   ✓ {fonte.sigla}: {fonte.nome_completo}")
        else:
            print(f"   - {fonte.sigla} já existe")

    session.commit()

    print("\n✅ Dados iniciais populados com sucesso!")


def verificar_schema(session):
    """
    Verifica se o schema foi criado corretamente

    Args:
        session: Sessão do SQLAlchemy
    """
    print("\n" + "="*80)
    print("VERIFICANDO SCHEMA")
    print("="*80 + "\n")

    # Contar registros
    contagens = {
        'TipoQuestao': session.query(TipoQuestao).count(),
        'Dificuldade': session.query(Dificuldade).count(),
        'FonteQuestao': session.query(FonteQuestao).count(),
    }

    print("📊 Contagem de registros:")
    for tabela, count in contagens.items():
        print(f"   {tabela}: {count} registro(s)")

    print("\n✅ Schema verificado!")


def main():
    """Função principal"""
    print("\n" + "="*80)
    print("CRIAÇÃO DO NOVO SCHEMA - UUID + ORM + NORMALIZAÇÃO")
    print("Versão 2.0.0")
    print("="*80)

    try:
        # Perguntar caminho do novo banco
        caminho_default = 'data/sistema_questoes_v2.db'
        print(f"\n📂 Caminho do novo banco: {caminho_default}")
        resposta = input("Deseja usar este caminho? (S/n): ").strip().lower()

        if resposta and resposta != 's':
            caminho_db = input("Digite o caminho desejado: ").strip()
        else:
            caminho_db = caminho_default

        # Verificar se arquivo já existe
        if os.path.exists(caminho_db):
            print(f"\n⚠️  ATENÇÃO: O arquivo {caminho_db} já existe!")
            resposta = input("Deseja sobrescrevê-lo? (s/N): ").strip().lower()
            if resposta != 's':
                print("\n❌ Operação cancelada pelo usuário.")
                return
            os.remove(caminho_db)
            print(f"   ✓ Arquivo antigo removido")

        # Criar engine e session
        engine = criar_engine_novo_banco(caminho_db)
        Session = sessionmaker(bind=engine)
        session = Session()

        # Executar etapas
        criar_todas_tabelas(engine)
        popular_dados_iniciais(session)
        verificar_schema(session)

        # Finalizar
        session.close()

        print("\n" + "="*80)
        print("✅ SCHEMA CRIADO COM SUCESSO!")
        print("="*80)
        print(f"\n📁 Banco de dados: {os.path.abspath(caminho_db)}")
        print("\n📋 Próximos passos:")
        print("   1. Execute o script de backup do banco atual")
        print("   2. Execute o script de migração de dados")
        print("   3. Valide a integridade dos dados migrados")

    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
