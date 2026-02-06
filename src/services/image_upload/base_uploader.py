"""
Interface abstrata para serviços de upload de imagem
"""
import os
from abc import ABC, abstractmethod
from typing import Optional, Tuple
from .upload_result import UploadResult


class BaseImageUploader(ABC):
    """Interface abstrata para serviços de upload de imagem"""

    @property
    @abstractmethod
    def nome_servico(self) -> str:
        """Nome identificador do serviço"""
        pass

    @abstractmethod
    def upload(self, caminho_arquivo: str, nome: Optional[str] = None) -> UploadResult:
        """
        Faz upload da imagem e retorna resultado

        Args:
            caminho_arquivo: Caminho local do arquivo
            nome: Nome customizado (opcional)

        Returns:
            UploadResult com URL ou erro
        """
        pass

    @abstractmethod
    def delete(self, id_remoto: str) -> bool:
        """
        Remove imagem do serviço externo

        Args:
            id_remoto: ID da imagem no serviço

        Returns:
            True se removido com sucesso
        """
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """
        Verifica se o serviço está configurado corretamente

        Returns:
            True se as credenciais estão configuradas
        """
        pass

    def validate_file(self, caminho_arquivo: str) -> Tuple[bool, str]:
        """
        Valida se o arquivo pode ser enviado

        Returns:
            Tupla (válido, mensagem_erro)
        """
        if not os.path.exists(caminho_arquivo):
            return False, "Arquivo não encontrado"

        # Verificar extensão
        extensoes_validas = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
        ext = os.path.splitext(caminho_arquivo)[1].lower()
        if ext not in extensoes_validas:
            return False, f"Extensão {ext} não suportada"

        # Verificar tamanho (max 32MB para ImgBB)
        tamanho = os.path.getsize(caminho_arquivo)
        if tamanho > 32 * 1024 * 1024:
            return False, "Arquivo maior que 32MB"

        return True, ""
