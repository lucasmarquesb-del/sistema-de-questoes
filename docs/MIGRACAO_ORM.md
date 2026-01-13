# 🔄 Guia de Migração para ORM SQLAlchemy

## 📋 Status da Migração

### ✅ Concluído
- **Fase 1:** Models ORM com UUID
- **Fase 2:** Scripts de migração de dados
- **Fase 3:** Repositories (camada de acesso a dados)
- **Fase 4 (Parcial):** Session Manager e Adapters

### 🚧 Em Andamento
- **Fase 4:** Atualização de Services e Controllers
- **Fase 5:** Atualização de Views e Forms

---

## 🏗️ Nova Arquitetura

### Estrutura de Camadas

```
Views (UI)
    ↓
Controllers
    ↓
Services (lógica de negócio)
    ↓
Repositories (acesso a dados)
    ↓
Models ORM (SQLAlchemy)
    ↓
Banco de Dados (SQLite)
```

### Diretórios

```
src/
├── models/orm/          # Models ORM SQLAlchemy
├── repositories/        # Repositories (acesso a dados)
├── database/           # Session manager
├── adapters/           # Adapters de compatibilidade
├── application/
│   └── services/       # Lógica de negócio
├── controllers/        # Controllers (coordenação)
└── views/             # Interface gráfica
```

---

## 💡 Como Usar

### 1. Usando Repositories Diretamente

```python
from database import session_manager
from repositories import QuestaoRepository

# Criar sessão
with session_manager.session_scope() as session:
    # Criar repository
    questao_repo = QuestaoRepository(session)

    # Criar questão
    questao = questao_repo.criar_questao_completa(
        codigo_tipo='OBJETIVA',
        enunciado='Qual é a raiz de x² - 4 = 0?',
        titulo='Equação do 2º Grau',
        sigla_fonte='ENEM',
        ano=2024,
        codigo_dificuldade='MEDIO'
    )

    print(f"Questão criada: {questao.codigo}")

    # Buscar questões
    questoes = questao_repo.buscar_por_ano(2024)
    for q in questoes:
        print(f"  - {q.codigo}: {q.titulo}")

    # Commit automático ao sair do context manager
```

### 2. Usando Adapter (Compatibilidade)

Para código existente que não pode ser modificado imediatamente:

```python
from adapters import questao_adapter

# Interface antiga funcionando com novo backend
resultado = questao_adapter.criar_questao(
    tipo='OBJETIVA',
    enunciado='Qual é...',
    titulo='Teste',
    fonte='ENEM',
    ano=2024
)

print(f"ID (código): {resultado['codigo']}")  # Q-2024-0001

# Buscar
questao = questao_adapter.buscar_questao('Q-2024-0001')
print(questao['titulo'])

# Commit manual
questao_adapter.commit()
questao_adapter.close()
```

### 3. Repositories Disponíveis

#### QuestaoRepository

```python
# Buscar por código
questao = repo.buscar_por_codigo('Q-2024-0001')

# Buscar por título
questoes = repo.buscar_por_titulo('função')

# Buscar com filtros combinados
questoes = repo.buscar_com_filtros({
    'fonte': 'ENEM',
    'ano': 2024,
    'tags': ['ÁLGEBRA', 'FUNÇÃO QUADRÁTICA'],
    'dificuldade': 'MEDIO'
})

# Adicionar tag
repo.adicionar_tag('Q-2024-0001', 'MATEMÁTICA')

# Estatísticas
stats = repo.estatisticas()
print(f"Total de questões: {stats['total']}")
print(f"Por tipo: {stats['por_tipo']}")
```

#### ListaRepository

```python
from repositories import ListaRepository

lista_repo = ListaRepository(session)

# Criar lista
lista = lista_repo.criar_lista(
    titulo='Simulado ENEM 2024',
    tipo='SIMULADO'
)

# Adicionar questões
lista_repo.adicionar_questao('LST-2024-0001', 'Q-2024-0001', ordem=1)
lista_repo.adicionar_questao('LST-2024-0001', 'Q-2024-0002', ordem=2)

# Reordenar
lista_repo.reordenar_questoes('LST-2024-0001', [
    'Q-2024-0002',  # Agora em primeiro
    'Q-2024-0001'   # Agora em segundo
])

# Buscar tags relacionadas
tags = lista_repo.buscar_tags_relacionadas('LST-2024-0001')
```

