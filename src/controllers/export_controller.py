"""
Controller para gerenciar a exportação de listas e outros dados.
"""
import logging
import re
from pathlib import Path
from typing import List

# Corrigindo a importação para o DTO
from src.application.dtos.export_dto import ExportOptionsDTO
# Corrigindo a importação para o Service
from src.application.services.export_service import ExportService, escape_latex
from src.services import services # Usando a fachada de serviços para buscar dados

logger = logging.getLogger(__name__)

class ExportController:
    def __init__(self):
        # O ExportService não depende de sessão, então pode ser instanciado diretamente
        self.export_service = ExportService()

    def _processar_imagens_inline(self, texto: str, centralizar: bool = True) -> str:
        """
        Processa placeholders de imagem [IMG:caminho:escala] e converte para LaTeX.

        Args:
            texto: Texto com placeholders de imagem
            centralizar: Se True, centraliza a imagem. Se False, usa minipage (para alternativas)

        Returns:
            Texto com comandos LaTeX includegraphics
        """
        # Padrão: [IMG:caminho:escala]
        # O caminho pode conter : (Windows drive), então usamos um padrão mais específico
        # Formato esperado: [IMG:C:/path/to/image.png:0.7] ou [IMG:C:\path\to\image.png:0.7]
        pattern = r'\[IMG:(.+?):([0-9.]+)\]'

        def replace_image(match):
            caminho = match.group(1)
            escala = match.group(2)
            # Normalizar caminho para LaTeX (usar /)
            caminho_latex = caminho.replace('\\', '/')
            if centralizar:
                return f"\n\n\\begin{{center}}\n\\includegraphics[scale={escala}]{{{caminho_latex}}}\n\\end{{center}}\n\n"
            else:
                # Usar minipage para alternativas (não centraliza)
                return f"\n\n\\begin{{minipage}}{{\\linewidth}}\n\\includegraphics[scale={escala}]{{{caminho_latex}}}\n\\end{{minipage}}\n\n"

        return re.sub(pattern, replace_image, texto)

    def _processar_tabelas(self, texto: str) -> str:
        """
        Processa tabelas LaTeX e envolve com resizebox se necessário.

        Tabelas que não estão envolvidas em resizebox são automaticamente
        envolvidas para garantir que não ultrapassem os limites da página/coluna.

        Args:
            texto: Texto com possíveis tabelas LaTeX

        Returns:
            Texto com tabelas envolvidas em resizebox
        """
        # Padrão para encontrar tabelas que NÃO estão já em resizebox
        # Procura por \begin{tabular} que não seja precedido por resizebox

        def wrap_table(match):
            tabular_content = match.group(0)
            # Verifica se já está envolvido em resizebox (olhando o contexto antes)
            return f"\\resizebox{{\\columnwidth}}{{!}}{{\n{tabular_content}\n}}"

        # Primeiro, encontra todas as tabelas
        # Padrão: \begin{tabular}...\end{tabular}
        tabular_pattern = r'\\begin\{tabular\}.*?\\end\{tabular\}'

        # Encontra tabelas que NÃO estão precedidas por resizebox
        # Usa negative lookbehind para verificar se não há resizebox antes
        # Nota: lookbehind tem limitações, então usamos abordagem diferente

        # Abordagem: marca tabelas já em resizebox, processa as outras
        # Padrão para resizebox existente
        resizebox_pattern = r'\\resizebox\{[^}]*\}\{[^}]*\}\{[^}]*\\begin\{tabular\}.*?\\end\{tabular\}[^}]*\}'

        # Salva os resizeboxes existentes com placeholders
        preserved = {}
        counter = [0]

        def save_resizebox(match):
            key = f"__RESIZEBOX_{counter[0]}__"
            preserved[key] = match.group(0)
            counter[0] += 1
            return key

        # Preserva resizeboxes existentes
        texto = re.sub(resizebox_pattern, save_resizebox, texto, flags=re.DOTALL)

        # Agora processa tabelas que não estão em resizebox
        texto = re.sub(tabular_pattern, wrap_table, texto, flags=re.DOTALL)

        # Restaura os resizeboxes preservados
        for key, value in preserved.items():
            texto = texto.replace(key, value)

        return texto

    def listar_templates_disponiveis(self) -> List[str]:
        """
        Lista os arquivos de template LaTeX (.tex) disponíveis na pasta de templates.
        """
        template_dir = Path('templates/latex')
        if not template_dir.exists():
            logger.warning(f"Diretório de templates não encontrado: {template_dir.resolve()}")
            return []
        
        templates = [f.name for f in template_dir.glob('*.tex')] 
        logger.info(f"Templates LaTeX encontrados: {templates}")
        return templates

    def _carregar_template(self, nome_template: str) -> str:
        """Carrega o conteúdo de um arquivo de template."""
        template_path = Path('templates/latex') / nome_template
        if not template_path.exists():
            raise FileNotFoundError(f"Template LaTeX '{nome_template}' não encontrado.")
        
        return template_path.read_text(encoding='utf-8')

    def _gerar_conteudo_latex(self, opcoes: ExportOptionsDTO) -> str:
        """
        Gera o conteudo LaTeX completo para a lista, aplicando as opcoes de exportacao.
        """
        # 1. Buscar dados da lista
        lista_dados = services.lista.buscar_lista(opcoes.id_lista)
        if not lista_dados:
            raise ValueError(f"Lista com codigo {opcoes.id_lista} nao encontrada.")

        # 2. Carregar o template base
        template_content = self._carregar_template(opcoes.template_latex)

        # 3. Substituir placeholders do cabecalho
        template_content = template_content.replace("[TITULO_LISTA]", escape_latex(lista_dados['titulo']))

        # Formulas (caixa de fórmulas opcional)
        formulas = lista_dados.get('formulas', '') or ''
        if formulas:
            formulas_block = f"\\begin{{tcolorbox}}[title=Fórmulas]\n{formulas}\n\\end{{tcolorbox}}\n\\vspace{{0.5cm}}"
            template_content = template_content.replace("% [FORMULAS_AQUI]", formulas_block)
        else:
            template_content = template_content.replace("% [FORMULAS_AQUI]", "")

        # 4. Gerar o bloco de questoes
        questoes_latex = []
        for i, questao in enumerate(lista_dados['questoes'], 1):
            enunciado_raw = questao.get('enunciado', '')
            # Primeiro escapar o texto, depois processar imagens e tabelas
            # (imagens e tabelas geram LaTeX puro que não precisa de escape)
            enunciado_escaped = escape_latex(enunciado_raw)
            enunciado = self._processar_imagens_inline(enunciado_escaped)
            enunciado = self._processar_tabelas(enunciado)
            fonte = questao.get('fonte') or ''
            ano = str(questao.get('ano') or '')

            # Cabecalho da questao: (FONTE - ANO) Enunciado (na mesma linha)
            if fonte and ano:
                item = f"\\item \\textbf{{({fonte} - {ano})}} {enunciado}\n\n"
            elif fonte:
                item = f"\\item \\textbf{{({fonte})}} {enunciado}\n\n"
            elif ano:
                item = f"\\item \\textbf{{({ano})}} {enunciado}\n\n"
            else:
                item = f"\\item {enunciado}\n\n"

            # Adicionar alternativas (se objetiva)
            alternativas = questao.get('alternativas', [])
            if alternativas:
                item += "\\begin{enumerate}[label=\\Alph*)]\n"
                for alt in alternativas:
                    texto_alt_raw = alt.get('texto', '')
                    texto_alt_escaped = escape_latex(texto_alt_raw)
                    texto_alt = self._processar_imagens_inline(texto_alt_escaped, centralizar=False)
                    texto_alt = self._processar_tabelas(texto_alt)
                    item += f"    \\item {texto_alt}\n"
                item += "\\end{enumerate}\n"

            item += "\\vspace{0.5cm}\n"
            questoes_latex.append(item)

        # Substituir placeholder de questoes
        questoes_block = "\n".join(questoes_latex)

        # Aplicar layout de colunas se necessário
        if opcoes.layout_colunas == 2:
            questoes_block = f"\\begin{{multicols}}{{2}}\n{questoes_block}\n\\end{{multicols}}"

        template_content = template_content.replace("% [QUESTOES_AQUI]", questoes_block)

        # 5. Gerar o bloco de gabarito ou remover secao inteira
        if opcoes.incluir_gabarito:
            gabarito_latex = []
            for i, questao in enumerate(lista_dados['questoes'], 1):
                resposta = questao.get('resposta') or 'N/A'
                gabarito_latex.append(f"\\item Questao {i}: {escape_latex(str(resposta))}")
            gabarito_block = "\n".join(gabarito_latex)
            template_content = template_content.replace("% [GABARITO_AQUI]", gabarito_block)
        else:
            # Remover secao inteira de gabarito
            template_content = re.sub(
                r'% ={10,}\s*\n% GABARITO \(opcional\)\s*\n% ={10,}\s*\n.*?\\end\{enumerate\}',
                '',
                template_content,
                flags=re.DOTALL
            )

        # 6. Remover secao inteira de resolucoes (nao implementada ainda)
        template_content = re.sub(
            r'% ={10,}\s*\n% RESOLU[ÇC][ÕO]ES \(opcional\)\s*\n% ={10,}\s*\n.*?\\end\{enumerate\}',
            '',
            template_content,
            flags=re.DOTALL
        )

        return template_content

    def exportar_lista(self, opcoes: ExportOptionsDTO) -> Path:
        """
        Orquestra a exportação de uma lista para LaTeX ou PDF.

        Args:
            opcoes: DTO com todas as configurações de exportação.

        Returns:
            Caminho do arquivo gerado (.tex ou .pdf).
        """
        logger.info(f"Iniciando exportação para lista ID {opcoes.id_lista} com opções: {opcoes}")

        # Gerar o conteúdo LaTeX dinamicamente
        # NOTE: A lógica de geração de conteúdo está agora no controller para acessar outros services
        latex_content = self._gerar_conteudo_latex(opcoes)

        output_dir = Path(opcoes.output_dir)
        lista_dados = services.lista.buscar_lista(opcoes.id_lista)
        base_filename = f"{lista_dados['titulo'].replace(' ', '_')}_{opcoes.template_latex.replace('.tex', '')}"

        if opcoes.tipo_exportacao == 'direta':
            logger.info(f"Compilando LaTeX para PDF para lista ID {opcoes.id_lista}...")
            pdf_path = self.export_service.compilar_latex_para_pdf(latex_content, output_dir, base_filename)
            return pdf_path
        else: # 'manual'
            tex_path = output_dir / f"{base_filename}.tex"
            logger.info(f"Escrevendo arquivo .tex manual para: {tex_path}")
            tex_path.write_text(latex_content, encoding='utf-8')
            return tex_path
