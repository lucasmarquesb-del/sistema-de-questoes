"""
Testes para UploaderFactory
"""
import os
import sys
import tempfile
import pytest
from unittest.mock import patch, MagicMock

# Adicionar src ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.services.image_upload import UploaderFactory, ImgBBUploader, LocalUploader


class TestUploaderFactory:
    """Testes para UploaderFactory"""

    @pytest.fixture
    def temp_config_local(self):
        """Cria arquivo de configuração temporário para upload local"""
        temp_dir = tempfile.mkdtemp()
        config_path = os.path.join(temp_dir, "config.ini")

        config_content = """
[IMAGES]
upload_service = local

[PATHS]
images_dir = imagens
"""
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_content)

        yield config_path

        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def temp_config_imgbb(self):
        """Cria arquivo de configuração temporário para ImgBB"""
        temp_dir = tempfile.mkdtemp()
        config_path = os.path.join(temp_dir, "config.ini")

        config_content = """
[IMAGES]
upload_service = imgbb

[IMGBB]
api_key = valid_api_key_12345678

[PATHS]
images_dir = imagens
"""
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_content)

        yield config_path

        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def temp_config_imgbb_no_key(self):
        """Cria arquivo de configuração temporário para ImgBB sem API key"""
        temp_dir = tempfile.mkdtemp()
        config_path = os.path.join(temp_dir, "config.ini")

        config_content = """
[IMAGES]
upload_service = imgbb

[IMGBB]
api_key =

[PATHS]
images_dir = imagens
"""
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_content)

        yield config_path

        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_criar_uploader_local(self, temp_config_local):
        """Testa criação de uploader local"""
        uploader = UploaderFactory.criar_uploader(temp_config_local)

        assert isinstance(uploader, LocalUploader)
        assert uploader.nome_servico == "local"

    def test_criar_uploader_imgbb(self, temp_config_imgbb):
        """Testa criação de uploader ImgBB"""
        uploader = UploaderFactory.criar_uploader(temp_config_imgbb)

        assert isinstance(uploader, ImgBBUploader)
        assert uploader.nome_servico == "imgbb"

    def test_criar_uploader_imgbb_fallback(self, temp_config_imgbb_no_key):
        """Testa fallback para local quando ImgBB não configurado"""
        uploader = UploaderFactory.criar_uploader(temp_config_imgbb_no_key)

        # Deve fazer fallback para local pois API key está vazia
        assert isinstance(uploader, LocalUploader)

    def test_criar_uploader_por_nome_imgbb(self, temp_config_imgbb):
        """Testa criação de uploader por nome - imgbb"""
        uploader = UploaderFactory.criar_uploader_por_nome("imgbb", temp_config_imgbb)

        assert isinstance(uploader, ImgBBUploader)

    def test_criar_uploader_por_nome_local(self, temp_config_local):
        """Testa criação de uploader por nome - local"""
        uploader = UploaderFactory.criar_uploader_por_nome("local", temp_config_local)

        assert isinstance(uploader, LocalUploader)

    def test_criar_uploader_por_nome_invalido(self, temp_config_local):
        """Testa criação de uploader por nome inválido"""
        uploader = UploaderFactory.criar_uploader_por_nome("servico_invalido", temp_config_local)

        assert uploader is None

    def test_criar_uploader_config_inexistente(self):
        """Testa criação com arquivo de config inexistente"""
        # Deve usar valores padrão (local)
        uploader = UploaderFactory.criar_uploader("/caminho/que/nao/existe.ini")

        assert isinstance(uploader, LocalUploader)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
