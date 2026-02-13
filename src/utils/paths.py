"""
Resolução centralizada de caminhos.
Funciona tanto em modo desenvolvimento quanto empacotado (PyInstaller).
"""

import sys
from pathlib import Path


def get_base_path() -> Path:
    """
    Retorna o diretório raiz do projeto.

    - Empacotado (PyInstaller --onedir): diretório onde está o .exe
    - Desenvolvimento: pasta raiz do projeto (dois níveis acima de src/utils/)
    """
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent.parent.parent
