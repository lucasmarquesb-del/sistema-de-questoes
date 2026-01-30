# src/views/components/question/preview_tab.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextBrowser, QScrollArea, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QUrl
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtWebEngineWidgets import QWebEngineView
from src.views.design.constants import Color, Spacing, Typography, Dimensions
from src.views.components.common.buttons import IconButton, PrimaryButton, SecondaryButton

class PreviewTab(QWidget):
    """
    Tab for previewing the rendered question.
    """
    print_requested = pyqtSignal()
    download_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("preview_tab")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        main_layout.setSpacing(Spacing.MD)

        # Controls (Zoom, Print, Download)
        controls_frame = QFrame(self)
        controls_frame.setFixedHeight(40)
        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        controls_layout.setSpacing(Spacing.SM)

        # Zoom controls (placeholder)
        controls_layout.addWidget(QLabel("Zoom:", self))
        self.zoom_in_btn = IconButton(icon_path="images/icons/zoom_in.png", size=QSize(24,24), parent=self)
        self.zoom_in_btn.setToolTip("Zoom In")
        controls_layout.addWidget(self.zoom_in_btn)

        self.zoom_out_btn = IconButton(icon_path="images/icons/zoom_out.png", size=QSize(24,24), parent=self)
        self.zoom_out_btn.setToolTip("Zoom Out")
        controls_layout.addWidget(self.zoom_out_btn)

        self.zoom_reset_btn = SecondaryButton("100%", parent=self)
        self.zoom_reset_btn.setFixedSize(QSize(50, 24))
        controls_layout.addWidget(self.zoom_reset_btn)

        controls_layout.addStretch()

        # Print/Download buttons
        self.print_btn = PrimaryButton("Imprimir", icon="images/icons/print.png", parent=self)
        self.print_btn.setFixedSize(QSize(120, 30))
        self.print_btn.clicked.connect(self.print_requested.emit)
        controls_layout.addWidget(self.print_btn)

        self.download_btn = PrimaryButton("Download", icon="images/icons/download.png", parent=self)
        self.download_btn.setFixedSize(QSize(120, 30))
        self.download_btn.clicked.connect(self.download_requested.emit)
        controls_layout.addWidget(self.download_btn)

        main_layout.addWidget(controls_frame)

        # Question Render Area - usando QWebEngineView para suporte completo a CSS
        self.question_render_area = QWebEngineView(self)
        self.question_render_area.setObjectName("question_render_area")
        self.question_render_area.setMinimumHeight(300)
        self.question_render_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.question_render_area.setStyleSheet(f"""
            QWebEngineView#question_render_area {{
                background-color: {Color.WHITE};
                border: 1px solid {Color.BORDER_LIGHT};
                border-radius: {Dimensions.BORDER_RADIUS_MD};
            }}
        """)
        main_layout.addWidget(self.question_render_area, 1)  # stretch factor 1

        # Professor's Resolution Section (hidden by default or toggleable)
        self.resolution_section = QFrame(self)
        self.resolution_section.setObjectName("resolution_section")
        self.resolution_section.setMaximumHeight(200)
        self.resolution_section.setStyleSheet(f"QFrame#resolution_section {{ border: 1px solid {Color.BORDER_MEDIUM}; border-radius: {Dimensions.BORDER_RADIUS_MD}; background-color: {Color.LIGHT_BACKGROUND}; padding: {Spacing.MD}px; }}")
        resolution_layout = QVBoxLayout(self.resolution_section)
        resolution_layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        resolution_layout.setSpacing(Spacing.SM)

        resolution_label = QLabel("Resolução (Visão Professor)", self.resolution_section)
        resolution_label.setStyleSheet(f"font-weight: {Typography.FONT_WEIGHT_BOLD}; color: {Color.DARK_TEXT};")
        resolution_layout.addWidget(resolution_label)

        self.resolution_text_browser = QTextBrowser(self.resolution_section)
        self.resolution_text_browser.setReadOnly(True)
        self.resolution_text_browser.setHtml("<i>Conteúdo da resolução renderizado aqui.</i>") # Placeholder content
        self.resolution_text_browser.setStyleSheet(f"""
            QTextBrowser {{
                background-color: transparent;
                border: none;
                font-size: {Typography.FONT_SIZE_MD};
                color: {Color.DARK_TEXT};
            }}
        """)
        resolution_layout.addWidget(self.resolution_text_browser)
        main_layout.addWidget(self.resolution_section)
        self.resolution_section.hide()  # Hidden by default

        self.setLayout(main_layout)
        self._update_preview_content("<p style='color:#888;'>Nenhuma questão para pré-visualizar.</p>")

    def _update_preview_content(self, html_content: str, resolution_html: str = None):
        """
        Updates the content displayed in the preview area.
        """
        # Envolver em HTML completo com CSS para tabelas compactas
        full_html = f"""<!DOCTYPE html>
<html>
<head>
<style>
body {{ font-family: 'Times New Roman', serif; font-size: 14px; padding: 15px; margin: 0; color: #333; }}
p {{ margin: 5px 0; }}
h2, h3 {{ margin: 10px 0 5px 0; }}
table {{ border-collapse: collapse; margin: 8px auto; }}
td, th {{ border: 1px solid #333; padding: 2px 6px; text-align: center; font-size: 11px; line-height: 1.2; }}
th {{ background-color: #e0e0e0; font-weight: bold; }}
ul, ol {{ margin: 5px 0; padding-left: 25px; }}
li {{ margin: 2px 0; }}
</style>
</head>
<body>{html_content}</body>
</html>"""
        self.question_render_area.setHtml(full_html)
        if resolution_html:
            self.resolution_text_browser.setHtml(resolution_html)
            self.resolution_section.show()
        else:
            self.resolution_section.hide()

    def set_question_data(self, question_html: str, resolution_html: str = None):
        """
        Sets the question and optional resolution HTML content for preview.
        """
        self._update_preview_content(question_html, resolution_html)


if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    from src.views.design.theme import ThemeManager
    ThemeManager.apply_global_theme(app)

    class TestMainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Preview Tab Test")
            self.setGeometry(100, 100, 800, 900)

            self.preview_tab = PreviewTab(self)
            self.setCentralWidget(self.preview_tab)

            # Example usage:
            sample_question_html = """
            <h2>Questão de Teste 1</h2>
            <p>Qual é o valor de $$x$$ na equação $$2x + 5 = 15$$?</p>
            <ol type="A">
                <li>$$x=2$$</li>
                <li>$$x=5$$</li>
                <li>$$x=10$$</li>
            </ol>
            """
            sample_resolution_html = """
            <h3>Resolução</h3>
            <p>Dado a equação $$2x + 5 = 15$$:</p>
            <ol>
                <li>Subtraia 5 de ambos os lados: $$2x = 10$$</li>
                <li>Divida ambos os lados por 2: $$x = 5$$</li>
            </ol>
            <p>Portanto, o valor de $$x$$ é 5.</p>
            """
            self.preview_tab.set_question_data(sample_question_html, sample_resolution_html)

            self.preview_tab.print_requested.connect(lambda: print("Print requested!"))
            self.preview_tab.download_requested.connect(lambda: print("Download requested!"))

    window = TestMainWindow()
    window.show()
    sys.exit(app.exec())
