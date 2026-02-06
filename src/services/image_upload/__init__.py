"""
Serviços de Upload de Imagens

Módulo responsável pelo upload de imagens para serviços externos
(ImgBB, Cloudinary, S3) ou armazenamento local.
"""

from .upload_result import UploadResult
from .base_uploader import BaseImageUploader
from .imgbb_uploader import ImgBBUploader
from .local_uploader import LocalUploader
from .uploader_factory import UploaderFactory

__all__ = [
    "UploadResult",
    "BaseImageUploader",
    "ImgBBUploader",
    "LocalUploader",
    "UploaderFactory"
]
