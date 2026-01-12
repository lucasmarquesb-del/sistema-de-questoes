"""
Util: Validators
DESCRIÇÃO: Funções de validação de dados
RELACIONAMENTOS: Todos os controllers
FUNCIONALIDADES:
    - Validar formato de imagens (PNG, JPG, JPEG, SVG)
    - Validar tamanho de arquivos
    - Validar sintaxe LaTeX
    - Validar campos obrigatórios
    - Validar tipos de dados
"""
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Formatos de imagem permitidos
FORMATOS_IMAGEM_PERMITIDOS = ['.png', '.jpg', '.jpeg', '.svg']
TAMANHO_MAX_IMAGEM_MB = 10

def validar_imagem(caminho: str) -> dict:
    """Valida se arquivo é uma imagem válida"""
    # TODO: Implementar validação completa
    pass

def validar_latex(codigo: str) -> dict:
    """Valida sintaxe básica de LaTeX"""
    # TODO: Implementar validação
    pass

logger.info("Validators carregado")