#### ImagemRepository

```python
from repositories import ImagemRepository

imagem_repo = ImagemRepository(session)

# Upload com deduplicação automática
imagem = imagem_repo.upload_imagem('path/to/imagem.png')
print(f"Hash MD5: {imagem.hash_md5}")

# Se tentar fazer upload da mesma imagem novamente, retorna a existente
imagem2 = imagem_repo.upload_imagem('path/to/imagem_copia.png')
print(f"Mesma imagem? {imagem.uuid == imagem2.uuid}")  # True se for igual

# Verificar uso
usos = imagem_repo.contar_usos(imagem.uuid)
print(f"Usada em {usos['questoes']} questões e {usos['alternativas']} alternativas")

# Deletar apenas se não estiver em uso
imagem_repo.deletar_se_nao_usado(imagem.uuid)
```

---

## 🔧 Migração Gradual

### Estratégia Recomendada

1. **Manter código antigo funcionando** com adapters
2. **Migrar módulo por módulo** para usar repositories
3. **Testar incrementalmente**
4. **Remover código antigo** após validação

### Exemplo de Migração

#### Antes (código antigo)

```python
# models/questao.py
def criar_questao(titulo, enunciado, tipo, **kwargs):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO questao (...) VALUES (...)",
        (titulo, enunciado, tipo)
    )
    conn.commit()
    return cursor.lastrowid
```

#### Depois (com adapter - compatível)

```python
# Substitui implementação interna mas mantém interface
from adapters import questao_adapter

def criar_questao(titulo, enunciado, tipo, **kwargs):
    return questao_adapter.criar_questao(
        titulo=titulo,
        enunciado=enunciado,
        tipo=tipo,
        **kwargs
    )
```

#### Ideal (código novo)

```python
# Novo código usando repositories diretamente
from database import session_manager
from repositories import QuestaoRepository

def criar_questao_service(titulo, enunciado, tipo, **kwargs):
    with session_manager.session_scope() as session:
        repo = QuestaoRepository(session)
        questao = repo.criar_questao_completa(
            codigo_tipo=tipo,
            titulo=titulo,
            enunciado=enunciado,
            **kwargs
        )
        return questao.to_dict()
```

---

## 🎯 Vantagens do Novo Sistema

### 1. UUIDs Globalmente Únicos
- Sem colisão entre ambientes
- Segurança (não sequencial)
- Fácil distribuição/replicação

### 2. Códigos Legíveis
- `Q-2024-0001` ao invés de `123`
- `LST-2024-0001` para listas
- Fácil identificação e busca

### 3. Normalização
- Tabelas separadas (fonte, ano, tipo)
- Sem dados duplicados
- Queries mais eficientes

### 4. Tabela Centralizada de Imagens
- Deduplicação automática por hash MD5
- Reduz drasticamente o tamanho do banco
- Controle de uso

### 5. Respostas Unificadas
- Uma tabela para objetivas E discursivas
- Mais simples de gerenciar
- Menos joins

### 6. ORM SQLAlchemy
- Type safety
- Migrations automáticas (Alembic)
- Menos SQL raw
- Relacionamentos explícitos

---

## 📚 Próximos Passos

1. ✅ Testar repositories em ambiente de desenvolvimento
2. 🚧 Migrar Services para usar repositories
3. 🚧 Migrar Controllers para usar novos services
4. ⏳ Atualizar Views/Forms
5. ⏳ Testes integrados
6. ⏳ Deploy em produção

---

## 🐛 Troubleshooting

### Erro: "No module named 'sqlalchemy'"
```bash
source venv/bin/activate
pip install sqlalchemy pillow
```

### Erro: "No such table"
Certifique-se de usar o banco V2:
```python
# database/session_manager.py
db_path = 'database/sistema_questoes_v2.db'  # Banco novo
```

### Sessão não commitando
Use context manager:
```python
with session_manager.session_scope() as session:
    # operações aqui
    pass  # Commit automático
```

---

**Última atualização:** 2026-01-13
**Versão:** 2.0.0
