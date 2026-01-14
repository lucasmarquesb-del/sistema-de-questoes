"""
Controller para gerenciar a exportação de listas e outros dados.
"""
import logging
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
        Gera o conteúdo LaTeX completo para a lista, aplicando as opções de exportação.
        """
        # 1. Buscar dados da lista e questões usando o service layer
        # Assumindo que a fachada de serviço pode buscar uma lista por ID (ou código)
        # NOTA: O DTO tem id_lista, mas o service layer usa códigos (ex: "LST-2026-0001")
        # Esta parte pode precisar de um adapter se a view só passa o ID inteiro.
        # Por simplicidade, vamos assumir que o service facade pode lidar com isso.
        
        # Esta é uma implementação de placeholder. A lógica real dependeria do `lista_service`
        lista_dados = services.lista.buscar_lista_por_id_legacy(opcoes.id_lista)
        if not lista_dados:
            raise ValueError(f"Lista com ID {opcoes.id_lista} não encontrada.")

        # 2. Carregar o template base
        template_content = self._carregar_template(opcoes.template_latex)

        # 3. Substituir placeholders no template (exemplo simples)
        # Um sistema de template mais robusto (como Jinja2) seria melhor aqui.
        template_content = template_content.replace("{LISTA_TITULO}", escape_latex(lista_dados['titulo']))
        template_content = template_content.replace("{NUM_COLUNAS}", str(opcoes.layout_colunas))

        # 4. Gerar o bloco de questões
        questoes_latex = []
        for i, questao in enumerate(lista_dados['questoes'], 1):
            enunciado = escape_latex(questao['enunciado'])
            item = fr"\item {enunciado}\n"
            
            # Adicionar alternativas
            if questao.get('alternativas'):
                item += r"\begin{enumerate}\n"
                for alt in questao['alternativas']:
                    texto_alt = escape_latex(alt['texto'])
                    item += fr"  \item[{alt['letra']})] {texto_alt}\n"
                item += r"\end{enumerate}\n"
            
            questoes_latex.append(item)
            
        template_content = template_content.replace("{BLOCO_QUESTOES}", "\n".join(questoes_latex))
        
        # 5. Gerar o bloco de gabarito
        if opcoes.incluir_gabarito:
            gabarito_latex = [r"\section*{Gabarito}"]
            gabarito_latex.append(r"\begin{enumerate}")
            for i, questao in enumerate(lista_dados['questoes'], 1):
                resposta = escape_latex(str(questao.get('resposta', 'N/A')))
                gabarito_latex.append(fr"  \item {resposta}")
            gabarito_latex.append(r"\end{enumerate}")
            template_content = template_content.replace("{BLOCO_GABARITO}", "\n".join(gabarito_latex))
        else:
            template_content = template_content.replace("{BLOCO_GABARITO}", "")

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
        lista_dados = services.lista.buscar_lista_por_id_legacy(opcoes.id_lista)
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
