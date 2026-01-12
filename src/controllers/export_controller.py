"""
Controller: Export
DESCRIÇÃO: Gerencia exportação de listas para LaTeX/PDF
RELACIONAMENTOS: ListaModel, QuestaoModel, AlternativaModel
USADO POR: ExportDialog (view)
FUNCIONALIDADES:
    - Gerar arquivo .tex a partir de uma lista
    - Compilar LaTeX para PDF
    - Aplicar randomização de questões
    - Incluir/excluir gabarito e resoluções
"""
import logging
logger = logging.getLogger(__name__)
# TODO: Implementar geração de arquivo .tex
# TODO: Implementar compilação com pdflatex
# TODO: Implementar randomização de ordem
logger.info("ExportController carregado")
