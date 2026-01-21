# src/views/pages/taxonomy_page.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGridLayout, QScrollArea, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QSizePolicy, QSpacerItem, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QColor
from typing import Dict, List, Any, Optional

from src.views.design.constants import Color, Spacing, Typography, Dimensions, Text, IconPath
from src.views.components.common.inputs import TextInput
from src.views.components.common.buttons import PrimaryButton, SecondaryButton
from src.views.components.layout.sidebar import TagTreeView
from src.controllers.tag_controller_orm import TagControllerORM
from src.controllers.lista_controller_orm import ListaControllerORM


class TaxonomyPage(QWidget):
    """
    Page for managing the hierarchical taxonomy of tags.
    Data is loaded from the database via controllers.
    """
    tag_selected = pyqtSignal(str)
    save_tag_requested = pyqtSignal(dict)
    delete_tag_requested = pyqtSignal(str)
    merge_tag_requested = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("taxonomy_page")

        # State
        self.current_tag_uuid: Optional[str] = None
        self.current_tag_data: Optional[Dict] = None
        self.tags_data: List = []
        self.total_tags: int = 0

        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        """Setup the UI layout."""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(Spacing.XL, Spacing.LG, Spacing.XL, Spacing.LG)
        main_layout.setSpacing(Spacing.LG)

        # 1. Left Panel - Tag Tree
        tree_frame = self._create_tree_panel()
        main_layout.addWidget(tree_frame)

        # 2. Center Panel - Edit Tag Form
        edit_frame = self._create_edit_panel()
        main_layout.addWidget(edit_frame, 2)

        # 3. Right Panel - Stats & Quick Actions
        stats_frame = self._create_stats_panel()
        main_layout.addWidget(stats_frame, 1)

    def _create_tree_panel(self) -> QFrame:
        """Create the tag tree panel."""
        frame = QFrame(self)
        frame.setObjectName("taxonomy_tree_frame")
        frame.setFixedWidth(Dimensions.TAXONOMY_TREE_WIDTH)
        frame.setStyleSheet(f"""
            QFrame#taxonomy_tree_frame {{
                background-color: {Color.WHITE};
                border: 1px solid {Color.BORDER_LIGHT};
                border-radius: {Dimensions.BORDER_RADIUS_LG};
            }}
        """)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.SM)

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel(Text.TAXONOMY_MATH, frame)
        title_label.setStyleSheet(f"""
            font-weight: {Typography.FONT_WEIGHT_BOLD};
            font-size: {Typography.FONT_SIZE_LG};
            color: {Color.DARK_TEXT};
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        self.tags_count_label = QLabel("0 tags", frame)
        self.tags_count_label.setStyleSheet(f"""
            font-size: {Typography.FONT_SIZE_SM};
            color: {Color.GRAY_TEXT};
        """)
        header_layout.addWidget(self.tags_count_label)
        layout.addLayout(header_layout)

        # Action buttons
        btn_layout = QHBoxLayout()
        collapse_btn = SecondaryButton(Text.BUTTON_COLLAPSE_ALL, parent=frame)
        collapse_btn.clicked.connect(self._collapse_all_tags)
        btn_layout.addWidget(collapse_btn)

        filter_btn = SecondaryButton(Text.BUTTON_FILTER, parent=frame)
        btn_layout.addWidget(filter_btn)
        layout.addLayout(btn_layout)

        # Tag Tree
        self.tag_tree_view = TagTreeView(frame)
        self.tag_tree_view.tag_selected.connect(self._on_tree_tag_selected)
        layout.addWidget(self.tag_tree_view)

        return frame

    def _create_edit_panel(self) -> QFrame:
        """Create the tag edit panel."""
        frame = QFrame(self)
        frame.setObjectName("edit_tag_frame")
        frame.setStyleSheet(f"""
            QFrame#edit_tag_frame {{
                background-color: {Color.WHITE};
                border: 1px solid {Color.BORDER_LIGHT};
                border-radius: {Dimensions.BORDER_RADIUS_LG};
            }}
        """)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        layout.setSpacing(Spacing.MD)

        # Header
        self.edit_header_label = QLabel(Text.TAXONOMY_EDIT_TAG.format(name=""), frame)
        self.edit_header_label.setStyleSheet(f"""
            font-size: {Typography.FONT_SIZE_XL};
            font-weight: {Typography.FONT_WEIGHT_BOLD};
            color: {Color.DARK_TEXT};
        """)
        layout.addWidget(self.edit_header_label)

        # Basic Information Section
        basic_section = QLabel(f"ℹ️ {Text.TAXONOMY_BASIC_INFO}", frame)
        basic_section.setStyleSheet(f"""
            font-size: {Typography.FONT_SIZE_MD};
            font-weight: {Typography.FONT_WEIGHT_SEMIBOLD};
            color: {Color.DARK_TEXT};
            margin-top: {Spacing.SM}px;
        """)
        layout.addWidget(basic_section)

        # Form fields
        form_grid = QGridLayout()
        form_grid.setSpacing(Spacing.SM)

        # Name
        form_grid.addWidget(QLabel(f"{Text.LABEL_NAME}:", frame), 0, 0)
        self.tag_name_input = TextInput(parent=frame)
        form_grid.addWidget(self.tag_name_input, 0, 1)

        # Slug/Numbering
        form_grid.addWidget(QLabel(f"{Text.LABEL_SLUG}:", frame), 1, 0)
        self.tag_slug_input = TextInput(parent=frame)
        form_grid.addWidget(self.tag_slug_input, 1, 1)

        # Description
        form_grid.addWidget(QLabel(f"{Text.LABEL_DESCRIPTION}:", frame), 2, 0)
        self.tag_description_input = TextInput(parent=frame)
        form_grid.addWidget(self.tag_description_input, 2, 1)

        layout.addLayout(form_grid)

        # Visual Identity Section
        visual_section = QLabel(f"🎨 {Text.TAXONOMY_VISUAL_IDENTITY}", frame)
        visual_section.setStyleSheet(f"""
            font-size: {Typography.FONT_SIZE_MD};
            font-weight: {Typography.FONT_WEIGHT_SEMIBOLD};
            color: {Color.DARK_TEXT};
            margin-top: {Spacing.MD}px;
        """)
        layout.addWidget(visual_section)

        visual_grid = QGridLayout()
        visual_grid.setSpacing(Spacing.SM)

        visual_grid.addWidget(QLabel(f"{Text.LABEL_COLOR}:", frame), 0, 0)
        self.color_picker = self._create_color_picker(frame)
        visual_grid.addWidget(self.color_picker, 0, 1)

        visual_grid.addWidget(QLabel(f"{Text.LABEL_ICON}:", frame), 1, 0)
        self.icon_picker = self._create_icon_picker(frame)
        visual_grid.addWidget(self.icon_picker, 1, 1)

        layout.addLayout(visual_grid)

        # Associated Exams Section
        exams_section = QLabel(f"📋 {Text.TAXONOMY_ASSOCIATED_EXAMS}", frame)
        exams_section.setStyleSheet(f"""
            font-size: {Typography.FONT_SIZE_MD};
            font-weight: {Typography.FONT_WEIGHT_SEMIBOLD};
            color: {Color.DARK_TEXT};
            margin-top: {Spacing.MD}px;
        """)
        layout.addWidget(exams_section)

        self.exams_table = self._create_exams_table(frame)
        layout.addWidget(self.exams_table)

        # Save Button
        save_btn = PrimaryButton(f"💾 {Text.TAXONOMY_SAVE_CHANGES}", parent=frame)
        save_btn.clicked.connect(self._on_save_tag)
        layout.addWidget(save_btn)

        layout.addStretch()

        return frame

    def _create_stats_panel(self) -> QFrame:
        """Create the statistics and quick actions panel."""
        frame = QFrame(self)
        frame.setObjectName("stats_actions_frame")
        frame.setStyleSheet(f"""
            QFrame#stats_actions_frame {{
                background-color: {Color.WHITE};
                border: 1px solid {Color.BORDER_LIGHT};
                border-radius: {Dimensions.BORDER_RADIUS_LG};
            }}
        """)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        layout.setSpacing(Spacing.MD)

        # Tag Statistics Section
        stats_label = QLabel(f"📊 {Text.TAXONOMY_TAG_STATISTICS}", frame)
        stats_label.setStyleSheet(f"""
            font-size: {Typography.FONT_SIZE_MD};
            font-weight: {Typography.FONT_WEIGHT_SEMIBOLD};
            color: {Color.DARK_TEXT};
        """)
        layout.addWidget(stats_label)

        stats_grid = QGridLayout()
        stats_grid.setSpacing(Spacing.SM)

        stats_grid.addWidget(QLabel(f"📄 {Text.STAT_QUESTIONS}:", frame), 0, 0)
        self.stat_questions_label = QLabel("0", frame)
        self.stat_questions_label.setStyleSheet(f"font-weight: {Typography.FONT_WEIGHT_BOLD};")
        stats_grid.addWidget(self.stat_questions_label, 0, 1)

        stats_grid.addWidget(QLabel(f"✅ {Text.STAT_AVG_SUCCESS}:", frame), 1, 0)
        self.stat_success_label = QLabel("-", frame)
        self.stat_success_label.setStyleSheet(f"font-weight: {Typography.FONT_WEIGHT_BOLD};")
        stats_grid.addWidget(self.stat_success_label, 1, 1)

        stats_grid.addWidget(QLabel(f"📈 {Text.STAT_DIFFICULTY}:", frame), 2, 0)
        self.stat_difficulty_label = QLabel("-", frame)
        self.stat_difficulty_label.setStyleSheet(f"font-weight: {Typography.FONT_WEIGHT_BOLD};")
        stats_grid.addWidget(self.stat_difficulty_label, 2, 1)

        layout.addLayout(stats_grid)

        # Quick Actions Section
        actions_label = QLabel(f"⚡ {Text.TAXONOMY_QUICK_ACTIONS}", frame)
        actions_label.setStyleSheet(f"""
            font-size: {Typography.FONT_SIZE_MD};
            font-weight: {Typography.FONT_WEIGHT_SEMIBOLD};
            color: {Color.DARK_TEXT};
            margin-top: {Spacing.LG}px;
        """)
        layout.addWidget(actions_label)

        merge_btn = SecondaryButton(Text.TAXONOMY_MERGE_WITH, parent=frame)
        merge_btn.clicked.connect(self._on_merge_tag)
        layout.addWidget(merge_btn)

        delete_btn = SecondaryButton(Text.TAXONOMY_DELETE_TAG, parent=frame)
        delete_btn.clicked.connect(self._on_delete_tag)
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                color: {Color.TAG_RED};
                border-color: {Color.TAG_RED};
            }}
            QPushButton:hover {{
                background-color: rgba(220, 38, 38, 0.1);
            }}
        """)
        layout.addWidget(delete_btn)

        layout.addStretch()

        return frame

    def _create_color_picker(self, parent) -> QWidget:
        """Create a simple color picker widget."""
        container = QWidget(parent)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Spacing.XS)

        colors = [
            Color.TAG_BLUE, Color.TAG_GREEN, Color.TAG_RED,
            Color.TAG_YELLOW, Color.TAG_PURPLE, Color.TAG_ORANGE
        ]

        self.color_buttons = []
        for color in colors:
            btn = QPushButton(parent)
            btn.setFixedSize(24, 24)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    border: 2px solid transparent;
                    border-radius: 12px;
                }}
                QPushButton:hover {{
                    border-color: {Color.DARK_TEXT};
                }}
            """)
            btn.setProperty("color", color)
            btn.clicked.connect(lambda checked, c=color: self._select_color(c))
            layout.addWidget(btn)
            self.color_buttons.append(btn)

        layout.addStretch()
        return container

    def _select_color(self, color: str):
        """Handle color selection."""
        for btn in self.color_buttons:
            if btn.property("color") == color:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {color};
                        border: 3px solid {Color.DARK_TEXT};
                        border-radius: 12px;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {btn.property("color")};
                        border: 2px solid transparent;
                        border-radius: 12px;
                    }}
                    QPushButton:hover {{
                        border-color: {Color.DARK_TEXT};
                    }}
                """)

    def _create_icon_picker(self, parent) -> QWidget:
        """Create a simple icon picker widget."""
        container = QWidget(parent)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Spacing.XS)

        icons = ["Σ", "📊", "📐", "∫", "≈", "π"]

        for icon in icons:
            btn = QPushButton(icon, parent)
            btn.setFixedSize(32, 32)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Color.LIGHT_BACKGROUND};
                    border: 1px solid {Color.BORDER_LIGHT};
                    border-radius: {Dimensions.BORDER_RADIUS_SM};
                    font-size: 14px;
                }}
                QPushButton:hover {{
                    background-color: {Color.LIGHT_BLUE_BG_2};
                    border-color: {Color.PRIMARY_BLUE};
                }}
            """)
            layout.addWidget(btn)

        layout.addStretch()
        return container

    def _create_exams_table(self, parent) -> QTableWidget:
        """Create the associated exams table."""
        table = QTableWidget(parent)
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels([
            Text.TABLE_EXAM_NAME, Text.TABLE_WEIGHT, Text.TABLE_DATE_ADDED
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setMaximumHeight(150)
        table.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid {Color.BORDER_LIGHT};
                border-radius: {Dimensions.BORDER_RADIUS_MD};
            }}
        """)
        return table

    def _load_data(self):
        """Load data from database."""
        try:
            # Load tag tree
            self.tags_data = TagControllerORM.obter_arvore_conteudos()
            self.tag_tree_view.load_tags_from_database()

            # Count total tags
            all_tags = TagControllerORM.listar_todas()
            self.total_tags = len(all_tags) if all_tags else 0
            self.tags_count_label.setText(
                Text.TAXONOMY_TAGS_COUNT.format(count=self.total_tags)
            )

        except Exception as e:
            print(f"Error loading taxonomy data: {e}")
            self.tags_count_label.setText("Error loading tags")

    def _on_tree_tag_selected(self, tag_uuid: str, tag_path: str, is_checked: bool):
        """Handle tag selection from tree."""
        self.current_tag_uuid = tag_uuid
        self._load_tag_details(tag_uuid)
        self.tag_selected.emit(tag_uuid)

    def _load_tag_details(self, tag_uuid: str):
        """Load tag details for editing."""
        try:
            # Find tag by UUID in the flat list
            all_tags = TagControllerORM.listar_todas()
            tag_data = None

            for tag in all_tags:
                if tag.get('uuid') == tag_uuid:
                    tag_data = tag
                    break

            if not tag_data:
                return

            self.current_tag_data = tag_data

            # Update form
            name = tag_data.get('nome', '')
            self.edit_header_label.setText(Text.TAXONOMY_EDIT_TAG.format(name=name))
            self.tag_name_input.setText(name)
            self.tag_slug_input.setText(tag_data.get('numeracao', ''))
            self.tag_description_input.setText(tag_data.get('descricao', ''))

            # Update statistics (simulated - would need real data)
            self.stat_questions_label.setText(str(tag_data.get('questoes_count', 0)))
            self.stat_success_label.setText("68%")  # Placeholder
            self.stat_difficulty_label.setText("Medium")  # Placeholder

            # Load associated exams
            self._load_associated_exams(tag_uuid)

        except Exception as e:
            print(f"Error loading tag details: {e}")

    def _load_associated_exams(self, tag_uuid: str):
        """Load exams associated with the tag."""
        try:
            # Get all lists and filter by tag (simplified)
            listas = ListaControllerORM.listar_listas()
            self.exams_table.setRowCount(0)

            row = 0
            for lista in listas[:5]:  # Limit to 5 for display
                self.exams_table.insertRow(row)
                self.exams_table.setItem(row, 0, QTableWidgetItem(lista.get('titulo', '')))
                self.exams_table.setItem(row, 1, QTableWidgetItem(str(lista.get('total_questoes', 0))))
                self.exams_table.setItem(row, 2, QTableWidgetItem(
                    lista.get('data_criacao', '-')[:10] if lista.get('data_criacao') else '-'
                ))
                row += 1

        except Exception as e:
            print(f"Error loading associated exams: {e}")

    def _on_save_tag(self):
        """Handle save tag button click."""
        if not self.current_tag_uuid:
            return

        tag_data = {
            "uuid": self.current_tag_uuid,
            "nome": self.tag_name_input.text(),
            "numeracao": self.tag_slug_input.text(),
            "descricao": self.tag_description_input.text(),
        }

        try:
            # Update via controller
            result = TagControllerORM.atualizar_tag(
                numeracao_atual=self.current_tag_data.get('numeracao', ''),
                novo_nome=tag_data['nome']
            )

            if result:
                self.save_tag_requested.emit(tag_data)
                QMessageBox.information(self, "Sucesso", "Tag atualizada com sucesso!")
                self._load_data()  # Refresh
            else:
                QMessageBox.warning(self, "Erro", "Não foi possível atualizar a tag.")

        except Exception as e:
            print(f"Error saving tag: {e}")
            QMessageBox.warning(self, "Erro", f"Erro ao salvar: {str(e)}")

    def _on_delete_tag(self):
        """Handle delete tag button click."""
        if not self.current_tag_uuid:
            return

        reply = QMessageBox.question(
            self, "Confirmar Exclusão",
            f"Tem certeza que deseja excluir a tag '{self.tag_name_input.text()}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                result = TagControllerORM.deletar_tag(
                    self.current_tag_data.get('numeracao', '')
                )

                if result:
                    self.delete_tag_requested.emit(self.current_tag_uuid)
                    QMessageBox.information(self, "Sucesso", "Tag excluída com sucesso!")
                    self._load_data()
                    self._clear_edit_form()
                else:
                    QMessageBox.warning(self, "Erro", "Não foi possível excluir a tag.")

            except Exception as e:
                print(f"Error deleting tag: {e}")
                QMessageBox.warning(self, "Erro", f"Erro ao excluir: {str(e)}")

    def _on_merge_tag(self):
        """Handle merge tag button click."""
        if not self.current_tag_uuid:
            return

        QMessageBox.information(
            self, "Merge",
            "Funcionalidade de merge será implementada em breve."
        )

    def _collapse_all_tags(self):
        """Collapse all tags in the tree."""
        for i in range(self.tag_tree_view.topLevelItemCount()):
            item = self.tag_tree_view.topLevelItem(i)
            if item:
                self.tag_tree_view.collapseItem(item)

    def _clear_edit_form(self):
        """Clear the edit form."""
        self.current_tag_uuid = None
        self.current_tag_data = None
        self.edit_header_label.setText(Text.TAXONOMY_EDIT_TAG.format(name=""))
        self.tag_name_input.clear()
        self.tag_slug_input.clear()
        self.tag_description_input.clear()
        self.stat_questions_label.setText("0")
        self.stat_success_label.setText("-")
        self.stat_difficulty_label.setText("-")
        self.exams_table.setRowCount(0)

    def refresh_data(self):
        """Public method to refresh data."""
        self._load_data()


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
            self.setWindowTitle("Taxonomy Page Test")
            self.setGeometry(100, 100, 1200, 900)

            self.taxonomy_page = TaxonomyPage(self)
            self.setCentralWidget(self.taxonomy_page)

            self.taxonomy_page.tag_selected.connect(
                lambda uuid: print(f"Tag selected: {uuid}")
            )
            self.taxonomy_page.save_tag_requested.connect(
                lambda data: print(f"Save tag: {data}")
            )
            self.taxonomy_page.delete_tag_requested.connect(
                lambda uuid: print(f"Delete tag: {uuid}")
            )

    window = TestMainWindow()
    window.show()
    sys.exit(app.exec())
