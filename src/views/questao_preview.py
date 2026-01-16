"""
View: Questão Preview
DESCRIÇÃO: Janela modal de visualização da questão no formato PDF
COMPONENTES:
    - Enunciado renderizado com imagens
    - Alternativas (se objetiva)
    - Indicação de alternativa correta
    - Resolução (se preenchida)
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QFont
import logging
import re
import os

from src.utils import ErrorHandler

logger = logging.getLogger(__name__)


class QuestaoPreview(QDialog):
    """Janela de preview da questão no formato PDF"""

    def __init__(self, questao_data, parent=None):
        super().__init__(parent)
        self.questao_data = questao_data
        self.setWindowTitle("Preview - Formato PDF")
        self.setMinimumSize(850, 650)
        self.resize(900, 750)

        try:
            self.init_ui()
            logger.info(f"QuestaoPreview inicializado (ID: {questao_data.get('id')})")
        except Exception as e:
            ErrorHandler.handle_exception(
                self,
                e,
                "Erro ao carregar preview"
            )
            self.close()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Header com info do preview
        header_layout = QHBoxLayout()
        header_label = QLabel("Preview - Visualização no formato PDF")
        header_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #555;")
        header_layout.addWidget(header_label)
        header_layout.addStretch()

        # Badge de tipo
        tipo = self.questao_data.get('tipo', 'N/A')
        tipo_label = QLabel(tipo)
        color = "#2196f3" if tipo == 'OBJETIVA' else "#9c27b0"
        tipo_label.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: white;
                padding: 4px 12px;
                border-radius: 3px;
                font-weight: bold;
                font-size: 11px;
            }}
        """)
        header_layout.addWidget(tipo_label)
        layout.addLayout(header_layout)

        # Área de scroll com fundo branco (simula página PDF)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ccc;
                background-color: #f0f0f0;
            }
        """)

        # Container da "página PDF"
        page_container = QWidget()
        page_container.setStyleSheet("""
            QWidget {
                background-color: white;
            }
        """)
        page_layout = QVBoxLayout(page_container)
        page_layout.setContentsMargins(40, 30, 40, 30)
        page_layout.setSpacing(15)

        # Número da questão e cabeçalho
        fonte = self.questao_data.get('fonte') or ''
        ano = self.questao_data.get('ano') or ''

        # Montar cabeçalho no estilo PDF
        questao_header = "1."
        if fonte and ano:
            questao_header += f" <b>({fonte} - {ano})</b>"
        elif fonte:
            questao_header += f" <b>({fonte})</b>"
        elif ano:
            questao_header += f" <b>({ano})</b>"

        # Processar enunciado
        enunciado = self.questao_data.get('enunciado', '')
        enunciado_widgets = self._processar_texto_com_imagens(enunciado)

        # Primeira linha: número + cabeçalho + início do enunciado
        first_line_layout = QHBoxLayout()
        first_line_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        header_label = QLabel(questao_header)
        header_label.setFont(QFont("Times New Roman", 12))
        header_label.setTextFormat(Qt.TextFormat.RichText)
        first_line_layout.addWidget(header_label)
        first_line_layout.addStretch()

        page_layout.addLayout(first_line_layout)

        # Adicionar widgets do enunciado (texto e imagens)
        for widget in enunciado_widgets:
            page_layout.addWidget(widget)

        # Alternativas (se objetiva)
        if tipo == 'OBJETIVA' and 'alternativas' in self.questao_data:
            page_layout.addSpacing(10)

            for alt in self.questao_data['alternativas']:
                # Letra da alternativa
                letra = alt.get('letra', '')
                correta = alt.get('correta', False)

                letra_text = f"<b>{letra})</b>"
                if correta:
                    letra_text = f"<b style='color: green;'>{letra})</b>"

                # Container principal da alternativa
                alt_container = QWidget()
                alt_container_layout = QVBoxLayout(alt_container)
                alt_container_layout.setContentsMargins(20, 2, 0, 2)
                alt_container_layout.setSpacing(2)

                # Primeira linha: letra + texto
                first_line = QHBoxLayout()
                first_line.setAlignment(Qt.AlignmentFlag.AlignTop)

                letra_label = QLabel(letra_text)
                letra_label.setFont(QFont("Times New Roman", 12))
                letra_label.setTextFormat(Qt.TextFormat.RichText)
                letra_label.setFixedWidth(30)
                first_line.addWidget(letra_label)

                # Processar texto da alternativa (pode conter imagens)
                texto_alt_raw = alt.get('texto', '')
                alt_widgets = self._processar_texto_com_imagens(texto_alt_raw)

                # Se há widgets, adicionar o primeiro na mesma linha da letra
                if alt_widgets:
                    first_widget = alt_widgets[0]
                    # Alinhar imagens à esquerda nas alternativas
                    if isinstance(first_widget, QLabel) and first_widget.pixmap() and not first_widget.pixmap().isNull():
                        first_widget.setAlignment(Qt.AlignmentFlag.AlignLeft)
                    elif correta and isinstance(first_widget, QLabel):
                        # É um label de texto, aplicar cor verde
                        texto_atual = first_widget.text()
                        first_widget.setText(f"<span style='color: green;'>{texto_atual}</span> ✓")
                    first_line.addWidget(first_widget, 1)
                else:
                    # Sem conteúdo, adicionar label vazio
                    empty_label = QLabel("")
                    first_line.addWidget(empty_label, 1)

                alt_container_layout.addLayout(first_line)

                # Adicionar widgets restantes (imagens ou mais texto)
                for widget in alt_widgets[1:]:
                    # Alinhar imagens à esquerda nas alternativas
                    if isinstance(widget, QLabel) and widget.pixmap() and not widget.pixmap().isNull():
                        widget.setAlignment(Qt.AlignmentFlag.AlignLeft)
                    widget.setContentsMargins(30, 0, 0, 0)  # Indentar para alinhar com texto
                    alt_container_layout.addWidget(widget)

                page_layout.addWidget(alt_container)

        # Resolução (se houver)
        resolucao = self.questao_data.get('resolucao')
        if resolucao and resolucao.strip():
            page_layout.addSpacing(20)

            res_title = QLabel("<b>Resolução:</b>")
            res_title.setFont(QFont("Times New Roman", 12))
            res_title.setTextFormat(Qt.TextFormat.RichText)
            page_layout.addWidget(res_title)

            res_widgets = self._processar_texto_com_imagens(resolucao)
            for widget in res_widgets:
                page_layout.addWidget(widget)

        # Tags (rodapé informativo)
        tags = self.questao_data.get('tags', [])
        if tags:
            page_layout.addSpacing(20)

            tags_layout = QHBoxLayout()
            tags_layout.addWidget(QLabel("<i>Tags:</i>"))

            for tag in tags:
                tag_nome = tag.get('nome') if isinstance(tag, dict) else tag
                tag_label = QLabel(tag_nome)
                tag_label.setStyleSheet("""
                    QLabel {
                        background-color: #e8e8e8;
                        color: #555;
                        padding: 2px 8px;
                        border-radius: 2px;
                        font-size: 10px;
                    }
                """)
                tags_layout.addWidget(tag_label)

            tags_layout.addStretch()
            page_layout.addLayout(tags_layout)

        page_layout.addStretch()

        scroll.setWidget(page_container)
        layout.addWidget(scroll)

        # Botões
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_close = QPushButton("Fechar")
        btn_close.setStyleSheet("""
            QPushButton {
                padding: 8px 25px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)

        layout.addLayout(btn_layout)

    def _processar_texto_com_imagens(self, texto: str) -> list:
        """
        Processa texto e retorna lista de widgets (QLabel para texto, QLabel com pixmap para imagens).
        """
        widgets = []

        if not texto:
            return widgets

        # Padrão para encontrar imagens: [IMG:caminho:escala]
        pattern = r'\[IMG:(.+?):([0-9.]+)\]'

        # Dividir texto por imagens
        parts = re.split(pattern, texto)

        i = 0
        while i < len(parts):
            part = parts[i]

            if i + 2 < len(parts):
                # Verificar se próximas partes são caminho e escala de imagem
                next_part = parts[i + 1] if i + 1 < len(parts) else None
                scale_part = parts[i + 2] if i + 2 < len(parts) else None

                # Se part atual é texto antes da imagem
                if part.strip():
                    text_widget = self._criar_label_texto(part)
                    widgets.append(text_widget)

                # Verificar se temos caminho de imagem válido
                if next_part and scale_part and os.path.exists(next_part):
                    try:
                        scale = float(scale_part)
                        img_widget = self._criar_label_imagem(next_part, scale)
                        if img_widget:
                            widgets.append(img_widget)
                        i += 3
                        continue
                    except (ValueError, Exception):
                        pass

            # Texto normal
            if part.strip():
                text_widget = self._criar_label_texto(part)
                widgets.append(text_widget)

            i += 1

        return widgets

    def _criar_label_texto(self, texto: str) -> QLabel:
        """Cria QLabel com texto formatado."""
        texto_formatado = self._formatar_texto_latex(texto)

        label = QLabel(texto_formatado)
        label.setFont(QFont("Times New Roman", 12))
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setWordWrap(True)
        label.setStyleSheet("padding: 5px 0;")

        return label

    def _criar_label_imagem(self, caminho: str, escala: float) -> QLabel:
        """Cria QLabel com imagem."""
        if not os.path.exists(caminho):
            return None

        pixmap = QPixmap(caminho)
        if pixmap.isNull():
            return None

        # Aplicar escala
        new_width = int(pixmap.width() * escala)
        new_height = int(pixmap.height() * escala)

        # Limitar tamanho máximo
        max_width = 600
        if new_width > max_width:
            ratio = max_width / new_width
            new_width = max_width
            new_height = int(new_height * ratio)

        scaled_pixmap = pixmap.scaled(
            new_width, new_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        label = QLabel()
        label.setPixmap(scaled_pixmap)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("padding: 10px 0;")

        return label

    def _formatar_texto_latex(self, texto: str) -> str:
        """
        Converte comandos LaTeX básicos para HTML.
        """
        if not texto:
            return ""

        # Negrito: \textbf{texto}
        texto = re.sub(r'\\textbf\{([^}]*)\}', r'<b>\1</b>', texto)

        # Itálico: \textit{texto}
        texto = re.sub(r'\\textit\{([^}]*)\}', r'<i>\1</i>', texto)

        # Sublinhado: \underline{texto}
        texto = re.sub(r'\\underline\{([^}]*)\}', r'<u>\1</u>', texto)

        # Preservar quebras de linha
        texto = texto.replace('\n', '<br>')

        return texto


logger.info("QuestaoPreview carregado")
