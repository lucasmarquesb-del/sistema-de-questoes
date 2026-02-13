"""Janela de login com Google OAuth."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QFont

from src.views.design.constants import Color, Spacing, Typography


class LoginWindow(QWidget):
    """Janela de login exibida antes do app principal.

    Signals:
        login_requested: Emitido quando o botão de login é clicado.
    """

    login_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("MathBank - Login")
        self.setFixedSize(480, 520)
        self._center_on_screen()
        self._setup_ui()

    def _center_on_screen(self):
        screen = QApplication.primaryScreen()
        if screen:
            rect = screen.availableGeometry()
            x = (rect.width() - self.width()) // 2
            y = (rect.height() - self.height()) // 2
            self.move(x, y)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.XXL * 2, Spacing.XXL * 2, Spacing.XXL * 2, Spacing.XXL * 2)
        layout.setSpacing(Spacing.LG)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Logo / Título
        logo_label = QLabel("MathBank")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setStyleSheet(f"""
            font-size: 36px;
            font-weight: {Typography.FONT_WEIGHT_BOLD};
            color: {Color.PRIMARY_BLUE};
            font-family: {Typography.FONT_FAMILY};
            margin-bottom: 8px;
        """)
        layout.addWidget(logo_label)

        # Subtítulo
        subtitle = QLabel("Sistema de Banco de Questoes Educacionais")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(f"""
            font-size: {Typography.FONT_SIZE_MD};
            color: {Color.GRAY_TEXT};
            font-family: {Typography.FONT_FAMILY};
            margin-bottom: 24px;
        """)
        layout.addWidget(subtitle)

        # Separador visual
        layout.addSpacing(Spacing.XL)

        # Botão Login com Google
        self.login_button = QPushButton("  Login com Google")
        self.login_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_button.setFixedSize(QSize(300, 50))
        self.login_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {Color.WHITE};
                color: {Color.DARK_TEXT};
                border: 2px solid {Color.BORDER_MEDIUM};
                border-radius: 8px;
                font-size: 15px;
                font-weight: {Typography.FONT_WEIGHT_MEDIUM};
                font-family: {Typography.FONT_FAMILY};
                padding: 8px 24px;
            }}
            QPushButton:hover {{
                border-color: {Color.PRIMARY_BLUE};
                background-color: {Color.LIGHT_BLUE_BG_2};
            }}
            QPushButton:pressed {{
                background-color: {Color.LIGHT_BLUE_BG_1};
            }}
        """)
        self.login_button.clicked.connect(self._on_login_clicked)

        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_layout.addWidget(self.login_button)
        layout.addLayout(btn_layout)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet(f"""
            font-size: {Typography.FONT_SIZE_SM};
            color: {Color.GRAY_TEXT};
            font-family: {Typography.FONT_FAMILY};
            margin-top: 16px;
        """)
        layout.addWidget(self.status_label)

        layout.addStretch()

        # Estilo geral da janela
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {Color.WHITE};
            }}
        """)

    def _on_login_clicked(self):
        self.set_loading(True)
        self.login_requested.emit()

    def set_loading(self, loading: bool):
        """Alterna estado de loading."""
        if loading:
            self.login_button.setEnabled(False)
            self.login_button.setText("  Aguardando autenticacao...")
            self.status_label.setText("Uma janela do navegador foi aberta.\nFaca login com sua conta Google.")
            self.status_label.setStyleSheet(f"""
                font-size: {Typography.FONT_SIZE_SM};
                color: {Color.PRIMARY_BLUE};
                font-family: {Typography.FONT_FAMILY};
                margin-top: 16px;
            """)
        else:
            self.login_button.setEnabled(True)
            self.login_button.setText("  Login com Google")
            self.status_label.setText("")

    def show_error(self, message: str):
        """Exibe mensagem de erro."""
        self.set_loading(False)
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"""
            font-size: {Typography.FONT_SIZE_SM};
            color: #dc2626;
            font-family: {Typography.FONT_FAMILY};
            margin-top: 16px;
        """)

    def show_pending(self, email: str):
        """Exibe mensagem de conta pendente de aprovação."""
        self.set_loading(False)
        self.status_label.setText(
            f"A conta {email} foi registrada.\n"
            "Aguarde a aprovacao do administrador para acessar o sistema."
        )
        self.status_label.setStyleSheet(f"""
            font-size: {Typography.FONT_SIZE_SM};
            color: #ca8a04;
            font-family: {Typography.FONT_FAMILY};
            margin-top: 16px;
        """)
