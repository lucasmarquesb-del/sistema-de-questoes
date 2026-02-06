"""
Factory para criar o uploader apropriado baseado na configuração
"""
import configparser
import logging
from typing import Optional
from .base_uploader import BaseImageUploader
from .imgbb_uploader import ImgBBUploader
from .local_uploader import LocalUploader

logger = logging.getLogger(__name__)


class UploaderFactory:
    """Factory para criar o uploader apropriado baseado na configuração"""

    @staticmethod
    def criar_uploader(config_path: str = "config.ini") -> BaseImageUploader:
        """
        Cria o uploader baseado na configuração

        Args:
            config_path: Caminho para o arquivo de configuração

        Returns:
            Instância do uploader configurado
        """
        config = configparser.ConfigParser()
        config.read(config_path, encoding='utf-8')

        # Ler serviço configurado
        servico = config.get("IMAGES", "upload_service", fallback="local")
        logger.info(f"Serviço de upload configurado: {servico}")

        if servico == "imgbb":
            api_key = config.get("IMGBB", "api_key", fallback="")
            uploader = ImgBBUploader(api_key)

            if uploader.is_configured():
                logger.info("ImgBB configurado com sucesso")
                return uploader
            else:
                logger.warning("ImgBB não configurado, usando fallback local")

        # Fallback para local
        images_dir = config.get("PATHS", "images_dir", fallback="imagens")
        return LocalUploader(images_dir)

    @staticmethod
    def criar_uploader_por_nome(nome: str, config_path: str = "config.ini") -> Optional[BaseImageUploader]:
        """
        Cria um uploader específico pelo nome

        Args:
            nome: Nome do serviço (imgbb, local)
            config_path: Caminho para o arquivo de configuração
        """
        config = configparser.ConfigParser()
        config.read(config_path, encoding='utf-8')

        if nome == "imgbb":
            api_key = config.get("IMGBB", "api_key", fallback="")
            return ImgBBUploader(api_key)
        elif nome == "local":
            images_dir = config.get("PATHS", "images_dir", fallback="imagens")
            return LocalUploader(images_dir)

        return None
