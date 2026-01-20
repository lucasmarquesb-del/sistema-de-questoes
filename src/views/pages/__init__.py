"""
Views: Pages
Paginas completas da aplicacao (telas principais)
"""

from src.views.pages.main_window import MainWindow
from src.views.pages.tag_manager_page import TagManager
from src.views.pages.export_page import ExportDialog
from src.views.pages.lista_form_page import ListaForm
from src.views.pages.questao_selector_page import QuestaoSelectorDialog, QuestaoSelectorCard
from src.views.pages.questao_preview_page import QuestaoPreview
from src.views.pages.search_page import SearchPage, SearchPanel
from src.views.pages.lista_page import ListaPage, ListaPanel
from src.views.pages.questao_form_page import QuestaoFormPage, QuestaoForm
from src.views.pages.dashboard_page import DashboardPage, Dashboard

__all__ = [
    'MainWindow',
    'TagManager',
    'ExportDialog',
    'ListaForm',
    'QuestaoSelectorDialog',
    'QuestaoSelectorCard',
    'QuestaoPreview',
    'SearchPage',
    'SearchPanel',
    'ListaPage',
    'ListaPanel',
    'QuestaoFormPage',
    'QuestaoForm',
    'DashboardPage',
    'Dashboard',
]
