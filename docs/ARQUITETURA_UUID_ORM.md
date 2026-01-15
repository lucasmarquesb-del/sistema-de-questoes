claud# 🏗️ NOVA ARQUITETURA - UUID + ORM + NORMALIZAÇÃO

**Data:** 2026-01-13
**Versão:** 2.0.0
**Status:** Em Planejamento

---

## 📋 OBJETIVOS

1. ✅ **UUID** - Substituir INTEGER AUTO_INCREMENT por UUID em todos os IDs
2. ✅ **SQLAlchemy ORM** - Migrar de SQL raw para ORM completo
3. ✅ **Normalização** - Separar dados em tabelas específicas
4. ✅ **Busca por Nome** - Usuário nunca interage diretamente com IDs/UUIDs
5. ✅ **Tabela Centralizada de Imagens** - Evitar duplicação, usar hash MD5
6. ✅ **Redução de Logging** - Apenas logs essenciais

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
├── imagem_enunciado (VARCHAR - CAMINHO DO ARQUIVO)    # ❌ Duplicação possível
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
├── imagem (VARCHAR - CAMINHO DO ARQUIVO)              # ❌ Duplicação possível
├── escala_imagem
└── correta (BOOLEAN)

# ⚠️ PROBLEMA: Mesma imagem pode ser salva várias vezes
# ⚠️ PROBLEMA: Sem controle de duplicatas
# ⚠️ PROBLEMA: Dificulta backup e gerenciamento
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
├── uuid_imagem_enunciado (TEXT FK NULL) # FK para imagem
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
└── nome (VARCHAR)                     # 'Questão Objetiva', 'Questão Discursiva'
```

#### 🔑 Tabela: fonte_questao (NOVA)
```
fonte_questao
├── uuid (TEXT PRIMARY KEY)
├── sigla (VARCHAR UNIQUE)             # 'ENEM', 'FUVEST', 'AUTORAL'
├── nome_completo (VARCHAR)            # 'Exame Nacional do Ensino Médio'
├── tipo_instituicao (VARCHAR)         # 'VESTIBULAR', 'CONCURSO', 'AUTORAL'
└── data_criacao (DATETIME)
```

#### 🔑 Tabela: ano_referencia (NOVA)
```
ano_referencia
├── uuid (TEXT PRIMARY KEY)
├── ano (INTEGER UNIQUE)               # 2024, 2025, etc.
├── descricao (VARCHAR)                # '2024', '2025'
└── ativo (BOOLEAN)
```

#### 🔑 Tabela: resposta_questao (NOVA - Unificada)
```
resposta_questao
├── uuid (TEXT PRIMARY KEY)
├── uuid_questao (TEXT UNIQUE FK)      # FK para questao (1:1)
├── uuid_alternativa_correta (TEXT FK NULL) # FK para alternativa (apenas objetivas)
├── gabarito_discursivo (TEXT NULL)    # Gabarito LaTeX (apenas discursivas)
├── resolucao (TEXT)                   # Resolução detalhada em LaTeX
├── justificativa (TEXT)               # Explicação/critérios de avaliação
├── autor_resolucao (VARCHAR)          # Autor da resolução
└── data_criacao (DATETIME)
```

#### 🔑 Tabela: alternativa
```
alternativa
├── uuid (TEXT PRIMARY KEY)
├── uuid_questao (TEXT FK)
├── letra (CHAR)                       # A, B, C, D, E
├── ordem (INTEGER)                    # 1, 2, 3, 4, 5 (para randomização)
├── texto (TEXT)
├── uuid_imagem (TEXT FK NULL)         # FK para imagem
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
└── codigo (VARCHAR UNIQUE)            # 'FACIL', 'MEDIO', 'DIFICIL'
```

#### 🔑 Tabela: imagem (NOVA - Centralizada)
```
imagem
├── uuid (TEXT PRIMARY KEY)
├── nome_arquivo (VARCHAR UNIQUE)      # Nome único do arquivo
├── caminho_relativo (VARCHAR)         # Caminho relativo no sistema
├── hash_md5 (VARCHAR UNIQUE)          # Hash MD5 para detectar duplicatas
├── tamanho_bytes (INTEGER)            # Tamanho do arquivo em bytes
├── largura (INTEGER)                  # Largura em pixels
├── altura (INTEGER)                   # Altura em pixels
├── formato (VARCHAR)                  # 'PNG', 'JPG', 'SVG', etc.
├── mime_type (VARCHAR)                # 'image/png', 'image/jpeg', etc.
├── data_upload (DATETIME)
└── ativo (BOOLEAN)

# Vantagens:
# - Evita duplicação de imagens (mesmo arquivo usado em múltiplas questões)
# - Controle centralizado de imagens
# - Facilita backup e migração
# - Permite análise de uso (quantas questões usam cada imagem)
# - Otimização de armazenamento via hash MD5
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
├── data_criacao (DATETIME)
└── data_modificacao (DATETIME)

