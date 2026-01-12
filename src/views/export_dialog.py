"""
View: Export Dialog
DESCRIÇÃO: Diálogo de configuração de exportação
RELACIONAMENTOS: ExportController
COMPONENTES:
    - Radio buttons: Exportação Direta / Manual
    - Checkbox: Incluir Gabarito
    - Checkbox: Incluir Resoluções
    - Checkbox: Randomizar Questões
    - Spinner: Colunas (1 ou 2)
    - Spinner: Espaço para respostas (linhas)
    - Slider: Escala de imagens
    - ComboBox: Template LaTeX
    - Botões: Exportar, Cancelar
"""
from PyQt6.QtWidgets import QDialog
import logging
logger = logging.getLogger(__name__)
# TODO: Implementar diálogo de exportação
logger.info("ExportDialog carregado")
