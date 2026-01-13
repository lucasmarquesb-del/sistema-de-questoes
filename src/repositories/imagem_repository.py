"""Repository para Imagens (com deduplicação por hash MD5)"""
from typing import Optional, Dict
from sqlalchemy.orm import Session
from models.orm import Imagem
from .base_repository import BaseRepository

class ImagemRepository(BaseRepository[Imagem]):
    def __init__(self, session: Session):
        super().__init__(Imagem, session)
    
    def buscar_por_hash(self, hash_md5: str) -> Optional[Imagem]:
        return self.session.query(Imagem).filter_by(hash_md5=hash_md5, ativo=True).first()
    
    def buscar_por_nome(self, nome_arquivo: str) -> Optional[Imagem]:
        return self.session.query(Imagem).filter_by(nome_arquivo=nome_arquivo, ativo=True).first()
    
    def upload_imagem(self, caminho_arquivo: str, nome_arquivo: str = None) -> Imagem:
        return Imagem.criar_de_arquivo(self.session, caminho_arquivo, nome_arquivo)
    
    def esta_em_uso(self, uuid: str) -> bool:
        imagem = self.buscar_por_uuid(uuid)
        return imagem.esta_em_uso(self.session) if imagem else False
    
    def contar_usos(self, uuid: str) -> Dict[str, int]:
        imagem = self.buscar_por_uuid(uuid)
        return imagem.contar_usos(self.session) if imagem else {'questoes': 0, 'alternativas': 0, 'total': 0}
    
    def deletar_se_nao_usado(self, uuid: str) -> bool:
        if not self.esta_em_uso(uuid):
            return self.deletar(uuid)
        return False
