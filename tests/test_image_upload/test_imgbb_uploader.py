"""
Testes para ImgBBUploader
"""
import os
import sys
import tempfile
import pytest
from unittest.mock import patch, MagicMock

# Adicionar src ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.services.image_upload import ImgBBUploader, UploadResult


class TestImgBBUploader:
    """Testes para ImgBBUploader"""

    @pytest.fixture
    def temp_image(self):
        """Cria imagem temporária de teste"""
        temp_dir = tempfile.mkdtemp()
        img_path = os.path.join(temp_dir, "test_image.png")
        # PNG header mínimo
        png_data = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
            0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4,
            0x89, 0x00, 0x00, 0x00, 0x0A, 0x49, 0x44, 0x41,
            0x54, 0x78, 0x9C, 0x63, 0x00, 0x01, 0x00, 0x00,
            0x05, 0x00, 0x01, 0x0D, 0x0A, 0x2D, 0xB4, 0x00,
            0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE,
            0x42, 0x60, 0x82
        ])
        with open(img_path, 'wb') as f:
            f.write(png_data)
        yield img_path
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_nome_servico(self):
        """Testa nome do serviço"""
        uploader = ImgBBUploader("fake_api_key_12345")
        assert uploader.nome_servico == "imgbb"

    def test_is_configured_with_valid_key(self):
        """Testa configuração com API key válida"""
        uploader = ImgBBUploader("valid_api_key_12345678")
        assert uploader.is_configured() is True

    def test_is_configured_with_short_key(self):
        """Testa configuração com API key curta"""
        uploader = ImgBBUploader("short")
        assert uploader.is_configured() is False

    def test_is_configured_with_empty_key(self):
        """Testa configuração com API key vazia"""
        uploader = ImgBBUploader("")
        assert uploader.is_configured() is False

    def test_upload_without_configuration(self, temp_image):
        """Testa upload sem API key configurada"""
        uploader = ImgBBUploader("")
        result = uploader.upload(temp_image)

        assert result.success is False
        assert "não configurada" in result.erro.lower()

    @patch('requests.post')
    def test_upload_success(self, mock_post, temp_image):
        """Testa upload bem-sucedido (mockado)"""
        # Configurar mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "data": {
                "id": "abc123",
                "url": "https://i.ibb.co/abc123/image.png",
                "thumb": {"url": "https://i.ibb.co/abc123/image_thumb.png"},
                "medium": {"url": "https://i.ibb.co/abc123/image_medium.png"},
                "delete_url": "https://ibb.co/abc123/delete"
            }
        }
        mock_post.return_value = mock_response

        uploader = ImgBBUploader("valid_api_key_12345678")
        result = uploader.upload(temp_image)

        assert result.success is True
        assert result.url == "https://i.ibb.co/abc123/image.png"
        assert result.id_remoto == "abc123"
        assert result.servico == "imgbb"
        assert result.url_thumbnail is not None

    @patch('requests.post')
    def test_upload_api_error(self, mock_post, temp_image):
        """Testa upload com erro da API"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": False,
            "error": {"message": "Invalid image"}
        }
        mock_post.return_value = mock_response

        uploader = ImgBBUploader("valid_api_key_12345678")
        result = uploader.upload(temp_image)

        assert result.success is False
        assert "Invalid image" in result.erro

    @patch('requests.post')
    def test_upload_http_error(self, mock_post, temp_image):
        """Testa upload com erro HTTP"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        uploader = ImgBBUploader("valid_api_key_12345678")
        result = uploader.upload(temp_image)

        assert result.success is False
        assert "500" in result.erro

    @patch('requests.post')
    def test_upload_timeout(self, mock_post, temp_image):
        """Testa upload com timeout"""
        import requests
        mock_post.side_effect = requests.Timeout()

        uploader = ImgBBUploader("valid_api_key_12345678")
        result = uploader.upload(temp_image)

        assert result.success is False
        assert "timeout" in result.erro.lower()

    @patch('requests.post')
    def test_upload_connection_error(self, mock_post, temp_image):
        """Testa upload com erro de conexão"""
        import requests
        mock_post.side_effect = requests.ConnectionError("Connection refused")

        uploader = ImgBBUploader("valid_api_key_12345678")
        result = uploader.upload(temp_image)

        assert result.success is False
        assert "conexão" in result.erro.lower()

    def test_upload_file_not_found(self):
        """Testa upload com arquivo inexistente"""
        uploader = ImgBBUploader("valid_api_key_12345678")
        result = uploader.upload("/arquivo/que/nao/existe.png")

        assert result.success is False
        assert "não encontrado" in result.erro.lower()

    def test_delete_not_supported(self):
        """Testa que deleção retorna False (não suportada)"""
        uploader = ImgBBUploader("valid_api_key_12345678")
        assert uploader.delete("some_id") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
