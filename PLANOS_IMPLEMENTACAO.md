# Planos de Implementação

Este documento contém três planos de implementação independentes para evolução do sistema.

---

## PLANO 1: Refatoração do Banco de Dados - Separação de Níveis e Fontes

### 1.1 Problema Atual

Atualmente, a tabela `tag` mistura três conceitos diferentes:
- **Tags de Conteúdo**: Taxonomia matemática (1=Números, 2=Álgebra, etc.)
- **Tags de Vestibular**: Fontes de questões (V1=ENEM, V2=FUVEST, V3=UNICAMP...)
- **Tags de Nível Escolar**: Escolaridade (N1=E.F.2, N2=E.M., N3=E.J.A.)

Isso causa:
- Confusão semântica (tags de vestibular não são categorias de conteúdo)
- Dificuldade em filtros específicos
- Relacionamento incorreto (vestibular deveria relacionar com `fonte` da questão)

### 1.2 Solução Proposta

Separar em três estruturas distintas:

```
┌─────────────────────────────────────────────────────────────────┐
│                        ESTRUTURA ATUAL                          │
├─────────────────────────────────────────────────────────────────┤
│ tag                                                             │
│   ├── 1=Números, 2=Álgebra... (conteúdo)                       │
│   ├── V1=ENEM, V2=FUVEST... (vestibular) ← PROBLEMA            │
│   └── N1=E.F.2, N2=E.M... (nível) ← PROBLEMA                   │
└─────────────────────────────────────────────────────────────────┘

                              ↓

┌─────────────────────────────────────────────────────────────────┐
│                       ESTRUTURA NOVA                            │
├─────────────────────────────────────────────────────────────────┤
│ tag (apenas conteúdo matemático)                                │
│   └── 1=Números, 2=Álgebra, 2.1=Funções...                     │
│                                                                 │
│ nivel_escolar (nova tabela)                                     │
│   └── EF2, EM, EJA, SUPERIOR                                   │
│                                                                 │
│ fonte_questao (já existe, expandir)                             │
│   └── ENEM, FUVEST, UNICAMP, AUTORAL...                        │
│   └── + campos: ano_inicio, ano_fim, tipo_instituicao          │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 Mudanças no Schema

#### Nova Tabela: `nivel_escolar`
```sql
CREATE TABLE IF NOT EXISTS nivel_escolar (
    id_nivel INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo VARCHAR(10) NOT NULL UNIQUE,     -- EF2, EM, EJA, SUP
    nome VARCHAR(100) NOT NULL,             -- Ensino Fundamental 2
    descricao TEXT,
    ordem INTEGER NOT NULL,
    ativo BOOLEAN NOT NULL DEFAULT 1
);

-- Dados iniciais
INSERT INTO nivel_escolar (codigo, nome, ordem) VALUES
('EF1', 'Ensino Fundamental I', 1),
('EF2', 'Ensino Fundamental II', 2),
('EM', 'Ensino Médio', 3),
('EJA', 'Educação de Jovens e Adultos', 4),
('TEC', 'Ensino Técnico', 5),
('SUP', 'Ensino Superior', 6);
```

#### Relacionamento N:N: `questao_nivel`
```sql
CREATE TABLE IF NOT EXISTS questao_nivel (
    id_questao INTEGER NOT NULL,
    id_nivel INTEGER NOT NULL,
    PRIMARY KEY (id_questao, id_nivel),
    FOREIGN KEY (id_questao) REFERENCES questao(id_questao) ON DELETE CASCADE,
    FOREIGN KEY (id_nivel) REFERENCES nivel_escolar(id_nivel) ON DELETE CASCADE
);
```

#### Expandir Tabela: `fonte_questao`
```sql
-- Adicionar colunas (se não existirem)
ALTER TABLE fonte_questao ADD COLUMN tipo_instituicao VARCHAR(50);
-- Tipos: VESTIBULAR, CONCURSO, OLIMPIADA, AUTORAL, DIDATICO

