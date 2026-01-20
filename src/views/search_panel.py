"""
View: Search Panel
DESCRIÇÃO: Re-export para compatibilidade. A implementacao real esta em pages/search_page.py
"""
# Re-export para compatibilidade com imports existentes
from src.views.pages.search_page import SearchPage, SearchPanel

__all__ = ['SearchPage', 'SearchPanel']
