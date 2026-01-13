"""
Controllers - Export de todos os controllers

NOVA ARQUITETURA (ORM):
- questao_controller_orm.py - Controller de questões usando ORM
- lista_controller_orm.py - Controller de listas usando ORM
- tag_controller_orm.py - Controller de tags usando ORM
- alternativa_controller_orm.py - Controller de alternativas usando ORM

LEGACY (Para referência e migração gradual):
- questao_controller.py - Controller legado de questões
- questao_controller_refactored.py - Controller DDD (intermediário)
- lista_controller.py - Controller legado de listas
- tag_controller.py - Controller legado de tags
- export_controller.py - Controller de exportação
"""

# Controllers ORM (NOVA ARQUITETURA - USAR ESTES)
from .questao_controller_orm import QuestaoControllerORM
from .lista_controller_orm import ListaControllerORM
from .tag_controller_orm import TagControllerORM
from .alternativa_controller_orm import AlternativaControllerORM

# Export dos novos controllers
__all__ = [
    'QuestaoControllerORM',
    'ListaControllerORM',
    'TagControllerORM',
    'AlternativaControllerORM',
]