ALTER TABLE fonte_questao ADD COLUMN estado VARCHAR(2);  -- SP, RJ, etc.
ALTER TABLE fonte_questao ADD COLUMN ano_inicio INTEGER; -- Primeiro ano conhecido
ALTER TABLE fonte_questao ADD COLUMN ano_fim INTEGER;    -- Último ano (NULL se ainda ativo)
ALTER TABLE fonte_questao ADD COLUMN url_oficial VARCHAR(500);
```

### 1.4 Migração de Dados

```sql
-- 1. Migrar tags V* para fonte_questao
INSERT INTO fonte_questao (sigla, nome_completo, tipo_instituicao)
SELECT
    REPLACE(numeracao, 'V', '') || '_' || nome,
    nome,
    'VESTIBULAR'
FROM tag
WHERE numeracao LIKE 'V%';

-- 2. Migrar tags N* para nivel_escolar (já inseridos acima)
-- 3. Remover tags V* e N* da tabela tag
DELETE FROM tag WHERE numeracao LIKE 'V%' OR numeracao LIKE 'N%';

-- 4. Atualizar questões que usavam tags de vestibular
-- (criar script de migração separado)
```

### 1.5 Arquivos a Modificar

| Arquivo | Mudança |
|---------|---------|
| `database/init_db.sql` | Adicionar novas tabelas, remover tags V/N |
| `src/models/orm/nivel_escolar.py` | **NOVO** - Model ORM |
| `src/models/orm/fonte_questao.py` | Expandir campos |
| `src/models/orm/questao.py` | Adicionar relacionamento com nivel_escolar |
| `src/models/orm/__init__.py` | Exportar novo model |
| `src/repositories/nivel_escolar_repository.py` | **NOVO** |
| `src/repositories/fonte_questao_repository.py` | Expandir métodos |
| `src/views/components/forms/tag_tree.py` | Remover tags V/N da exibição |
| `src/views/search_panel.py` | Adicionar filtro de nível escolar separado |
| `src/views/questao_form.py` | Adicionar seletor de nível escolar |
| `database/migrations/001_separar_niveis_fontes.sql` | **NOVO** - Script migração |

### 1.6 Ordem de Implementação

1. Criar script de migração SQL
2. Criar model `NivelEscolar`
3. Expandir model `FonteQuestao`
4. Criar repository `NivelEscolarRepository`
5. Atualizar `QuestaoRepository` com novos filtros
6. Atualizar views (forms e filtros)
7. Executar migração em banco de testes
8. Validar integridade dos dados
9. Aplicar em produção

### 1.7 Impacto

- **Baixo risco**: Mudanças aditivas, não quebram funcionalidade existente
- **Migração**: Necessária para dados existentes
- **Compatibilidade**: Re-exports mantêm imports funcionando

---

## PLANO 2: Upload de Imagens para Serviço Externo

### 2.1 Problema Atual

- Imagens armazenadas localmente em `imagens/`
- Caminho relativo salvo no banco
- Difícil compartilhar o sistema entre máquinas
- Backup de imagens separado do banco

### 2.2 Solução Proposta

Integrar com serviços de upload de imagens (ImgBB, Cloudinary, ou AWS S3) e armazenar URLs no banco.

```
┌─────────────────────────────────────────────────────────────────┐
│                         FLUXO ATUAL                             │
├─────────────────────────────────────────────────────────────────┤
│ Usuário seleciona imagem → Copia para imagens/ → Salva caminho │
└─────────────────────────────────────────────────────────────────┘

                              ↓

┌─────────────────────────────────────────────────────────────────┐
│                         FLUXO NOVO                              │
├─────────────────────────────────────────────────────────────────┤
│ Usuário seleciona imagem                                        │
│     ↓                                                           │
│ Upload para serviço externo (ImgBB/Cloudinary/S3)              │
│     ↓                                                           │
│ Recebe URL pública                                              │
│     ↓                                                           │
│ Salva URL no banco (campo url_remota)                          │
│     ↓                                                           │
│ Exibe imagem via URL                                            │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 Serviços Suportados

