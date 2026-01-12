"""
View: Tag Manager
DESCRIÇÃO: Interface de gerenciamento de tags
RELACIONAMENTOS: TagController
COMPONENTES:
    - Árvore hierárquica de tags
    - Botões: Nova Tag, Editar, Inativar, Reativar
    - Drag-and-drop para reorganizar (opcional)
    - Contador de questões por tag
    - Validação de nomes duplicados
"""
from PyQt6.QtWidgets import QDialog
import logging
logger = logging.getLogger(__name__)
# TODO: Implementar gerenciador de tags
logger.info("TagManager carregado")
