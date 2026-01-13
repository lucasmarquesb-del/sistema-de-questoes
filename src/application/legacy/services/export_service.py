"""
Service: ExportService
DESCRIÇÃO: Gerencia a lógica de geração de arquivos LaTeX e PDF a partir de listas de questões.
SEGURANÇA: Sanitiza conteúdo LaTeX e usa pdflatex com -no-shell-escape
"""
import logging
import subprocess
import shutil
import random
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.domain.interfaces import IListaRepository, IQuestaoRepository
from src.application.dtos.export_dto import ExportOptionsDTO
from src.application.dtos.lista_dto import ListaResponseDTO
from src.application.dtos.questao_dto import QuestaoResponseDTO
from src.models.database import db # Para obter o project_root
from src.constants import LatexConfig

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

    @staticmethod
    def _sanitize_latex(content: str) -> str:
        """
        Sanitiza conteúdo LaTeX para prevenir execução de comandos perigosos.

        SEGURANÇA: Remove ou neutraliza comandos LaTeX que podem executar código arbitrário.

        Args:
            content: Conteúdo LaTeX a ser sanitizado

        Returns:
            Conteúdo LaTeX sanitizado
        """
        if not content:
            return ""

        # Lista de comandos perigosos que devem ser removidos
        dangerous_commands = LatexConfig.COMANDOS_PERIGOSOS

        sanitized = content

        # Remover comandos perigosos (case-insensitive)
        for cmd in dangerous_commands:
            # Remove comando com ou sem argumentos
            pattern = re.escape(cmd) + r'(\{[^}]*\}|\[[^\]]*\])*'
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)

        # Verificar se restou algum \write18 (muito perigoso)
        if r'\write' in sanitized.lower():
            logger.warning("Tentativa de usar comando \\write detectada e bloqueada")
            sanitized = sanitized.replace(r'\write', r'%BLOCKED:write')

        # Escapar barras invertidas isoladas que possam ser usadas para bypass
        # (mantém comandos LaTeX válidos como \textbf, \frac, etc)

        return sanitized

    @staticmethod
    def _validate_image_path(image_path: str, project_root: Path) -> bool:
        """
        Valida que o caminho da imagem está dentro do diretório do projeto.

        SEGURANÇA: Previne path traversal attacks.

        Args:
            image_path: Caminho da imagem a ser validado
            project_root: Diretório raiz do projeto

        Returns:
            True se o caminho é válido e seguro
        """
        try:
            full_path = (project_root / image_path).resolve()
            project_root_resolved = project_root.resolve()

            # Verificar se o caminho está dentro do projeto
            return full_path.is_relative_to(project_root_resolved)
        except Exception as e:
            logger.error(f"Erro ao validar caminho de imagem: {e}")
            return False

    @staticmethod
    def _validate_scale(scale: float) -> float:
        """
        Valida e normaliza o valor de escala de imagem.

        Args:
            scale: Valor de escala

        Returns:
            Escala validada dentro dos limites seguros
        """
        from src.constants import ImagemConfig

        if scale is None or scale <= 0:
            return ImagemConfig.ESCALA_PADRAO

        # Limitar escala a valores razoáveis
        if scale < ImagemConfig.ESCALA_MINIMA:
            return ImagemConfig.ESCALA_MINIMA
        if scale > ImagemConfig.ESCALA_MAXIMA:
            return ImagemConfig.ESCALA_MAXIMA

        return scale

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
        """
        Gera o código LaTeX para uma única questão.
        SEGURANÇA: Sanitiza todo o conteúdo LaTeX antes de incluir no documento.
        """
        latex_parts = []

        # Enunciado (SANITIZADO)
        enunciado_sanitizado = self._sanitize_latex(questao_dto.enunciado)
        latex_parts.append(f"\\item {enunciado_sanitizado}\n")

        # Imagem do enunciado (VALIDADA)
        if questao_dto.imagem_enunciado:
            # SEGURANÇA: Validar caminho da imagem
            if self._validate_image_path(questao_dto.imagem_enunciado, self.project_root):
                image_path_relative = Path(questao_dto.imagem_enunciado)

                # SEGURANÇA: Validar escala
                scale = self._validate_scale(
                    questao_dto.escala_imagem_enunciado if questao_dto.escala_imagem_enunciado
                    else opcoes.escala_imagens
                )

                latex_parts.append(f"\\includegraphics[scale={scale:.2f}]{{{image_path_relative}}}\n")
            else:
                logger.warning(f"Caminho de imagem inválido ignorado: {questao_dto.imagem_enunciado}")

        # Alternativas (se objetiva) - SANITIZADAS
        if questao_dto.tipo == 'OBJETIVA' and questao_dto.alternativas:
            latex_parts.append("\\begin{enumerate}[label=\\Alph*)]\n")
            for alt_dto in questao_dto.alternativas:
                texto_sanitizado = self._sanitize_latex(alt_dto.texto)
                latex_parts.append(f"  \\item {texto_sanitizado}\n")
            latex_parts.append("\\end{enumerate}\n")

        # Resolução (SANITIZADA)
        if opcoes.incluir_resolucoes and questao_dto.resolucao:
            resolucao_sanitizada = self._sanitize_latex(questao_dto.resolucao)
            latex_parts.append(f"\\paragraph*{{Resolução:}} {resolucao_sanitizada}\n")

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
        SEGURANÇA: Usa -no-shell-escape para prevenir execução de comandos shell.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        temp_dir = output_dir / f"temp_latex_{base_filename}"
        temp_dir.mkdir(exist_ok=True)

        # SEGURANÇA: Validar base_filename para prevenir path traversal
        if '..' in base_filename or '/' in base_filename or '\\' in base_filename:
            raise ValueError(f"Nome de arquivo inválido: {base_filename}")

        tex_file_path = temp_dir / f"{base_filename}.tex"
        pdf_file_path = output_dir / f"{base_filename}.pdf"

        try:
            logger.info(f"Escrevendo conteúdo LaTeX para: {tex_file_path}")
            with open(tex_file_path, 'w', encoding='utf-8') as f:
                f.write(tex_content)

            # SEGURANÇA: Comando pdflatex com -no-shell-escape
            # Isso previne que comandos LaTeX executem shell commands via \write18
            cmd = [
                "pdflatex",
                "-no-shell-escape",  # CRÍTICO: Previne execução de comandos shell
                "-interaction=nonstopmode",
                "-output-directory", str(temp_dir),
                str(tex_file_path)
            ]

            logger.info(f"Comando pdflatex: {' '.join(cmd)}")

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
