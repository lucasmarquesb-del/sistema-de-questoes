"""Repository para Imagens (com deduplicação por hash MD5 e upload remoto)"""
import logging
from typing import Optional, Dict, List
from datetime import datetime
from sqlalchemy.orm import Session
from src.models.orm import Imagem
from src.services.image_upload import UploaderFactory, UploadResult
from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class ImagemRepository(BaseRepository[Imagem]):
    def __init__(self, session: Session):
        super().__init__(Imagem, session)

    def buscar_por_hash(self, hash_md5: str) -> Optional[Imagem]:
        return self.session.query(Imagem).filter_by(hash_md5=hash_md5, ativo=True).first()

    def buscar_por_nome(self, nome_arquivo: str) -> Optional[Imagem]:
        return self.session.query(Imagem).filter_by(nome_arquivo=nome_arquivo, ativo=True).first()

    def buscar_por_url_remota(self, url: str) -> Optional[Imagem]:
        """Busca imagem por URL remota"""
        return self.session.query(Imagem).filter_by(url_remota=url, ativo=True).first()

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

    def upload_para_servico_externo(self, uuid: str, config_path: str = "config.ini") -> UploadResult:
        """
        Faz upload de imagem existente para serviço externo

        Args:
            uuid: UUID da imagem no banco
            config_path: Caminho para arquivo de configuração

        Returns:
            UploadResult com URL ou erro
        """
        imagem = self.buscar_por_uuid(uuid)
        if not imagem:
            return UploadResult(success=False, erro="Imagem não encontrada")

        # Se já tem URL remota, retorna ela
        if imagem.tem_url_remota():
            return UploadResult(
                success=True,
                url=imagem.url_remota,
                url_thumbnail=imagem.url_thumbnail,
                id_remoto=imagem.id_remoto,
                servico=imagem.servico_hospedagem
            )

        # Criar uploader e fazer upload
        uploader = UploaderFactory.criar_uploader(config_path)
        result = uploader.upload(imagem.caminho_relativo, imagem.nome_arquivo)

        # Se sucesso, atualiza a imagem no banco
        if result.success:
            self.atualizar_url_remota(uuid, result)

        return result

    def atualizar_url_remota(self, uuid: str, result: UploadResult) -> bool:
        """
        Atualiza dados de URL remota de uma imagem

        Args:
            uuid: UUID da imagem
            result: Resultado do upload com URLs

        Returns:
            True se atualizado com sucesso
        """
        imagem = self.buscar_por_uuid(uuid)
        if not imagem:
            return False

        imagem.url_remota = result.url
        imagem.servico_hospedagem = result.servico
        imagem.id_remoto = result.id_remoto
        imagem.url_thumbnail = result.url_thumbnail
        imagem.data_upload_remoto = datetime.utcnow()

        self.session.flush()
        logger.info(f"URL remota atualizada para imagem {uuid}: {result.url}")
        return True

    def listar_sem_url_remota(self) -> List[Imagem]:
        """Lista imagens locais que não foram sincronizadas para serviço externo"""
        return self.session.query(Imagem).filter(
            Imagem.url_remota.is_(None),
            Imagem.ativo == True
        ).all()

    def sincronizar_todas_para_remoto(self, config_path: str = "config.ini") -> Dict[str, any]:
        """
        Faz upload em lote de todas as imagens sem URL remota

        Args:
            config_path: Caminho para arquivo de configuração

        Returns:
            Dict com estatísticas do processo
        """
        imagens = self.listar_sem_url_remota()
        resultado = {
            "total": len(imagens),
            "sucesso": 0,
            "erros": 0,
            "detalhes_erros": []
        }

        uploader = UploaderFactory.criar_uploader(config_path)

        for imagem in imagens:
            upload_result = uploader.upload(imagem.caminho_relativo, imagem.nome_arquivo)

            if upload_result.success:
                self.atualizar_url_remota(imagem.uuid, upload_result)
                resultado["sucesso"] += 1
            else:
                resultado["erros"] += 1
                resultado["detalhes_erros"].append({
                    "uuid": imagem.uuid,
                    "nome": imagem.nome_arquivo,
                    "erro": upload_result.erro
                })
                logger.error(f"Erro ao sincronizar {imagem.nome_arquivo}: {upload_result.erro}")

        logger.info(f"Sincronização concluída: {resultado['sucesso']}/{resultado['total']} sucesso")
        return resultado
