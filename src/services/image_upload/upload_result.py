"""
Dataclass para resultado de upload de imagem
"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class UploadResult:
    """Resultado de uma operação de upload"""
    success: bool
    url: Optional[str] = None
    url_thumbnail: Optional[str] = None
    url_medium: Optional[str] = None
    id_remoto: Optional[str] = None
    servico: Optional[str] = None
    delete_url: Optional[str] = None
    erro: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
