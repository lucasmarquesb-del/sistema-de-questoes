"""
Controller para gerenciar a exportação de listas e outros dados.
"""
import logging
import os
import re
import subprocess
import sys
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

    def _escape_preservando_comandos(self, texto: str) -> str:
        """
        Escapa caracteres especiais do LaTeX, mas preserva comandos LaTeX já gerados.

        Usa abordagem de placeholders para preservar comandos LaTeX de listas e tabelas.

        Args:
            texto: Texto com possíveis comandos LaTeX

        Returns:
            Texto com caracteres escapados, mas comandos LaTeX preservados
        """
        # Padrões de comandos LaTeX a preservar (listas e tabelas)
        patterns = [
            # Comandos de lista
            r'\\begin\{itemize\}',
            r'\\end\{itemize\}',
            r'\\begin\{enumerate\}(?:\[label=\\[a-zA-Z]+\*[\.\)]\])?',
            r'\\end\{enumerate\}',
            r'\\item\s',
            # Comandos de tabela
            r'\\begin\{tabular\}\{[^}]+\}',
            r'\\end\{tabular\}',
            r'\\hline',
            r'\\textbf\{[^}]*\}',
            r'\s*&\s*',  # Separador de células
            r'\s*\\\\\s*',  # Quebra de linha em tabela
        ]

        # Salvar comandos com placeholders
        preserved = {}
        counter = [0]

        def save_command(match):
            key = f"__LATEX_CMD_{counter[0]}__"
            preserved[key] = match.group(0)
            counter[0] += 1
            return key

        # Substituir cada padrão por placeholder
        texto_temp = texto
        for pattern in patterns:
            texto_temp = re.sub(pattern, save_command, texto_temp)

        # Escapar o texto (sem os comandos LaTeX)
        texto_escaped = escape_latex(texto_temp)

        # Restaurar os comandos LaTeX
        for key, value in preserved.items():
            texto_escaped = texto_escaped.replace(key, value)

        return texto_escaped

    def _processar_formatacao_celula(self, cell_text: str) -> str:
        r"""
        Processa formatações de uma célula de tabela e converte para LaTeX.

        Formatos suportados:
        - <b>texto</b> -> \textbf{texto}
        - <i>texto</i> -> \textit{texto}
        - <u>texto</u> -> \underline{texto}
        - <sup>texto</sup> -> \textsuperscript{texto}
        - <sub>texto</sub> -> \textsubscript{texto}
        - [COR:#hexcolor]texto[/COR] -> \cellcolor[HTML]{hexcolor}texto

        Args:
            cell_text: Texto da célula com possíveis formatações

        Returns:
            Texto convertido para LaTeX
        """
        result = cell_text

        # Processar cor de fundo primeiro
        color_pattern = re.compile(r'\[COR:#([a-fA-F0-9]{6})\](.*?)\[/COR\]', re.DOTALL)
        color_match = color_pattern.search(result)
        cell_color = None
        if color_match:
            cell_color = color_match.group(1).upper()
            result = color_pattern.sub(r'\2', result)

        # Extrair formatações ANTES do escape
        # Usar placeholders para preservar as formatações
        format_placeholders = {}
        placeholder_counter = [0]

        def extract_format(pattern, latex_cmd):
            nonlocal result
            def replacer(match):
                inner_text = match.group(1)
                # Escapar o texto interno
                escaped_inner = escape_latex(inner_text)
                key = f"__FMT_{placeholder_counter[0]}__"
                # Usar concatenação para evitar problema com \u sendo interpretado como unicode
                format_placeholders[key] = '\\' + latex_cmd + '{' + escaped_inner + '}'
                placeholder_counter[0] += 1
                return key
            result = re.sub(pattern, replacer, result)

        # Processar formatações (ordem: mais interno primeiro)
        extract_format(r'<sup>(.*?)</sup>', 'textsuperscript')
        extract_format(r'<sub>(.*?)</sub>', 'textsubscript')
        extract_format(r'<b>(.*?)</b>', 'textbf')
        extract_format(r'<i>(.*?)</i>', 'textit')
        extract_format(r'<u>(.*?)</u>', 'underline')

        # Escapar o texto restante (que não está em tags)
        result = escape_latex(result)

        # Restaurar as formatações
        for key, value in format_placeholders.items():
            result = result.replace(key, value)

        # Adicionar cor de fundo se definida
        if cell_color:
            result = '\\cellcolor[HTML]{' + cell_color + '}' + result

        return result

    def _processar_tabelas_visuais(self, texto: str) -> str:
        """
        Processa tabelas no formato visual e converte para LaTeX.

        Formato de entrada:
        [TABELA]
        [CABECALHO]Col1 | Col2 | Col3[/CABECALHO]
        Cell1 | Cell2 | Cell3
        Cell4 | Cell5 | Cell6
        [/TABELA]

        Args:
            texto: Texto com tabelas em formato visual

        Returns:
            Texto com tabelas convertidas para LaTeX
        """
        # Padrão para encontrar tabelas
        table_pattern = re.compile(
            r'\[TABELA\]\s*\n(.*?)\[/TABELA\]',
            re.DOTALL
        )

        def convert_table(match):
            table_content = match.group(1).strip()
            lines = table_content.split('\n')

            if not lines:
                return ''

            # Detectar número de colunas pela primeira linha
            first_line = lines[0]
            # Remover marcadores de cabeçalho e formatação para contar colunas
            clean_first = re.sub(r'\[CABECALHO\]|\[/CABECALHO\]|\[COR:[^\]]+\]|\[/COR\]', '', first_line)
            num_cols = len(clean_first.split('|'))

            # Criar especificação de colunas (centralizado)
            col_spec = '|' + '|'.join(['c'] * num_cols) + '|'

            latex_lines = []
            # Centralizar e ajustar largura para 0.8 da página com fonte menor
            latex_lines.append('\\begin{center}')
            latex_lines.append('\\small')
            latex_lines.append('\\resizebox{0.8\\linewidth}{!}{%')
            latex_lines.append('\\begin{tabular}{' + col_spec + '}')
            latex_lines.append('\\hline')

            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue

                # Verificar se é cabeçalho
                is_header = '[CABECALHO]' in line
                if is_header:
                    line = line.replace('[CABECALHO]', '').replace('[/CABECALHO]', '')

                # Separar células
                cells = [cell.strip() for cell in line.split('|')]

                # Processar formatação de cada célula
                processed_cells = []
                for cell in cells:
                    processed = self._processar_formatacao_celula(cell)
                    if is_header and not processed.startswith('\\textbf') and not processed.startswith('\\cellcolor'):
                        # Adicionar negrito ao cabeçalho se não tiver
                        processed = '\\textbf{' + processed + '}'
                    processed_cells.append(processed)

                latex_lines.append(' & '.join(processed_cells) + ' \\\\')
                latex_lines.append('\\hline')

            latex_lines.append('\\end{tabular}')
            latex_lines.append('}')  # Fecha resizebox
            latex_lines.append('\\end{center}')

            return '\n'.join(latex_lines)

        return table_pattern.sub(convert_table, texto)

    def _processar_listas(self, texto: str) -> str:
        """
        Processa listas visuais (itemizadas e enumeradas) e converte para LaTeX.

        IMPORTANTE: Para evitar falsos positivos, os padrões exigem que a linha
        comece com 2-4 espaços seguidos pelo marcador (como gerado pelo diálogo de listas).

        Formatos suportados:
        - Itemizadas: •, ○, ■, □, ▸, –, ✓, ★
        - Enumeradas: 1., a), A), i., I.

        Args:
            texto: Texto com listas em formato visual

        Returns:
            Texto com listas convertidas para LaTeX
        """
        lines = texto.split('\n')
        result = []
        in_itemize = False
        in_enumerate = False
        enumerate_type = None

        # Padrões para detectar itens de lista
        # IMPORTANTE: Exigem 2-4 espaços no início para evitar falsos positivos
        # O diálogo de listas gera: "   • Item" (3 espaços)
        itemize_symbols = r'[•○■□▸✓★]'
        itemize_pattern = re.compile(rf'^[ ]{{2,4}}({itemize_symbols})\s+(.+)$')

        # Enumerate patterns - também exigem 2-4 espaços no início
        arabic_pattern = re.compile(r'^[ ]{2,4}(\d+)\.\s+(.+)$')  # 1. 2. 3.
        alpha_lower_pattern = re.compile(r'^[ ]{2,4}([a-z])\)\s+(.+)$')  # a) b) c)
        alpha_upper_pattern = re.compile(r'^[ ]{2,4}([A-Z])\)\s+(.+)$')  # A) B) C)
        roman_lower_pattern = re.compile(r'^[ ]{2,4}(i{1,3}|iv|vi{0,3}|ix|xi{0,3})\.\s+(.+)$')  # i. ii. iii.
        roman_upper_pattern = re.compile(r'^[ ]{2,4}(I{1,3}|IV|VI{0,3}|IX|XI{0,3})\.\s+(.+)$')  # I. II. III.

        def close_list():
            nonlocal in_itemize, in_enumerate, enumerate_type
            if in_itemize:
                result.append('\\end{itemize}')
                in_itemize = False
            if in_enumerate:
                result.append('\\end{enumerate}')
                in_enumerate = False
                enumerate_type = None

        for line in lines:
            # Verificar lista itemizada
            itemize_match = itemize_pattern.match(line)
            if itemize_match:
                if not in_itemize:
                    if in_enumerate:
                        close_list()
                    result.append('\\begin{itemize}')
                    in_itemize = True
                item_text = itemize_match.group(2)
                result.append(f'    \\item {item_text}')
                continue

            # Verificar lista enumerada - arábico (1. 2. 3.)
            arabic_match = arabic_pattern.match(line)
            if arabic_match:
                if not in_enumerate or enumerate_type != 'arabic':
                    close_list()
                    result.append('\\begin{enumerate}')
                    in_enumerate = True
                    enumerate_type = 'arabic'
                item_text = arabic_match.group(2)
                result.append(f'    \\item {item_text}')
                continue

            # Verificar lista enumerada - alfabético minúsculo (a) b) c))
            alpha_lower_match = alpha_lower_pattern.match(line)
            if alpha_lower_match:
                if not in_enumerate or enumerate_type != 'alpha_lower':
                    close_list()
                    result.append('\\begin{enumerate}[label=\\alph*)]')
                    in_enumerate = True
                    enumerate_type = 'alpha_lower'
                item_text = alpha_lower_match.group(2)
                result.append(f'    \\item {item_text}')
                continue

            # Verificar lista enumerada - alfabético maiúsculo (A) B) C))
            alpha_upper_match = alpha_upper_pattern.match(line)
            if alpha_upper_match:
                if not in_enumerate or enumerate_type != 'alpha_upper':
                    close_list()
                    result.append('\\begin{enumerate}[label=\\Alph*)]')
                    in_enumerate = True
                    enumerate_type = 'alpha_upper'
                item_text = alpha_upper_match.group(2)
                result.append(f'    \\item {item_text}')
                continue

            # Verificar lista enumerada - romano minúsculo (i. ii. iii.)
            roman_lower_match = roman_lower_pattern.match(line)
            if roman_lower_match and roman_lower_match.group(1).islower():
                if not in_enumerate or enumerate_type != 'roman_lower':
                    close_list()
                    result.append('\\begin{enumerate}[label=\\roman*.]')
                    in_enumerate = True
                    enumerate_type = 'roman_lower'
                item_text = roman_lower_match.group(2)
                result.append(f'    \\item {item_text}')
                continue

            # Verificar lista enumerada - romano maiúsculo (I. II. III.)
            if roman_upper_pattern.match(line):
                roman_upper_match = roman_upper_pattern.match(line)
                if not in_enumerate or enumerate_type != 'roman_upper':
                    close_list()
                    result.append('\\begin{enumerate}[label=\\Roman*.]')
                    in_enumerate = True
                    enumerate_type = 'roman_upper'
                item_text = roman_upper_match.group(2)
                result.append(f'    \\item {item_text}')
                continue

            # Linha não é item de lista
            # Fechar listas abertas se linha não vazia (parágrafo normal)
            if line.strip() and (in_itemize or in_enumerate):
                close_list()

            result.append(line)

        # Fechar qualquer lista aberta no final
        close_list()

        return '\n'.join(result)

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

        # Substituir placeholders específicos de templates (ex: wallon_av2)
        if opcoes.trimestre:
            template_content = template_content.replace("[TRIMESTRE]", escape_latex(opcoes.trimestre))
        if opcoes.professor:
            template_content = template_content.replace("[PROFESSOR]", escape_latex(opcoes.professor))
        if opcoes.disciplina:
            template_content = template_content.replace("[DISCIPLINA]", escape_latex(opcoes.disciplina))
        if opcoes.ano:
            template_content = template_content.replace("[ANO]", escape_latex(opcoes.ano))

        # Substituir placeholders específicos do template CEAB (simuladoCeab)
        if opcoes.data_aplicacao:
            template_content = template_content.replace("[DATA_APLICACAO]", escape_latex(opcoes.data_aplicacao))
        if opcoes.serie_simulado:
            template_content = template_content.replace("[SERIE_SIMULADO]", escape_latex(opcoes.serie_simulado))
        if opcoes.unidade:
            template_content = template_content.replace("[UNIDADE]", escape_latex(opcoes.unidade))
        if opcoes.tipo_simulado:
            template_content = template_content.replace("[TIPO_SIMULADO]", escape_latex(opcoes.tipo_simulado))

        # Formulas (caixa de fórmulas opcional)
        formulas = lista_dados.get('formulas', '') or ''
        if formulas:
            # Caixa simples sem cor, apenas com borda
            formulas_block = f"\\begin{{tcolorbox}}[colback=white, colframe=black, boxrule=0.5pt, title=Fórmulas, fonttitle=\\bfseries]\n{formulas}\n\\end{{tcolorbox}}\n\\vspace{{0.5cm}}"
            template_content = template_content.replace("% [FORMULAS_AQUI]", formulas_block)
        else:
            template_content = template_content.replace("% [FORMULAS_AQUI]", "")

        # 4. Gerar o bloco de questoes
        questoes_latex = []
        for i, questao in enumerate(lista_dados['questoes'], 1):
            enunciado_raw = questao.get('enunciado', '')
            # Processar tabelas visuais PRIMEIRO (converte [TABELA] para LaTeX)
            enunciado_com_tabelas = self._processar_tabelas_visuais(enunciado_raw)
            # Processar listas (converte símbolos visuais para LaTeX)
            enunciado_com_listas = self._processar_listas(enunciado_com_tabelas)
            # Escapar apenas o texto que não é comando LaTeX
            enunciado_escaped = self._escape_preservando_comandos(enunciado_com_listas)
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
                    # Processar tabelas e listas nas alternativas também
                    texto_alt_com_tabelas = self._processar_tabelas_visuais(texto_alt_raw)
                    texto_alt_com_listas = self._processar_listas(texto_alt_com_tabelas)
                    texto_alt_escaped = self._escape_preservando_comandos(texto_alt_com_listas)
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

    def abrir_arquivo(self, caminho: Path) -> None:
        """
        Abre um arquivo com o aplicativo padrão do sistema.

        Args:
            caminho: Caminho do arquivo a ser aberto
        """
        try:
            caminho_str = str(caminho)
            if sys.platform == 'win32':
                # Windows
                os.startfile(caminho_str)
            elif sys.platform == 'darwin':
                # macOS
                subprocess.run(['open', caminho_str], check=True)
            else:
                # Linux e outros
                subprocess.run(['xdg-open', caminho_str], check=True)
            logger.info(f"Arquivo aberto: {caminho_str}")
        except Exception as e:
            logger.warning(f"Não foi possível abrir o arquivo automaticamente: {e}")

    def _obter_variantes_questao(self, codigo_questao: str) -> List[dict]:
        """
        Obtém as variantes de uma questão.

        Args:
            codigo_questao: Código da questão original

        Returns:
            Lista de dicts com dados das variantes ordenadas por código
        """
        try:
            variantes = services.questao.obter_variantes(codigo_questao)
            # Ordenar por código para garantir ordem consistente (A, B, C)
            return sorted(variantes, key=lambda v: v.get('codigo', ''))
        except Exception as e:
            logger.warning(f"Erro ao obter variantes de {codigo_questao}: {e}")
            return []

    def _randomizar_alternativas_com_gabarito(self, alternativas: List[dict], resposta_original: str, seed: int) -> tuple:
        """
        Randomiza a ordem das alternativas e retorna a nova letra da resposta correta.

        Args:
            alternativas: Lista de alternativas
            resposta_original: Letra da resposta correta original (ex: "A", "B", etc.)
            seed: Seed para randomização (garante reprodutibilidade)

        Returns:
            Tuple (alternativas_randomizadas, nova_resposta)
        """
        import random

        if not alternativas:
            return alternativas, resposta_original

        # Usar seed para garantir que a mesma versão sempre gere a mesma ordem
        rng = random.Random(seed)

        # Letras padrão
        letras = ['A', 'B', 'C', 'D', 'E']

        # Copiar alternativas e atribuir letra original baseada na posição (se não tiver)
        alternativas_copia = []
        for idx, alt in enumerate(alternativas):
            alt_copy = alt.copy()
            # Se não tem letra, usar a posição
            letra_atual = alt.get('letra', letras[idx] if idx < len(letras) else str(idx))
            alt_copy['letra_original'] = letra_atual
            alternativas_copia.append(alt_copy)

        # Embaralhar
        rng.shuffle(alternativas_copia)

        # Atualizar letras e encontrar nova posição da resposta correta
        nova_resposta = resposta_original

        for i, alt in enumerate(alternativas_copia):
            if i < len(letras):
                # Verificar se esta era a alternativa correta
                letra_original = alt.get('letra_original', '').upper()
                if letra_original == resposta_original.upper():
                    nova_resposta = letras[i]
                alt['letra'] = letras[i]
                # Remover campo temporário
                if 'letra_original' in alt:
                    del alt['letra_original']

        logger.info(f"Alternativas randomizadas: resposta {resposta_original} -> {nova_resposta}")
        return alternativas_copia, nova_resposta

    def _obter_versao_questao_ciclica(self, questao: dict, indice_versao: int) -> dict:
        """
        Obtém a versão da questão a ser usada de forma cíclica.

        Lógica:
        - índice 0 (TIPO A): questão original
        - índice 1 (TIPO B): variante 1 (se existir), senão original
        - índice 2 (TIPO C): variante 2 (se existir), senão cicla
        - índice 3 (TIPO D): cicla de volta

        Se a questão tem 2 variantes e pede 4 versões:
        A=original, B=var1, C=var2, D=original

        Args:
            questao: Dados da questão original
            indice_versao: Índice da versão (0=A, 1=B, 2=C, 3=D)

        Returns:
            Dados da questão a ser usada
        """
        codigo_questao = questao.get('codigo', '')
        variantes = self._obter_variantes_questao(codigo_questao)

        # Montar lista: [original, variante1, variante2, ...]
        todas_versoes = [questao]  # índice 0 = original

        for var in variantes:
            var_data = services.questao.buscar_questao(var['codigo'])
            if var_data:
                todas_versoes.append(var_data)

        # Usar índice cíclico
        indice_ciclico = indice_versao % len(todas_versoes)
        questao_escolhida = todas_versoes[indice_ciclico]

        if indice_ciclico == 0:
            logger.info(f"Questão {codigo_questao}: usando ORIGINAL para TIPO {chr(65 + indice_versao)}")
        else:
            logger.info(f"Questão {codigo_questao}: usando VARIANTE {indice_ciclico} para TIPO {chr(65 + indice_versao)}")

        return questao_escolhida

    def _randomizar_ordem_questoes(self, questoes: List[dict], seed: int) -> List[dict]:
        """
        Randomiza a ordem das questões mantendo consistência com a seed.

        Args:
            questoes: Lista de questões
            seed: Seed para randomização

        Returns:
            Lista de questões com ordem randomizada
        """
        import random

        if not questoes:
            return questoes

        rng = random.Random(seed)
        questoes_copia = questoes.copy()
        rng.shuffle(questoes_copia)

        return questoes_copia

    def _gerar_conteudo_latex_randomizado(self, opcoes: ExportOptionsDTO, indice_versao: int) -> str:
        """
        Gera o conteúdo LaTeX para uma versão randomizada específica.

        Lógica:
        - A ORDEM das questões é randomizada para cada versão
        - Para cada questão, usa-se a versão cíclica (original, var1, var2, original, ...)

        Args:
            opcoes: Opções de exportação
            indice_versao: Índice da versão (0=A, 1=B, 2=C, 3=D)

        Returns:
            Conteúdo LaTeX completo
        """
        import random

        # 1. Buscar dados da lista
        lista_dados = services.lista.buscar_lista(opcoes.id_lista)
        if not lista_dados:
            raise ValueError(f"Lista com código {opcoes.id_lista} não encontrada.")

        # 2. Carregar o template base
        template_content = self._carregar_template(opcoes.template_latex)

        # 3. Substituir placeholders do cabeçalho
        titulo_com_tipo = f"{lista_dados['titulo']}-{opcoes.sufixo_versao}"
        template_content = template_content.replace("[TITULO_LISTA]", escape_latex(titulo_com_tipo))

        # Substituir placeholders específicos de templates
        if opcoes.trimestre:
            template_content = template_content.replace("[TRIMESTRE]", escape_latex(opcoes.trimestre))
        if opcoes.professor:
            template_content = template_content.replace("[PROFESSOR]", escape_latex(opcoes.professor))
        if opcoes.disciplina:
            template_content = template_content.replace("[DISCIPLINA]", escape_latex(opcoes.disciplina))
        if opcoes.ano:
            template_content = template_content.replace("[ANO]", escape_latex(opcoes.ano))

        # Substituir placeholders específicos do template CEAB (simuladoCeab)
        if opcoes.data_aplicacao:
            template_content = template_content.replace("[DATA_APLICACAO]", escape_latex(opcoes.data_aplicacao))
        if opcoes.serie_simulado:
            template_content = template_content.replace("[SERIE_SIMULADO]", escape_latex(opcoes.serie_simulado))
        if opcoes.unidade:
            template_content = template_content.replace("[UNIDADE]", escape_latex(opcoes.unidade))
        if opcoes.tipo_simulado:
            template_content = template_content.replace("[TIPO_SIMULADO]", escape_latex(opcoes.tipo_simulado))

        # Fórmulas
        formulas = lista_dados.get('formulas', '') or ''
        if formulas:
            formulas_block = f"\\begin{{tcolorbox}}[colback=white, colframe=black, boxrule=0.5pt, title=Fórmulas, fonttitle=\\bfseries]\n{formulas}\n\\end{{tcolorbox}}\n\\vspace{{0.5cm}}"
            template_content = template_content.replace("% [FORMULAS_AQUI]", formulas_block)
        else:
            template_content = template_content.replace("% [FORMULAS_AQUI]", "")

        # 4. Randomizar a ORDEM das questões
        questoes_originais = lista_dados.get('questoes', [])
        seed_ordem = indice_versao * 12345  # Seed diferente para cada versão
        questoes_randomizadas = self._randomizar_ordem_questoes(questoes_originais, seed_ordem)

        logger.info(f"TIPO {chr(65 + indice_versao)}: ordem das questões randomizada com seed {seed_ordem}")

        # 5. Gerar o bloco de questões
        # Armazenar mapeamento de respostas para o gabarito
        respostas_gabarito = {}

        questoes_latex = []
        for i, questao in enumerate(questoes_randomizadas, 1):
            # Verificar se a questão tem variantes
            codigo_questao = questao.get('codigo', '')
            variantes = self._obter_variantes_questao(codigo_questao)
            tem_variantes = len(variantes) > 0

            # Obter a versão cíclica da questão (original ou variante)
            questao_para_usar = self._obter_versao_questao_ciclica(questao, indice_versao)

            enunciado_raw = questao_para_usar.get('enunciado', '')
            # Processar formatações
            enunciado_com_tabelas = self._processar_tabelas_visuais(enunciado_raw)
            enunciado_com_listas = self._processar_listas(enunciado_com_tabelas)
            enunciado_escaped = self._escape_preservando_comandos(enunciado_com_listas)
            enunciado = self._processar_imagens_inline(enunciado_escaped)
            enunciado = self._processar_tabelas(enunciado)
            fonte = questao_para_usar.get('fonte') or ''
            ano = str(questao_para_usar.get('ano') or '')

            # Cabeçalho da questão
            if fonte and ano:
                item = f"\\item \\textbf{{({fonte} - {ano})}} {enunciado}\n\n"
            elif fonte:
                item = f"\\item \\textbf{{({fonte})}} {enunciado}\n\n"
            elif ano:
                item = f"\\item \\textbf{{({ano})}} {enunciado}\n\n"
            else:
                item = f"\\item {enunciado}\n\n"

            # Alternativas
            alternativas = questao_para_usar.get('alternativas', [])
            resposta_atual = questao_para_usar.get('resposta') or 'N/A'

            # Se NÃO tem variantes, randomizar as alternativas para criar diferenciação
            if alternativas and not tem_variantes and indice_versao > 0:
                # Seed baseada na versão e índice da questão para consistência
                seed_alternativas = (indice_versao * 1000) + i
                alternativas, resposta_atual = self._randomizar_alternativas_com_gabarito(
                    alternativas, resposta_atual, seed_alternativas
                )
                logger.info(f"Questão {i} sem variantes: alternativas randomizadas para TIPO {chr(65 + indice_versao)}")

            # Armazenar resposta para o gabarito
            respostas_gabarito[i] = resposta_atual

            if alternativas:
                item += "\\begin{enumerate}[label=\\Alph*)]\n"
                for alt in alternativas:
                    texto_alt_raw = alt.get('texto', '')
                    texto_alt_com_tabelas = self._processar_tabelas_visuais(texto_alt_raw)
                    texto_alt_com_listas = self._processar_listas(texto_alt_com_tabelas)
                    texto_alt_escaped = self._escape_preservando_comandos(texto_alt_com_listas)
                    texto_alt = self._processar_imagens_inline(texto_alt_escaped, centralizar=False)
                    texto_alt = self._processar_tabelas(texto_alt)
                    item += f"    \\item {texto_alt}\n"
                item += "\\end{enumerate}\n"

            item += "\\vspace{0.5cm}\n"
            questoes_latex.append(item)

        # Substituir placeholder de questões
        questoes_block = "\n".join(questoes_latex)

        if opcoes.layout_colunas == 2:
            questoes_block = f"\\begin{{multicols}}{{2}}\n{questoes_block}\n\\end{{multicols}}"

        template_content = template_content.replace("% [QUESTOES_AQUI]", questoes_block)

        # 6. Gerar gabarito usando as respostas armazenadas (já ajustadas para alternativas randomizadas)
        if opcoes.incluir_gabarito:
            gabarito_latex = []
            for i in range(1, len(questoes_randomizadas) + 1):
                resposta = respostas_gabarito.get(i, 'N/A')
                gabarito_latex.append(f"\\item Questão {i}: {escape_latex(str(resposta))}")

            gabarito_block = "\n".join(gabarito_latex)
            template_content = template_content.replace("% [GABARITO_AQUI]", gabarito_block)
        else:
            template_content = re.sub(
                r'% ={10,}\s*\n% GABARITO \(opcional\)\s*\n% ={10,}\s*\n.*?\\end\{enumerate\}',
                '',
                template_content,
                flags=re.DOTALL
            )

        # 7. Remover seção de resoluções
        template_content = re.sub(
            r'% ={10,}\s*\n% RESOLU[ÇC][ÕO]ES \(opcional\)\s*\n% ={10,}\s*\n.*?\\end\{enumerate\}',
            '',
            template_content,
            flags=re.DOTALL
        )

        return template_content

    def exportar_lista_randomizada(self, opcoes: ExportOptionsDTO, indice_versao: int) -> Path:
        """
        Exporta uma versão randomizada da lista.

        Args:
            opcoes: Opções de exportação com sufixo_versao definido
            indice_versao: Índice da versão (0=A, 1=B, 2=C, 3=D)

        Returns:
            Caminho do arquivo gerado
        """
        logger.info(f"Exportando versão randomizada {opcoes.sufixo_versao} da lista {opcoes.id_lista}")

        latex_content = self._gerar_conteudo_latex_randomizado(opcoes, indice_versao)

        output_dir = Path(opcoes.output_dir)
        lista_dados = services.lista.buscar_lista(opcoes.id_lista)

        # Nome do arquivo: "Nome da Lista-TIPO A"
        titulo_sanitizado = lista_dados['titulo'].replace(' ', '_')
        sufixo_sanitizado = opcoes.sufixo_versao.replace(' ', '_')
        base_filename = f"{titulo_sanitizado}-{sufixo_sanitizado}"

        if opcoes.tipo_exportacao == 'direta':
            pdf_path = self.export_service.compilar_latex_para_pdf(latex_content, output_dir, base_filename)
            logger.info(f"PDF gerado: {pdf_path}")
            return pdf_path
        else:
            tex_path = output_dir / f"{base_filename}.tex"
            tex_path.write_text(latex_content, encoding='utf-8')
            return tex_path
