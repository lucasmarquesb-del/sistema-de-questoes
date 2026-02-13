"""Página de gerenciamento de usuários (somente admin)."""

import logging
from typing import Optional, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QSizePolicy, QAbstractItemView
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor

from src.views.design.constants import Color, Spacing, Typography, Text
from src.services.api_client import ApiClient

logger = logging.getLogger(__name__)


class UserManagementPage(QWidget):
    """Página administrativa para gerenciar acesso de usuários."""

    def __init__(self, api_client: ApiClient, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.setObjectName("user_management_page")
        self._users_cache: List[dict] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.XL, Spacing.LG, Spacing.XL, Spacing.LG)
        layout.setSpacing(Spacing.LG)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Gerenciamento de Usuarios")
        title.setStyleSheet(f"""
            font-size: {Typography.FONT_SIZE_PAGE_TITLE};
            font-weight: {Typography.FONT_WEIGHT_BOLD};
            color: {Color.DARK_TEXT};
            font-family: {Typography.FONT_FAMILY};
        """)
        header_layout.addWidget(title)
        header_layout.addStretch()

        # Botão atualizar
        self.refresh_button = QPushButton("Atualizar")
        self.refresh_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {Color.PRIMARY_BLUE};
                color: {Color.WHITE};
                border: none;
                border-radius: 6px;
                font-size: {Typography.FONT_SIZE_SM};
                font-weight: {Typography.FONT_WEIGHT_MEDIUM};
                font-family: {Typography.FONT_FAMILY};
                padding: 8px 20px;
            }}
            QPushButton:hover {{
                background-color: {Color.HOVER_BLUE};
            }}
        """)
        self.refresh_button.clicked.connect(self.load_users)
        header_layout.addWidget(self.refresh_button)

        layout.addLayout(header_layout)

        # Descrição
        desc = QLabel("Ative ou desative o acesso de usuarios ao sistema.")
        desc.setStyleSheet(f"""
            font-size: {Typography.FONT_SIZE_SM};
            color: {Color.GRAY_TEXT};
            font-family: {Typography.FONT_FAMILY};
        """)
        layout.addWidget(desc)

        # Tabela de usuários
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Email", "Nome", "Perfil", "Status", "Acao"])
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid {Color.BORDER_LIGHT};
                border-radius: 8px;
                background-color: {Color.WHITE};
                font-family: {Typography.FONT_FAMILY};
                font-size: {Typography.FONT_SIZE_SM};
                gridline-color: {Color.BORDER_LIGHT};
            }}
            QTableWidget::item {{
                padding: 8px 12px;
            }}
            QHeaderView::section {{
                background-color: {Color.LIGHT_BACKGROUND};
                color: {Color.DARK_TEXT};
                font-weight: {Typography.FONT_WEIGHT_SEMIBOLD};
                font-size: {Typography.FONT_SIZE_SM};
                padding: 10px 12px;
                border: none;
                border-bottom: 2px solid {Color.BORDER_MEDIUM};
            }}
        """)
        layout.addWidget(self.table)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"""
            font-size: {Typography.FONT_SIZE_XS};
            color: {Color.GRAY_TEXT};
            font-family: {Typography.FONT_FAMILY};
        """)
        layout.addWidget(self.status_label)

    def load_users(self):
        """Carrega lista de usuários do backend."""
        self.status_label.setText("Carregando...")
        users = self.api_client.list_users()

        if users is None:
            self.status_label.setText("Erro ao carregar usuarios. Verifique a conexao com o servidor.")
            return

        self._users_cache = users
        self._populate_table(users)
        self.status_label.setText(f"{len(users)} usuario(s) encontrado(s)")

    def _populate_table(self, users: list):
        """Preenche tabela com dados dos usuários."""
        self.table.setRowCount(len(users))

        for row, user in enumerate(users):
            # Email
            email_item = QTableWidgetItem(user.get("email", ""))
            self.table.setItem(row, 0, email_item)

            # Nome
            name_item = QTableWidgetItem(user.get("name", "") or "")
            self.table.setItem(row, 1, name_item)

            # Perfil/Role
            role = user.get("role", "user")
            role_item = QTableWidgetItem("Administrador" if role == "admin" else "Usuario")
            if role == "admin":
                role_item.setForeground(QColor(Color.PRIMARY_BLUE))
            self.table.setItem(row, 2, role_item)

            # Status
            is_active = user.get("is_active", False)
            status_item = QTableWidgetItem("Ativo" if is_active else "Inativo")
            status_item.setForeground(
                QColor(Color.DIFFICULTY_EASY) if is_active else QColor(Color.TAG_RED)
            )
            self.table.setItem(row, 3, status_item)

            # Botão ação
            user_id = user.get("id")
            if role != "admin":
                btn = QPushButton("Desativar" if is_active else "Ativar")
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                if is_active:
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {Color.TAG_RED};
                            color: {Color.WHITE};
                            border: none;
                            border-radius: 4px;
                            font-size: 12px;
                            padding: 6px 16px;
                        }}
                        QPushButton:hover {{ background-color: #b91c1c; }}
                    """)
                else:
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {Color.DIFFICULTY_EASY};
                            color: {Color.WHITE};
                            border: none;
                            border-radius: 4px;
                            font-size: 12px;
                            padding: 6px 16px;
                        }}
                        QPushButton:hover {{ background-color: #15803d; }}
                    """)
                btn.clicked.connect(lambda checked, uid=user_id, active=is_active: self._toggle_user(uid, not active))
                self.table.setCellWidget(row, 4, btn)
            else:
                admin_label = QLabel("  -")
                admin_label.setStyleSheet(f"color: {Color.GRAY_TEXT}; font-size: 12px;")
                self.table.setCellWidget(row, 4, admin_label)

        self.table.resizeRowsToContents()

    def _toggle_user(self, user_id: int, new_active: bool):
        """Ativa ou desativa um usuário."""
        result = self.api_client.update_user(user_id, {"is_active": new_active})
        if result:
            action = "ativado" if new_active else "desativado"
            self.status_label.setText(f"Usuario {result.get('email', '')} {action} com sucesso.")
            self.load_users()
        else:
            self.status_label.setText("Erro ao atualizar usuario.")

    def showEvent(self, event):
        """Recarrega dados ao exibir a página."""
        super().showEvent(event)
        self.load_users()
