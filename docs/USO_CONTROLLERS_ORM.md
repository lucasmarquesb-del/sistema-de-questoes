# 📘 Guia de Uso - Controllers ORM

**Data:** 2026-01-13
**Versão:** 2.0.0
**Status:** ✅ Completo

---

## 📋 ÍNDICE

1. [Visão Geral](#visão-geral)
2. [QuestaoControllerORM](#questaocontrollerorm)
3. [ListaControllerORM](#listacontrollerorm)
4. [TagControllerORM](#tagcontrollerorm)
5. [AlternativaControllerORM](#alternativacontrollerorm)
6. [Migração do Código Legacy](#migração-do-código-legacy)

---

## 🎯 VISÃO GERAL

### Nova Arquitetura

```
View (GUI)
    ↓
Controller ORM (controller_orm.py)
    ↓
Service Facade (service_facade.py)
    ↓
Service Layer (questao_service.py, lista_service.py, etc)
    ↓
Repository (questao_repository.py, lista_repository.py, etc)
    ↓
ORM Models (questao.py, lista.py, etc)
    ↓
Database (SQLite)
```

### Principais Mudanças

1. **UUIDs em vez de IDs inteiros**
   - Antes: `id_questao=123`
   - Agora: `uuid='550e8400-e29b-41d4-a716-446655440000'`

2. **Códigos legíveis**
   - Questões: `Q-2024-0001`, `Q-2024-0002`
   - Listas: `LST-2026-0001`, `LST-2026-0002`

3. **Busca por nome, não por ID**
   - Antes: `buscar_por_id(123)`
   - Agora: `buscar_questao('Q-2024-0001')`

4. **Gerenciamento automático de transações**
   - Context manager cuida de commit/rollback
   - Não precisa mais chamar `session.commit()` manualmente

---

## 📝 QuestaoControllerORM

### Criar Questão Objetiva Completa

```python
from src.controllers import QuestaoControllerORM

# Dados da questão
dados = {
    'tipo': 'OBJETIVA',
    'enunciado': 'Qual é a capital do Brasil?',
    'titulo': 'Geografia - Capitais Brasileiras',
    'fonte': 'ENEM',
    'ano': 2024,
    'dificuldade': 'FACIL',
    'observacoes': 'Questão de geografia básica',
    'tags': ['Geografia', 'Brasil', 'Capitais'],
    'alternativas': [
        {'letra': 'A', 'texto': 'São Paulo'},
        {'letra': 'B', 'texto': 'Rio de Janeiro'},
        {'letra': 'C', 'texto': 'Brasília'},
        {'letra': 'D', 'texto': 'Salvador'},
        {'letra': 'E', 'texto': 'Belo Horizonte'}
    ],
    'resposta_objetiva': {
        'uuid_alternativa_correta': 'uuid-da-alternativa-c',  # Você obtém isso após criar alternativas
        'resolucao': 'Brasília é a capital federal do Brasil desde 1960.',
        'justificativa': 'A capital foi transferida do Rio de Janeiro para Brasília em 21 de abril de 1960.'
    }
}

# Criar questão
questao = QuestaoControllerORM.criar_questao_completa(dados)

if questao:
    print(f"✅ Questão criada: {questao['codigo']}")  # Q-2024-0001
    print(f"   UUID: {questao['uuid']}")
    print(f"   Título: {questao['titulo']}")
    print(f"   Total de alternativas: {len(questao['alternativas'])}")
else:
    print("❌ Erro ao criar questão")
```

### Criar Questão Discursiva

```python
dados = {
    'tipo': 'DISCURSIVA',
    'enunciado': 'Explique o ciclo da água e sua importância para o planeta.',
    'titulo': 'Ciências - Ciclo da Água',
    'fonte': 'AUTORAL',
    'ano': 2026,
    'dificuldade': 'MEDIO',
    'tags': ['Ciências', 'Meio Ambiente', 'Água'],
    'resposta_discursiva': {
        'gabarito': 'O ciclo da água consiste em evaporação, condensação, precipitação e escoamento...',
        'resolucao': 'Resposta esperada deve incluir: evaporação, condensação, precipitação...',
        'justificativa': 'Critérios de avaliação: clareza, completude, exemplos práticos'
    }
}

questao = QuestaoControllerORM.criar_questao_completa(dados)
```

### Buscar Questão

```python
# Buscar por código legível
questao = QuestaoControllerORM.buscar_questao('Q-2024-0001')

if questao:
    print(f"Título: {questao['titulo']}")
    print(f"Tipo: {questao['tipo']}")
    print(f"Ano: {questao['ano']}")
    print(f"Fonte: {questao['fonte']}")
    print(f"Dificuldade: {questao['dificuldade']}")
    print(f"Tags: {', '.join(questao['tags'])}")

    # Se objetiva, listar alternativas
    if questao['tipo'] == 'OBJETIVA':
        for alt in questao['alternativas']:
            marca = '✓' if alt['correta'] else ' '
            print(f"  [{marca}] {alt['letra']}) {alt['texto']}")
```

### Listar Questões com Filtros

```python
# Buscar todas as questões de matemática, difíceis, do ENEM
filtros = {
    'fonte': 'ENEM',
    'tags': ['Matemática'],
    'dificuldade': 'DIFICIL',
    'ano': 2024
}

questoes = QuestaoControllerORM.listar_questoes(filtros)

for q in questoes:
    print(f"{q['codigo']} - {q['titulo']}")
```

### Atualizar Questão

```python
# Atualizar título e dificuldade
resultado = QuestaoControllerORM.atualizar_questao(
    'Q-2024-0001',
    titulo='Geografia - Capitais do Brasil (Revisado)',
    dificuldade='MEDIO'
)

if resultado:
    print("✅ Questão atualizada")
```

### Deletar Questão (Soft Delete)

```python
# Desativa a questão (não deleta permanentemente)
sucesso = QuestaoControllerORM.deletar_questao('Q-2024-0001')

if sucesso:
    print("✅ Questão desativada")
```

### Gerenciar Tags

```python
# Adicionar tag
QuestaoControllerORM.adicionar_tag('Q-2024-0001', 'História')

# Remover tag
QuestaoControllerORM.remover_tag('Q-2024-0001', 'Geografia')
```

### Estatísticas

```python
stats = QuestaoControllerORM.obter_estatisticas()

print(f"Total de questões: {stats['total']}")
print(f"Objetivas: {stats['objetivas']}")
print(f"Discursivas: {stats['discursivas']}")
print(f"Por dificuldade:")
print(f"  - Fáceis: {stats['faceis']}")
print(f"  - Médias: {stats['medias']}")
print(f"  - Difíceis: {stats['dificeis']}")
```

---

## 📋 ListaControllerORM

### Criar Lista

```python
from src.controllers import ListaControllerORM

# Criar prova com questões
lista = ListaControllerORM.criar_lista(
    titulo='Prova de Geografia - 1º Bimestre',
    tipo='PROVA',
    cabecalho='Escola ABC - Turma 9º Ano',
    instrucoes='Responda todas as questões a caneta azul ou preta',
    codigos_questoes=['Q-2024-0001', 'Q-2024-0002', 'Q-2024-0003']
)

if lista:
    print(f"✅ Lista criada: {lista['codigo']}")  # LST-2026-0001
    print(f"   Título: {lista['titulo']}")
    print(f"   Tipo: {lista['tipo']}")
    print(f"   Total de questões: {lista['total_questoes']}")
```

### Buscar Lista

```python
lista = ListaControllerORM.buscar_lista('LST-2026-0001')

if lista:
    print(f"Título: {lista['titulo']}")
    print(f"Tipo: {lista['tipo']}")
    print(f"Total de questões: {lista['total_questoes']}")
    print(f"Tags relacionadas: {', '.join(lista['tags_relacionadas'])}")

    print("\nQuestões:")
    for q in lista['questoes']:
        print(f"  - {q['codigo']}: {q['titulo']}")
```

### Listar Todas as Listas

```python
# Listar todas
todas = ListaControllerORM.listar_listas()

# Listar apenas provas
provas = ListaControllerORM.listar_listas(tipo='PROVA')

# Listar apenas simulados
simulados = ListaControllerORM.listar_listas(tipo='SIMULADO')

for lista in provas:
    print(f"{lista['codigo']} - {lista['titulo']} ({lista['total_questoes']} questões)")
```

### Adicionar Questão à Lista

```python
# Adicionar ao final
sucesso = ListaControllerORM.adicionar_questao(
    codigo_lista='LST-2026-0001',
    codigo_questao='Q-2024-0004'
)

# Adicionar em posição específica
sucesso = ListaControllerORM.adicionar_questao(
    codigo_lista='LST-2026-0001',
    codigo_questao='Q-2024-0005',
    ordem=2  # Será a segunda questão
)
```

### Remover Questão da Lista

```python
sucesso = ListaControllerORM.remover_questao(
    codigo_lista='LST-2026-0001',
    codigo_questao='Q-2024-0003'
)
```

### Reordenar Questões

```python
# Nova ordem das questões
nova_ordem = [
    'Q-2024-0003',
    'Q-2024-0001',
    'Q-2024-0002',
    'Q-2024-0004'
]

sucesso = ListaControllerORM.reordenar_questoes('LST-2026-0001', nova_ordem)
```

### Deletar Lista

```python
sucesso = ListaControllerORM.deletar_lista('LST-2026-0001')
```

---

## 🏷️ TagControllerORM

### Listar Todas as Tags

```python
from src.controllers import TagControllerORM

tags = TagControllerORM.listar_todas()

for tag in tags:
    print(f"{tag['numeracao']} - {tag['nome']}")
    print(f"   Caminho: {tag['caminho_completo']}")
```

### Listar Tags Raiz

```python
raizes = TagControllerORM.listar_raizes()

for tag in raizes:
    print(f"{tag['numeracao']} - {tag['nome']}")
```

### Listar Tags Filhas

```python
# Listar filhas da tag "1" (ex: Matemática)
filhas = TagControllerORM.listar_filhas('1')

for tag in filhas:
    print(f"{tag['numeracao']} - {tag['nome']}")
```

### Buscar Tag por Nome

```python
tag = TagControllerORM.buscar_por_nome('Matemática')

if tag:
    print(f"UUID: {tag['uuid']}")
    print(f"Nome: {tag['nome']}")
    print(f"Numeração: {tag['numeracao']}")
    print(f"Nível: {tag['nivel']}")
    print(f"Caminho: {tag['caminho_completo']}")
```

### Buscar Tag por Numeração

```python
tag = TagControllerORM.buscar_por_numeracao('1.2.3')

if tag:
    print(f"Nome: {tag['nome']}")
    print(f"Caminho: {tag['caminho_completo']}")
```

### Obter Árvore Hierárquica

```python
arvore = TagControllerORM.obter_arvore_hierarquica()

def imprimir_arvore(tags, indent=0):
    for tag in tags:
        print('  ' * indent + f"{tag['numeracao']} - {tag['nome']}")
        if tag.get('filhas'):
            imprimir_arvore(tag['filhas'], indent + 1)

imprimir_arvore(arvore)
```

**Saída:**
```
1 - Matemática
  1.1 - Álgebra
    1.1.1 - Equações
    1.1.2 - Funções
  1.2 - Geometria
2 - Português
  2.1 - Gramática
  2.2 - Literatura
```

---

## 🔤 AlternativaControllerORM

### Criar Alternativa

```python
from src.controllers import AlternativaControllerORM

alternativa = AlternativaControllerORM.criar_alternativa(
    codigo_questao='Q-2024-0001',
    letra='A',
    texto='São Paulo',
    uuid_imagem=None,  # Opcional
    escala_imagem=1.0
)

if alternativa:
    print(f"✅ Alternativa criada: {alternativa['letra']}")
    print(f"   UUID: {alternativa['uuid']}")
```

### Listar Alternativas de uma Questão

```python
alternativas = AlternativaControllerORM.listar_alternativas('Q-2024-0001')

for alt in alternativas:
    print(f"{alt['letra']}) {alt['texto']}")
```

### Buscar Alternativa Correta

```python
correta = AlternativaControllerORM.buscar_alternativa_correta('Q-2024-0001')

if correta:
    print(f"Alternativa correta: {correta['letra']}) {correta['texto']}")
```

---

## 🔄 MIGRAÇÃO DO CÓDIGO LEGACY

### Antes (Legacy)

```python
# Código antigo
from src.models.questao import QuestaoModel

# Buscar por ID inteiro
questao = QuestaoModel.buscar_por_id(123)

# Criar questão
id_questao = QuestaoModel.criar(
    titulo='Teste',
    enunciado='...',
    tipo='OBJETIVA',
    ano=2024,
    fonte='ENEM',
    id_dificuldade=1
)

# Commit manual
from src.models.database import db
db.commit()
```

### Depois (ORM)

```python
# Código novo
from src.controllers import QuestaoControllerORM

# Buscar por código legível
questao = QuestaoControllerORM.buscar_questao('Q-2024-0001')

# Criar questão (commit automático via context manager)
questao = QuestaoControllerORM.criar_questao_completa({
    'titulo': 'Teste',
    'enunciado': '...',
    'tipo': 'OBJETIVA',
    'ano': 2024,
    'fonte': 'ENEM',
    'dificuldade': 'FACIL'  # Agora usa código, não ID
})

# Não precisa de commit manual!
```

### Tabela de Conversão

| Legacy | ORM |
|--------|-----|
| `id_questao=123` | `codigo='Q-2024-0001'` |
| `id_lista=45` | `codigo='LST-2026-0001'` |
| `id_tag=5` | `nome='Matemática'` ou `numeracao='1.2'` |
| `id_dificuldade=1` | `dificuldade='FACIL'` |
| `tipo='OBJETIVA'` | `tipo='OBJETIVA'` (sem mudança) |
| `buscar_por_id(123)` | `buscar_questao('Q-2024-0001')` |
| `db.commit()` | Automático com `services.transaction()` |

---

## ✅ CHECKLIST DE MIGRAÇÃO

- [ ] Substituir imports de `src.models.*` por `src.controllers.*ORM`
- [ ] Trocar IDs inteiros por códigos legíveis
- [ ] Remover chamadas manuais de `commit()`
- [ ] Usar context managers para transações
- [ ] Atualizar testes para usar novos controllers
- [ ] Atualizar views (GUI) para usar novos controllers
- [ ] Testar todas as funcionalidades migradas
- [ ] Remover código legacy após validação completa

---

## 📚 REFERÊNCIAS

- **Arquitetura**: `ARQUITETURA_UUID_ORM.md`
- **Migração ORM**: `docs/MIGRACAO_ORM.md`
- **Modelos ORM**: `src/models/orm/`
- **Repositórios**: `src/repositories/`
- **Services**: `src/services/`
- **Controllers ORM**: `src/controllers/*_orm.py`

---

**Última atualização:** 2026-01-13
**Versão:** 2.0.0
