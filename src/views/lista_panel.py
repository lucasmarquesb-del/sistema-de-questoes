"""
View: Lista Panel
DESCRIÇÃO: Re-export para compatibilidade. A implementacao real esta em pages/lista_page.py
"""
# Re-export para compatibilidade com imports existentes
from src.views.pages.lista_page import ListaPage, ListaPanel

__all__ = ['ListaPage', 'ListaPanel']
