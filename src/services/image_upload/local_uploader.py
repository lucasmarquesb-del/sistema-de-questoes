"""
Uploader local (fallback) - comportamento atual do sistema
"""
import os
import shutil
import uuid
import logging
from typing import Optional
from .base_uploader import BaseImageUploader
from .upload_result import UploadResult

logger = logging.getLogger(__name__)


class LocalUploader(BaseImageUploader):
    """Uploader local (fallback) - comportamento atual do sistema"""

    def __init__(self, diretorio_base: str):
        self._diretorio_base = diretorio_base

    @property
    def nome_servico(self) -> str:
        return "local"

    def is_configured(self) -> bool:
        return os.path.isdir(self._diretorio_base)

    def upload(self, caminho_arquivo: str, nome: Optional[str] = None) -> UploadResult:
        """Copia imagem para diretório local"""

        valido, erro = self.validate_file(caminho_arquivo)
        if not valido:
            return UploadResult(success=False, erro=erro, servico=self.nome_servico)

        try:
            # Gerar nome único
            ext = os.path.splitext(caminho_arquivo)[1]
            nome_final = nome or f"{uuid.uuid4().hex}{ext}"
            destino = os.path.join(self._diretorio_base, nome_final)

            # Criar diretório se não existir
            os.makedirs(self._diretorio_base, exist_ok=True)

            # Copiar arquivo
            shutil.copy2(caminho_arquivo, destino)
            logger.info(f"Imagem copiada para: {destino}")

            return UploadResult(
                success=True,
                url=destino,  # Caminho local como "URL"
                id_remoto=nome_final,
                servico=self.nome_servico
            )
        except Exception as e:
            logger.error(f"Erro no upload local: {e}")
            return UploadResult(
                success=False,
                erro=str(e),
                servico=self.nome_servico
            )

    def delete(self, id_remoto: str) -> bool:
        """Remove arquivo local"""
        try:
            caminho = os.path.join(self._diretorio_base, id_remoto)
            if os.path.exists(caminho):
                os.remove(caminho)
                logger.info(f"Arquivo removido: {caminho}")
                return True
            return False
        except Exception as e:
            logger.error(f"Erro ao remover arquivo: {e}")
            return False
