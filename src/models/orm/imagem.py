"""
Model ORM para Imagem (Centralizada)
"""
import hashlib
import os
from typing import Optional
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import BaseModel


class Imagem(BaseModel):
    """
    Tabela centralizada de imagens
    Evita duplicação através de hash MD5
    Suporta upload para serviços externos (ImgBB, etc.)
    """
    __tablename__ = 'imagem'

    nome_arquivo = Column(String(255), unique=True, nullable=False, index=True)
    caminho_relativo = Column(String(500), nullable=False)
    hash_md5 = Column(String(32), unique=True, nullable=False, index=True)
    tamanho_bytes = Column(Integer, nullable=False)
    largura = Column(Integer, nullable=False)
    altura = Column(Integer, nullable=False)
    formato = Column(String(10), nullable=False)
    mime_type = Column(String(50), nullable=False)
    data_upload = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Campos para imagem remota
    url_remota = Column(String(1000), nullable=True, index=True)
    servico_hospedagem = Column(String(50), nullable=True, index=True)
    id_remoto = Column(String(255), nullable=True)
    url_thumbnail = Column(String(1000), nullable=True)
    data_upload_remoto = Column(DateTime, nullable=True)

    # Relationships
    questoes_enunciado = relationship("Questao", back_populates="imagem_enunciado", foreign_keys="Questao.uuid_imagem_enunciado")
    alternativas = relationship("Alternativa", back_populates="imagem")

    def __repr__(self):
        return f"<Imagem(nome={self.nome_arquivo}, hash={self.hash_md5[:8]})>"

    def tem_url_remota(self) -> bool:
        """Verifica se a imagem tem URL externa"""
        return bool(self.url_remota)

    def get_url_para_exibicao(self) -> str:
        """Retorna URL remota ou caminho local"""
        if self.url_remota:
            return self.url_remota
        return self.caminho_relativo

    @classmethod
    def calcular_hash_md5(cls, caminho_arquivo: str) -> str:
        """
        Calcula hash MD5 do arquivo para detectar duplicatas

        Args:
            caminho_arquivo: Caminho completo do arquivo

        Returns:
            String com hash MD5 em hexadecimal
        """
        hash_md5 = hashlib.md5()
        with open(caminho_arquivo, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    @classmethod
    def buscar_por_hash(cls, session, hash_md5: str):
        """
        Busca imagem pelo hash MD5 (detecta duplicatas)

        Args:
            session: Sessão do SQLAlchemy
            hash_md5: Hash MD5 da imagem

        Returns:
            Objeto Imagem ou None
        """
        return session.query(cls).filter_by(hash_md5=hash_md5, ativo=True).first()

    @classmethod
    def buscar_por_nome(cls, session, nome_arquivo: str):
        """Busca imagem por nome de arquivo"""
        return session.query(cls).filter_by(nome_arquivo=nome_arquivo, ativo=True).first()

    @classmethod
    def criar_de_arquivo(cls, session, caminho_arquivo: str, nome_arquivo: str = None):
        """
        Cria registro de imagem a partir de arquivo físico
        Se já existir uma imagem com o mesmo hash, retorna a existente

        Args:
            session: Sessão do SQLAlchemy
            caminho_arquivo: Caminho completo do arquivo de imagem
            nome_arquivo: Nome customizado (opcional)

        Returns:
            Objeto Imagem (novo ou existente)
        """
        # Calcular hash
        hash_md5 = cls.calcular_hash_md5(caminho_arquivo)

        # Verificar se já existe (deduplicação)
        imagem_existente = cls.buscar_por_hash(session, hash_md5)
        if imagem_existente:
            return imagem_existente

        # Obter metadados da imagem usando Pillow
        try:
            from PIL import Image as PILImage
            with PILImage.open(caminho_arquivo) as img:
                largura, altura = img.size
                formato = img.format.upper() if img.format else 'UNKNOWN'
        except Exception:
            # Fallback se não conseguir abrir com PIL
            largura = altura = 0
            formato = os.path.splitext(caminho_arquivo)[1].upper().replace('.', '')

        # Obter tamanho do arquivo
        tamanho_bytes = os.path.getsize(caminho_arquivo)

        # Determinar MIME type
        extensao_para_mime = {
            'PNG': 'image/png',
            'JPG': 'image/jpeg',
            'JPEG': 'image/jpeg',
            'GIF': 'image/gif',
            'BMP': 'image/bmp',
            'SVG': 'image/svg+xml',
            'WEBP': 'image/webp'
        }
        mime_type = extensao_para_mime.get(formato, 'image/unknown')

        # Criar novo registro
        nova_imagem = cls(
            nome_arquivo=nome_arquivo or os.path.basename(caminho_arquivo),
            caminho_relativo=caminho_arquivo,
            hash_md5=hash_md5,
            tamanho_bytes=tamanho_bytes,
            largura=largura,
            altura=altura,
            formato=formato,
            mime_type=mime_type
        )

        session.add(nova_imagem)
        session.flush()
        return nova_imagem

    def esta_em_uso(self, session) -> bool:
        """
        Verifica se a imagem está sendo usada em questões ou alternativas

        Returns:
            True se está em uso, False caso contrário
        """
        from .questao import Questao
        from .alternativa import Alternativa

        questoes_count = session.query(Questao).filter(
            Questao.uuid_imagem_enunciado == self.uuid,
            Questao.ativo == True
        ).count()

        alternativas_count = session.query(Alternativa).filter(
            Alternativa.uuid_imagem == self.uuid
        ).count()

        return (questoes_count + alternativas_count) > 0

    def contar_usos(self, session) -> dict:
        """
        Retorna a contagem de usos da imagem

        Returns:
            Dict com contagem de questões e alternativas
        """
        from .questao import Questao
        from .alternativa import Alternativa

        questoes_count = session.query(Questao).filter(
            Questao.uuid_imagem_enunciado == self.uuid,
            Questao.ativo == True
        ).count()

        alternativas_count = session.query(Alternativa).filter(
            Alternativa.uuid_imagem == self.uuid
        ).count()

        return {
            'questoes': questoes_count,
            'alternativas': alternativas_count,
            'total': questoes_count + alternativas_count
        }
