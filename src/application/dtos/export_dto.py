"""
DTOs para Export - Compatibilidade com views
"""
from dataclasses import dataclass, field
from typing import Optional, List


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
    # Campos para exportação randomizada (múltiplas versões)
    gerar_versoes_randomizadas: bool = False
    quantidade_versoes: int = 1  # 1-4 versões (TIPO A, B, C, D)
    sufixo_versao: Optional[str] = None  # Ex: "TIPO A", "TIPO B"
    # Campos específicos para template CEAB (simuladoCeab)
    data_aplicacao: Optional[str] = None  # Ex: "02/12/2025"
    serie_simulado: Optional[str] = None  # Ex: "3º ANO VESPERTINO"
    unidade: Optional[str] = None  # I, II ou III
    tipo_simulado: Optional[str] = None  # Ex: "LINGUAGENS, CÓDIGOS E SUAS TECNOLOGIAS"
