# Plano de Refatoração das Views

## Objetivo
Reorganizar as views do projeto separando em **páginas** e **componentes** reutilizáveis, integrando o novo design do MathBank.

---

## Estrutura Final Proposta

```
src/views/
├── __init__.py                 # Re-exports para compatibilidade
├── pages/                      # Páginas completas (telas)
│   ├── __init__.py
│   ├── main_window.py          # Janela principal (shell)
│   ├── dashboard_page.py       # Página inicial/dashboard
│   ├── search_page.py          # Página de busca de questões
│   ├── lista_page.py           # Página de gerenciamento de listas
│   ├── questao_form_page.py    # Página de criar/editar questão
│   ├── tag_manager_page.py     # Página de gerenciamento de tags
│   ├── export_page.py          # Diálogo de exportação
│   ├── lista_form_page.py      # Formulário de lista
│   ├── questao_selector_page.py # Seletor de questões
│   └── questao_preview_page.py # Preview de questão
│
├── components/                 # Componentes reutilizáveis
│   ├── __init__.py
│   ├── layout/                 # Componentes de layout
│   │   ├── __init__.py
│   │   ├── header.py           # Header com logo e navegação
│   │   └── sidebar.py          # Sidebar com árvore de tags
│   │
│   ├── cards/                  # Componentes de card
│   │   ├── __init__.py
│   │   ├── questao_card.py     # Card de questão
│   │   └── lista_card.py       # Card de lista (futuro)
│   │
│   ├── forms/                  # Componentes de formulário
│   │   ├── __init__.py
│   │   ├── latex_editor.py     # Editor LaTeX
│   │   ├── tag_tree.py         # Árvore de tags com checkboxes
│   │   ├── difficulty_selector.py
│   │   └── image_picker.py     # Seletor de imagem
│   │
│   ├── filters/                # Componentes de filtro
│   │   ├── __init__.py
│   │   ├── search_bar.py       # Barra de busca (futuro)
│   │   └── filter_panel.py     # Painel de filtros (futuro)
│   │
│   ├── dialogs/                # Diálogos modais
│   │   ├── __init__.py
│   │   ├── image_insert_dialog.py
│   │   ├── table_editor_dialog.py
│   │   └── color_picker_dialog.py
│   │
│   └── common/                 # Componentes genéricos
│       ├── __init__.py
│       ├── tags_display.py     # Exibição de tags (futuro)
│       └── empty_state.py      # Estado vazio (futuro)
│
├── styles/                     # Estilos
│   ├── __init__.py
│   └── mathbank.qss            # Stylesheet principal
│
└── novas-views/                # [A SER REMOVIDA após migração completa]
    ├── mathbank_main.py
    ├── mathbank_dashboard.py
    ├── mathbank_sidebar.py
    ├── mathbank_card.py
    └── mathbank_styles.css
```

---

## Fases de Implementação

### ✅ Fase 1: Criar estrutura de diretórios
**Status: CONCLUÍDA**

- [x] Criar diretórios `pages/`, `components/`, `styles/`
- [x] Criar subdiretórios de componentes
- [x] Criar arquivos `__init__.py`

---

### ✅ Fase 2: Extrair componentes de `widgets.py`
**Status: CONCLUÍDA**

Componentes extraídos:

| Componente | Novo Local |
|------------|------------|
| `DifficultySelector` | `components/forms/difficulty_selector.py` |
| `ImagePicker` | `components/forms/image_picker.py` |
| `TagTreeWidget` | `components/forms/tag_tree.py` |
| `LatexEditor` | `components/forms/latex_editor.py` |
| `QuestaoCard` | `components/cards/questao_card.py` |
| `ImageInsertDialog` | `components/dialogs/image_insert_dialog.py` |
| `TableSizeDialog` | `components/dialogs/table_editor_dialog.py` |
| `TableEditorDialog` | `components/dialogs/table_editor_dialog.py` |
| `ColorPickerDialog` | `components/dialogs/color_picker_dialog.py` |

---

### ✅ Fase 3: Integrar novas views (mathbank)
**Status: CONCLUÍDA**

- [x] Criar `components/layout/header.py` baseado no design mathbank
- [x] Criar `components/layout/sidebar.py` baseado no design mathbank
- [x] Mover `mathbank_styles.css` → `styles/mathbank.qss`
- [x] Criar helper `load_stylesheet()` em `styles/__init__.py`

---

### ✅ Fase 4: Refatorar páginas existentes para `pages/`
**Status: CONCLUÍDA**

Páginas migradas:

| Arquivo Original | Novo Local |
|-----------------|------------|
| `tag_manager.py` | `pages/tag_manager_page.py` |
| `export_dialog.py` | `pages/export_page.py` |
| `lista_form.py` | `pages/lista_form_page.py` |
| `questao_selector_dialog.py` | `pages/questao_selector_page.py` |
| `questao_preview.py` | `pages/questao_preview_page.py` |

Arquivos originais convertidos para re-exports (mantém compatibilidade).

---

### ✅ Fase 5: Refatorar `main_window.py` para usar novos componentes
**Status: CONCLUÍDA**

Tarefas:
- [x] Mover `main_window.py` para `pages/main_window.py`
- [x] Integrar `Header` do novo layout
- [x] Integrar `Sidebar` do novo layout
- [x] Aplicar estilos de `mathbank.qss`
- [x] Atualizar navegação para usar signals do Header
- [x] Criar re-export para compatibilidade

Mudanças principais:
- Nova interface com Header no topo (logo, navegação, botão Nova Questão)
- Sidebar com árvore de tags hierárquica
- Estilos do MathBank aplicados automaticamente
- Navegação via signals entre componentes
- Método `filter_by_tag` adicionado ao SearchPanel para integração com sidebar

