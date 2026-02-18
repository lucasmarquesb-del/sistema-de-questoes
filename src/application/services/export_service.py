"""
Service para exportação de dados, especialmente para LaTeX/PDF.
"""
import logging
import subprocess
import sys
import locale
import re
import shutil
import urllib.request
import urllib.error
import hashlib
from pathlib import Path

logger = logging.getLogger(__name__)

def escape_latex(text: str) -> str:
    """
    Escapa caracteres especiais do LaTeX em uma string,
    preservando blocos matematicos e comandos LaTeX.
    """
    if not isinstance(text, str):
        return text

    # Usar um contador único para placeholders
    placeholder_counter = [0]
    preserved_blocks = {}

    def save_block(match):
        key = f'__PRESERVED_{placeholder_counter[0]}__'
        preserved_blocks[key] = match.group(0)
        placeholder_counter[0] += 1
        return key

    # 1. Preservar blocos matemáticos display mode ($$...$$)
    text = re.sub(r'\$\$.*?\$\$', save_block, text, flags=re.DOTALL)

    # 2. Preservar blocos matemáticos inline ($...$)
    # Padrão mais flexível: $ seguido de conteúdo que não começa com espaço+dígito
    text = re.sub(r'\$(?!\s*\d)[^\$]+\$', save_block, text, flags=re.DOTALL)

    # 3. Preservar ambientes matemáticos \[...\] e \(...\)
    text = re.sub(r'\\\[.*?\\\]', save_block, text, flags=re.DOTALL)
    text = re.sub(r'\\\(.*?\\\)', save_block, text, flags=re.DOTALL)

    # 4. Preservar ambientes begin/end
    text = re.sub(r'\\begin\{[^}]+\}.*?\\end\{[^}]+\}', save_block, text, flags=re.DOTALL)

    # 5. Envolver letras gregas isoladas com $ (apenas se não estiver já em modo matemático)
    # Padrão: letra grega que NÃO é precedida por $ e NÃO é seguida por letra
    gregas = r'(?<!\$)(\\(?:alpha|beta|gamma|delta|epsilon|varepsilon|zeta|eta|theta|vartheta|iota|kappa|lambda|mu|nu|xi|pi|varpi|rho|varrho|sigma|varsigma|tau|upsilon|phi|varphi|chi|psi|omega|Gamma|Delta|Theta|Lambda|Xi|Pi|Sigma|Upsilon|Phi|Psi|Omega))(?![a-zA-Z])(?!\$)'
    text = re.sub(gregas, r'$\1$', text)

    # 6. Preservar comandos LaTeX (ex: \textbf{...}, \frac{}{})
    # Inclui comandos com múltiplos argumentos {}
    text = re.sub(r'\\[a-zA-Z]+(?:\s*\{[^}]*\})*', save_block, text)

    # 6. Escapar caracteres especiais restantes
    # Apenas caracteres que causam erro fora de math mode
    replacements = [
        ('&', r'\&'),
        ('%', r'\%'),
        ('#', r'\#'),
    ]

    for char, replacement in replacements:
        text = text.replace(char, replacement)

    # 6.1 Escapar TODOS os $ restantes (moeda, etc.)
    # Neste ponto, todos os blocos matemáticos ($...$, $$...$$) já foram
    # preservados como placeholders. Qualquer $ restante é literal e deve ser escapado.
    # IMPORTANTE: Fazer ANTES das substituições Unicode que criam novos blocos $...$
    text = text.replace('$', '\\$')

    # 6.2 Substituir caracteres Unicode problemáticos
    # Esses caracteres não são suportados pelo pdflatex por padrão
    unicode_replacements = [
        ('✓', ''),      # Checkmark - remover (redundante com gabarito)
        ('✗', ''),      # X mark - remover
        ('★', '*'),     # Estrela cheia
        ('☆', '*'),     # Estrela vazia
        ('→', r'$\rightarrow$'),  # Seta direita
        ('←', r'$\leftarrow$'),   # Seta esquerda
        ('↔', r'$\leftrightarrow$'),  # Seta dupla
        ('≤', r'$\leq$'),    # Menor ou igual
        ('≥', r'$\geq$'),    # Maior ou igual
        ('≠', r'$\neq$'),    # Diferente
        ('±', r'$\pm$'),     # Mais ou menos
        ('×', r'$\times$'),  # Multiplicação
        ('÷', r'$\div$'),    # Divisão
        ('°', r'$^\circ$'),  # Grau
        ('º', r'\textordmasculine{}'),  # Ordinal masculino
        ('²', r'$^2$'),      # Quadrado
        ('³', r'$^3$'),      # Cubo
        ('½', r'$\frac{1}{2}$'),  # Meio
        ('¼', r'$\frac{1}{4}$'),  # Um quarto
        ('¾', r'$\frac{3}{4}$'),  # Três quartos
        ('∞', r'$\infty$'),  # Infinito
        ('√', r'$\sqrt{}$'), # Raiz quadrada (símbolo isolado)
        ('∑', r'$\sum$'),    # Somatório
        ('∏', r'$\prod$'),   # Produtório
        ('∫', r'$\int$'),    # Integral
        ('∂', r'$\partial$'), # Derivada parcial
        ('∈', r'$\in$'),     # Pertence
        ('∉', r'$\notin$'),  # Não pertence
        ('⊂', r'$\subset$'), # Subconjunto
        ('⊃', r'$\supset$'), # Superconjunto
        ('∪', r'$\cup$'),    # União
        ('∩', r'$\cap$'),    # Interseção
        ('∅', r'$\emptyset$'), # Conjunto vazio
        ('∀', r'$\forall$'), # Para todo
        ('∃', r'$\exists$'), # Existe
        ('¬', r'$\neg$'),    # Negação
        ('∧', r'$\land$'),   # E lógico
        ('∨', r'$\lor$'),    # Ou lógico
        ('⇒', r'$\Rightarrow$'),  # Implica
        ('⇔', r'$\Leftrightarrow$'),  # Se e somente se
        ('≈', r'$\approx$'), # Aproximadamente
        ('∝', r'$\propto$'), # Proporcional
        ('·', r'$\cdot$'),   # Ponto de multiplicação
    ]

    for char, replacement in unicode_replacements:
        text = text.replace(char, replacement)

    # 8. Restaurar todos os blocos preservados
    for key, value in preserved_blocks.items():
        text = text.replace(key, value)

    return text


