"""
DTOs: Exportação
DESCRIÇÃO: Data Transfer Objects para opções de exportação
"""

from dataclasses import dataclass
from typing import Optional, List

@dataclass
class ExportOptionsDTO:
    """DTO para opções de exportação LaTeX/PDF."""
    id_lista: int  # ID da lista a ser exportada
    layout_colunas: int = 1  # 1 ou 2 colunas
    incluir_gabarito: bool = False
    incluir_resolucoes: bool = False
    randomizar_questoes: bool = False
    escala_imagens: float = 0.7  # Escala das imagens no LaTeX (0.0 a 1.0)
    template_latex: str = "default.tex" # Nome do arquivo do template LaTeX
    tipo_exportacao: str = "direta" # "direta" (PDF) ou "manual" (TEX)
    output_dir: Optional[str] = None # Diretório onde salvar os arquivos

    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return self.__dict__
