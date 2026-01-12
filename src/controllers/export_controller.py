"""
Controller: Export
DESCRIÇÃO: Gerencia a lógica de negócio para exportação de listas de questões para LaTeX/PDF.
"""
import logging
from pathlib import Path
from typing import List, Optional

from src.domain.interfaces import IListaRepository, IQuestaoRepository
from src.application.services.export_service import ExportService
from src.application.dtos.export_dto import ExportOptionsDTO

logger = logging.getLogger(__name__)


class ExportController:
    """Controller para orquestrar o processo de exportação de listas."""

    def __init__(self, export_service: ExportService, lista_repository: IListaRepository):
        self.export_service = export_service
        self.lista_repository = lista_repository
        logger.info("ExportController inicializado com injeção de dependências.")

    def exportar_lista(self, opcoes: ExportOptionsDTO) -> Optional[Path]:
        """
        Exporta uma lista de questões para LaTeX ou PDF, conforme as opções.
        Retorna o Path para o arquivo gerado (PDF ou .tex).
        """
        try:
            lista_dto = self.lista_repository.buscar_por_id(opcoes.id_lista)
            if not lista_dto:
                raise ValueError(f"Lista com ID {opcoes.id_lista} não encontrada para exportação.")
            
            # Gerar nome base do arquivo
            base_filename = f"{lista_dto['titulo'].replace(' ', '_')}_{Path(opcoes.template_latex).stem}"
            
            # Gerar conteúdo LaTeX
            latex_content = self.export_service.exportar_para_latex(opcoes.id_lista, opcoes)
            
            output_dir = Path(opcoes.output_dir) if opcoes.output_dir else self.export_service.exports_dir
            output_dir.mkdir(parents=True, exist_ok=True) # Garante que o diretório de saída existe

            if opcoes.tipo_exportacao == "direta":
                logger.info(f"Compilando LaTeX para PDF para lista ID {opcoes.id_lista}...")
                pdf_path = self.export_service.compilar_latex_para_pdf(latex_content, output_dir, base_filename)
                logger.info(f"PDF gerado em: {pdf_path}")
                return pdf_path
            else: # "manual"
                tex_file_path = output_dir / f"{base_filename}.tex"
                logger.info(f"Gerando arquivo .tex para lista ID {opcoes.id_lista} em: {tex_file_path}")
                with open(tex_file_path, 'w', encoding='utf-8') as f:
                    f.write(latex_content)
                return tex_file_path

        except Exception as e:
            logger.error(f"Erro ao exportar lista ID {opcoes.id_lista}: {e}", exc_info=True)
            raise

    def listar_templates_disponiveis(self) -> List[str]:
        """Lista os nomes dos templates LaTeX disponíveis."""
        return self.export_service.listar_templates_disponiveis()


def criar_export_controller() -> ExportController:
    """Factory para criar uma instância do ExportController com suas dependências."""
    from src.infrastructure.repositories.lista_repository_impl import ListaRepositoryImpl
    from src.infrastructure.repositories.questao_repository_impl import QuestaoRepositoryImpl
    
    # É necessário também um IQuestaoRepository para o ExportService
    questao_repo = QuestaoRepositoryImpl()
    lista_repo = ListaRepositoryImpl()

    export_service = ExportService(lista_repository=lista_repo, questao_repository=questao_repo)
    
    controller = ExportController(
        export_service=export_service,
        lista_repository=lista_repo # Passa para o controller para buscar o título da lista
    )
    logger.info("ExportController criado via factory.")
    return controller