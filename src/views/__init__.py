"""
Views Package
Contem todas as views (paginas e componentes) da aplicacao

Estrutura:
    - pages/: Paginas completas (telas principais)
    - components/: Componentes reutilizaveis
        - layout/: Componentes de layout (header, sidebar)
        - cards/: Cards de exibicao de dados
        - forms/: Componentes de formulario
        - filters/: Componentes de filtro e busca
        - dialogs/: Dialogos modais
        - common/: Componentes genericos
    - styles/: Estilos e temas
"""

# Re-exports para compatibilidade com imports existentes
from src.views.widgets import (
    LatexEditor,
    ImagePicker,
    TagTreeWidget,
    QuestaoCard,
    DifficultySelector,
    ImageInsertDialog,
    TableSizeDialog,
    TableEditorDialog,
    ColorPickerDialog,
)

from src.views.tag_manager import TagManager
from src.views.export_dialog import ExportDialog
from src.views.lista_form import ListaForm
from src.views.questao_selector_dialog import QuestaoSelectorDialog
from src.views.questao_preview import QuestaoPreview
from src.views.search_panel import SearchPanel, SearchPage
from src.views.lista_panel import ListaPanel, ListaPage
from src.views.questao_form import QuestaoForm, QuestaoFormPage

__all__ = [
    # Widgets/Componentes
    'LatexEditor',
    'ImagePicker',
    'TagTreeWidget',
    'QuestaoCard',
    'DifficultySelector',
    'ImageInsertDialog',
    'TableSizeDialog',
    'TableEditorDialog',
    'ColorPickerDialog',
    # Paginas/Dialogos
    'TagManager',
    'ExportDialog',
    'ListaForm',
    'QuestaoSelectorDialog',
    'QuestaoPreview',
    'SearchPanel',
    'SearchPage',
    'ListaPanel',
    'ListaPage',
    'QuestaoForm',
    'QuestaoFormPage',
]