# Relacionamento N:N com ordem customizada
# As questões são gerenciadas via lista_questao
# Busca por tags: JOIN lista_questao -> questao -> questao_tag -> tag
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
├── ordem_na_lista (INTEGER)           # Ordem customizada para cada lista
└── data_adicao (DATETIME)

# Este relacionamento permite:
# - Manipular ordem das questões em cada lista
# - Buscar listas por questões
# - Buscar tags relacionadas: lista -> questoes -> questao_tag -> tags

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

# Busca de listas
lista = buscar_lista_por_codigo("LST-2026-0001")
listas = buscar_lista_por_titulo("Simulado ENEM")

# Buscar questões de uma lista (com ordem)
questoes_ordenadas = buscar_questoes_da_lista("LST-2026-0001")

# Buscar tags relacionadas a uma lista (via suas questões)
tags_da_lista = buscar_tags_da_lista("LST-2026-0001")

# Manipular ordem de questões em uma lista
reordenar_questoes_lista("LST-2026-0001", ["Q-2026-0003", "Q-2026-0001", "Q-2026-0002"])

# Upload e gerenciamento de imagens
imagem = upload_imagem("caminho/para/imagem.png")
# Retorna: {"uuid": "...", "hash_md5": "...", "nome_arquivo": "..."}

# Verificar se imagem já existe (por hash MD5)
imagem_existente = buscar_imagem_por_hash("d41d8cd98f00b204e9800998ecf8427e")

# Usar imagem em questão
criar_questao(
    titulo="Nova Questão",
    enunciado="...",
    uuid_imagem_enunciado=imagem.uuid,  # Reutiliza imagem existente
    escala_imagem_enunciado=1.0
)

# Buscar questões que usam determinada imagem
questoes_usando_imagem = buscar_questoes_por_imagem(imagem.uuid)

# Remover imagem (apenas se não estiver em uso)
remover_imagem(imagem.uuid)  # Valida se não há FK antes de deletar
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
    resposta = relationship("RespostaQuestao", back_populates="questao", uselist=False)

    # Métodos de busca por nome
    @classmethod
    def buscar_por_codigo(cls, session, codigo: str):
        return session.query(cls).filter_by(codigo=codigo, ativo=True).first()

    @classmethod
    def buscar_por_titulo(cls, session, titulo: str):
        return session.query(cls).filter(cls.titulo.ilike(f"%{titulo}%"), cls.ativo == True).all()
```

### Exemplo: Model Lista
```python
class Lista(BaseModel):
    __tablename__ = 'lista'

    codigo = Column(String(20), unique=True, nullable=False, index=True)
    titulo = Column(String(200), nullable=False, index=True)
    tipo = Column(String(50), nullable=False)
    cabecalho = Column(Text)
    instrucoes = Column(Text)
    data_modificacao = Column(DateTime, onupdate=datetime.utcnow)

    # Relationship com questões (via tabela associativa)
    questoes = relationship("Questao", secondary="lista_questao",
                           back_populates="listas",
                           order_by="ListaQuestao.ordem_na_lista")

    @classmethod
    def buscar_por_codigo(cls, session, codigo: str):
        return session.query(cls).filter_by(codigo=codigo, ativo=True).first()

    @classmethod
    def buscar_tags_relacionadas(cls, session, codigo_lista: str):
        """Busca todas as tags das questões desta lista"""
        lista = cls.buscar_por_codigo(session, codigo_lista)
        if not lista:
            return []

        tags = set()
        for questao in lista.questoes:
            tags.update(questao.tags)
        return list(tags)

    def reordenar_questoes(self, session, codigos_questoes_ordenados: list):
        """Reordena questões da lista baseado em códigos"""
        # Implementação via ListaQuestao
        pass
```

### Exemplo: Model Imagem
```python
import hashlib
from PIL import Image as PILImage

