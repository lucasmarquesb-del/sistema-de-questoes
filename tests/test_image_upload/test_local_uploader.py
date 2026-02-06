"""
Testes para LocalUploader
"""
import os
import sys
import tempfile
import shutil
import pytest
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.services.image_upload import LocalUploader, UploadResult


class TestLocalUploader:
    """Testes para LocalUploader"""

    @pytest.fixture
    def temp_dir(self):
        """Cria diretório temporário para testes"""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp, ignore_errors=True)

    @pytest.fixture
    def temp_image(self, temp_dir):
        """Cria imagem temporária de teste"""
        # Criar uma imagem PNG simples (1x1 pixel transparente)
        img_path = os.path.join(temp_dir, "test_image.png")
        # PNG header mínimo para um pixel transparente
        png_data = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1 pixels
            0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4,
            0x89, 0x00, 0x00, 0x00, 0x0A, 0x49, 0x44, 0x41,
            0x54, 0x78, 0x9C, 0x63, 0x00, 0x01, 0x00, 0x00,
            0x05, 0x00, 0x01, 0x0D, 0x0A, 0x2D, 0xB4, 0x00,
            0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE,
            0x42, 0x60, 0x82
        ])
        with open(img_path, 'wb') as f:
            f.write(png_data)
        return img_path

    def test_nome_servico(self, temp_dir):
        """Testa nome do serviço"""
        uploader = LocalUploader(temp_dir)
        assert uploader.nome_servico == "local"

    def test_is_configured_with_existing_dir(self, temp_dir):
        """Testa configuração com diretório existente"""
        uploader = LocalUploader(temp_dir)
        assert uploader.is_configured() is True

    def test_is_configured_with_nonexistent_dir(self):
        """Testa configuração com diretório inexistente"""
        uploader = LocalUploader("/caminho/que/nao/existe")
        assert uploader.is_configured() is False

    def test_upload_success(self, temp_dir, temp_image):
        """Testa upload bem-sucedido"""
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir)

        uploader = LocalUploader(output_dir)
        result = uploader.upload(temp_image)

        assert result.success is True
        assert result.url is not None
        assert result.servico == "local"
        assert os.path.exists(result.url)

    def test_upload_with_custom_name(self, temp_dir, temp_image):
        """Testa upload com nome customizado"""
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir)

        uploader = LocalUploader(output_dir)
        result = uploader.upload(temp_image, nome="minha_imagem.png")

        assert result.success is True
        assert "minha_imagem.png" in result.url

    def test_upload_file_not_found(self, temp_dir):
        """Testa upload com arquivo inexistente"""
        uploader = LocalUploader(temp_dir)
        result = uploader.upload("/arquivo/que/nao/existe.png")

        assert result.success is False
        assert "não encontrado" in result.erro.lower()

    def test_upload_invalid_extension(self, temp_dir):
        """Testa upload com extensão inválida"""
        # Criar arquivo com extensão inválida
        invalid_file = os.path.join(temp_dir, "arquivo.txt")
        with open(invalid_file, 'w') as f:
            f.write("teste")

        uploader = LocalUploader(temp_dir)
        result = uploader.upload(invalid_file)

        assert result.success is False
        assert "não suportada" in result.erro.lower()

    def test_delete_success(self, temp_dir, temp_image):
        """Testa deleção bem-sucedida"""
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir)

        uploader = LocalUploader(output_dir)
        result = uploader.upload(temp_image, nome="para_deletar.png")

        assert result.success is True
        assert uploader.delete("para_deletar.png") is True
        assert not os.path.exists(result.url)

    def test_delete_nonexistent(self, temp_dir):
        """Testa deleção de arquivo inexistente"""
        uploader = LocalUploader(temp_dir)
        assert uploader.delete("arquivo_que_nao_existe.png") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
