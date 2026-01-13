# 🏗️ NOVA ARQUITETURA - UUID + ORM + NORMALIZAÇÃO

**Data:** 2026-01-13
**Versão:** 2.0.0
**Status:** Em Planejamento

---

## 📋 OBJETIVOS

1. ✅ **UUID** - Substituir INTEGER AUTO_INCREMENT por UUID em todos os IDs
2. ✅ **SQLAlchemy ORM** - Migrar de SQL raw para ORM completo
3. ✅ **Normalização** - Separar dados em tabelas específicas
4. ✅ **Busca por Nome** - Usuário nunca interage diretamente com IDs/UUIDs
5. ✅ **Redução de Logging** - Apenas logs essenciais

---

## 🗄️ ESTRUTURA ATUAL vs NOVA

### ATUAL (Versão 1.x)
```
questao
├── id_questao (INTEGER)
├── titulo
├── enunciado
├── tipo (VARCHAR - 'OBJETIVA'/'DISCURSIVA')
├── ano (INTEGER)
├── fonte (VARCHAR)
├── id_dificuldade (INTEGER FK)
├── imagem_enunciado
├── escala_imagem_enunciado
├── resolucao
├── gabarito_discursiva
├── observacoes
└── ativo

alternativa
├── id_alternativa (INTEGER)
├── id_questao (INTEGER FK)
├── letra (A-E)
├── texto
├── imagem
├── escala_imagem
└── correta (BOOLEAN)
```

### NOVA (Versão 2.0)

#### 🔑 Tabela: questao
```
questao
├── uuid (TEXT PRIMARY KEY)           # UUID v4
├── codigo (VARCHAR UNIQUE)            # Código legível: "Q-2026-0001"
├── titulo (VARCHAR)                   # Título para busca e exibição
├── enunciado (TEXT)                   # LaTeX
├── uuid_tipo_questao (TEXT FK)        # FK para tipo_questao
├── uuid_fonte (TEXT FK)               # FK para fonte_questao
├── uuid_ano_referencia (TEXT FK)      # FK para ano_referencia
├── uuid_dificuldade (TEXT FK)         # FK para dificuldade
├── imagem_enunciado (VARCHAR)
├── escala_imagem_enunciado (DECIMAL)
├── observacoes (TEXT)
├── data_criacao (DATETIME)
├── data_modificacao (DATETIME)
└── ativo (BOOLEAN)
```

#### 🔑 Tabela: tipo_questao (NOVA)
```
tipo_questao
├── uuid (TEXT PRIMARY KEY)
├── codigo (VARCHAR UNIQUE)            # 'OBJETIVA', 'DISCURSIVA'
├── nome (VARCHAR)                     # 'Questão Objetiva', 'Questão Discursiva'
├── descricao (TEXT)
└── ativo (BOOLEAN)
```

#### 🔑 Tabela: fonte_questao (NOVA)
```
fonte_questao
├── uuid (TEXT PRIMARY KEY)
├── sigla (VARCHAR UNIQUE)             # 'ENEM', 'FUVEST', 'AUTORAL'
├── nome_completo (VARCHAR)            # 'Exame Nacional do Ensino Médio'
├── tipo_instituicao (VARCHAR)         # 'VESTIBULAR', 'CONCURSO', 'AUTORAL'
├── ativo (BOOLEAN)
└── data_criacao (DATETIME)
```

#### 🔑 Tabela: ano_referencia (NOVA)
```
ano_referencia
├── uuid (TEXT PRIMARY KEY)
├── ano (INTEGER UNIQUE)               # 2024, 2025, etc.
├── semestre (INTEGER NULL)            # 1, 2 (NULL se não aplicável)
├── descricao (VARCHAR)                # '2024 - 1º Semestre', '2025'
└── ativo (BOOLEAN)
```

#### 🔑 Tabela: resposta_objetiva (NOVA - Separada)
```
resposta_objetiva
├── uuid (TEXT PRIMARY KEY)
├── uuid_questao (TEXT UNIQUE FK)      # FK para questao
├── uuid_alternativa_correta (TEXT FK) # FK para alternativa
├── justificativa (TEXT)               # Explicação da resposta correta
└── data_criacao (DATETIME)
```

