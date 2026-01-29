# PLANO DE IMPLEMENTAÇÃO DETALHADO (ATUALIZADO)
# Refatoração do Banco de Dados - Disciplinas, Níveis e Fontes

---

## SOBRE ESTE DOCUMENTO

Este guia detalha como refatorar o banco de dados para:
1. **Criar tabela de Disciplinas** (Matemática, Física, Português, etc.)
2. **Associar conteúdos (tags) a disciplinas** - Cada disciplina tem seus próprios conteúdos
3. **Separar níveis escolares** em tabela própria
4. **Separar fontes/vestibulares** em tabela própria

**Tempo estimado:** 2-3 dias de trabalho
**Nível:** Intermediário

---

## ÍNDICE

1. [Entendendo o Problema e a Nova Estrutura](#1-entendendo-o-problema-e-a-nova-estrutura)
2. [Preparação e Backup](#2-preparação-e-backup)
3. [Fase 1: Criar Script de Migração](#3-fase-1-criar-script-de-migração)
4. [Fase 2: Criar Model Disciplina](#4-fase-2-criar-model-disciplina)
5. [Fase 3: Atualizar Model Tag (Conteúdo)](#5-fase-3-atualizar-model-tag-conteúdo)
6. [Fase 4: Criar Model NivelEscolar](#6-fase-4-criar-model-nivelescolar)
7. [Fase 5: Expandir Model FonteQuestao](#7-fase-5-expandir-model-fontequestao)
8. [Fase 6: Criar Repositories](#8-fase-6-criar-repositories)
9. [Fase 7: Executar Migração](#9-fase-7-executar-migração)
10. [Fase 8: Atualizar as Views](#10-fase-8-atualizar-as-views)
11. [Testes e Validação](#11-testes-e-validação)
12. [Checklist Final](#12-checklist-final)

---

## 1. ENTENDENDO O PROBLEMA E A NOVA ESTRUTURA

### 1.1 Situação Atual

```
TABELA: tag (MISTURA TUDO!)
┌────────────────────────────────────────────────────────────┐
│ id │ numeracao │ nome                │ problema           │
├────────────────────────────────────────────────────────────┤
│ 1  │ 1         │ Números             │ conteúdo (sem disciplina!)
│ 2  │ 1.1       │ Números Naturais    │ conteúdo (sem disciplina!)
│ 3  │ 2         │ Álgebra             │ conteúdo (sem disciplina!)
│ 50 │ V1        │ ENEM                │ vestibular (errado!)
│ 51 │ V2        │ FUVEST              │ vestibular (errado!)
│ 60 │ N1        │ Ensino Fundamental  │ nível (errado!)
│ 61 │ N2        │ Ensino Médio        │ nível (errado!)
└────────────────────────────────────────────────────────────┘
```

### 1.2 Nova Estrutura Proposta

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           NOVA ESTRUTURA                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         DISCIPLINA                                   │    │
│  │  ┌──────────────────────────────────────────────────────────────┐   │    │
│  │  │ id │ codigo │ nome        │ descricao                        │   │    │
│  │  ├──────────────────────────────────────────────────────────────┤   │    │
│  │  │ 1  │ MAT    │ Matemática  │ Matemática e Raciocínio Lógico  │   │    │
│  │  │ 2  │ FIS    │ Física      │ Física Geral                     │   │    │
│  │  │ 3  │ QUI    │ Química     │ Química Geral                    │   │    │
│  │  │ 4  │ BIO    │ Biologia    │ Biologia Geral                   │   │    │
│  │  │ 5  │ POR    │ Português   │ Língua Portuguesa                │   │    │
│  │  │ 6  │ HIS    │ História    │ História Geral e do Brasil       │   │    │
│  │  │ 7  │ GEO    │ Geografia   │ Geografia Geral e do Brasil      │   │    │
│  │  └──────────────────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    │ 1:N (uma disciplina tem muitos          │
│                                    │      conteúdos)                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    TAG / CONTEÚDO (por disciplina)                   │    │
│  │  ┌──────────────────────────────────────────────────────────────┐   │    │
│  │  │ id │ id_disciplina │ numeracao │ nome                       │   │    │
│  │  ├──────────────────────────────────────────────────────────────┤   │    │
│  │  │ 1  │ 1 (MAT)       │ 1         │ Números                    │   │    │
│  │  │ 2  │ 1 (MAT)       │ 1.1       │ Números Naturais           │   │    │
│  │  │ 3  │ 1 (MAT)       │ 2         │ Álgebra                    │   │    │
│  │  │ 4  │ 1 (MAT)       │ 2.1       │ Equações do 1º Grau        │   │    │
│  │  │ 5  │ 2 (FIS)       │ 1         │ Mecânica                   │   │    │
│  │  │ 6  │ 2 (FIS)       │ 1.1       │ Cinemática                 │   │    │
│  │  │ 7  │ 2 (FIS)       │ 2         │ Termodinâmica              │   │    │
│  │  └──────────────────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         NIVEL_ESCOLAR                                │    │
│  │  ┌──────────────────────────────────────────────────────────────┐   │    │
│  │  │ id │ codigo │ nome                       │ ordem              │   │    │
│  │  ├──────────────────────────────────────────────────────────────┤   │    │
│  │  │ 1  │ EF1    │ Ensino Fundamental I       │ 1                  │   │    │
│  │  │ 2  │ EF2    │ Ensino Fundamental II      │ 2                  │   │    │
│  │  │ 3  │ EM     │ Ensino Médio               │ 3                  │   │    │
│  │  │ 4  │ EJA    │ Educação Jovens e Adultos  │ 4                  │   │    │
│  │  │ 5  │ TEC    │ Ensino Técnico             │ 5                  │   │    │
│  │  │ 6  │ SUP    │ Ensino Superior            │ 6                  │   │    │
│  │  └──────────────────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         FONTE_QUESTAO                                │    │
│  │  ┌──────────────────────────────────────────────────────────────┐   │    │
│  │  │ id │ sigla  │ nome_completo    │ tipo         │ estado       │   │    │
│  │  ├──────────────────────────────────────────────────────────────┤   │    │
│  │  │ 1  │ ENEM   │ Exame Nacional.. │ VESTIBULAR   │ NULL         │   │    │
│  │  │ 2  │ FUVEST │ Fund. Univ. Vest │ VESTIBULAR   │ SP           │   │    │
│  │  │ 3  │ UNICAMP│ Univ. Est. Camp. │ VESTIBULAR   │ SP           │   │    │
│  │  │ 4  │ OBMEP  │ Olimp. Bras. Mat │ OLIMPIADA    │ NULL         │   │    │
│  │  └──────────────────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Diagrama de Relacionamentos

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RELACIONAMENTOS                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│    ┌────────────┐                                                           │
│    │ disciplina │                                                           │
│    └─────┬──────┘                                                           │
│          │                                                                   │
│          │ 1:N                                                              │
│          ▼                                                                   │
│    ┌────────────┐         ┌─────────────┐         ┌─────────────┐          │
│    │    tag     │◄───N:N──│ questao_tag │───N:N──►│   questao   │          │
│    │ (conteúdo) │         └─────────────┘         └──────┬──────┘          │
│    └────────────┘                                        │                  │
│                                                          │                  │
│                           ┌──────────────┐               │                  │
│    ┌──────────────┐       │              │               │                  │
│    │nivel_escolar │◄──N:N─┤questao_nivel ├───N:N─────────┤                  │
│    └──────────────┘       │              │               │                  │
│                           └──────────────┘               │                  │
│                                                          │                  │
│    ┌──────────────┐                                      │                  │
│    │ fonte_questao│◄─────────────N:1─────────────────────┘                  │
│    └──────────────┘                                                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

LEGENDA:
  1:N = Um para Muitos (uma disciplina tem muitos conteúdos)
  N:N = Muitos para Muitos (uma questão pode ter várias tags e vice-versa)
  N:1 = Muitos para Um (várias questões podem ter a mesma fonte)
```

### 1.4 Benefícios da Nova Estrutura

| Aspecto | Antes | Depois |
|---------|-------|--------|
| **Disciplinas** | Não existia | Tabela própria, expansível |
| **Conteúdos** | Misturados com vestibulares e níveis | Organizados por disciplina |
| **Vestibulares** | Tags V1, V2, V3... | Tabela fonte_questao com metadados |
| **Níveis** | Tags N1, N2, N3... | Tabela nivel_escolar |
| **Filtros** | Complexos e confusos | Simples e diretos |
| **Escalabilidade** | Difícil adicionar disciplinas | Fácil adicionar disciplinas |

---

## 2. PREPARAÇÃO E BACKUP

### 2.1 IMPORTANTE: Faça Backup!

```bash
# Navegue até a pasta do banco de dados
cd seu-projeto/database

# Copie o arquivo do banco
cp mathbank.db mathbank_backup_$(date +%Y%m%d_%H%M%S).db

# No Windows (PowerShell):
# Copy-Item mathbank.db -Destination "mathbank_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').db"
```

### 2.2 Script para Verificar Estrutura Atual

**Caminho:** `scripts/verificar_estrutura.py`

```python
"""
Script para verificar a estrutura atual do banco de dados.
Execute ANTES de iniciar a migração.
"""

import sqlite3
from pathlib import Path

DATABASE_PATH = "database/mathbank.db"


def main():
    if not Path(DATABASE_PATH).exists():
        print(f"❌ Banco não encontrado: {DATABASE_PATH}")
        return
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    print("=" * 70)
    print(" VERIFICAÇÃO DA ESTRUTURA DO BANCO DE DADOS")
    print("=" * 70)
    
    # 1. Listar tabelas
    print("\n📋 TABELAS EXISTENTES:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tabelas = [t[0] for t in cursor.fetchall()]
    for tabela in tabelas:
        cursor.execute(f"SELECT COUNT(*) FROM {tabela}")
        qtd = cursor.fetchone()[0]
        print(f"   • {tabela}: {qtd} registros")
    
    # 2. Verificar se tabela disciplina existe
    print("\n📋 TABELA 'disciplina':")
    if 'disciplina' in tabelas:
        print("   ✅ Já existe")
        cursor.execute("SELECT * FROM disciplina")
        for row in cursor.fetchall():
            print(f"      {row}")
    else:
        print("   ⚠️  NÃO existe (será criada)")
    
    # 3. Verificar estrutura da tabela tag
    print("\n📋 ESTRUTURA DA TABELA 'tag':")
    cursor.execute("PRAGMA table_info(tag)")
    colunas = cursor.fetchall()
    for col in colunas:
        print(f"   • {col[1]} ({col[2]})")
    
    # Verificar se tem coluna id_disciplina
    nomes_colunas = [col[1] for col in colunas]
    if 'id_disciplina' in nomes_colunas:
        print("   ✅ Coluna id_disciplina existe")
    else:
        print("   ⚠️  Coluna id_disciplina NÃO existe (será criada)")
    
    # 4. Contar tags por tipo
    print("\n📋 TAGS POR TIPO:")
    
    cursor.execute("SELECT COUNT(*) FROM tag WHERE numeracao NOT LIKE 'V%' AND numeracao NOT LIKE 'N%'")
    qtd_conteudo = cursor.fetchone()[0]
    print(f"   • Tags de Conteúdo: {qtd_conteudo}")
    
    cursor.execute("SELECT COUNT(*) FROM tag WHERE numeracao LIKE 'V%'")
    qtd_vestibular = cursor.fetchone()[0]
    print(f"   • Tags de Vestibular (V*): {qtd_vestibular}")
    
    cursor.execute("SELECT COUNT(*) FROM tag WHERE numeracao LIKE 'N%'")
    qtd_nivel = cursor.fetchone()[0]
    print(f"   • Tags de Nível (N*): {qtd_nivel}")
    
    # 5. Listar tags V*
    if qtd_vestibular > 0:
        print("\n📋 TAGS DE VESTIBULAR (V*):")
        cursor.execute("SELECT id_tag, numeracao, nome FROM tag WHERE numeracao LIKE 'V%' ORDER BY numeracao")
        for row in cursor.fetchall():
            print(f"   • {row[1]}: {row[2]}")
    
    # 6. Listar tags N*
    if qtd_nivel > 0:
        print("\n📋 TAGS DE NÍVEL (N*):")
        cursor.execute("SELECT id_tag, numeracao, nome FROM tag WHERE numeracao LIKE 'N%' ORDER BY numeracao")
        for row in cursor.fetchall():
            print(f"   • {row[1]}: {row[2]}")
    
    # 7. Verificar tabela fonte_questao
    print("\n📋 TABELA 'fonte_questao':")
    if 'fonte_questao' in tabelas:
        print("   ✅ Existe")
        cursor.execute("PRAGMA table_info(fonte_questao)")
        for col in cursor.fetchall():
            print(f"      • {col[1]} ({col[2]})")
    else:
        print("   ⚠️  NÃO existe (será criada)")
    
    print("\n" + "=" * 70)
    print(" VERIFICAÇÃO CONCLUÍDA")
    print("=" * 70)
    print("\n💾 Guarde esta saída para comparar após a migração!\n")
    
    conn.close()


if __name__ == "__main__":
    main()
```

Execute:
```bash
python scripts/verificar_estrutura.py > estrutura_antes.txt
```

---

## 3. FASE 1: CRIAR SCRIPT DE MIGRAÇÃO

### 3.1 Criar Pasta de Migrações

```bash
mkdir -p database/migrations
mkdir -p scripts
```

### 3.2 Script Python de Migração Completo

**Caminho:** `scripts/migrar_banco.py`

```python
"""
Script de Migração do Banco de Dados
====================================

Este script executa a migração completa:
1. Cria tabela disciplina
2. Adiciona coluna id_disciplina na tabela tag
3. Cria tabela nivel_escolar
4. Cria tabela questao_nivel
5. Expande tabela fonte_questao
6. Migra tags V* para fonte_questao
7. Migra tags N* para nivel_escolar/questao_nivel
8. Remove tags V* e N*

USO:
    python scripts/migrar_banco.py --dry-run    # Apenas mostra o que faria
    python scripts/migrar_banco.py              # Executa a migração
    python scripts/migrar_banco.py --no-backup  # Sem backup (não recomendado)
"""

import sqlite3
import shutil
import argparse
from datetime import datetime
from pathlib import Path

# ============================================================
# CONFIGURAÇÃO
# ============================================================

DATABASE_PATH = "database/mathbank.db"
BACKUP_DIR = "database/backups"

# Disciplinas padrão
DISCIPLINAS_PADRAO = [
    ("MAT", "Matemática", "Matemática e Raciocínio Lógico", "#3498db", 1),
    ("FIS", "Física", "Física Geral e Aplicada", "#e74c3c", 2),
    ("QUI", "Química", "Química Geral, Orgânica e Inorgânica", "#9b59b6", 3),
    ("BIO", "Biologia", "Biologia Geral, Ecologia e Genética", "#27ae60", 4),
    ("POR", "Português", "Língua Portuguesa e Literatura", "#f39c12", 5),
    ("RED", "Redação", "Produção Textual", "#e67e22", 6),
    ("HIS", "História", "História Geral e do Brasil", "#1abc9c", 7),
    ("GEO", "Geografia", "Geografia Geral e do Brasil", "#16a085", 8),
    ("FIL", "Filosofia", "Filosofia Geral", "#8e44ad", 9),
    ("SOC", "Sociologia", "Sociologia Geral", "#2c3e50", 10),
    ("ING", "Inglês", "Língua Inglesa", "#c0392b", 11),
    ("ESP", "Espanhol", "Língua Espanhola", "#d35400", 12),
]

# Níveis escolares padrão
NIVEIS_PADRAO = [
    ("EF1", "Ensino Fundamental I", "1º ao 5º ano", 1),
    ("EF2", "Ensino Fundamental II", "6º ao 9º ano", 2),
    ("EM", "Ensino Médio", "1ª a 3ª série", 3),
    ("PRE", "Pré-Vestibular", "Cursinho preparatório", 4),
    ("EJA", "Educação de Jovens e Adultos", "EJA Fundamental e Médio", 5),
    ("TEC", "Ensino Técnico", "Cursos técnicos", 6),
    ("SUP", "Ensino Superior", "Graduação", 7),
    ("POS", "Pós-Graduação", "Especialização, Mestrado, Doutorado", 8),
]

# Mapeamento de tags N* para níveis
MAPEAMENTO_NIVEIS = {
    'fundamental i': 'EF1',
    'fundamental 1': 'EF1',
    'fundamental ii': 'EF2',
    'fundamental 2': 'EF2',
    'médio': 'EM',
    'medio': 'EM',
    'pré-vestibular': 'PRE',
    'pre-vestibular': 'PRE',
    'cursinho': 'PRE',
    'eja': 'EJA',
    'jovens e adultos': 'EJA',
    'técnico': 'TEC',
    'tecnico': 'TEC',
    'superior': 'SUP',
    'graduação': 'SUP',
    'graduacao': 'SUP',
    'pós': 'POS',
    'pos': 'POS',
}


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def print_header(texto):
    print("\n" + "=" * 60)
    print(f" {texto}")
    print("=" * 60)


def print_ok(texto):
    print(f"   ✅ {texto}")


def print_erro(texto):
    print(f"   ❌ {texto}")


def print_aviso(texto):
    print(f"   ⚠️  {texto}")


def print_info(texto):
    print(f"   ℹ️  {texto}")


def criar_backup(db_path: str) -> str:
    """Cria backup do banco de dados."""
    backup_dir = Path(BACKUP_DIR)
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"backup_pre_migracao_{timestamp}.db"
    
    shutil.copy2(db_path, backup_path)
    print_ok(f"Backup criado: {backup_path}")
    
    return str(backup_path)


def coluna_existe(cursor, tabela: str, coluna: str) -> bool:
    """Verifica se uma coluna existe em uma tabela."""
    cursor.execute(f"PRAGMA table_info({tabela})")
    colunas = [col[1] for col in cursor.fetchall()]
    return coluna in colunas


def tabela_existe(cursor, tabela: str) -> bool:
    """Verifica se uma tabela existe."""
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name=?
    """, (tabela,))
    return cursor.fetchone() is not None


# ============================================================
# FUNÇÕES DE MIGRAÇÃO
# ============================================================

def criar_tabela_disciplina(cursor, dry_run: bool = False):
    """Cria a tabela disciplina."""
    print_header("ETAPA 1: Criar tabela DISCIPLINA")
    
    if tabela_existe(cursor, 'disciplina'):
        print_aviso("Tabela disciplina já existe")
        return
    
    if dry_run:
        print_info("Criaria tabela disciplina com as colunas:")
        print_info("  id_disciplina, codigo, nome, descricao, cor, ordem, ativo")
        print_info(f"Inseriria {len(DISCIPLINAS_PADRAO)} disciplinas padrão")
        return
    
    cursor.execute("""
        CREATE TABLE disciplina (
            id_disciplina INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo VARCHAR(10) NOT NULL UNIQUE,
            nome VARCHAR(100) NOT NULL,
            descricao TEXT,
            cor VARCHAR(7) DEFAULT '#3498db',
            ordem INTEGER NOT NULL DEFAULT 0,
            ativo BOOLEAN NOT NULL DEFAULT 1,
            data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
            data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print_ok("Tabela disciplina criada")
    
    # Inserir disciplinas padrão
    for codigo, nome, descricao, cor, ordem in DISCIPLINAS_PADRAO:
        cursor.execute("""
            INSERT INTO disciplina (codigo, nome, descricao, cor, ordem)
            VALUES (?, ?, ?, ?, ?)
        """, (codigo, nome, descricao, cor, ordem))
    
    print_ok(f"{len(DISCIPLINAS_PADRAO)} disciplinas padrão inseridas")
    
    # Listar
    cursor.execute("SELECT codigo, nome FROM disciplina ORDER BY ordem")
    for codigo, nome in cursor.fetchall():
        print_info(f"  {codigo}: {nome}")


def adicionar_disciplina_na_tag(cursor, dry_run: bool = False):
    """Adiciona coluna id_disciplina na tabela tag."""
    print_header("ETAPA 2: Adicionar id_disciplina na tabela TAG")
    
    if coluna_existe(cursor, 'tag', 'id_disciplina'):
        print_aviso("Coluna id_disciplina já existe na tabela tag")
        return
    
    if dry_run:
        print_info("Adicionaria coluna id_disciplina na tabela tag")
        print_info("Associaria tags existentes à disciplina Matemática")
        return
    
    # Adiciona a coluna
    cursor.execute("""
        ALTER TABLE tag ADD COLUMN id_disciplina INTEGER 
        REFERENCES disciplina(id_disciplina)
    """)
    print_ok("Coluna id_disciplina adicionada")
    
    # Busca o ID da disciplina Matemática
    cursor.execute("SELECT id_disciplina FROM disciplina WHERE codigo = 'MAT'")
    resultado = cursor.fetchone()
    
    if resultado:
        id_matematica = resultado[0]
        
        # Associa todas as tags de conteúdo (não V* nem N*) à Matemática
        cursor.execute("""
            UPDATE tag 
            SET id_disciplina = ?
            WHERE numeracao NOT LIKE 'V%' 
            AND numeracao NOT LIKE 'N%'
        """, (id_matematica,))
        
        qtd = cursor.rowcount
        print_ok(f"{qtd} tags de conteúdo associadas à Matemática")
    else:
        print_erro("Disciplina Matemática não encontrada!")


def criar_tabela_nivel_escolar(cursor, dry_run: bool = False):
    """Cria a tabela nivel_escolar."""
    print_header("ETAPA 3: Criar tabela NIVEL_ESCOLAR")
    
    if tabela_existe(cursor, 'nivel_escolar'):
        print_aviso("Tabela nivel_escolar já existe")
        return
    
    if dry_run:
        print_info("Criaria tabela nivel_escolar")
        print_info(f"Inseriria {len(NIVEIS_PADRAO)} níveis padrão")
        return
    
    cursor.execute("""
        CREATE TABLE nivel_escolar (
            id_nivel INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo VARCHAR(10) NOT NULL UNIQUE,
            nome VARCHAR(100) NOT NULL,
            descricao TEXT,
            ordem INTEGER NOT NULL DEFAULT 0,
            ativo BOOLEAN NOT NULL DEFAULT 1,
            data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
            data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print_ok("Tabela nivel_escolar criada")
    
    # Inserir níveis padrão
    for codigo, nome, descricao, ordem in NIVEIS_PADRAO:
        cursor.execute("""
            INSERT INTO nivel_escolar (codigo, nome, descricao, ordem)
            VALUES (?, ?, ?, ?)
        """, (codigo, nome, descricao, ordem))
    
    print_ok(f"{len(NIVEIS_PADRAO)} níveis escolares inseridos")


def criar_tabela_questao_nivel(cursor, dry_run: bool = False):
    """Cria a tabela de relacionamento questao_nivel."""
    print_header("ETAPA 4: Criar tabela QUESTAO_NIVEL")
    
    if tabela_existe(cursor, 'questao_nivel'):
        print_aviso("Tabela questao_nivel já existe")
        return
    
    if dry_run:
        print_info("Criaria tabela questao_nivel (relacionamento N:N)")
        return
    
    cursor.execute("""
        CREATE TABLE questao_nivel (
            id_questao INTEGER NOT NULL,
            id_nivel INTEGER NOT NULL,
            data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id_questao, id_nivel),
            FOREIGN KEY (id_questao) REFERENCES questao(id_questao) ON DELETE CASCADE,
            FOREIGN KEY (id_nivel) REFERENCES nivel_escolar(id_nivel) ON DELETE CASCADE
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_qn_questao ON questao_nivel(id_questao)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_qn_nivel ON questao_nivel(id_nivel)")
    
    print_ok("Tabela questao_nivel criada com índices")


def expandir_fonte_questao(cursor, dry_run: bool = False):
    """Expande a tabela fonte_questao com novas colunas."""
    print_header("ETAPA 5: Expandir tabela FONTE_QUESTAO")
    
    # Verifica se a tabela existe
    if not tabela_existe(cursor, 'fonte_questao'):
        if dry_run:
            print_info("Criaria tabela fonte_questao")
            return
        
        cursor.execute("""
            CREATE TABLE fonte_questao (
                id_fonte INTEGER PRIMARY KEY AUTOINCREMENT,
                sigla VARCHAR(20) NOT NULL UNIQUE,
                nome_completo VARCHAR(200) NOT NULL,
                tipo_instituicao VARCHAR(50),
                estado VARCHAR(2),
                ano_inicio INTEGER,
                ano_fim INTEGER,
                url_oficial VARCHAR(500),
                ativo BOOLEAN NOT NULL DEFAULT 1,
                data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
                data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print_ok("Tabela fonte_questao criada")
        return
    
    # Adiciona colunas que não existem
    novas_colunas = [
        ("tipo_instituicao", "VARCHAR(50)"),
        ("estado", "VARCHAR(2)"),
        ("ano_inicio", "INTEGER"),
        ("ano_fim", "INTEGER"),
        ("url_oficial", "VARCHAR(500)"),
        ("ativo", "BOOLEAN DEFAULT 1"),
    ]
    
    for nome_col, tipo in novas_colunas:
        if not coluna_existe(cursor, 'fonte_questao', nome_col):
            if dry_run:
                print_info(f"Adicionaria coluna {nome_col}")
            else:
                cursor.execute(f"ALTER TABLE fonte_questao ADD COLUMN {nome_col} {tipo}")
                print_ok(f"Coluna {nome_col} adicionada")
        else:
            print_aviso(f"Coluna {nome_col} já existe")


def migrar_tags_vestibular(cursor, dry_run: bool = False):
    """Migra tags V* para fonte_questao."""
    print_header("ETAPA 6: Migrar tags de VESTIBULAR (V*)")
    
    cursor.execute("""
        SELECT id_tag, numeracao, nome 
        FROM tag 
        WHERE numeracao LIKE 'V%'
        ORDER BY numeracao
    """)
    tags_vest = cursor.fetchall()
    
    if not tags_vest:
        print_info("Nenhuma tag de vestibular encontrada")
        return
    
    print_info(f"{len(tags_vest)} tags de vestibular encontradas")
    
    for id_tag, numeracao, nome in tags_vest:
        print_info(f"  {numeracao}: {nome}")
        
        if dry_run:
            continue
        
        # Cria sigla a partir da numeração
        sigla = numeracao.replace('V', '').strip()
        if not sigla or sigla.isdigit():
            # Usa parte do nome como sigla
            sigla = ''.join(word[0] for word in nome.split()[:3]).upper()
        
        # Verifica se já existe
        cursor.execute("SELECT id_fonte FROM fonte_questao WHERE sigla = ? OR nome_completo = ?", 
                      (sigla, nome))
        existente = cursor.fetchone()
        
        if existente:
            id_fonte = existente[0]
            print_info(f"    → Já existe em fonte_questao (id={id_fonte})")
        else:
            # Insere nova fonte
            cursor.execute("""
                INSERT INTO fonte_questao (sigla, nome_completo, tipo_instituicao, ativo)
                VALUES (?, ?, 'VESTIBULAR', 1)
            """, (sigla, nome))
            id_fonte = cursor.lastrowid
            print_ok(f"    → Inserido em fonte_questao (id={id_fonte})")
        
        # Atualiza questões (se tabela questao tem campo id_fonte)
        if coluna_existe(cursor, 'questao', 'id_fonte'):
            cursor.execute("""
                UPDATE questao
                SET id_fonte = ?
                WHERE id_questao IN (
                    SELECT id_questao FROM questao_tag WHERE id_tag = ?
                )
                AND (id_fonte IS NULL OR id_fonte = 0)
            """, (id_fonte, id_tag))
            if cursor.rowcount > 0:
                print_info(f"    → {cursor.rowcount} questões atualizadas")
        
        # Remove relacionamentos e tag
        cursor.execute("DELETE FROM questao_tag WHERE id_tag = ?", (id_tag,))
        cursor.execute("DELETE FROM tag WHERE id_tag = ?", (id_tag,))
    
    if not dry_run:
        print_ok("Tags de vestibular migradas e removidas")


def migrar_tags_nivel(cursor, dry_run: bool = False):
    """Migra tags N* para nivel_escolar."""
    print_header("ETAPA 7: Migrar tags de NÍVEL (N*)")
    
    cursor.execute("""
        SELECT id_tag, numeracao, nome 
        FROM tag 
        WHERE numeracao LIKE 'N%'
        ORDER BY numeracao
    """)
    tags_nivel = cursor.fetchall()
    
    if not tags_nivel:
        print_info("Nenhuma tag de nível encontrada")
        return
    
    print_info(f"{len(tags_nivel)} tags de nível encontradas")
    
    for id_tag, numeracao, nome in tags_nivel:
        print_info(f"  {numeracao}: {nome}")
        
        # Encontra o código do nível correspondente
        codigo_nivel = None
        nome_lower = nome.lower()
        
        for chave, codigo in MAPEAMENTO_NIVEIS.items():
            if chave in nome_lower:
                codigo_nivel = codigo
                break
        
        if not codigo_nivel:
            print_aviso(f"    → Não foi possível mapear para nível escolar")
            continue
        
        if dry_run:
            print_info(f"    → Seria mapeado para {codigo_nivel}")
            continue
        
        # Busca o id do nível
        cursor.execute("SELECT id_nivel FROM nivel_escolar WHERE codigo = ?", (codigo_nivel,))
        resultado = cursor.fetchone()
        
        if not resultado:
            print_aviso(f"    → Nível {codigo_nivel} não encontrado")
            continue
        
        id_nivel = resultado[0]
        print_ok(f"    → Mapeado para {codigo_nivel} (id={id_nivel})")
        
        # Migra relacionamentos para questao_nivel
        cursor.execute("""
            INSERT OR IGNORE INTO questao_nivel (id_questao, id_nivel)
            SELECT id_questao, ?
            FROM questao_tag
            WHERE id_tag = ?
        """, (id_nivel, id_tag))
        
        if cursor.rowcount > 0:
            print_info(f"    → {cursor.rowcount} questões associadas ao nível")
        
        # Remove relacionamentos e tag
        cursor.execute("DELETE FROM questao_tag WHERE id_tag = ?", (id_tag,))
        cursor.execute("DELETE FROM tag WHERE id_tag = ?", (id_tag,))
    
    if not dry_run:
        print_ok("Tags de nível migradas e removidas")


def criar_indices(cursor, dry_run: bool = False):
    """Cria índices para melhor performance."""
    print_header("ETAPA 8: Criar ÍNDICES")
    
    indices = [
        ("idx_tag_disciplina", "tag", "id_disciplina"),
        ("idx_disciplina_codigo", "disciplina", "codigo"),
        ("idx_disciplina_ativo", "disciplina", "ativo"),
        ("idx_nivel_codigo", "nivel_escolar", "codigo"),
        ("idx_nivel_ativo", "nivel_escolar", "ativo"),
        ("idx_fonte_tipo", "fonte_questao", "tipo_instituicao"),
        ("idx_fonte_ativo", "fonte_questao", "ativo"),
    ]
    
    for nome_idx, tabela, coluna in indices:
        if dry_run:
            print_info(f"Criaria índice {nome_idx} em {tabela}({coluna})")
        else:
            try:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS {nome_idx} ON {tabela}({coluna})")
                print_ok(f"Índice {nome_idx} criado")
            except Exception as e:
                print_aviso(f"Índice {nome_idx}: {e}")


def verificar_resultado(cursor):
    """Verifica o resultado da migração."""
    print_header("VERIFICAÇÃO FINAL")
    
    # Disciplinas
    cursor.execute("SELECT COUNT(*) FROM disciplina")
    print_info(f"Disciplinas: {cursor.fetchone()[0]}")
    
    # Níveis
    cursor.execute("SELECT COUNT(*) FROM nivel_escolar")
    print_info(f"Níveis escolares: {cursor.fetchone()[0]}")
    
    # Fontes
    cursor.execute("SELECT COUNT(*) FROM fonte_questao")
    print_info(f"Fontes de questão: {cursor.fetchone()[0]}")
    
    # Tags restantes
    cursor.execute("SELECT COUNT(*) FROM tag WHERE numeracao LIKE 'V%' OR numeracao LIKE 'N%'")
    tags_resto = cursor.fetchone()[0]
    if tags_resto == 0:
        print_ok("Nenhuma tag V*/N* restante")
    else:
        print_erro(f"{tags_resto} tags V*/N* ainda existem!")
    
    # Tags com disciplina
    cursor.execute("SELECT COUNT(*) FROM tag WHERE id_disciplina IS NOT NULL")
    print_info(f"Tags com disciplina definida: {cursor.fetchone()[0]}")
    
    # Relacionamentos questao_nivel
    cursor.execute("SELECT COUNT(*) FROM questao_nivel")
    print_info(f"Relacionamentos questão-nível: {cursor.fetchone()[0]}")


# ============================================================
# FUNÇÃO PRINCIPAL
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Migração do banco de dados")
    parser.add_argument("--dry-run", action="store_true", help="Apenas mostra o que seria feito")
    parser.add_argument("--no-backup", action="store_true", help="Não criar backup")
    args = parser.parse_args()
    
    print("=" * 60)
    print(" MIGRAÇÃO DO BANCO DE DADOS")
    print(" Disciplinas, Níveis e Fontes")
    print("=" * 60)
    
    if args.dry_run:
        print("\n⚠️  MODO DRY-RUN: Nenhuma alteração será feita\n")
    
    # Verifica se o banco existe
    if not Path(DATABASE_PATH).exists():
        print_erro(f"Banco não encontrado: {DATABASE_PATH}")
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
            print_ok("\nAlterações salvas no banco de dados")
        
        verificar_resultado(cursor)
        
    except Exception as e:
        conn.rollback()
        print_erro(f"\nERRO: {e}")
        print_info("Alterações foram revertidas")
        raise
        
    finally:
        conn.close()
    
    print("\n" + "=" * 60)
    if args.dry_run:
        print(" DRY-RUN CONCLUÍDO")
    else:
        print(" MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 60 + "\n")
    
    return 0


if __name__ == "__main__":
    exit(main())
```

---

## 4. FASE 2: CRIAR MODEL DISCIPLINA

### 4.1 Criar o Model

**Caminho:** `src/models/orm/disciplina.py`

```python
"""
Model ORM para a tabela disciplina.

Representa as disciplinas do sistema (Matemática, Física, Português, etc.)
Cada disciplina possui seus próprios conteúdos (tags).
"""

from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship

from src.models.orm.base import Base

if TYPE_CHECKING:
    from src.models.orm.tag import Tag


class Disciplina(Base):
    """
    Model para disciplinas.
    
    Attributes:
        id_disciplina: Identificador único
        codigo: Código curto (MAT, FIS, QUI, etc.)
        nome: Nome completo (Matemática, Física, etc.)
        descricao: Descrição da disciplina
        cor: Cor para exibição na UI (hexadecimal)
        ordem: Ordem de exibição
        ativo: Se está ativa para uso
    """
    
    __tablename__ = 'disciplina'
    
    # Colunas
    id_disciplina = Column(Integer, primary_key=True, autoincrement=True)
    codigo = Column(String(10), unique=True, nullable=False)
    nome = Column(String(100), nullable=False)
    descricao = Column(Text, nullable=True)
    cor = Column(String(7), default='#3498db')  # Cor hexadecimal
    ordem = Column(Integer, nullable=False, default=0)
    ativo = Column(Boolean, nullable=False, default=True)
    data_criacao = Column(DateTime, default=datetime.now)
    data_atualizacao = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relacionamentos
    tags = relationship("Tag", back_populates="disciplina", lazy="dynamic")
    
    def __repr__(self) -> str:
        return f"<Disciplina(id={self.id_disciplina}, codigo='{self.codigo}', nome='{self.nome}')>"
    
    def __str__(self) -> str:
        return f"{self.codigo} - {self.nome}"
    
    def to_dict(self) -> dict:
        """Converte o model para dicionário."""
        return {
            "id_disciplina": self.id_disciplina,
            "codigo": self.codigo,
            "nome": self.nome,
            "descricao": self.descricao,
            "cor": self.cor,
            "ordem": self.ordem,
            "ativo": self.ativo,
        }
    
    @property
    def total_conteudos(self) -> int:
        """Retorna o total de conteúdos (tags) da disciplina."""
        return self.tags.count()
    
    @property
    def conteudos_raiz(self) -> List["Tag"]:
        """Retorna apenas os conteúdos de primeiro nível (sem pai)."""
        return [tag for tag in self.tags if tag.id_pai is None]
    
    @classmethod
    def get_disciplinas_padrao(cls) -> List[dict]:
        """Retorna disciplinas padrão para inserção inicial."""
        return [
            {"codigo": "MAT", "nome": "Matemática", "descricao": "Matemática e Raciocínio Lógico", "cor": "#3498db", "ordem": 1},
            {"codigo": "FIS", "nome": "Física", "descricao": "Física Geral e Aplicada", "cor": "#e74c3c", "ordem": 2},
            {"codigo": "QUI", "nome": "Química", "descricao": "Química Geral, Orgânica e Inorgânica", "cor": "#9b59b6", "ordem": 3},
            {"codigo": "BIO", "nome": "Biologia", "descricao": "Biologia Geral, Ecologia e Genética", "cor": "#27ae60", "ordem": 4},
            {"codigo": "POR", "nome": "Português", "descricao": "Língua Portuguesa e Literatura", "cor": "#f39c12", "ordem": 5},
            {"codigo": "RED", "nome": "Redação", "descricao": "Produção Textual", "cor": "#e67e22", "ordem": 6},
            {"codigo": "HIS", "nome": "História", "descricao": "História Geral e do Brasil", "cor": "#1abc9c", "ordem": 7},
            {"codigo": "GEO", "nome": "Geografia", "descricao": "Geografia Geral e do Brasil", "cor": "#16a085", "ordem": 8},
            {"codigo": "FIL", "nome": "Filosofia", "descricao": "Filosofia Geral", "cor": "#8e44ad", "ordem": 9},
            {"codigo": "SOC", "nome": "Sociologia", "descricao": "Sociologia Geral", "cor": "#2c3e50", "ordem": 10},
            {"codigo": "ING", "nome": "Inglês", "descricao": "Língua Inglesa", "cor": "#c0392b", "ordem": 11},
            {"codigo": "ESP", "nome": "Espanhol", "descricao": "Língua Espanhola", "cor": "#d35400", "ordem": 12},
        ]
```

---

## 5. FASE 3: ATUALIZAR MODEL TAG (CONTEÚDO)

### 5.1 Modificar o Model Tag

**Caminho:** `src/models/orm/tag.py`

Adicione o relacionamento com disciplina:

```python
"""
Model ORM para a tabela tag.

Representa os conteúdos/tópicos de cada disciplina.
Cada tag pertence a uma disciplina específica.
"""

from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from src.models.orm.base import Base

if TYPE_CHECKING:
    from src.models.orm.disciplina import Disciplina


class Tag(Base):
    """
    Model para tags (conteúdos).
    
    Attributes:
        id_tag: Identificador único
        id_disciplina: ID da disciplina à qual pertence (NOVO!)
        id_pai: ID da tag pai (para hierarquia)
        numeracao: Numeração hierárquica (1, 1.1, 1.1.1, etc.)
        nome: Nome do conteúdo
        descricao: Descrição detalhada
        ativo: Se está ativa para uso
    """
    
    __tablename__ = 'tag'
    
    # Colunas existentes
    id_tag = Column(Integer, primary_key=True, autoincrement=True)
    id_pai = Column(Integer, ForeignKey('tag.id_tag'), nullable=True)
    numeracao = Column(String(50), nullable=False)
    nome = Column(String(200), nullable=False)
    descricao = Column(Text, nullable=True)
    ativo = Column(Boolean, nullable=False, default=True)
    data_criacao = Column(DateTime, default=datetime.now)
    data_atualizacao = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # NOVA coluna: relacionamento com disciplina
    id_disciplina = Column(Integer, ForeignKey('disciplina.id_disciplina'), nullable=True)
    
    # Relacionamentos
    disciplina = relationship("Disciplina", back_populates="tags")
    pai = relationship("Tag", remote_side=[id_tag], backref="filhos")
    questoes = relationship("Questao", secondary="questao_tag", back_populates="tags")
    
    def __repr__(self) -> str:
        return f"<Tag(id={self.id_tag}, numeracao='{self.numeracao}', nome='{self.nome}')>"
    
    def __str__(self) -> str:
        return f"{self.numeracao} - {self.nome}"
    
    def to_dict(self) -> dict:
        """Converte o model para dicionário."""
        return {
            "id_tag": self.id_tag,
            "id_disciplina": self.id_disciplina,
            "id_pai": self.id_pai,
            "numeracao": self.numeracao,
            "nome": self.nome,
            "descricao": self.descricao,
            "ativo": self.ativo,
            "disciplina_codigo": self.disciplina.codigo if self.disciplina else None,
            "disciplina_nome": self.disciplina.nome if self.disciplina else None,
        }
    
    @property
    def caminho_completo(self) -> str:
        """Retorna o caminho completo da tag (ex: 'Números > Naturais > Primos')."""
        partes = [self.nome]
        tag_atual = self.pai
        
        while tag_atual:
            partes.insert(0, tag_atual.nome)
            tag_atual = tag_atual.pai
        
        return " > ".join(partes)
    
    @property
    def nivel(self) -> int:
        """Retorna o nível de profundidade da tag (1, 2, 3, etc.)."""
        return self.numeracao.count('.') + 1
    
    @property
    def eh_raiz(self) -> bool:
        """Retorna True se é uma tag raiz (sem pai)."""
        return self.id_pai is None
    
    def get_descendentes(self) -> List["Tag"]:
        """Retorna todos os descendentes (filhos, netos, etc.)."""
        descendentes = []
        for filho in self.filhos:
            descendentes.append(filho)
            descendentes.extend(filho.get_descendentes())
        return descendentes
```

---

## 6. FASE 4: CRIAR MODEL NIVELESCOLAR

### 6.1 Criar o Model

**Caminho:** `src/models/orm/nivel_escolar.py`

```python
"""
Model ORM para a tabela nivel_escolar.

Representa os níveis de escolaridade que podem ser associados às questões.
"""

from datetime import datetime
from typing import List
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship

from src.models.orm.base import Base


class NivelEscolar(Base):
    """
    Model para níveis escolares.
    
    Attributes:
        id_nivel: Identificador único
        codigo: Código curto (EF1, EF2, EM, etc.)
        nome: Nome completo (Ensino Fundamental I, etc.)
        descricao: Descrição detalhada
        ordem: Ordem de exibição
        ativo: Se está ativo para uso
    """
    
    __tablename__ = 'nivel_escolar'
    
    id_nivel = Column(Integer, primary_key=True, autoincrement=True)
    codigo = Column(String(10), unique=True, nullable=False)
    nome = Column(String(100), nullable=False)
    descricao = Column(Text, nullable=True)
    ordem = Column(Integer, nullable=False, default=0)
    ativo = Column(Boolean, nullable=False, default=True)
    data_criacao = Column(DateTime, default=datetime.now)
    data_atualizacao = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relacionamento N:N com questões
    questoes = relationship(
        "Questao",
        secondary="questao_nivel",
        back_populates="niveis_escolares"
    )
    
    def __repr__(self) -> str:
        return f"<NivelEscolar(id={self.id_nivel}, codigo='{self.codigo}')>"
    
    def __str__(self) -> str:
        return f"{self.codigo} - {self.nome}"
    
    def to_dict(self) -> dict:
        return {
            "id_nivel": self.id_nivel,
            "codigo": self.codigo,
            "nome": self.nome,
            "descricao": self.descricao,
            "ordem": self.ordem,
            "ativo": self.ativo,
        }
    
    @classmethod
    def get_niveis_padrao(cls) -> List[dict]:
        """Retorna níveis padrão para inserção inicial."""
        return [
            {"codigo": "EF1", "nome": "Ensino Fundamental I", "descricao": "1º ao 5º ano", "ordem": 1},
            {"codigo": "EF2", "nome": "Ensino Fundamental II", "descricao": "6º ao 9º ano", "ordem": 2},
            {"codigo": "EM", "nome": "Ensino Médio", "descricao": "1ª a 3ª série", "ordem": 3},
            {"codigo": "PRE", "nome": "Pré-Vestibular", "descricao": "Cursinho preparatório", "ordem": 4},
            {"codigo": "EJA", "nome": "Educação de Jovens e Adultos", "descricao": "EJA", "ordem": 5},
            {"codigo": "TEC", "nome": "Ensino Técnico", "descricao": "Cursos técnicos", "ordem": 6},
            {"codigo": "SUP", "nome": "Ensino Superior", "descricao": "Graduação", "ordem": 7},
            {"codigo": "POS", "nome": "Pós-Graduação", "descricao": "Mestrado e Doutorado", "ordem": 8},
        ]
```

### 6.2 Criar Tabela de Relacionamento

**Caminho:** `src/models/orm/questao_nivel.py`

```python
"""
Tabela de relacionamento N:N entre Questao e NivelEscolar.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey, Table

from src.models.orm.base import Base

questao_nivel = Table(
    'questao_nivel',
    Base.metadata,
    Column('id_questao', Integer, ForeignKey('questao.id_questao', ondelete='CASCADE'), primary_key=True),
    Column('id_nivel', Integer, ForeignKey('nivel_escolar.id_nivel', ondelete='CASCADE'), primary_key=True),
    Column('data_criacao', DateTime, default=datetime.now)
)
```

---

## 7. FASE 5: EXPANDIR MODEL FONTEQUESTAO

### 7.1 Modificar o Model

**Caminho:** `src/models/orm/fonte_questao.py`

```python
"""
Model ORM para a tabela fonte_questao.

Representa as fontes/origens das questões (vestibulares, concursos, olimpíadas, etc.)
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship

from src.models.orm.base import Base


class FonteQuestao(Base):
    """
    Model para fontes de questões.
    
    Attributes:
        id_fonte: Identificador único
        sigla: Sigla curta (ENEM, FUVEST, etc.)
        nome_completo: Nome completo da instituição/prova
        tipo_instituicao: Tipo (VESTIBULAR, CONCURSO, OLIMPIADA, AUTORAL)
        estado: UF da instituição (NULL para nacional)
        ano_inicio: Ano da primeira edição
        ano_fim: Ano da última edição (NULL se ainda ativa)
        url_oficial: Site oficial
        ativo: Se está ativo para uso
    """
    
    __tablename__ = 'fonte_questao'
    
    id_fonte = Column(Integer, primary_key=True, autoincrement=True)
    sigla = Column(String(20), unique=True, nullable=False)
    nome_completo = Column(String(200), nullable=False)
    tipo_instituicao = Column(String(50), nullable=True)
    estado = Column(String(2), nullable=True)
    ano_inicio = Column(Integer, nullable=True)
    ano_fim = Column(Integer, nullable=True)
    url_oficial = Column(String(500), nullable=True)
    ativo = Column(Boolean, nullable=False, default=True)
    data_criacao = Column(DateTime, default=datetime.now)
    data_atualizacao = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relacionamento com questões
    questoes = relationship("Questao", back_populates="fonte")
    
    # Constantes
    TIPO_VESTIBULAR = "VESTIBULAR"
    TIPO_CONCURSO = "CONCURSO"
    TIPO_OLIMPIADA = "OLIMPIADA"
    TIPO_AUTORAL = "AUTORAL"
    TIPO_DIDATICO = "DIDATICO"
    
    TIPOS_VALIDOS = [TIPO_VESTIBULAR, TIPO_CONCURSO, TIPO_OLIMPIADA, TIPO_AUTORAL, TIPO_DIDATICO]
    
    def __repr__(self) -> str:
        return f"<FonteQuestao(id={self.id_fonte}, sigla='{self.sigla}')>"
    
    def __str__(self) -> str:
        return f"{self.sigla} - {self.nome_completo}"
    
    def to_dict(self) -> dict:
        return {
            "id_fonte": self.id_fonte,
            "sigla": self.sigla,
            "nome_completo": self.nome_completo,
            "tipo_instituicao": self.tipo_instituicao,
            "estado": self.estado,
            "ano_inicio": self.ano_inicio,
            "ano_fim": self.ano_fim,
            "url_oficial": self.url_oficial,
            "ativo": self.ativo,
        }
    
    @property
    def esta_ativa(self) -> bool:
        """Retorna True se a fonte ainda está ativa."""
        return self.ano_fim is None
    
    @property
    def descricao_completa(self) -> str:
        """Retorna descrição formatada."""
        partes = [self.nome_completo]
        if self.estado:
            partes.append(f"({self.estado})")
        if self.ano_inicio:
            if self.ano_fim:
                partes.append(f"[{self.ano_inicio}-{self.ano_fim}]")
            else:
                partes.append(f"[desde {self.ano_inicio}]")
        return " ".join(partes)
```

---

## 8. FASE 6: CRIAR REPOSITORIES

### 8.1 Atualizar __init__.py dos Models

**Caminho:** `src/models/orm/__init__.py`

```python
"""Módulo de models ORM."""

from .base import Base
from .disciplina import Disciplina
from .tag import Tag
from .nivel_escolar import NivelEscolar
from .questao_nivel import questao_nivel
from .fonte_questao import FonteQuestao
from .questao import Questao
# ... outros models existentes ...

__all__ = [
    "Base",
    "Disciplina",
    "Tag",
    "NivelEscolar",
    "questao_nivel",
    "FonteQuestao",
    "Questao",
    # ... outros ...
]
```

### 8.2 Criar Repository de Disciplina

**Caminho:** `src/repositories/disciplina_repository.py`

```python
"""
Repository para operações com Disciplina.
"""

import logging
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.models.orm.disciplina import Disciplina

logger = logging.getLogger(__name__)


class DisciplinaRepository:
    """Repository para CRUD de disciplinas."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def listar_todas(self, apenas_ativas: bool = True) -> List[Disciplina]:
        """Lista todas as disciplinas."""
        query = self.session.query(Disciplina)
        if apenas_ativas:
            query = query.filter(Disciplina.ativo == True)
        return query.order_by(Disciplina.ordem).all()
    
    def buscar_por_id(self, id_disciplina: int) -> Optional[Disciplina]:
        """Busca uma disciplina pelo ID."""
        return self.session.query(Disciplina).filter(
            Disciplina.id_disciplina == id_disciplina
        ).first()
    
    def buscar_por_codigo(self, codigo: str) -> Optional[Disciplina]:
        """Busca uma disciplina pelo código (MAT, FIS, etc.)."""
        return self.session.query(Disciplina).filter(
            Disciplina.codigo == codigo.upper()
        ).first()
    
    def criar(self, dados: dict) -> Optional[Disciplina]:
        """Cria uma nova disciplina."""
        try:
            disciplina = Disciplina(
                codigo=dados["codigo"].upper(),
                nome=dados["nome"],
                descricao=dados.get("descricao"),
                cor=dados.get("cor", "#3498db"),
                ordem=dados.get("ordem", 0),
                ativo=dados.get("ativo", True),
            )
            self.session.add(disciplina)
            self.session.commit()
            logger.info(f"Disciplina criada: {disciplina.codigo}")
            return disciplina
        except IntegrityError:
            self.session.rollback()
            logger.error(f"Disciplina já existe: {dados.get('codigo')}")
            return None
        except Exception as e:
            self.session.rollback()
            logger.error(f"Erro ao criar disciplina: {e}")
            return None
    
    def atualizar(self, id_disciplina: int, dados: dict) -> Optional[Disciplina]:
        """Atualiza uma disciplina."""
        try:
            disciplina = self.buscar_por_id(id_disciplina)
            if not disciplina:
                return None
            
            if "codigo" in dados:
                disciplina.codigo = dados["codigo"].upper()
            if "nome" in dados:
                disciplina.nome = dados["nome"]
            if "descricao" in dados:
                disciplina.descricao = dados["descricao"]
            if "cor" in dados:
                disciplina.cor = dados["cor"]
            if "ordem" in dados:
                disciplina.ordem = dados["ordem"]
            if "ativo" in dados:
                disciplina.ativo = dados["ativo"]
            
            self.session.commit()
            return disciplina
        except Exception as e:
            self.session.rollback()
            logger.error(f"Erro ao atualizar disciplina: {e}")
            return None
    
    def inativar(self, id_disciplina: int) -> bool:
        """Inativa uma disciplina (soft delete)."""
        try:
            disciplina = self.buscar_por_id(id_disciplina)
            if not disciplina:
                return False
            disciplina.ativo = False
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"Erro ao inativar disciplina: {e}")
            return False
    
    def listar_para_select(self) -> List[tuple]:
        """Retorna lista formatada para combobox."""
        disciplinas = self.listar_todas(apenas_ativas=True)
        return [(d.id_disciplina, f"{d.codigo} - {d.nome}") for d in disciplinas]
    
    def popular_padrao(self) -> int:
        """Popula com disciplinas padrão. Retorna quantidade inserida."""
        padrao = Disciplina.get_disciplinas_padrao()
        inseridas = 0
        for dados in padrao:
            existente = self.buscar_por_codigo(dados["codigo"])
            if not existente:
                if self.criar(dados):
                    inseridas += 1
        return inseridas
```

### 8.3 Criar Repository de Nível Escolar

**Caminho:** `src/repositories/nivel_escolar_repository.py`

```python
"""
Repository para operações com NivelEscolar.
"""

import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from src.models.orm.nivel_escolar import NivelEscolar

logger = logging.getLogger(__name__)


class NivelEscolarRepository:
    """Repository para CRUD de níveis escolares."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def listar_todos(self, apenas_ativos: bool = True) -> List[NivelEscolar]:
        """Lista todos os níveis escolares."""
        query = self.session.query(NivelEscolar)
        if apenas_ativos:
            query = query.filter(NivelEscolar.ativo == True)
        return query.order_by(NivelEscolar.ordem).all()
    
    def buscar_por_id(self, id_nivel: int) -> Optional[NivelEscolar]:
        """Busca um nível pelo ID."""
        return self.session.query(NivelEscolar).filter(
            NivelEscolar.id_nivel == id_nivel
        ).first()
    
    def buscar_por_codigo(self, codigo: str) -> Optional[NivelEscolar]:
        """Busca um nível pelo código (EF1, EM, etc.)."""
        return self.session.query(NivelEscolar).filter(
            NivelEscolar.codigo == codigo.upper()
        ).first()
    
    def criar(self, dados: dict) -> Optional[NivelEscolar]:
        """Cria um novo nível escolar."""
        try:
            nivel = NivelEscolar(
                codigo=dados["codigo"].upper(),
                nome=dados["nome"],
                descricao=dados.get("descricao"),
                ordem=dados.get("ordem", 0),
                ativo=dados.get("ativo", True),
            )
            self.session.add(nivel)
            self.session.commit()
            return nivel
        except Exception as e:
            self.session.rollback()
            logger.error(f"Erro ao criar nível: {e}")
            return None
    
    def listar_para_select(self) -> List[tuple]:
        """Retorna lista formatada para combobox."""
        niveis = self.listar_todos(apenas_ativos=True)
        return [(n.id_nivel, f"{n.codigo} - {n.nome}") for n in niveis]
    
    def popular_padrao(self) -> int:
        """Popula com níveis padrão."""
        padrao = NivelEscolar.get_niveis_padrao()
        inseridos = 0
        for dados in padrao:
            existente = self.buscar_por_codigo(dados["codigo"])
            if not existente:
                if self.criar(dados):
                    inseridos += 1
        return inseridos
```

### 8.4 Atualizar TagRepository

**Caminho:** `src/repositories/tag_repository.py`

Adicione métodos para trabalhar com disciplinas:

```python
"""
Repository para operações com Tag (Conteúdo).
"""

import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from src.models.orm.tag import Tag
from src.models.orm.disciplina import Disciplina

logger = logging.getLogger(__name__)


class TagRepository:
    """Repository para CRUD de tags (conteúdos)."""
    
    def __init__(self, session: Session):
        self.session = session
    
    # ... métodos existentes ...
    
    # NOVOS MÉTODOS PARA DISCIPLINA
    
    def listar_por_disciplina(
        self, 
        id_disciplina: int, 
        apenas_ativas: bool = True
    ) -> List[Tag]:
        """
        Lista todas as tags de uma disciplina específica.
        
        Args:
            id_disciplina: ID da disciplina
            apenas_ativas: Se True, retorna apenas tags ativas
            
        Returns:
            Lista de Tag ordenada por numeração
        """
        query = self.session.query(Tag).filter(
            Tag.id_disciplina == id_disciplina
        )
        
        if apenas_ativas:
            query = query.filter(Tag.ativo == True)
        
        return query.order_by(Tag.numeracao).all()
    
    def listar_raiz_por_disciplina(
        self, 
        id_disciplina: int,
        apenas_ativas: bool = True
    ) -> List[Tag]:
        """
        Lista as tags raiz (sem pai) de uma disciplina.
        
        Args:
            id_disciplina: ID da disciplina
            apenas_ativas: Se True, retorna apenas tags ativas
            
        Returns:
            Lista de Tag de primeiro nível
        """
        query = self.session.query(Tag).filter(
            Tag.id_disciplina == id_disciplina,
            Tag.id_pai == None
        )
        
        if apenas_ativas:
            query = query.filter(Tag.ativo == True)
        
        return query.order_by(Tag.numeracao).all()
    
    def criar_para_disciplina(
        self, 
        id_disciplina: int, 
        dados: dict
    ) -> Optional[Tag]:
        """
        Cria uma nova tag associada a uma disciplina.
        
        Args:
            id_disciplina: ID da disciplina
            dados: Dicionário com os dados da tag
            
        Returns:
            Tag criada ou None se falhar
        """
        try:
            tag = Tag(
                id_disciplina=id_disciplina,
                id_pai=dados.get("id_pai"),
                numeracao=dados["numeracao"],
                nome=dados["nome"],
                descricao=dados.get("descricao"),
                ativo=dados.get("ativo", True),
            )
            self.session.add(tag)
            self.session.commit()
            
            logger.info(f"Tag criada: {tag.numeracao} - {tag.nome} (disciplina {id_disciplina})")
            return tag
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Erro ao criar tag: {e}")
            return None
    
    def mover_para_disciplina(
        self, 
        id_tag: int, 
        id_disciplina: int
    ) -> bool:
        """
        Move uma tag (e seus filhos) para outra disciplina.
        
        Args:
            id_tag: ID da tag a mover
            id_disciplina: ID da disciplina destino
            
        Returns:
            True se movido com sucesso
        """
        try:
            tag = self.buscar_por_id(id_tag)
            if not tag:
                return False
            
            # Move a tag
            tag.id_disciplina = id_disciplina
            
            # Move todos os descendentes
            for descendente in tag.get_descendentes():
                descendente.id_disciplina = id_disciplina
            
            self.session.commit()
            return True
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Erro ao mover tag: {e}")
            return False
    
    def buscar_arvore_disciplina(self, id_disciplina: int) -> List[dict]:
        """
        Retorna a árvore completa de tags de uma disciplina.
        
        Formato para exibição em TreeView.
        
        Args:
            id_disciplina: ID da disciplina
            
        Returns:
            Lista de dicionários com estrutura hierárquica
        """
        def construir_arvore(tag: Tag) -> dict:
            return {
                "id": tag.id_tag,
                "numeracao": tag.numeracao,
                "nome": tag.nome,
                "texto": f"{tag.numeracao} - {tag.nome}",
                "filhos": [construir_arvore(filho) for filho in tag.filhos if filho.ativo]
            }
        
        tags_raiz = self.listar_raiz_por_disciplina(id_disciplina)
        return [construir_arvore(tag) for tag in tags_raiz]
```

---

## 11. TESTES E VALIDAÇÃO

### 11.1 Script de Teste Completo

**Caminho:** `scripts/testar_migracao.py`

```python
"""
Script para validar a migração do banco de dados.

Execute após a migração para verificar se tudo funcionou corretamente.

Uso:
    python scripts/testar_migracao.py
"""

import sqlite3
from pathlib import Path

DATABASE_PATH = "database/mathbank.db"


def print_header(texto):
    print("\n" + "=" * 60)
    print(f" {texto}")
    print("=" * 60)


def print_ok(msg):
    print(f"   ✅ {msg}")


def print_erro(msg):
    print(f"   ❌ {msg}")


def print_aviso(msg):
    print(f"   ⚠️  {msg}")


def print_info(msg):
    print(f"   ℹ️  {msg}")


def testar_tabela_disciplina(cursor) -> bool:
    """Testa a tabela disciplina."""
    print_header("TESTE 1: Tabela DISCIPLINA")
    
    # Verifica existência
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='disciplina'
    """)
    if not cursor.fetchone():
        print_erro("Tabela disciplina NÃO existe")
        return False
    print_ok("Tabela disciplina existe")
    
    # Verifica colunas
    cursor.execute("PRAGMA table_info(disciplina)")
    colunas = {col[1] for col in cursor.fetchall()}
    colunas_esperadas = {'id_disciplina', 'codigo', 'nome', 'descricao', 'cor', 'ordem', 'ativo'}
    faltando = colunas_esperadas - colunas
    
    if faltando:
        print_erro(f"Colunas faltando: {faltando}")
        return False
    print_ok("Todas as colunas existem")
    
    # Verifica dados
    cursor.execute("SELECT COUNT(*) FROM disciplina")
    qtd = cursor.fetchone()[0]
    if qtd == 0:
        print_erro("Tabela disciplina está vazia")
        return False
    print_ok(f"{qtd} disciplinas cadastradas")
    
    # Lista disciplinas
    cursor.execute("SELECT codigo, nome FROM disciplina ORDER BY ordem")
    for codigo, nome in cursor.fetchall():
        print_info(f"  {codigo}: {nome}")
    
    return True


def testar_tag_com_disciplina(cursor) -> bool:
    """Testa se a tabela tag tem coluna id_disciplina."""
    print_header("TESTE 2: Coluna id_disciplina na TAG")
    
    cursor.execute("PRAGMA table_info(tag)")
    colunas = {col[1] for col in cursor.fetchall()}
    
    if 'id_disciplina' not in colunas:
        print_erro("Coluna id_disciplina NÃO existe na tabela tag")
        return False
    print_ok("Coluna id_disciplina existe")
    
    # Verifica tags com disciplina definida
    cursor.execute("SELECT COUNT(*) FROM tag WHERE id_disciplina IS NOT NULL")
    com_disciplina = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM tag WHERE id_disciplina IS NULL")
    sem_disciplina = cursor.fetchone()[0]
    
    print_info(f"Tags com disciplina: {com_disciplina}")
    print_info(f"Tags sem disciplina: {sem_disciplina}")
    
    if sem_disciplina > 0:
        print_aviso("Existem tags sem disciplina definida")
        cursor.execute("""
            SELECT numeracao, nome FROM tag 
            WHERE id_disciplina IS NULL 
            LIMIT 5
        """)
        for num, nome in cursor.fetchall():
            print_info(f"    {num}: {nome}")
    
    return True


def testar_tabela_nivel_escolar(cursor) -> bool:
    """Testa a tabela nivel_escolar."""
    print_header("TESTE 3: Tabela NIVEL_ESCOLAR")
    
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='nivel_escolar'
    """)
    if not cursor.fetchone():
        print_erro("Tabela nivel_escolar NÃO existe")
        return False
    print_ok("Tabela nivel_escolar existe")
    
    cursor.execute("SELECT COUNT(*) FROM nivel_escolar")
    qtd = cursor.fetchone()[0]
    if qtd == 0:
        print_erro("Tabela nivel_escolar está vazia")
        return False
    print_ok(f"{qtd} níveis cadastrados")
    
    cursor.execute("SELECT codigo, nome FROM nivel_escolar ORDER BY ordem")
    for codigo, nome in cursor.fetchall():
        print_info(f"  {codigo}: {nome}")
    
    return True


def testar_tabela_questao_nivel(cursor) -> bool:
    """Testa a tabela questao_nivel."""
    print_header("TESTE 4: Tabela QUESTAO_NIVEL")
    
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='questao_nivel'
    """)
    if not cursor.fetchone():
        print_erro("Tabela questao_nivel NÃO existe")
        return False
    print_ok("Tabela questao_nivel existe")
    
    cursor.execute("SELECT COUNT(*) FROM questao_nivel")
    qtd = cursor.fetchone()[0]
    print_info(f"{qtd} relacionamentos questão-nível")
    
    return True


def testar_tabela_fonte_questao(cursor) -> bool:
    """Testa a tabela fonte_questao."""
    print_header("TESTE 5: Tabela FONTE_QUESTAO")
    
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='fonte_questao'
    """)
    if not cursor.fetchone():
        print_erro("Tabela fonte_questao NÃO existe")
        return False
    print_ok("Tabela fonte_questao existe")
    
    # Verifica colunas expandidas
    cursor.execute("PRAGMA table_info(fonte_questao)")
    colunas = {col[1] for col in cursor.fetchall()}
    novas = {'tipo_instituicao', 'estado', 'ano_inicio', 'ano_fim'}
    faltando = novas - colunas
    
    if faltando:
        print_aviso(f"Colunas opcionais faltando: {faltando}")
    else:
        print_ok("Colunas expandidas existem")
    
    cursor.execute("SELECT COUNT(*) FROM fonte_questao")
    qtd = cursor.fetchone()[0]
    print_info(f"{qtd} fontes cadastradas")
    
    if qtd > 0:
        cursor.execute("SELECT sigla, nome_completo, tipo_instituicao FROM fonte_questao LIMIT 5")
        for sigla, nome, tipo in cursor.fetchall():
            print_info(f"  {sigla}: {nome} ({tipo or 'sem tipo'})")
    
    return True


def testar_tags_migradas(cursor) -> bool:
    """Verifica se não restaram tags V* e N*."""
    print_header("TESTE 6: Tags V* e N* migradas")
    
    cursor.execute("SELECT COUNT(*) FROM tag WHERE numeracao LIKE 'V%'")
    qtd_v = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM tag WHERE numeracao LIKE 'N%'")
    qtd_n = cursor.fetchone()[0]
    
    sucesso = True
    
    if qtd_v > 0:
        print_erro(f"Ainda existem {qtd_v} tags V* (vestibular)")
        cursor.execute("SELECT numeracao, nome FROM tag WHERE numeracao LIKE 'V%'")
        for num, nome in cursor.fetchall():
            print_info(f"  {num}: {nome}")
        sucesso = False
    else:
        print_ok("Nenhuma tag V* encontrada")
    
    if qtd_n > 0:
        print_erro(f"Ainda existem {qtd_n} tags N* (nível)")
        cursor.execute("SELECT numeracao, nome FROM tag WHERE numeracao LIKE 'N%'")
        for num, nome in cursor.fetchall():
            print_info(f"  {num}: {nome}")
        sucesso = False
    else:
        print_ok("Nenhuma tag N* encontrada")
    
    return sucesso


def testar_relacionamentos(cursor) -> bool:
    """Testa se os relacionamentos funcionam."""
    print_header("TESTE 7: Relacionamentos")
    
    sucesso = True
    
    # Tag -> Disciplina
    try:
        cursor.execute("""
            SELECT t.numeracao, t.nome, d.codigo, d.nome
            FROM tag t
            JOIN disciplina d ON t.id_disciplina = d.id_disciplina
            LIMIT 3
        """)
        resultados = cursor.fetchall()
        if resultados:
            print_ok("Join tag -> disciplina funcionando")
            for num, nome_tag, cod, nome_disc in resultados:
                print_info(f"  {num} ({nome_tag}) -> {cod} ({nome_disc})")
        else:
            print_aviso("Nenhuma tag com disciplina encontrada")
    except Exception as e:
        print_erro(f"Erro no join tag -> disciplina: {e}")
        sucesso = False
    
    # Questao -> Nivel
    try:
        cursor.execute("""
            SELECT qn.id_questao, n.codigo, n.nome
            FROM questao_nivel qn
            JOIN nivel_escolar n ON qn.id_nivel = n.id_nivel
            LIMIT 3
        """)
        resultados = cursor.fetchall()
        if resultados:
            print_ok("Join questao_nivel -> nivel_escolar funcionando")
            for id_q, cod, nome in resultados:
                print_info(f"  Questão {id_q} -> {cod} ({nome})")
        else:
            print_aviso("Nenhum relacionamento questão-nível encontrado")
    except Exception as e:
        print_erro(f"Erro no join questao_nivel: {e}")
        sucesso = False
    
    return sucesso


def testar_indices(cursor) -> bool:
    """Verifica se os índices foram criados."""
    print_header("TESTE 8: Índices")
    
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='index' AND name LIKE 'idx_%'
    """)
    indices = [row[0] for row in cursor.fetchall()]
    
    if indices:
        print_ok(f"{len(indices)} índices encontrados")
        for idx in indices:
            print_info(f"  {idx}")
    else:
        print_aviso("Nenhum índice personalizado encontrado")
    
    return True


def main():
    print("=" * 60)
    print(" VALIDAÇÃO DA MIGRAÇÃO")
    print(" Disciplinas, Níveis e Fontes")
    print("=" * 60)
    
    if not Path(DATABASE_PATH).exists():
        print(f"\n❌ Banco não encontrado: {DATABASE_PATH}")
        return 1
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    testes = [
        ("Disciplina", testar_tabela_disciplina),
        ("Tag com Disciplina", testar_tag_com_disciplina),
        ("Nível Escolar", testar_tabela_nivel_escolar),
        ("Questão-Nível", testar_tabela_questao_nivel),
        ("Fonte Questão", testar_tabela_fonte_questao),
        ("Tags Migradas", testar_tags_migradas),
        ("Relacionamentos", testar_relacionamentos),
        ("Índices", testar_indices),
    ]
    
    resultados = []
    for nome, func in testes:
        try:
            resultado = func(cursor)
            resultados.append((nome, resultado))
        except Exception as e:
            print_erro(f"Erro no teste {nome}: {e}")
            resultados.append((nome, False))
    
    conn.close()
    
    # Resumo
    print_header("RESUMO DOS TESTES")
    
    passou = 0
    falhou = 0
    
    for nome, resultado in resultados:
        if resultado:
            print_ok(f"{nome}: PASSOU")
            passou += 1
        else:
            print_erro(f"{nome}: FALHOU")
            falhou += 1
    
    print("\n" + "-" * 40)
    print(f"   Total: {passou + falhou} testes")
    print(f"   Passou: {passou}")
    print(f"   Falhou: {falhou}")
    
    if falhou == 0:
        print("\n🎉 MIGRAÇÃO BEM-SUCEDIDA!")
        return 0
    else:
        print("\n⚠️  Alguns testes falharam. Verifique os erros acima.")
        return 1


if __name__ == "__main__":
    exit(main())
```

### 11.2 Executar os Testes

```bash
python scripts/testar_migracao.py
```

---

## 12. CHECKLIST FINAL

### Preparação
- [ ] Backup do banco de dados criado
- [ ] Script `verificar_estrutura.py` executado
- [ ] Saída salva em `estrutura_antes.txt`

### Arquivos Criados
- [ ] `scripts/migrar_banco.py`
- [ ] `scripts/testar_migracao.py`
- [ ] `scripts/verificar_estrutura.py`
- [ ] `src/models/orm/disciplina.py`
- [ ] `src/models/orm/nivel_escolar.py`
- [ ] `src/models/orm/questao_nivel.py`
- [ ] `src/repositories/disciplina_repository.py`
- [ ] `src/repositories/nivel_escolar_repository.py`

### Arquivos Modificados
- [ ] `src/models/orm/__init__.py` (adicionar novos models)
- [ ] `src/models/orm/tag.py` (adicionar id_disciplina)
- [ ] `src/models/orm/fonte_questao.py` (novas colunas)
- [ ] `src/models/orm/questao.py` (relacionamento com nível)
- [ ] `src/repositories/tag_repository.py` (métodos por disciplina)

### Migração
- [ ] `python scripts/migrar_banco.py --dry-run` executado
- [ ] Resultado do dry-run verificado
- [ ] `python scripts/migrar_banco.py` executado
- [ ] `python scripts/testar_migracao.py` executado
- [ ] Todos os testes passaram

### Verificações Manuais
- [ ] Tabela `disciplina` criada com 12 disciplinas
- [ ] Tags de conteúdo associadas à disciplina Matemática
- [ ] Tags V* migradas para `fonte_questao`
- [ ] Tags N* migradas para `nivel_escolar` e `questao_nivel`
- [ ] Nenhuma tag V* ou N* restante na tabela `tag`

### Atualização das Views (se aplicável)
- [ ] Seletor de disciplina implementado
- [ ] Árvore de tags filtra por disciplina
- [ ] Painel de busca com filtros de disciplina, nível e fonte
- [ ] Formulário de questão atualizado

---

## TROUBLESHOOTING

### "table disciplina already exists"
**Causa:** A migração já foi executada antes.
**Solução:** O script usa `CREATE TABLE IF NOT EXISTS`, então isso é apenas um aviso.

### Tags não foram associadas à Matemática
**Causa:** A disciplina Matemática não foi encontrada.
**Solução:** Verifique se a disciplina com código 'MAT' existe:
```sql
SELECT * FROM disciplina WHERE codigo = 'MAT';
```

### Erro "no such column: id_disciplina"
**Causa:** A coluna não foi adicionada à tabela tag.
**Solução:** Execute manualmente:
```sql
ALTER TABLE tag ADD COLUMN id_disciplina INTEGER REFERENCES disciplina(id_disciplina);
```

### Tags V* ou N* não foram removidas
**Causa:** O mapeamento não encontrou correspondência.
**Solução:** Ajuste o dicionário `MAPEAMENTO_NIVEIS` no script de migração conforme os nomes das suas tags.

### Como restaurar o backup
Se algo der errado:
```bash
# Encontre o backup mais recente
ls -la database/backups/

# Restaure
cp database/backups/backup_pre_migracao_XXXXXX.db database/mathbank.db
```

---

## DIAGRAMA FINAL DA ESTRUTURA

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ESTRUTURA FINAL DO BANCO                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                          ┌──────────────┐                                    │
│                          │  disciplina  │                                    │
│                          │──────────────│                                    │
│                          │ id_disciplina│                                    │
│                          │ codigo       │ (MAT, FIS, QUI...)                 │
│                          │ nome         │                                    │
│                          │ cor          │                                    │
│                          └──────┬───────┘                                    │
│                                 │ 1:N                                        │
│                                 ▼                                            │
│  ┌──────────────┐         ┌──────────────┐         ┌──────────────┐         │
│  │   questao    │◄──N:N──►│     tag      │         │nivel_escolar │         │
│  │──────────────│         │──────────────│         │──────────────│         │
│  │ id_questao   │         │ id_tag       │         │ id_nivel     │         │
│  │ id_fonte     │         │ id_disciplina│◄────────│ codigo       │         │
│  │ enunciado    │         │ numeracao    │         │ nome         │         │
│  │ ...          │         │ nome         │         └──────┬───────┘         │
│  └──────┬───────┘         └──────────────┘                │                  │
│         │                                                  │                  │
│         │ N:1                              N:N             │                  │
│         │              ┌──────────────┐◄───────────────────┘                  │
│         │              │questao_nivel │                                       │
│         │              │──────────────│                                       │
│         │              │ id_questao   │                                       │
│         │              │ id_nivel     │                                       │
│         ▼              └──────────────┘                                       │
│  ┌──────────────┐                                                            │
│  │fonte_questao │                                                            │
│  │──────────────│                                                            │
│  │ id_fonte     │                                                            │
│  │ sigla        │ (ENEM, FUVEST...)                                          │
│  │ nome_completo│                                                            │
│  │ tipo         │ (VESTIBULAR, OLIMPIADA...)                                 │
│  │ estado       │                                                            │
│  └──────────────┘                                                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## RESUMO DAS MUDANÇAS

| Tabela | Ação | Descrição |
|--------|------|-----------|
| `disciplina` | **CRIADA** | Nova tabela para disciplinas |
| `tag` | **MODIFICADA** | Adicionada coluna `id_disciplina` |
| `nivel_escolar` | **CRIADA** | Nova tabela para níveis escolares |
| `questao_nivel` | **CRIADA** | Relacionamento N:N questão-nível |
| `fonte_questao` | **EXPANDIDA** | Novas colunas (tipo, estado, ano) |
| Tags V* | **MIGRADAS** | Movidas para `fonte_questao` |
| Tags N* | **MIGRADAS** | Movidas para `nivel_escolar` |

---

*Documento atualizado para incluir tabela de Disciplinas*
*Plano 1: Refatoração do Banco de Dados - Disciplinas, Níveis e Fontes*