---

### ✅ Fase 6: Refatorar `search_panel.py` e `lista_panel.py`
**Status: CONCLUIDA**

Tarefas:
- [x] Mover `search_panel.py` → `pages/search_page.py`
- [x] Mover `lista_panel.py` → `pages/lista_page.py`
- [x] Integrar com novo sistema de navegacao
- [x] Criar re-exports para compatibilidade

Arquivos criados/modificados:
- `src/views/pages/search_page.py` (nova implementacao)
- `src/views/pages/lista_page.py` (nova implementacao)
- `src/views/search_panel.py` (convertido para re-export)
- `src/views/lista_panel.py` (convertido para re-export)
- `src/views/pages/__init__.py` (adicionados exports)
- `src/views/__init__.py` (adicionados exports)

---

### ✅ Fase 7: Refatorar `questao_form.py`
**Status: CONCLUIDA**

Tarefas:
- [x] Mover `questao_form.py` → `pages/questao_form_page.py`
- [x] Usar componentes extraidos (LatexEditor, TagTree, etc.)
- [x] Criar re-export para compatibilidade

Arquivos criados/modificados:
- `src/views/pages/questao_form_page.py` (nova implementacao)
- `src/views/questao_form.py` (convertido para re-export)
- `src/views/pages/__init__.py` (adicionados exports)

---

### ✅ Fase 8: Criar pagina Dashboard (estatistica)
**Status: CONCLUIDA**

Tarefas:
- [x] Criar `pages/dashboard_page.py` baseado em `mathbank_dashboard.py`
- [x] Implementar estatisticas (total questoes, listas, etc.)
- [x] Implementar cards de acesso rapido
- [x] Integrar com main_window

Arquivos criados/modificados:
- `src/views/pages/dashboard_page.py` (nova implementacao)
- `src/views/pages/main_window.py` (integrado DashboardPage)
- `src/views/pages/__init__.py` (adicionados exports)

Funcionalidades implementadas:
- StatCard: Cards de estatisticas clicaveis
- QuickActionCard: Cards de acoes rapidas
- Estatisticas: Total questoes, listas, tags, objetivas/discursivas
- Navegacao integrada via sinais

---

### ✅ Fase 9: Limpeza e finalizacao
**Status: CONCLUIDA**

Tarefas:
- [x] Remover pasta `novas-views/` apos migracao completa
- [x] Atualizar todos os imports no projeto para usar nova estrutura
- [x] Verificar sintaxe de todos os arquivos
- [x] Atualizar documentacao

Limpeza realizada:
- Pasta `src/views/novas-views/` removida (arquivos de referencia)
- Todos os re-exports criados para compatibilidade
- Sintaxe verificada em todos os novos arquivos

---

## Compatibilidade

Durante toda a refatoração, a compatibilidade com imports existentes é mantida através de **re-exports**:

```python
# Exemplo: src/views/widgets.py
from src.views.components.forms.latex_editor import LatexEditor
from src.views.components.forms.tag_tree import TagTreeWidget
# ... etc

# Imports existentes continuam funcionando:
from src.views.widgets import LatexEditor  # OK!
```

---

## Como Usar os Novos Estilos

```python
from src.views.styles import load_stylesheet

# Na main_window ou onde aplicar o tema:
stylesheet = load_stylesheet("mathbank")
self.setStyleSheet(stylesheet)
```

---

## Status Final

**TODAS AS FASES CONCLUIDAS!**

A refatoracao das views foi concluida com sucesso. Estrutura final:

```
src/views/
├── pages/                      # Paginas completas
│   ├── main_window.py          # Janela principal
│   ├── dashboard_page.py       # Dashboard com estatisticas
│   ├── search_page.py          # Busca de questoes
│   ├── lista_page.py           # Gerenciamento de listas
│   ├── questao_form_page.py    # Formulario de questao
│   ├── tag_manager_page.py     # Gerenciador de tags
│   ├── export_page.py          # Dialogo de exportacao
│   ├── lista_form_page.py      # Formulario de lista
│   ├── questao_selector_page.py# Seletor de questoes
│   └── questao_preview_page.py # Preview de questao
│
├── components/                 # Componentes reutilizaveis
│   ├── layout/                 # Header, Sidebar
│   ├── cards/                  # QuestaoCard
│   ├── forms/                  # LatexEditor, TagTree, etc.
│   ├── dialogs/                # ImageInsert, TableEditor, etc.
│   ├── filters/                # (extensivel)
│   └── common/                 # (extensivel)
│
├── styles/                     # Estilos
│   └── mathbank.qss            # Stylesheet principal
│
├── search_panel.py             # Re-export → pages/search_page.py
├── lista_panel.py              # Re-export → pages/lista_page.py
├── questao_form.py             # Re-export → pages/questao_form_page.py
├── widgets.py                  # Re-export → components/*
└── __init__.py                 # Re-exports gerais
```

## Proximos Passos Recomendados

1. **Testar a aplicacao** - Rodar `main.py` e verificar todas as funcionalidades
2. **Implementar Plano 1** - Refatoracao do banco de dados (separar niveis e fontes)
3. **Implementar Plano 2** - Upload de imagens para servico externo
4. **Implementar Plano 3** - Sistema de logs/auditoria com MongoDB Atlas

Consulte o arquivo `PLANOS_IMPLEMENTACAO.md` para detalhes dos proximos planos.

---

## Notas Técnicas

- **PyQt6** é o framework de UI utilizado
- **Estilos** usam QSS (Qt Style Sheets), similar a CSS
- **Signals/Slots** são usados para comunicação entre componentes
- **DTOs** são usados para transferência de dados entre camadas
