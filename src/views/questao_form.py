"""
View: Questão Form
DESCRIÇÃO: Formulário de cadastro/edição de questões
RELACIONAMENTOS: QuestaoController, AlternativaModel, TagModel
COMPONENTES:
    - Campo título (opcional)
    - Editor de enunciado (suporta LaTeX)
    - Radio buttons: Objetiva/Discursiva
    - Campos: Ano, Fonte, Dificuldade
    - Botão adicionar imagem
    - Preview LaTeX
    - 5 campos de alternativas (se objetiva)
    - Seleção de tags (árvore hierárquica)
    - Botões: Salvar, Cancelar, Preview
"""
from PyQt6.QtWidgets import QDialog
import logging
logger = logging.getLogger(__name__)
# TODO: Implementar formulário completo
logger.info("QuestaoForm carregado")
