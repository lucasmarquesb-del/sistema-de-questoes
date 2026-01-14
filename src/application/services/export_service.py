"""
Service para exportação de dados, especialmente para LaTeX/PDF.
"""
import logging
import subprocess
import locale
import re
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

def escape_latex(text: str) -> str:
    """
    Escapa caracteres especiais do LaTeX em uma string.
    """
    if not isinstance(text, str):
        return text
    
    # Ordem é importante
    conv = {
        '&': r'\\&',
        '%': r'\\%',
        '$': r'\\$',
        '#': r'\\#',
        '_': r'\\_',
        '{': r'\\{',
        '}': r'\\}',
        '~': r'\\textasciitilde{}',
        '^': r'\\textasciicircum{}',
        '\\': r'\\textbackslash{}',
        '<': r'\\textless{}',
        '>': r'\\textgreater{}',
    }
    regex = re.compile('|'.join(re.escape(str(key)) for key in sorted(conv.keys(), key=len, reverse=True)))
    return regex.sub(lambda match: conv[match.group()], text)


class ExportService:
    def __init__(self):
        pass

    def compilar_latex_para_pdf(self, latex_content: str, output_dir: Path, base_filename: str) -> Path:
        """
        Compila um conteúdo LaTeX para PDF.

        Args:
            latex_content: String contendo o LaTeX.
            output_dir: Diretório de saída.
            base_filename: Nome do arquivo base (sem extensão).

        Returns:
            O caminho para o arquivo PDF gerado.
        
        Raises:
            RuntimeError: Se a compilação do LaTeX falhar.
        """
        temp_dir = output_dir / f"temp_latex_{base_filename}"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        latex_file_path = temp_dir / f"{base_filename}.tex"
        
        try:
            logger.info(f"Escrevendo conteúdo LaTeX para: {latex_file_path}")
            with open(latex_file_path, "w", encoding="utf-8") as f:
                f.write(latex_content)

            # Usar a codificação preferida do sistema para o output do subprocesso
            # Isso corrige o UnicodeDecodeError em Windows
            system_encoding = locale.getpreferredencoding()

            command = [
                "pdflatex",
                "-no-shell-escape",
                "-interaction=nonstopmode",
                f"-output-directory={temp_dir}",
                str(latex_file_path)
            ]
            
            logger.info(f"Comando pdflatex: {' '.join(command)}")

            for i in range(1, 3): # Compilar duas vezes para referências cruzadas
                logger.info(f"Executando pdflatex ({i}/2) em {temp_dir}...")
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    encoding=system_encoding,
                    errors='replace' # Evita erros de decodificação
                )
                
                if result.returncode != 0:
                    log_file = temp_dir / f"{base_filename}.log"
                    log_content = log_file.read_text(encoding='utf-8', errors='ignore') if log_file.exists() else "Arquivo de log não encontrado."
                    logger.error(f"Erro pdflatex ({i}/2): \nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}\nLOG:\n{log_content}")
                    raise RuntimeError(f"Erro na compilação LaTeX ({i}/2). Verifique o log. Erro: {result.stderr}")

            pdf_filename = f"{base_filename}.pdf"
            generated_pdf = temp_dir / pdf_filename
            final_pdf_path = output_dir / pdf_filename

            if generated_pdf.exists():
                shutil.move(generated_pdf, final_pdf_path)
                logger.info(f"PDF gerado com sucesso: {final_pdf_path}")
                return final_pdf_path
            else:
                raise RuntimeError("Arquivo PDF não foi gerado após a compilação bem-sucedida.")

        finally:
            # Limpeza do diretório temporário
            if temp_dir.exists():
                logger.info(f"Limpando diretório temporário: {temp_dir}")
                shutil.rmtree(temp_dir, ignore_errors=True)

    # Outros métodos de exportação podem ser adicionados aqui
    def gerar_conteudo_latex_lista(self, opcoes) -> str:
        # TODO: Implementar a lógica de geração de conteúdo LaTeX
        # Esta é uma implementação de placeholder
        logger.info(f"Gerando conteúdo LaTeX para a lista ID: {opcoes.id_lista}")
        
        # Exemplo de conteúdo LaTeX (a ser substituído pela lógica real)
        latex_template = r"""
\documentclass{article}
\usepackage[utf8]{inputenc}
\usepackage{graphicx}

\title{Lista de Questões}
\author{Sistema de Questões}
\date{\today}

\begin{document}

\maketitle

\section{Questões}

% --- INÍCIO DAS QUESTÕES ---
{BLOCO_QUESTOES}
% --- FIM DAS QUESTÕES ---

{BLOCO_GABARITO}

\end{document}
"""
        
        # Placeholder para o bloco de questões, será substituído no controller
        # Placeholder para o bloco de gabarito, será substituído no controller

        return latex_template