| Serviço | Gratuito | Limite | Uso Recomendado |
|---------|----------|--------|-----------------|
| **ImgBB** | Sim | 32MB/img, ilimitado | Projetos pequenos |
| **Cloudinary** | 25GB | 25GB/mês transf. | Médio porte |
| **AWS S3** | Não | Pago | Produção/escala |

### 2.4 Mudanças no Schema

```sql
-- Adicionar colunas à tabela imagem
ALTER TABLE imagem ADD COLUMN url_remota VARCHAR(1000);
ALTER TABLE imagem ADD COLUMN servico_hospedagem VARCHAR(50); -- imgbb, cloudinary, s3
ALTER TABLE imagem ADD COLUMN id_remoto VARCHAR(255);         -- ID no serviço externo
ALTER TABLE imagem ADD COLUMN url_thumbnail VARCHAR(1000);    -- Thumbnail (opcional)
ALTER TABLE imagem ADD COLUMN data_expiracao DATETIME;        -- Se URL expira

-- Índice para busca por URL
CREATE INDEX IF NOT EXISTS idx_imagem_url_remota ON imagem(url_remota);
```

### 2.5 Nova Estrutura de Arquivos

```
src/
├── services/
│   └── image_upload/
│       ├── __init__.py
│       ├── base_uploader.py      # Interface abstrata
│       ├── imgbb_uploader.py     # Implementação ImgBB
│       ├── cloudinary_uploader.py # Implementação Cloudinary
│       ├── s3_uploader.py        # Implementação AWS S3
│       └── local_uploader.py     # Fallback local (atual)
```

### 2.6 Interface do Uploader

```python
# base_uploader.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

@dataclass
class UploadResult:
    success: bool
    url: Optional[str] = None
    url_thumbnail: Optional[str] = None
    id_remoto: Optional[str] = None
    servico: Optional[str] = None
    erro: Optional[str] = None

class BaseImageUploader(ABC):
    @abstractmethod
    def upload(self, caminho_arquivo: str, nome: str = None) -> UploadResult:
        """Faz upload da imagem e retorna resultado"""
        pass

    @abstractmethod
    def delete(self, id_remoto: str) -> bool:
        """Remove imagem do serviço"""
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Verifica se o serviço está configurado"""
        pass
```

### 2.7 Configuração (config.ini)

```ini
[IMAGES]
# Serviço de upload: local, imgbb, cloudinary, s3
upload_service = imgbb

[IMGBB]
api_key = sua_api_key_aqui

[CLOUDINARY]
cloud_name = seu_cloud_name
api_key = sua_api_key
api_secret = seu_api_secret

[AWS_S3]
bucket_name = seu_bucket
region = us-east-1
access_key_id = sua_access_key
secret_access_key = sua_secret_key
```

### 2.8 Arquivos a Criar/Modificar

| Arquivo | Ação |
|---------|------|
| `src/services/image_upload/__init__.py` | **NOVO** |
| `src/services/image_upload/base_uploader.py` | **NOVO** |
| `src/services/image_upload/imgbb_uploader.py` | **NOVO** |
| `src/services/image_upload/cloudinary_uploader.py` | **NOVO** |
| `src/services/image_upload/s3_uploader.py` | **NOVO** |
| `src/services/image_upload/local_uploader.py` | **NOVO** |
| `src/services/image_upload/uploader_factory.py` | **NOVO** |
| `src/models/orm/imagem.py` | Adicionar campos de URL |
| `src/repositories/imagem_repository.py` | Métodos para URL remota |
| `src/views/components/forms/image_picker.py` | Integrar upload |
| `config.ini` | Adicionar seções de configuração |
| `requirements.txt` | Adicionar dependências (requests, boto3, cloudinary) |

### 2.9 Dependências