#### 🔑 Tabela: resposta_discursiva (NOVA - Separada)
```
resposta_discursiva
├── uuid (TEXT PRIMARY KEY)
├── uuid_questao (TEXT UNIQUE FK)      # FK para questao
├── gabarito (TEXT)                    # LaTeX
├── criterios_avaliacao (TEXT)
└── data_criacao (DATETIME)
```

#### 🔑 Tabela: resolucao_questao (NOVA - Separada)
```
resolucao_questao
├── uuid (TEXT PRIMARY KEY)
├── uuid_questao (TEXT FK)             # FK para questao
├── numero_versao (INTEGER)            # Múltiplas resoluções possíveis
├── conteudo (TEXT)                    # LaTeX
├── autor (VARCHAR)
├── data_criacao (DATETIME)
└── principal (BOOLEAN)                # Resolução principal/oficial
```

#### 🔑 Tabela: alternativa
```
alternativa
├── uuid (TEXT PRIMARY KEY)
├── uuid_questao (TEXT FK)
├── letra (CHAR)                       # A, B, C, D, E
├── ordem (INTEGER)                    # 1, 2, 3, 4, 5 (para randomização)
├── texto (TEXT)
├── imagem (VARCHAR)
├── escala_imagem (DECIMAL)
└── data_criacao (DATETIME)
```

#### 🔑 Tabela: tag
```
tag
├── uuid (TEXT PRIMARY KEY)
├── nome (VARCHAR UNIQUE)              # Nome para busca do usuário
├── numeracao (VARCHAR UNIQUE)
├── nivel (INTEGER)
├── uuid_tag_pai (TEXT FK)             # Self-reference
├── ativo (BOOLEAN)
└── ordem (INTEGER)
```

#### 🔑 Tabela: dificuldade
```
dificuldade
├── uuid (TEXT PRIMARY KEY)
├── codigo (VARCHAR UNIQUE)            # 'FACIL', 'MEDIO', 'DIFICIL'
├── nome (VARCHAR)                     # 'Fácil', 'Médio', 'Difícil'
├── descricao (TEXT)
└── ordem (INTEGER)
```

#### 🔑 Tabela: lista
```
lista
├── uuid (TEXT PRIMARY KEY)
├── codigo (VARCHAR UNIQUE)            # 'LST-2026-0001'
├── titulo (VARCHAR)                   # Nome para busca
├── tipo (VARCHAR)                     # 'PROVA', 'LISTA', 'SIMULADO'
├── cabecalho (TEXT)
├── instrucoes (TEXT)
└── data_criacao (DATETIME)
```

---

## 🔄 RELACIONAMENTOS (Permanecidos com UUID)

```
questao_tag
├── uuid_questao (TEXT FK)
├── uuid_tag (TEXT FK)
└── data_associacao (DATETIME)

lista_questao
├── uuid_lista (TEXT FK)
├── uuid_questao (TEXT FK)
├── ordem_na_lista (INTEGER)           # NOVO: ordem customizada
└── data_adicao (DATETIME)

questao_versao
├── uuid_questao_original (TEXT FK)
├── uuid_questao_versao (TEXT FK)
├── observacao (TEXT)
└── data_vinculo (DATETIME)
```

---

## 🎯 MUDANÇAS NO COMPORTAMENTO

### Antes (com ID numérico)
```python
# Criar questão
id_questao = criar_questao(dados)  # Retorna: 123

# Buscar questão
questao = buscar_por_id(123)

# Exibir para usuário
print(f"Questão ID: {questao['id_questao']}")
```

### Depois (com UUID e Código)
```python
# Criar questão
resultado = criar_questao(dados)
# Retorna: {"uuid": "550e8400-e29b-41d4-a716-446655440000", "codigo": "Q-2026-0001"}

# Buscar questão (USUÁRIO USA CÓDIGO OU TÍTULO)
questao = buscar_por_codigo("Q-2026-0001")
questao = buscar_por_titulo("Função Quadrática")

# Exibir para usuário (NUNCA MOSTRAR UUID)
print(f"Questão: {questao['codigo']} - {questao['titulo']}")
```

