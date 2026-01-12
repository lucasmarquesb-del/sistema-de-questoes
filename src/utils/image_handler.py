"""
Util: Image Handler
DESCRIÇÃO: Manipulação e gerenciamento de imagens
RELACIONAMENTOS: Pillow, QuestaoModel, AlternativaModel
FUNCIONALIDADES:
    - Copiar imagens para pasta do sistema
    - Redimensionar imagens
    - Validar formato e tamanho
    - Gerar nomes únicos
    - Limpar imagens órfãs
CONVENÇÃO DE NOMES:
    - Enunciados: questao_{id}_enunciado.{ext}
    - Alternativas: questao_{id}_alt_{letra}.{ext}
"""
import logging
from pathlib import Path
logger = logging.getLogger(__name__)
# TODO: Implementar cópia de imagens
# TODO: Implementar limpeza de órfãs
logger.info("ImageHandler carregado")