```txt
# requirements.txt (adicionar)
requests>=2.28.0        # Para ImgBB API
cloudinary>=1.30.0      # Para Cloudinary
boto3>=1.26.0           # Para AWS S3
```

### 2.10 Ordem de Implementação

1. Criar estrutura de diretórios `services/image_upload/`
2. Implementar `BaseImageUploader` (interface)
3. Implementar `LocalUploader` (comportamento atual)
4. Implementar `ImgBBUploader` (mais simples)
5. Atualizar schema do banco (migration)
6. Atualizar model `Imagem`
7. Criar `UploaderFactory` para selecionar serviço
8. Integrar com `ImagePicker`
9. Atualizar exibição de imagens (usar URL se disponível)
10. Testar com cada serviço
11. Implementar Cloudinary e S3 (opcional)

### 2.11 Fallback e Resiliência

- Se upload falhar, manter cópia local
- Se URL expirar, re-upload automático
- Cache local para performance
- Timeout configurável para uploads

---

## PLANO 3: Sistema de Logs/Auditoria com MongoDB Atlas

### 3.1 Objetivo

Criar sistema de logging centralizado para:
- Rastrear erros em múltiplas instâncias
- Auditoria de ações dos usuários
- Debugging remoto
- Métricas de uso

### 3.2 Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                    ARQUITETURA DE LOGS                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
│  │ Instância 1 │     │ Instância 2 │     │ Instância N │       │
│  │  (Lucas)    │     │  (Colega A) │     │  (Colega B) │       │
│  └──────┬──────┘     └──────┬──────┘     └──────┬──────┘       │
│         │                   │                   │               │
│         └───────────────────┼───────────────────┘               │
│                             │                                   │
│                             ▼                                   │
│                   ┌─────────────────┐                           │
│                   │  MongoDB Atlas  │                           │
│                   │  (Cloud DB)     │                           │
│                   └─────────────────┘                           │
│                             │                                   │
│                             ▼                                   │
│                   ┌─────────────────┐                           │
│                   │   Collections   │                           │
│                   ├─────────────────┤                           │
│                   │ - errors        │                           │
│                   │ - audit         │                           │
│                   │ - metrics       │                           │
│                   └─────────────────┘                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.3 Estrutura dos Documentos MongoDB

#### Collection: `errors`
```json
{
    "_id": "ObjectId",
    "timestamp": "2026-01-20T10:30:00Z",
    "nivel": "ERROR",
    "usuario_id": "uuid-do-usuario",
    "maquina_id": "hash-unico-maquina",
    "app_version": "1.0.0",
    "erro": {
        "tipo": "DatabaseError",
        "mensagem": "UNIQUE constraint failed",
        "stacktrace": "Traceback (most recent call last)...",
        "arquivo": "questao_repository.py",
        "linha": 42,
        "funcao": "salvar_questao"
    },
    "contexto": {
        "acao": "criar_questao",
        "dados_entrada": {"titulo": "..."},
        "estado_app": "normal"
    },
    "ambiente": {
        "os": "macOS 14.0",
        "python": "3.14",
        "pyqt": "6.6.0"
    }
}
```

#### Collection: `audit`
```json
{
    "_id": "ObjectId",
    "timestamp": "2026-01-20T10:30:00Z",
    "usuario_id": "uuid-do-usuario",
    "maquina_id": "hash-unico-maquina",
    "acao": "QUESTAO_CRIADA",
    "entidade": "questao",
    "entidade_id": "uuid-da-questao",
    "detalhes": {
        "titulo": "Questão sobre funções",
        "tipo": "OBJETIVA"
    },
    "ip_origem": "192.168.1.100"  // se disponível
}
```

#### Collection: `metrics`
```json
{
    "_id": "ObjectId",
    "timestamp": "2026-01-20T10:30:00Z",
    "maquina_id": "hash-unico-maquina",
    "tipo": "SESSAO",
    "dados": {
        "duracao_segundos": 3600,
        "questoes_criadas": 5,
        "listas_exportadas": 2,
        "erros_ocorridos": 1
    }
}
```