class Imagem(BaseModel):
    __tablename__ = 'imagem'

    nome_arquivo = Column(String(255), unique=True, nullable=False)
    caminho_relativo = Column(String(500), nullable=False)
    hash_md5 = Column(String(32), unique=True, nullable=False, index=True)
    tamanho_bytes = Column(Integer, nullable=False)
    largura = Column(Integer, nullable=False)
    altura = Column(Integer, nullable=False)
    formato = Column(String(10), nullable=False)
    mime_type = Column(String(50), nullable=False)
    data_upload = Column(DateTime, default=datetime.utcnow, nullable=False)

    @classmethod
    def calcular_hash_md5(cls, caminho_arquivo: str) -> str:
        """Calcula hash MD5 do arquivo para detectar duplicatas"""
        hash_md5 = hashlib.md5()
        with open(caminho_arquivo, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    @classmethod
    def buscar_por_hash(cls, session, hash_md5: str):
        """Busca imagem pelo hash MD5 (detecta duplicatas)"""
        return session.query(cls).filter_by(hash_md5=hash_md5, ativo=True).first()

    @classmethod
    def criar_de_arquivo(cls, session, caminho_arquivo: str, nome_arquivo: str = None):
        """Cria registro de imagem a partir de arquivo físico"""
        # Calcular hash
        hash_md5 = cls.calcular_hash_md5(caminho_arquivo)

        # Verificar se já existe
        imagem_existente = cls.buscar_por_hash(session, hash_md5)
        if imagem_existente:
            return imagem_existente

        # Obter metadados da imagem
        with PILImage.open(caminho_arquivo) as img:
            largura, altura = img.size
            formato = img.format

        # Criar novo registro
        import os
        tamanho_bytes = os.path.getsize(caminho_arquivo)
        mime_type = f"image/{formato.lower()}"

        nova_imagem = cls(
            nome_arquivo=nome_arquivo or os.path.basename(caminho_arquivo),
            caminho_relativo=caminho_arquivo,
            hash_md5=hash_md5,
            tamanho_bytes=tamanho_bytes,
            largura=largura,
            altura=altura,
            formato=formato,
            mime_type=mime_type
        )

        session.add(nova_imagem)
        return nova_imagem

    def esta_em_uso(self, session) -> bool:
        """Verifica se a imagem está sendo usada em questões ou alternativas"""
        from sqlalchemy import or_
        questoes_count = session.query(Questao).filter(
            Questao.uuid_imagem_enunciado == self.uuid
        ).count()

        alternativas_count = session.query(Alternativa).filter(
            Alternativa.uuid_imagem == self.uuid
        ).count()

        return (questoes_count + alternativas_count) > 0
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
   - ✅ Migrar imagens para tabela centralizada (com hash MD5 para deduplicação)

3. **Migração de Questões**
   - ✅ Extrair anos únicos → tabela ano_referencia
   - ✅ Extrair fontes únicas → tabela fonte_questao
   - ✅ Criar tipos: OBJETIVA, DISCURSIVA
   - ✅ Migrar questões com UUIDs
   - ✅ Gerar códigos Q-AAAA-NNNN

4. **Migração de Respostas**
   - ✅ Unificar em resposta_questao
   - ✅ Alternativas → uuid_alternativa_correta (objetivas)
   - ✅ Gabarito discursivo → gabarito_discursivo (discursivas)
   - ✅ Resolução → resolucao (ambas)

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

### Fase 1: ORM e Models (PRIORIDADE MÁXIMA) ✅ CONCLUÍDA
- [x] Instalar SQLAlchemy
- [x] Criar Base Model com UUID
- [x] Criar todos os models ORM
- [x] Criar gerador de códigos
- [x] Criar script de criação do novo schema

### Fase 2: Migração de Dados ✅ SCRIPTS PRONTOS
- [x] Script de backup
- [x] Script de migração completo
- [ ] Executar migração em ambiente de teste
- [ ] Testes de validação
- [ ] Rollback plan

### Fase 3: Repositories (Substituir Models) ✅ CONCLUÍDA
- [x] QuestaoRepository com ORM
- [x] RespostaQuestaoRepository (unificado)
- [x] AlternativaRepository
- [x] TagRepository
- [x] ListaRepository (com métodos de ordenação e busca de tags)
- [x] DificuldadeRepository
- [x] ImagemRepository (com deduplicação por hash MD5)
- [x] FonteQuestaoRepository
- [x] AnoReferenciaRepository
- [x] TipoQuestaoRepository
- [x] BaseRepository (classe base com operações CRUD genéricas)

### Fase 4: Services e Controllers 🚧 EM ANDAMENTO
- [x] SessionManager para gerenciar sessões SQLAlchemy
- [x] Adapters de compatibilidade (QuestaoAdapter)
- [x] Documentação de migração (docs/MIGRACAO_ORM.md)
- [ ] Atualizar serviços para usar repos ORM
- [ ] Atualizar controllers
- [ ] Busca por nome/código (nunca UUID)

### Fase 5: Views ⏳ PENDENTE
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

### Tabela Centralizada de Imagens
- ✅ Elimina duplicação de arquivos (hash MD5)
- ✅ Reduz drasticamente o tamanho do banco
- ✅ Mesma imagem reutilizada em múltiplas questões/alternativas
- ✅ Controle de uso (saber quais questões usam cada imagem)
- ✅ Facilita backup (apenas imagens ativas)
- ✅ Metadados centralizados (dimensões, formato, tamanho)
- ✅ Migração e gerenciamento simplificados

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
