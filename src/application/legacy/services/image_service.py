"""
Service: Image Processing
DESCRIÇÃO: Serviço especializado em processamento de imagens
RESPONSABILIDADE ÚNICA: Gerenciar upload, processamento e armazenamento de imagens
BENEFÍCIOS:
    - Isola lógica de infraestrutura do controller
    - Facilita mudança de estratégia de armazenamento (local -> cloud)
    - Permite adicionar processamentos (resize, compress) sem modificar controller
"""

import shutil
import logging
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


class ImageService:
    """Serviço de processamento de imagens"""

    # Extensões de imagem suportadas
    EXTENSOES_VALIDAS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg'}

    def __init__(self, imagens_dir: Path):
        """
        Args:
            imagens_dir: Diretório raiz para armazenar imagens
        """
        self.imagens_dir = imagens_dir
        self._garantir_estrutura_diretorios()

    def _garantir_estrutura_diretorios(self):
        """Cria estrutura de diretórios se não existir"""
        subdirs = ['questoes', 'alternativas', 'temp']

        for subdir in subdirs:
            dir_path = self.imagens_dir / subdir
            dir_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Estrutura de diretórios garantida em: {self.imagens_dir}")

    def processar_imagem_questao(
        self,
        caminho_origem: str,
        id_questao: Optional[int] = None
    ) -> Optional[str]:
        """Processa e armazena imagem de questão

        Args:
            caminho_origem: Caminho da imagem original
            id_questao: ID da questão (opcional, para nomeação)

        Returns:
            Caminho relativo da imagem armazenada ou None em caso de erro
        """
        return self._processar_imagem(
            caminho_origem=caminho_origem,
            tipo_dir='questoes',
            prefixo='questao',
            id_entidade=id_questao
        )

    def processar_imagem_alternativa(
        self,
        caminho_origem: str,
        id_alternativa: Optional[int] = None
    ) -> Optional[str]:
        """Processa e armazena imagem de alternativa

        Args:
            caminho_origem: Caminho da imagem original
            id_alternativa: ID da alternativa (opcional, para nomeação)

        Returns:
            Caminho relativo da imagem armazenada ou None em caso de erro
        """
        return self._processar_imagem(
            caminho_origem=caminho_origem,
            tipo_dir='alternativas',
            prefixo='alternativa',
            id_entidade=id_alternativa
        )

    def _processar_imagem(
        self,
        caminho_origem: str,
        tipo_dir: str,
        prefixo: str,
        id_entidade: Optional[int] = None
    ) -> Optional[str]:
        """Processa e armazena imagem

        Args:
            caminho_origem: Caminho da imagem original
            tipo_dir: Subdiretório ('questoes' ou 'alternativas')
            prefixo: Prefixo do nome do arquivo
            id_entidade: ID da entidade (opcional)

        Returns:
            Caminho relativo da imagem ou None em caso de erro
        """
        try:
            origem = Path(caminho_origem)

            # Validar existência
            if not origem.exists():
                logger.error(f"Arquivo de imagem não encontrado: {caminho_origem}")
                return None

            # Validar extensão
            if origem.suffix.lower() not in self.EXTENSOES_VALIDAS:
                logger.error(
                    f"Extensão de imagem não suportada: {origem.suffix}. "
                    f"Extensões válidas: {', '.join(self.EXTENSOES_VALIDAS)}"
                )
                return None

            # Gerar nome único
            nome_arquivo = self._gerar_nome_unico(
                prefixo=prefixo,
                extensao=origem.suffix,
                id_entidade=id_entidade,
                caminho_origem=caminho_origem
            )

            # Diretório de destino
            dir_destino = self.imagens_dir / tipo_dir
            destino = dir_destino / nome_arquivo

            # Copiar arquivo
            shutil.copy2(origem, destino)

            # Retornar caminho relativo
            caminho_relativo = f"imagens/{tipo_dir}/{nome_arquivo}"

            logger.info(f"Imagem processada: {origem.name} -> {caminho_relativo}")

            return caminho_relativo

        except Exception as e:
            logger.error(f"Erro ao processar imagem: {e}", exc_info=True)
            return None

    def _gerar_nome_unico(
        self,
        prefixo: str,
        extensao: str,
        id_entidade: Optional[int],
        caminho_origem: str
    ) -> str:
        """Gera nome único para arquivo

        Args:
            prefixo: Prefixo do nome
            extensao: Extensão do arquivo
            id_entidade: ID da entidade (opcional)
            caminho_origem: Caminho original (para hash)

        Returns:
            Nome único do arquivo
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Hash do conteúdo para garantir unicidade
        hash_conteudo = self._calcular_hash_arquivo(caminho_origem)[:8]

        if id_entidade:
            nome = f"{prefixo}_{id_entidade}_{timestamp}_{hash_conteudo}{extensao}"
        else:
            nome = f"{prefixo}_{timestamp}_{hash_conteudo}{extensao}"

        return nome

    def _calcular_hash_arquivo(self, caminho: str) -> str:
        """Calcula hash MD5 de um arquivo

        Args:
            caminho: Caminho do arquivo

        Returns:
            Hash MD5 hexadecimal
        """
        try:
            hash_md5 = hashlib.md5()
            with open(caminho, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.warning(f"Erro ao calcular hash: {e}")
            return "nohash"

    def validar_imagem(self, caminho: str) -> Tuple[bool, Optional[str]]:
        """Valida se arquivo é uma imagem válida

        Args:
            caminho: Caminho do arquivo

        Returns:
            Tupla (valido, mensagem_erro)
        """
        origem = Path(caminho)

        if not origem.exists():
            return False, f"Arquivo não encontrado: {caminho}"

        if not origem.is_file():
            return False, f"Caminho não é um arquivo: {caminho}"

        if origem.suffix.lower() not in self.EXTENSOES_VALIDAS:
            return False, (
                f"Extensão não suportada: {origem.suffix}. "
                f"Extensões válidas: {', '.join(self.EXTENSOES_VALIDAS)}"
            )

        # Validar tamanho (máximo 10MB)
        tamanho_mb = origem.stat().st_size / (1024 * 1024)
        if tamanho_mb > 10:
            return False, f"Arquivo muito grande: {tamanho_mb:.1f}MB (máximo 10MB)"

        return True, None

    def deletar_imagem(self, caminho_relativo: str) -> bool:
        """Deleta uma imagem

        Args:
            caminho_relativo: Caminho relativo da imagem (ex: 'imagens/questoes/...')

        Returns:
            True se deleção bem-sucedida, False caso contrário
        """
        try:
            # Remover prefixo 'imagens/' se presente
            if caminho_relativo.startswith('imagens/'):
                caminho_relativo = caminho_relativo[8:]

            caminho_completo = self.imagens_dir / caminho_relativo

            if caminho_completo.exists():
                caminho_completo.unlink()
                logger.info(f"Imagem deletada: {caminho_relativo}")
                return True
            else:
                logger.warning(f"Imagem não encontrada para deleção: {caminho_relativo}")
                return False

        except Exception as e:
            logger.error(f"Erro ao deletar imagem: {e}", exc_info=True)
            return False

    def obter_caminho_completo(self, caminho_relativo: str) -> Optional[Path]:
        """Obtém caminho completo de uma imagem

        Args:
            caminho_relativo: Caminho relativo da imagem

        Returns:
            Path completo ou None se não existir
        """
        try:
            # Remover prefixo 'imagens/' se presente
            if caminho_relativo.startswith('imagens/'):
                caminho_relativo = caminho_relativo[8:]

            caminho_completo = self.imagens_dir / caminho_relativo

            if caminho_completo.exists():
                return caminho_completo
            else:
                return None

        except Exception:
            return None
