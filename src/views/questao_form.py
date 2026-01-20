"""
View: Questao Form
DESCRICAO: Re-export para compatibilidade. A implementacao real esta em pages/questao_form_page.py
"""
# Re-export para compatibilidade com imports existentes
from src.views.pages.questao_form_page import QuestaoFormPage, QuestaoForm

__all__ = ['QuestaoFormPage', 'QuestaoForm']
