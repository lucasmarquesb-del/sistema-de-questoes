"""
Implementação do uploader para ImgBB
"""
import base64
import logging
from typing import Optional

import requests

from .base_uploader import BaseImageUploader
from .upload_result import UploadResult

logger = logging.getLogger(__name__)


class ImgBBUploader(BaseImageUploader):
    """Implementação do uploader para ImgBB"""

    API_URL = "https://api.imgbb.com/1/upload"
    TIMEOUT = 30  # segundos

    def __init__(self, api_key: str):
        self._api_key = api_key

    @property
    def nome_servico(self) -> str:
        return "imgbb"

    def is_configured(self) -> bool:
        return bool(self._api_key and len(self._api_key) > 10)

    def upload(self, caminho_arquivo: str, nome: Optional[str] = None) -> UploadResult:
        """Faz upload da imagem para ImgBB"""

        # Validar arquivo
        valido, erro = self.validate_file(caminho_arquivo)
        if not valido:
            return UploadResult(success=False, erro=erro, servico=self.nome_servico)

        # Verificar configuração
        if not self.is_configured():
            return UploadResult(
                success=False,
                erro="API key do ImgBB não configurada",
                servico=self.nome_servico
            )

        try:
            # Ler e codificar imagem em base64
            with open(caminho_arquivo, "rb") as f:
                imagem_base64 = base64.b64encode(f.read()).decode("utf-8")

            # Preparar payload
            payload = {
                "key": self._api_key,
                "image": imagem_base64,
            }

            if nome:
                payload["name"] = nome

            # Fazer requisição
            logger.info(f"Iniciando upload para ImgBB: {caminho_arquivo}")
            response = requests.post(
                self.API_URL,
                data=payload,
                timeout=self.TIMEOUT
            )

            # Processar resposta
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    img_data = data["data"]
                    logger.info(f"Upload bem-sucedido. ID: {img_data['id']}")

                    return UploadResult(
                        success=True,
                        url=img_data["url"],
                        url_thumbnail=img_data.get("thumb", {}).get("url"),
                        url_medium=img_data.get("medium", {}).get("url"),
                        id_remoto=img_data["id"],
                        delete_url=img_data.get("delete_url"),
                        servico=self.nome_servico
                    )
                else:
                    erro = data.get("error", {}).get("message", "Erro desconhecido")
                    logger.error(f"Erro no upload: {erro}")
                    return UploadResult(success=False, erro=erro, servico=self.nome_servico)
            else:
                erro = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"Erro HTTP no upload: {erro}")
                return UploadResult(success=False, erro=erro, servico=self.nome_servico)

        except requests.Timeout:
            logger.error("Timeout no upload para ImgBB")
            return UploadResult(
                success=False,
                erro="Timeout - servidor não respondeu",
                servico=self.nome_servico
            )
        except requests.RequestException as e:
            logger.error(f"Erro de conexão: {e}")
            return UploadResult(
                success=False,
                erro=f"Erro de conexão: {str(e)}",
                servico=self.nome_servico
            )
        except Exception as e:
            logger.exception(f"Erro inesperado no upload: {e}")
            return UploadResult(
                success=False,
                erro=f"Erro inesperado: {str(e)}",
                servico=self.nome_servico
            )

    def delete(self, id_remoto: str) -> bool:
        """
        ImgBB não oferece API de deleção via ID.
        A deleção deve ser feita via delete_url (se salva)
        """
        logger.warning("ImgBB não suporta deleção via API. Use delete_url manualmente.")
        return False