### Exemplos de Busca

```python
# Busca por fonte
questoes = buscar_por_fonte("ENEM")        # Não buscar_por_fonte_uuid(...)

# Busca por ano
questoes = buscar_por_ano(2024)            # Ano direto, não UUID

# Busca por tag
questoes = buscar_por_tag("FUNÇÃO AFIM")   # Nome da tag, não UUID

# Busca por dificuldade
questoes = buscar_por_dificuldade("Médio") # Nome, não UUID

# Busca combinada
questoes = buscar_questoes(
    fonte="FUVEST",
    ano=2024,
    tags=["ÁLGEBRA", "FUNÇÃO QUADRÁTICA"],
    dificuldade="Difícil",
    tipo="OBJETIVA"
)
```

---

## 🏗️ ESTRUTURA SQLAlchemy

### Base Model
```python
from sqlalchemy import Column, Text, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True

    uuid = Column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    data_criacao = Column(DateTime, default=datetime.utcnow, nullable=False)
    ativo = Column(Boolean, default=True, nullable=False)
```

### Exemplo: Model Questao
```python
class Questao(BaseModel):
    __tablename__ = 'questao'

    codigo = Column(String(20), unique=True, nullable=False, index=True)
    titulo = Column(String(200), nullable=True, index=True)
    enunciado = Column(Text, nullable=False)

    # Relacionamentos
    uuid_tipo_questao = Column(Text, ForeignKey('tipo_questao.uuid'))
    uuid_fonte = Column(Text, ForeignKey('fonte_questao.uuid'))
    uuid_ano_referencia = Column(Text, ForeignKey('ano_referencia.uuid'))
    uuid_dificuldade = Column(Text, ForeignKey('dificuldade.uuid'))

    # Relationships
    tipo = relationship("TipoQuestao", back_populates="questoes")
    fonte = relationship("FonteQuestao", back_populates="questoes")
    ano = relationship("AnoReferencia", back_populates="questoes")
    dificuldade = relationship("Dificuldade", back_populates="questoes")
    alternativas = relationship("Alternativa", back_populates="questao", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary="questao_tag", back_populates="questoes")

    # Métodos de busca por nome
    @classmethod
    def buscar_por_codigo(cls, session, codigo: str):
        return session.query(cls).filter_by(codigo=codigo, ativo=True).first()

    @classmethod
    def buscar_por_titulo(cls, session, titulo: str):
        return session.query(cls).filter(cls.titulo.ilike(f"%{titulo}%"), cls.ativo == True).all()
```

---

## 📊 GERAÇÃO DE CÓDIGOS LEGÍVEIS

### Padrão de Códigos

```python
# Questões
Q-{ANO}-{SEQUENCIAL:04d}          # Q-2026-0001, Q-2026-0002

# Listas
LST-{ANO}-{SEQUENCIAL:04d}        # LST-2026-0001

# Tags (já tem numeracao: '2.1.3')
# Usa numeracao existente

# Fontes
{SIGLA}                           # ENEM, FUVEST, AUTORAL

# Anos
{ANO}                             # 2024, 2025

# Dificuldades
{CODIGO}                          # FACIL, MEDIO, DIFICIL
```

### Gerador de Códigos
```python
class CodigoGenerator:
    @staticmethod
    def gerar_codigo_questao(session, ano: int = None) -> str:
        if not ano:
            ano = datetime.now().year

        # Buscar último código do ano
        ultimo = session.query(Questao)\
            .filter(Questao.codigo.like(f"Q-{ano}-%"))\
            .order_by(Questao.codigo.desc())\
            .first()

        if ultimo:
            seq = int(ultimo.codigo.split('-')[-1]) + 1
        else:
            seq = 1

        return f"Q-{ano}-{seq:04d}"
```

---

## 🔄 MIGRAÇÃO DE DADOS

### Script de Migração

```python
import sqlite3
import uuid
from datetime import datetime

def migrar_v1_para_v2():
    # 1. Backup do banco antigo
    # 2. Criar novo schema com UUID
    # 3. Migrar dados mantendo relacionamentos
    # 4. Gerar códigos legíveis
    # 5. Validar integridade
    pass
```

