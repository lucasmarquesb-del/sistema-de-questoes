# Guia de Setup - Sistema de Banco de Questões

## ✅ Estrutura Base Criada

### Arquivos Principais

- ✅ `config.ini` - Arquivo de configuração do sistema
- ✅ `requirements.txt` - Dependências Python
- ✅ `README.md` - Documentação completa do projeto
- ✅ `.gitignore` - Arquivos a serem ignorados pelo Git

### Diretórios

```
✅ src/                      # Código fonte
   ✅ models/                # Camada de dados
      ✅ database.py         # Gerenciamento do banco
   ✅ views/                 # Interface (a ser implementado)
   ✅ controllers/           # Lógica de negócio (a ser implementado)
   ✅ utils/                 # Utilitários (a ser implementado)
   ✅ main.py               # Ponto de entrada

✅ database/                 # Banco de dados
   ✅ init_db.sql            # Script de inicialização
   ✅ questoes.db            # Banco SQLite (gerado)

✅ imagens/                  # Imagens das questões
   ✅ enunciados/
   ✅ alternativas/

✅ templates/                # Templates LaTeX
   ✅ latex/
      ✅ default.tex        # Template padrão

✅ exports/                  # PDFs e arquivos .tex gerados
✅ backups/                  # Backups do banco
✅ logs/                     # Logs da aplicação
```

---

## 🗄️ Banco de Dados

### Status: ✅ CRIADO E TESTADO

O banco de dados foi inicializado com sucesso e contém:

- **9 Tabelas:**
  - `tag` - Tags hierárquicas
  - `dificuldade` - Níveis de dificuldade (3 registros)
  - `questao` - Questões educacionais
  - `alternativa` - Alternativas das questões
  - `questao_tag` - Relacionamento N:N
  - `lista` - Listas/Provas
  - `lista_questao` - Relacionamento N:N
  - `questao_versao` - Versões alternativas
  - `configuracao` - Configurações do sistema (9 registros)

- **31 Tags Pré-cadastradas:**
  - Taxonomia matemática hierárquica
  - Tags de vestibulares (ENEM, FUVEST, etc.)
  - Tags de escolaridade (E.F.2, E.M., E.J.A.)

- **Índices e Triggers:**
  - Índices para otimização de queries
  - Triggers para garantir integridade

---

## 🧪 Testes Realizados

### Teste do Banco de Dados

```bash
python3 src/models/database.py
```

**Resultado:** ✅ SUCESSO

```
============================================================
TESTE DO MÓDULO DATABASE
============================================================

1. Inicializando banco de dados...
✓ Banco inicializado com sucesso!

2. Verificando integridade...
✓ Integridade verificada!

3. Testando queries básicas...
   - Dificuldades cadastradas: 3
   - Tags cadastradas: 31
   - Configurações: 9

4. Listando dificuldades:
   - FÁCIL: Questões de nível básico
   - MÉDIO: Questões de nível intermediário
   - DIFÍCIL: Questões de nível avançado

============================================================
TESTE CONCLUÍDO COM SUCESSO!
============================================================
```

---

## 📋 Próximos Passos

### 1. Instalar Dependências (Pendente)

```bash
# Criar ambiente virtual
python3 -m venv venv

# Ativar ambiente virtual
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### 2. Implementar Models (Próxima Etapa)

Criar classes model para cada entidade:

- [ ] `src/models/questao.py`
- [ ] `src/models/tag.py`
- [ ] `src/models/alternativa.py`
- [ ] `src/models/lista.py`
- [ ] `src/models/dificuldade.py`

### 3. Implementar Controllers (Próxima Etapa)

- [ ] `src/controllers/questao_controller.py`
- [ ] `src/controllers/tag_controller.py`
- [ ] `src/controllers/lista_controller.py`
- [ ] `src/controllers/export_controller.py`

### 4. Implementar Views (Próxima Etapa)

- [ ] `src/views/main_window.py` - Janela principal
- [ ] `src/views/questao_form.py` - Formulário de questões
- [ ] `src/views/tag_manager.py` - Gerenciador de tags
- [ ] `src/views/search_panel.py` - Painel de busca
- [ ] `src/views/lista_form.py` - Formulário de listas
- [ ] `src/views/export_dialog.py` - Diálogo de exportação

### 5. Implementar Utils (Próxima Etapa)

- [ ] `src/utils/latex_renderer.py` - Renderização de LaTeX
- [ ] `src/utils/image_handler.py` - Manipulação de imagens
- [ ] `src/utils/backup_manager.py` - Gerenciamento de backups
- [ ] `src/utils/validators.py` - Validações

---

## 🔧 Comandos Úteis

### Executar aplicação (quando interface estiver pronta)
```bash
python3 src/main.py
```

### Testar banco de dados
```bash
python3 src/models/database.py
```

### Ver estrutura do banco
```bash
sqlite3 database/questoes.db ".schema"
```

### Contar registros
```bash
sqlite3 database/questoes.db "SELECT COUNT(*) FROM tag;"
```

### Resetar banco de dados
```bash
rm database/questoes.db
python3 src/models/database.py
```

---

## 📊 Status do Projeto

### ✅ Concluído (Base do Sistema)

- [x] Estrutura de diretórios
- [x] Arquivo de configuração
- [x] Script SQL de inicialização
- [x] Módulo de conexão com banco
- [x] Arquivo de dependências
- [x] Template LaTeX padrão
- [x] README completo
- [x] .gitignore configurado
- [x] Banco de dados criado e testado

### 🔄 Em Desenvolvimento (MVP v1.0)

- [ ] Models (CRUD básico)
- [ ] Controllers (lógica de negócio)
- [ ] Views (interface gráfica PyQt6)
- [ ] Utils (utilitários diversos)

### 📅 Planejado (Versões Futuras)

- [ ] Sistema completo de tags
- [ ] Busca avançada
- [ ] Exportação para PDF
- [ ] Preview de LaTeX
- [ ] Sistema de backup
- [ ] Templates personalizados

---

## 🎯 Objetivo Atual

**Implementar as classes Model para CRUD básico das entidades.**

Isso permitirá:
1. Criar, ler, atualizar e deletar questões
2. Gerenciar tags
3. Criar listas
4. Base sólida para construir a interface

---

## 📝 Notas Importantes

1. **Banco de Dados:** O arquivo `questoes.db` já foi criado e testado. Não é versionado no Git.

2. **Imagens:** As pastas de imagens estão vazias e prontas para receber arquivos.

3. **Logs:** A pasta `logs/` receberá os logs da aplicação automaticamente.

4. **Configuração:** O arquivo `config.ini` pode ser editado para personalizar o sistema.

5. **Python:** Use `python3` para executar os scripts (testado com Python 3.11).

---

**Data de Criação:** 12 de Janeiro de 2026
**Versão:** 1.0.1
**Status:** Base do sistema implementada com sucesso! ✅
