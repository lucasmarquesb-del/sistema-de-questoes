"""
Service: ExportService
DESCRIÇÃO: Gerencia a lógica de geração de arquivos LaTeX e PDF a partir de listas de questões.
"""
import logging
import subprocess
import shutil
import random
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.domain.interfaces import IListaRepository, IQuestaoRepository
from src.application.dtos.export_dto import ExportOptionsDTO
from src.application.dtos.lista_dto import ListaResponseDTO
from src.application.dtos.questao_dto import QuestaoResponseDTO
from src.models.database import db # Para obter o project_root

logger = logging.getLogger(__name__)


class ExportService:
    """Serviço para gerar conteúdo LaTeX e compilar PDFs de listas de questões."""

    def __init__(self, lista_repository: IListaRepository, questao_repository: IQuestaoRepository):
        self.lista_repository = lista_repository
        self.questao_repository = questao_repository
        self.project_root = db.get_project_root()
        self.templates_dir = self.project_root / "templates" / "latex"
        self.exports_dir = self.project_root / "exports"
        self.exports_dir.mkdir(parents=True, exist_ok=True)
        logger.info("ExportService inicializado.")

    def _get_template_path(self, template_name: str) -> Path:
        """Retorna o caminho completo de um arquivo de template LaTeX."""
        path = self.templates_dir / template_name
        if not path.exists():
            raise FileNotFoundError(f"Template LaTeX não encontrado: {path}")
        return path

    def _load_template_content(self, template_name: str) -> str:
        """Carrega o conteúdo de um template LaTeX."""
        template_path = self._get_template_path(template_name)
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _generate_question_latex(self, questao_dto: QuestaoResponseDTO, opcoes: ExportOptionsDTO) -> str:
        """Gera o código LaTeX para uma única questão."""
        latex_parts = []
        
        # Enunciado
        latex_parts.append(f"\item {questao_dto.enunciado}\n")
        
        # Imagem do enunciado
        if questao_dto.imagem_enunciado:
            # Caminho relativo para a imagem
            image_path_relative = Path(questao_dto.imagem_enunciado)
            # Garantir que a imagem está no diretório correto para o LaTeX
            # (ou que o pdflatex consegue achá-la)
            # Por simplicidade, assumimos que as imagens são acessíveis.
            # Caminho relativo ao projeto, mas o LaTeX precisa do caminho relativo ao .tex
            # Isso pode ser complexo. Por enquanto, assumimos que o pdflatex está sendo executado no root do projeto
            # ou que o caminho está correto.
            scale = questao_dto.escala_imagem_enunciado if questao_dto.escala_imagem_enunciado else opcoes.escala_imagens
            latex_parts.append(f"\includegraphics[scale={scale}]{{{image_path_relative}}}\n")

        # Alternativas (se objetiva)
        if questao_dto.tipo == 'OBJETIVA' and questao_dto.alternativas:
            latex_parts.append("\begin{enumerate}[label=\\Alph*)]\n")
            for alt_dto in questao_dto.alternativas:
                latex_parts.append(f"  \item {alt_dto.texto}\n")
            latex_parts.append("\end{enumerate}\n")
        
        # Resolução
        if opcoes.incluir_resolucoes and questao_dto.resolucao:
            latex_parts.append(f"\paragraph*{{Resolução:}} {questao_dto.resolucao}\n")

        return "".join(latex_parts)

    def exportar_para_latex(self, id_lista: int, opcoes: ExportOptionsDTO) -> str:
        """
        Gera o conteúdo LaTeX completo de uma lista de questões.
        """
        try:
            logger.info(f"Gerando LaTeX para lista ID {id_lista} com opções: {opcoes.to_dict()}")
            lista_data = self.lista_repository.obter_lista_completa(id_lista)
            if not lista_data:
                raise ValueError(f"Lista com ID {id_lista} não encontrada.")
            
            # Mapear 'id_lista' para 'id' para compatibilidade com ListaResponseDTO
            lista_data['id'] = lista_data.get('id_lista')
            lista_dto = ListaResponseDTO.from_dict(lista_data)

            template_content = self._load_template_content(opcoes.template_latex)
            
            # Preparar cabeçalho, título e instruções
            header_latex = lista_dto.cabecalho or ""
            title_latex = lista_dto.titulo or "Lista de Questões"
            instructions_latex = lista_dto.instrucoes or ""

            # Coletar LaTeX das questões
            questoes_latex_list = []
            
            # Converter os dicionários de questões para DTOs antes de processar
            questoes_dtos_para_exportar = []
            for q_data in lista_dto.questoes:
                # Mapear 'id_questao' para 'id' para compatibilidade com QuestaoResponseDTO
                q_data['id'] = q_data.get('id_questao')
                questoes_dtos_para_exportar.append(QuestaoResponseDTO.from_dict(q_data))

            if opcoes.randomizar_questoes:
                random.shuffle(questoes_dtos_para_exportar)
                logger.info("Questões randomizadas para exportação.")

            for questao_dto in questoes_dtos_para_exportar:
                questoes_latex_list.append(self._generate_question_latex(questao_dto, opcoes))
            
            questoes_latex = "".join(questoes_latex_list)

            # Preparar gabarito
            gabarito_latex_list = []
            if opcoes.incluir_gabarito:
                gabarito_latex_list.append("\newpage\n\section*{Gabarito}\n\begin{enumerate}\n")
                for i, questao_dto in enumerate(questoes_dtos_para_exportar, 1):
                    if questao_dto.tipo == 'OBJETIVA':
                        correta = next((alt.letra for alt in questao_dto.alternativas if alt.correta), "N/A")
                        gabarito_latex_list.append(f"  \item {correta}\n")
                    elif questao_dto.tipo == 'DISCURSIVA':
                        gabarito_latex_list.append(f"  \item {questao_dto.gabarito_discursiva or 'Sem gabarito'}\n")
                gabarito_latex_list.append("\end{enumerate}\n")
            gabarito_latex = "".join(gabarito_latex_list)

            # Preencher template
            final_latex = template_content.replace("{{HEADER}}", header_latex)
            final_latex = final_latex.replace("{{TITULO_LISTA}}", title_latex)
            final_latex = final_latex.replace("{{INSTRUCOES}}", instructions_latex)
            final_latex = final_latex.replace("{{LAYOUT_COLUNAS}}", f"\\usepackage{{multicol}}\n\\begin{{multicols}}{{{opcoes.layout_colunas}}}" if opcoes.layout_colunas == 2 else "")
            final_latex = final_latex.replace("{{FIM_LAYOUT_COLUNAS}}", "\\end{{multicols}}" if opcoes.layout_colunas == 2 else "")
            final_latex = final_latex.replace("{{QUESTOES}}", questoes_latex)
            final_latex = final_latex.replace("{{GABARITO}}", gabarito_latex)
            
            return final_latex

        except Exception as e:
            logger.error(f"Erro ao gerar conteúdo LaTeX para lista ID {id_lista}: {e}", exc_info=True)
            raise

    def compilar_latex_para_pdf(self, tex_content: str, output_dir: Path, base_filename: str) -> Path:
        """
        Compila um conteúdo LaTeX em um arquivo PDF.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        temp_dir = output_dir / f"temp_latex_{base_filename}"
        temp_dir.mkdir(exist_ok=True)

        tex_file_path = temp_dir / f"{base_filename}.tex"
        pdf_file_path = output_dir / f"{base_filename}.pdf"

        try:
            logger.info(f"Escrevendo conteúdo LaTeX para: {tex_file_path}")
            with open(tex_file_path, 'w', encoding='utf-8') as f:
                f.write(tex_content)

            # Comando pdflatex
            cmd = ["pdflatex", "-interaction=nonstopmode", "-output-directory", str(temp_dir), str(tex_file_path)]
            
            # Rodar pdflatex duas vezes para resolver referências e layout
            logger.info(f"Executando pdflatex (1/2) em {temp_dir}...")
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', check=False)
            if result.returncode != 0:
                logger.error(f"Erro pdflatex (1/2): {result.stderr}\n{result.stdout}")
                raise RuntimeError(f"Erro na compilação LaTeX (1/2). Verifique o log. Erro: {result.stderr}")
            
            logger.info(f"Executando pdflatex (2/2) em {temp_dir}...")
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', check=False)
            if result.returncode != 0:
                logger.error(f"Erro pdflatex (2/2): {result.stderr}\n{result.stdout}")
                raise RuntimeError(f"Erro na compilação LaTeX (2/2). Verifique o log. Erro: {result.stderr}")
            
            # Mover PDF final para o output_dir
            temp_pdf_path = temp_dir / f"{base_filename}.pdf"
            if temp_pdf_path.exists():
                shutil.move(str(temp_pdf_path), str(pdf_file_path))
                logger.info(f"PDF gerado com sucesso: {pdf_file_path}")
                return pdf_file_path
            else:
                raise FileNotFoundError(f"Arquivo PDF não gerado por pdflatex: {temp_pdf_path}. Log: {result.stdout}")

        except FileNotFoundError:
            raise RuntimeError("Comando 'pdflatex' não encontrado. Certifique-se de que o MiKTeX/TeX Live está instalado e no PATH.")
        except Exception as e:
            logger.error(f"Erro ao compilar LaTeX para PDF: {e}", exc_info=True)
            raise
        finally:
            # Limpar arquivos temporários
            if temp_dir.exists():
                logger.info(f"Limpando diretório temporário: {temp_dir}")
                shutil.rmtree(temp_dir)

    def listar_templates_disponiveis(self) -> List[str]:
        """Lista os nomes dos templates LaTeX disponíveis."""
        try:
            return [p.name for p in self.templates_dir.glob("*.tex")]
        except Exception as e:
            logger.error(f"Erro ao listar templates LaTeX: {e}", exc_info=True)
            return ["default.tex"] # Retorna default como fallback
