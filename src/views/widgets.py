"""
View: Widgets Personalizados
DESCRIÇÃO: Componentes reutilizáveis da interface
WIDGETS INCLUÍDOS:
    - LatexEditor: Editor de texto com suporte a LaTeX
    - ImagePicker: Seletor de imagens com preview
    - TagTreeWidget: Árvore de tags com checkboxes
    - QuestaoCard: Card de preview de questão
    - DifficultySelector: Seletor de dificuldade com ícones
"""
from PyQt6.QtWidgets import QWidget
import logging
logger = logging.getLogger(__name__)
logger.info("Widgets carregado")
