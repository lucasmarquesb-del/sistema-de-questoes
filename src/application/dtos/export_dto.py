"""
DTOs para Export - Compatibilidade com views
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class ExportOptionsDTO:
    """DTO para opcoes de exportacao"""
    id_lista: str  # Codigo da lista (ex: LST-2026-0001)
    template_latex: str
    tipo_exportacao: str = "direta"  # "direta" ou "manual"
    output_dir: Optional[str] = None
    incluir_gabarito: bool = True
    incluir_resolucao: bool = False
    incluir_resolucoes: bool = False  # Alias para compatibilidade
    layout_colunas: int = 1
    randomizar_questoes: bool = False
    escala_imagens: float = 1.0
    # Campos opcionais para templates específicos (ex: wallon_av2)
    trimestre: Optional[str] = None
    professor: Optional[str] = None
    disciplina: Optional[str] = None
    ano: Optional[str] = None