### 3.4 Nova Estrutura de Arquivos

```
src/
├── infrastructure/
│   └── logging/
│       ├── __init__.py
│       ├── mongo_handler.py      # Handler de logging para MongoDB
│       ├── audit_logger.py       # Logger de auditoria
│       ├── error_reporter.py     # Reporter de erros
│       ├── metrics_collector.py  # Coletor de métricas
│       └── machine_id.py         # Identificador único da máquina
```

### 3.5 Configuração (config.ini)

```ini
[LOGGING]
# Níveis: DEBUG, INFO, WARNING, ERROR, CRITICAL
nivel_console = INFO
nivel_arquivo = DEBUG
nivel_remoto = ERROR

# Logging remoto
remote_logging_enabled = true

[MONGODB]
# Connection string do Atlas
connection_string = mongodb+srv://usuario:senha@cluster.mongodb.net/mathbank_logs
database = mathbank_logs

# Collections
collection_errors = errors
collection_audit = audit
collection_metrics = metrics

# Retry e timeout
connection_timeout_ms = 5000
retry_writes = true

[AUDIT]
# Ações a auditar
auditar_questoes = true
auditar_listas = true
auditar_tags = true
auditar_exportacoes = true
```

### 3.6 Implementação do Handler

```python
# mongo_handler.py
import logging
from pymongo import MongoClient
from datetime import datetime
import platform
import hashlib
import uuid

class MongoDBHandler(logging.Handler):
    """Handler de logging que envia para MongoDB Atlas"""

    def __init__(self, connection_string: str, database: str, collection: str):
        super().__init__()
        self.client = MongoClient(connection_string)
        self.db = self.client[database]
        self.collection = self.db[collection]
        self.machine_id = self._get_machine_id()

    def _get_machine_id(self) -> str:
        """Gera ID único da máquina"""
        import socket
        data = f"{platform.node()}-{socket.gethostname()}-{uuid.getnode()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def emit(self, record: logging.LogRecord):
        """Envia log para MongoDB"""
        try:
            doc = {
                "timestamp": datetime.utcnow(),
                "nivel": record.levelname,
                "maquina_id": self.machine_id,
                "app_version": self._get_app_version(),
                "erro": {
                    "tipo": record.exc_info[0].__name__ if record.exc_info else None,
                    "mensagem": record.getMessage(),
                    "stacktrace": self.format(record) if record.exc_info else None,
                    "arquivo": record.pathname,
                    "linha": record.lineno,
                    "funcao": record.funcName
                },
                "ambiente": {
                    "os": f"{platform.system()} {platform.release()}",
                    "python": platform.python_version()
                }
            }
            self.collection.insert_one(doc)
        except Exception:
            # Falha silenciosa - não pode travar o app por erro de log
            pass
```

### 3.7 Logger de Auditoria

