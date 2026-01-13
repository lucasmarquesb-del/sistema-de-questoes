"""
DTOs: Filtros
DESCRIÇÃO: Data Transfer Objects para filtros de busca
"""

from typing import Optional, List
from dataclasses import dataclass, field


@dataclass
class FiltroQuestaoDTO:
    """DTO para filtros de busca de questões"""

    titulo: Optional[str] = None
    tipo: Optional[str] = None  # 'OBJETIVA' ou 'DISCURSIVA'
    ano_inicio: Optional[int] = None
    ano_fim: Optional[int] = None
    fonte: Optional[str] = None
    id_dificuldade: Optional[int] = None
    tags: List[int] = field(default_factory=list)
    ativa: bool = True

    def to_dict(self) -> dict:
        """Converte para dicionário (apenas campos não-None/não-vazios)"""
        dados = {}

        if self.titulo:
            dados['titulo'] = self.titulo
        if self.tipo:
            dados['tipo'] = self.tipo
        if self.ano_inicio is not None:
            dados['ano_inicio'] = self.ano_inicio
        if self.ano_fim is not None:
            dados['ano_fim'] = self.ano_fim
        if self.fonte:
            dados['fonte'] = self.fonte
        if self.id_dificuldade is not None:
            dados['id_dificuldade'] = self.id_dificuldade
        if self.tags:
            dados['tags'] = self.tags
        dados['ativa'] = self.ativa

        return dados

    @classmethod
    def from_dict(cls, data: dict) -> 'FiltroQuestaoDTO':
        """Cria DTO a partir de dicionário"""
        return cls(
            titulo=data.get('titulo'),
            tipo=data.get('tipo'),
            ano_inicio=data.get('ano_inicio'),
            ano_fim=data.get('ano_fim'),
            fonte=data.get('fonte'),
            id_dificuldade=data.get('id_dificuldade'),
            tags=data.get('tags', []),
            ativa=data.get('ativa', True)
        )

    def tem_filtros(self) -> bool:
        """Verifica se há filtros ativos (além de 'ativa')"""
        return any([
            self.titulo,
            self.tipo,
            self.ano_inicio is not None,
            self.ano_fim is not None,
            self.fonte,
            self.id_dificuldade is not None,
            self.tags
        ])