class ExportService:
    def __init__(self):
        pass

    def _encontrar_pdflatex(self) -> str:
        """
        Procura o executável pdflatex.
        Primeiro verifica na pasta miktex-portable embutida no app,
        depois no PATH do sistema.

        Returns:
            Caminho para o pdflatex encontrado.

        Raises:
            FileNotFoundError: Se pdflatex não for encontrado.
        """
        # Determinar diretório base do app (funciona tanto em dev quanto empacotado)
        if getattr(sys, 'frozen', False):
            # Executável empacotado pelo PyInstaller
            app_dir = Path(sys.executable).parent
        else:
            # Desenvolvimento
            app_dir = Path(__file__).resolve().parent.parent.parent.parent

        # Caminhos possíveis do MiKTeX Portable
        miktex_paths = [
            app_dir / "miktex-portable" / "texmfs" / "install" / "miktex" / "bin" / "x64" / "pdflatex.exe",
            app_dir / "miktex-portable" / "miktex" / "bin" / "x64" / "pdflatex.exe",
        ]

        for miktex_path in miktex_paths:
            if miktex_path.exists():
                logger.info(f"pdflatex encontrado no MiKTeX Portable: {miktex_path}")
                return str(miktex_path)

        # Fallback: pdflatex no PATH do sistema
        import shutil as _shutil
        system_pdflatex = _shutil.which("pdflatex")
        if system_pdflatex:
            logger.info(f"pdflatex encontrado no PATH do sistema: {system_pdflatex}")
            return system_pdflatex

        raise FileNotFoundError(
            "pdflatex não encontrado. Instale o MiKTeX (https://miktex.org) "
            "ou verifique se o MiKTeX Portable está na pasta do aplicativo."
        )

    def _baixar_imagem_remota(self, url: str, destino: Path) -> bool:
        """
        Baixa uma imagem de uma URL remota para o diretório de destino.

        Args:
            url: URL da imagem (ex: https://i.ibb.co/xxx/imagem.png)
            destino: Caminho completo de destino para a imagem

        Returns:
            True se o download foi bem-sucedido, False caso contrário
        """
        try:
            logger.info(f"Baixando imagem remota: {url}")
            # Configurar headers para evitar bloqueio
            request = urllib.request.Request(
                url,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Sistema de Questões'}
            )

            with urllib.request.urlopen(request, timeout=30) as response:
                with open(destino, 'wb') as f:
                    f.write(response.read())

            logger.info(f"Imagem baixada com sucesso: {destino.name}")
            return True

        except urllib.error.URLError as e:
            logger.error(f"Erro de URL ao baixar {url}: {e}")
            return False
        except Exception as e:
            logger.error(f"Erro ao baixar imagem {url}: {e}")
            return False

    def _processar_imagens_remotas_no_latex(self, latex_content: str, temp_dir: Path) -> str:
        """
        Processa o conteúdo LaTeX, identifica URLs de imagens remotas,
        baixa para o diretório temporário e substitui as URLs pelos nomes locais.

        Args:
            latex_content: Conteúdo LaTeX com possíveis URLs de imagens
            temp_dir: Diretório temporário onde baixar as imagens

        Returns:
            Conteúdo LaTeX com URLs substituídas por nomes de arquivos locais
        """
        # Padrão para encontrar includegraphics com URLs remotas
        # Formato: \includegraphics[options]{http://...} ou \includegraphics[options]{https://...}
        pattern = r'\\includegraphics(\[[^\]]*\])?\{(https?://[^}]+)\}'

        def substituir_url(match):
            opcoes = match.group(1) or ''
            url = match.group(2)

            # Extrair nome do arquivo da URL ou gerar um baseado em hash
            url_path = url.split('/')[-1].split('?')[0]  # Remove query params
            if not url_path or len(url_path) < 3:
                # Gerar nome baseado em hash da URL
                url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
                url_path = f"img_{url_hash}.png"

            # Garantir extensão válida
            if not any(url_path.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.pdf']):
                url_path += '.png'

            destino = temp_dir / url_path

            # Baixar a imagem se ainda não existe
            if not destino.exists():
                sucesso = self._baixar_imagem_remota(url, destino)
                if not sucesso:
                    logger.warning(f"Falha ao baixar {url}, mantendo URL original")
                    return match.group(0)  # Manter original se falhar

            # Retornar includegraphics com caminho local
            return f'\\includegraphics{opcoes}{{{url_path}}}'

        # Substituir todas as URLs por nomes locais
        novo_conteudo = re.sub(pattern, substituir_url, latex_content)

        return novo_conteudo

    def _copiar_imagens_para_temp(self, temp_dir: Path):
        """
        Copia as imagens necessárias para o diretório temporário.
        Isso garante que o pdflatex encontre as imagens durante a compilação.
        """
        import os

        # Diretórios de imagens do projeto
        diretorios_imagens = [
            Path('imagens/logos'),
            Path('imagens/questoes'),
            Path('imagens/alternativas'),
            Path('imagens')
        ]

        for dir_img in diretorios_imagens:
            if dir_img.exists():
                for img_file in dir_img.glob('*'):
                    if img_file.is_file() and img_file.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.pdf', '.eps']:
                        destino = temp_dir / img_file.name
                        if not destino.exists():
                            try:
                                shutil.copy2(img_file, destino)
                                logger.debug(f"Imagem copiada: {img_file.name}")
                            except Exception as e:
                                logger.warning(f"Erro ao copiar imagem {img_file}: {e}")

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
            # Copiar imagens locais para o diretório temporário
            logger.info("Copiando imagens locais para diretório temporário...")
            self._copiar_imagens_para_temp(temp_dir)

            # Processar e baixar imagens remotas (ImgBB, etc)
            logger.info("Processando imagens remotas no LaTeX...")
            latex_content = self._processar_imagens_remotas_no_latex(latex_content, temp_dir)

            logger.info(f"Escrevendo conteúdo LaTeX para: {latex_file_path}")
            with open(latex_file_path, "w", encoding="utf-8") as f:
                f.write(latex_content)

            # Usar a codificação preferida do sistema para o output do subprocesso
            # Isso corrige o UnicodeDecodeError em Windows
            system_encoding = locale.getpreferredencoding()

            # Procurar pdflatex: primeiro no MiKTeX Portable embutido, depois no PATH
            pdflatex_cmd = self._encontrar_pdflatex()

            command = [
                pdflatex_cmd,
                "-no-shell-escape",
                "-interaction=nonstopmode",
                f"-output-directory={temp_dir}",
                str(latex_file_path)
            ]

            logger.info(f"Comando pdflatex: {' '.join(command)}")

            # No Windows, ocultar janela de terminal do pdflatex
            subprocess_kwargs = {}
            if sys.platform == 'win32':
                subprocess_kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

            for i in range(1, 3): # Compilar duas vezes para referências cruzadas
                logger.info(f"Executando pdflatex ({i}/2) em {temp_dir}...")
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    encoding=system_encoding,
                    errors='replace', # Evita erros de decodificação
                    **subprocess_kwargs
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
