"""
DTOs para Export - Compatibilidade com views
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class ExportOptionsDTO:
    """DTO para opções de exportação"""
    id_lista: int
    template_latex: str
    tipo_exportacao: str = "direta"  # "direta" ou "manual"
    output_dir: Optional[str] = None
    incluir_gabarito: bool = True
    incluir_resolucao: bool = False