```python
# audit_logger.py
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Any
from datetime import datetime

class AcaoAuditoria(Enum):
    # Questões
    QUESTAO_CRIADA = "questao.criada"
    QUESTAO_EDITADA = "questao.editada"
    QUESTAO_INATIVADA = "questao.inativada"
    QUESTAO_REATIVADA = "questao.reativada"

    # Listas
    LISTA_CRIADA = "lista.criada"
    LISTA_EDITADA = "lista.editada"
    LISTA_DELETADA = "lista.deletada"
    LISTA_EXPORTADA = "lista.exportada"

    # Tags
    TAG_CRIADA = "tag.criada"
    TAG_EDITADA = "tag.editada"
    TAG_DELETADA = "tag.deletada"

    # Sistema
    SESSAO_INICIADA = "sessao.iniciada"
    SESSAO_ENCERRADA = "sessao.encerrada"
    BACKUP_CRIADO = "backup.criado"
    BACKUP_RESTAURADO = "backup.restaurado"

@dataclass
class EventoAuditoria:
    acao: AcaoAuditoria
    entidade: str
    entidade_id: str
    detalhes: Optional[dict] = None
    usuario_id: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

class AuditLogger:
    """Logger de auditoria para MongoDB"""

    def __init__(self, mongo_client, database: str, collection: str):
        self.collection = mongo_client[database][collection]
        self.machine_id = self._get_machine_id()

    def log(self, evento: EventoAuditoria):
        """Registra evento de auditoria"""
        doc = {
            "timestamp": evento.timestamp,
            "maquina_id": self.machine_id,
            "usuario_id": evento.usuario_id,
            "acao": evento.acao.value,
            "entidade": evento.entidade,
            "entidade_id": evento.entidade_id,
            "detalhes": evento.detalhes
        }
        self.collection.insert_one(doc)

    def questao_criada(self, questao_id: str, titulo: str, tipo: str):
        """Atalho para log de questão criada"""
        self.log(EventoAuditoria(
            acao=AcaoAuditoria.QUESTAO_CRIADA,
            entidade="questao",
            entidade_id=questao_id,
            detalhes={"titulo": titulo, "tipo": tipo}
        ))
```

### 3.8 Arquivos a Criar/Modificar

| Arquivo | Ação |
|---------|------|
| `src/infrastructure/logging/__init__.py` | **NOVO** |
| `src/infrastructure/logging/mongo_handler.py` | **NOVO** |
| `src/infrastructure/logging/audit_logger.py` | **NOVO** |
| `src/infrastructure/logging/error_reporter.py` | **NOVO** |
| `src/infrastructure/logging/metrics_collector.py` | **NOVO** |
| `src/infrastructure/logging/machine_id.py` | **NOVO** |
| `config.ini` | Adicionar seções MONGODB e AUDIT |
| `requirements.txt` | Adicionar pymongo e dnspython |
| `src/main.py` | Configurar logging global |
| `src/repositories/*.py` | Adicionar chamadas de auditoria |

### 3.9 Dependências

```txt
# requirements.txt (adicionar)
pymongo>=4.6.0          # Driver MongoDB
dnspython>=2.4.0        # Para connection string SRV
```

### 3.10 Ordem de Implementação

1. Criar cluster no MongoDB Atlas (gratuito)
2. Configurar connection string
3. Criar estrutura `infrastructure/logging/`
4. Implementar `MongoDBHandler`
5. Implementar `AuditLogger`
6. Configurar logging global em `main.py`
7. Adicionar decorators/chamadas nos repositories
8. Implementar `ErrorReporter` para exceções não tratadas
9. Implementar `MetricsCollector` (opcional)
10. Testar com múltiplas instâncias
11. Criar dashboard no Atlas para visualização

### 3.11 Segurança

- Connection string NÃO deve estar em código versionado
- Usar variáveis de ambiente ou arquivo `.env` local
- Criar usuário com permissões mínimas (apenas insert)
- Não logar dados sensíveis (senhas, tokens)
- Hash do machine_id para anonimização

### 3.12 Fallback

- Se MongoDB não estiver disponível, log apenas local
- Queue local para retry de logs falhados
- Timeout curto para não travar a aplicação

---

## Resumo dos Planos

| Plano | Complexidade | Prioridade Sugerida | Dependências |
|-------|--------------|---------------------|--------------|
| 1. Refatoração Banco | Média | Alta | Nenhuma |
| 2. Upload Imagens | Média | Média | API key do serviço |
| 3. Logs MongoDB | Baixa-Média | Alta | Cluster MongoDB Atlas |

**Recomendação de Ordem:**
1. **Plano 3** (Logs) - Permite monitorar erros das próximas mudanças
2. **Plano 1** (Banco) - Melhora a estrutura fundamental
3. **Plano 2** (Imagens) - Funcionalidade adicional

---

*Documento criado em: 2026-01-20*
*Autor: Sistema de Planejamento*