### Etapas da Migração

1. **Preparação**
   - ✅ Backup completo do banco atual
   - ✅ Criar novo banco com schema UUID
   - ✅ Mapear IDs antigos → UUIDs novos

2. **Migração de Dados Base**
   - ✅ Dificuldade (3 registros)
   - ✅ Tags (hierarquia completa)
   - ✅ Criar tabelas novas (tipo_questao, fonte_questao, ano_referencia)

3. **Migração de Questões**
   - ✅ Extrair anos únicos → tabela ano_referencia
   - ✅ Extrair fontes únicas → tabela fonte_questao
   - ✅ Criar tipos: OBJETIVA, DISCURSIVA
   - ✅ Migrar questões com UUIDs
   - ✅ Gerar códigos Q-AAAA-NNNN

4. **Migração de Respostas**
   - ✅ Alternativas → resposta_objetiva
   - ✅ Gabarito discursivo → resposta_discursiva
   - ✅ Resolução → resolucao_questao

5. **Migração de Relacionamentos**
   - ✅ questao_tag
   - ✅ lista_questao
   - ✅ questao_versao

6. **Validação**
   - ✅ Conferir contadores
   - ✅ Validar FKs
   - ✅ Testar buscas

---

## 🛠️ IMPLEMENTAÇÃO

### Fase 1: ORM e Models (PRIORIDADE MÁXIMA)
- [ ] Instalar SQLAlchemy
- [ ] Criar Base Model com UUID
- [ ] Criar todos os models ORM
- [ ] Criar gerador de códigos
- [ ] Criar script de criação do novo schema

### Fase 2: Migração de Dados
- [ ] Script de backup
- [ ] Script de migração completo
- [ ] Testes de validação
- [ ] Rollback plan

### Fase 3: Repositories (Substituir Models)
- [ ] QuestaoRepository com ORM
- [ ] AlternativaRepository
- [ ] TagRepository
- [ ] ListaRepository
- [ ] DificuldadeRepository

### Fase 4: Services e Controllers
- [ ] Atualizar serviços para usar repos ORM
- [ ] Atualizar controllers
- [ ] Busca por nome/código (nunca UUID)

### Fase 5: Views
- [ ] Atualizar forms (exibir códigos, não UUIDs)
- [ ] Atualizar listas e tabelas
- [ ] Busca autocomplete por nome

### Fase 6: Logging
- [ ] Reduzir logs desnecessários
- [ ] Manter apenas logs de erro e operações críticas

---

## ✅ VANTAGENS DA NOVA ARQUITETURA

### UUID
- ✅ IDs únicos globalmente
- ✅ Sem colisão entre ambientes (dev, prod)
- ✅ Segurança (não sequencial)
- ✅ Distribuição/replicação facilitada

### Normalização
- ✅ Dados não duplicados (ano, fonte)
- ✅ Facilidade para adicionar atributos (ex: site da fonte)
- ✅ Consistência garantida
- ✅ Queries mais eficientes

### Busca por Nome
- ✅ UX melhorada (usuário não vê UUIDs)
- ✅ Códigos legíveis (Q-2026-0001)
- ✅ Busca natural (por título, tag, fonte)

### ORM
- ✅ Menos SQL raw
- ✅ Migrations automáticas (Alembic)
- ✅ Relacionamentos explícitos
- ✅ Type safety
- ✅ Menos vulnerável a SQL Injection

---

## 🎓 COMPATIBILIDADE

### Durante a Transição
- Manter banco antigo como backup
- Sistema novo com dados migrados
- Possibilidade de rollback

### Após Migração
- Remover código legacy após 100% testado
- Documentar breaking changes
- Atualizar documentação de API

---

## 📝 PRÓXIMOS PASSOS

1. ✅ Aprovar este documento de arquitetura
2. ⏳ Criar models SQLAlchemy
3. ⏳ Criar script de migração
4. ⏳ Executar migração em ambiente de teste
5. ⏳ Atualizar repositories
6. ⏳ Atualizar controllers e views
7. ⏳ Testes completos
8. ⏳ Deploy em produção

---

**Fim do Documento**
