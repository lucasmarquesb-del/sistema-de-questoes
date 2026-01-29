# src/views/components/question/tags_tab.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from src.views.design.constants import Color, Spacing, Typography, Dimensions
from src.views.components.common.inputs import SearchInput
from src.views.components.common.badges import RemovableBadge, Badge
from src.views.components.forms.tag_tree import TagTreeWidget
from src.controllers.adapters import criar_tag_controller

class TagsTab(QWidget):
    """
    Tab for managing tags associated with a question.
    Allows searching, selecting from a taxonomy tree, and displaying selected tags.
    """
    tags_changed = pyqtSignal(list) # Emits a list of selected tag UUIDs

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("tags_tab")
        self.selected_tag_uuids = [] # List to store UUIDs of selected tags

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        main_layout.setSpacing(Spacing.LG)

        # 1. Selected Tags (Chips removíveis)
        selected_tags_frame = QFrame(self)
        selected_tags_frame.setObjectName("selected_tags_frame")
        selected_tags_frame.setStyleSheet(f"QFrame#selected_tags_frame {{ border: 1px solid {Color.BORDER_LIGHT}; border-radius: {Dimensions.BORDER_RADIUS_MD}; padding: {Spacing.MD}px; background-color: {Color.LIGHT_BACKGROUND}; }}")
        selected_tags_layout = QVBoxLayout(selected_tags_frame)
        selected_tags_layout.setContentsMargins(Spacing.SM, Spacing.SM, Spacing.SM, Spacing.SM)
        selected_tags_layout.setSpacing(Spacing.SM)

        selected_tags_label = QLabel("Tags Selecionadas:", selected_tags_frame)
        selected_tags_label.setStyleSheet(f"font-weight: {Typography.FONT_WEIGHT_SEMIBOLD}; color: {Color.DARK_TEXT};")
        selected_tags_layout.addWidget(selected_tags_label)

        self.selected_tags_flow_layout = QHBoxLayout() # For flowing removable badges
        self.selected_tags_flow_layout.setContentsMargins(0,0,0,0)
        self.selected_tags_flow_layout.setSpacing(Spacing.SM)
        self.selected_tags_flow_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        selected_tags_layout.addLayout(self.selected_tags_flow_layout)

        selected_tags_layout.addStretch() # Push tags to the top left
        main_layout.addWidget(selected_tags_frame)


        # 2. Tag Search
        tag_search_frame = QFrame(self)
        tag_search_frame.setObjectName("tag_search_frame")
        tag_search_frame.setStyleSheet(f"QFrame#tag_search_frame {{ border: 1px solid {Color.BORDER_LIGHT}; border-radius: {Dimensions.BORDER_RADIUS_MD}; padding: {Spacing.MD}px; }}")
        tag_search_layout = QVBoxLayout(tag_search_frame)
        tag_search_layout.setContentsMargins(Spacing.SM, Spacing.SM, Spacing.SM, Spacing.SM)
        tag_search_layout.setSpacing(Spacing.SM)

        tag_search_label = QLabel("Buscar Tags:", tag_search_frame)
        tag_search_label.setStyleSheet(f"font-weight: {Typography.FONT_WEIGHT_SEMIBOLD}; color: {Color.DARK_TEXT};")
        tag_search_layout.addWidget(tag_search_label)

        self.tag_search_input = SearchInput(placeholder_text="Pesquisar tags...", parent=tag_search_frame)
        self.tag_search_input.textChanged.connect(self._on_tag_search_changed)
        tag_search_layout.addWidget(self.tag_search_input)
        main_layout.addWidget(tag_search_frame)


        # 3. Tags and Taxonomy Tree
        taxonomy_frame = QFrame(self)
        taxonomy_frame.setObjectName("taxonomy_frame")
        taxonomy_frame.setStyleSheet(f"QFrame#taxonomy_frame {{ border: 1px solid {Color.BORDER_LIGHT}; border-radius: {Dimensions.BORDER_RADIUS_MD}; padding: {Spacing.MD}px; }}")
        taxonomy_layout = QHBoxLayout(taxonomy_frame)
        taxonomy_layout.setContentsMargins(Spacing.SM, Spacing.SM, Spacing.SM, Spacing.SM)
        taxonomy_layout.setSpacing(Spacing.LG)

        # Most Used Tags (Sidebar-like)
        most_used_frame = QFrame(taxonomy_frame)
        most_used_layout = QVBoxLayout(most_used_frame)
        most_used_layout.setContentsMargins(0,0,0,0)
        most_used_layout.setSpacing(Spacing.SM)

        most_used_label = QLabel("Tags Mais Usadas:", most_used_frame)
        most_used_label.setStyleSheet(f"font-weight: {Typography.FONT_WEIGHT_SEMIBOLD}; color: {Color.DARK_TEXT};")
        most_used_layout.addWidget(most_used_label)

        self.most_used_tags_layout = QVBoxLayout()
        self.most_used_tags_layout.setContentsMargins(0,0,0,0)
        self.most_used_tags_layout.setSpacing(Spacing.XS)
        self._add_most_used_tags_placeholders() # Add some dummy tags
        most_used_layout.addLayout(self.most_used_tags_layout)
        most_used_layout.addStretch() # Push most used tags to top

        taxonomy_layout.addWidget(most_used_frame, 1)

        # Taxonomy Tree - usando TagTreeWidget que carrega do banco de dados
        self.tag_tree_widget = TagTreeWidget(taxonomy_frame)
        self.tag_tree_widget.selectionChanged.connect(self._on_tags_selection_changed)
        taxonomy_layout.addWidget(self.tag_tree_widget, 2)

        main_layout.addWidget(taxonomy_frame, 1) # Occupy remaining space

        self.setLayout(main_layout)

        # Carregar tags do banco de dados
        self._load_tags_from_database()

    def _add_most_used_tags_placeholders(self):
        # Dummy data for most used tags
        tags_data = [
            ("Algebra", Color.TAG_BLUE),
            ("Calculus", Color.TAG_GREEN),
            ("Geometry", Color.TAG_PURPLE),
            ("ENEM", Color.TAG_ORANGE),
        ]
        for tag_text, tag_color in tags_data:
            tag_widget = Badge(tag_text, tag_color, Color.WHITE)
            self.most_used_tags_layout.addWidget(tag_widget)


    def _load_tags_from_database(self):
        """Carrega as tags de conteúdo do banco de dados."""
        try:
            self.tag_controller = criar_tag_controller()
            tags_arvore = self.tag_controller.obter_arvore_conteudos()
            self.tag_tree_widget.load_tags(tags_arvore)
        except Exception as e:
            print(f"Erro ao carregar tags: {e}")

    def _on_tag_search_changed(self, text: str):
        # TODO: Implementar filtro na árvore de tags
        print(f"Tag search: {text}")

    def _on_tags_selection_changed(self, selected_uuids: list):
        """Handler quando a seleção de tags muda na árvore."""
        # Atualizar lista interna
        self.selected_tag_uuids = selected_uuids

        # Atualizar badges visuais
        self._update_selected_badges()

        # Emitir sinal
        self.tags_changed.emit(self.selected_tag_uuids)

    def _update_selected_badges(self):
        """Atualiza os badges visuais com base nas tags selecionadas."""
        # Limpar badges existentes
        while self.selected_tags_flow_layout.count():
            item = self.selected_tags_flow_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Obter tags selecionadas com nomes
        selected_tags = self.tag_tree_widget.get_selected_content_tags_with_names()

        # Cores para as tags
        colors = [Color.TAG_BLUE, Color.TAG_GREEN, Color.TAG_PURPLE,
                  Color.TAG_ORANGE, Color.TAG_RED, Color.TAG_YELLOW]

        for i, (tag_uuid, tag_name) in enumerate(selected_tags):
            color = colors[i % len(colors)]
            badge = RemovableBadge(tag_name, color=color, text_color=Color.WHITE, parent=self)
            badge.tag_uuid = tag_uuid
            badge.removed.connect(self._on_removable_badge_removed)
            self.selected_tags_flow_layout.addWidget(badge)

    def _add_removable_badge(self, tag_uuid: str, tag_name: str):
        """Adiciona um badge removível para uma tag."""
        colors = [Color.TAG_BLUE, Color.TAG_GREEN, Color.TAG_PURPLE,
                  Color.TAG_ORANGE, Color.TAG_RED, Color.TAG_YELLOW]
        color = colors[len(self.selected_tag_uuids) % len(colors)]

        badge = RemovableBadge(tag_name, color=color, text_color=Color.WHITE, parent=self)
        badge.tag_uuid = tag_uuid
        badge.removed.connect(self._on_removable_badge_removed)
        self.selected_tags_flow_layout.addWidget(badge)

    def _remove_removable_badge(self, tag_uuid: str):
        """Remove um badge pelo UUID da tag."""
        for i in range(self.selected_tags_flow_layout.count()):
            widget = self.selected_tags_flow_layout.itemAt(i).widget()
            if hasattr(widget, 'tag_uuid') and widget.tag_uuid == tag_uuid:
                widget.setParent(None)
                widget.deleteLater()
                break

    def _on_removable_badge_removed(self, tag_name: str):
        """Handler quando um badge é removido pelo usuário."""
        # Encontrar o UUID pelo nome
        tag_uuid = None
        for i in range(self.selected_tags_flow_layout.count()):
            widget = self.selected_tags_flow_layout.itemAt(i).widget()
            if widget and hasattr(widget, 'tag_uuid') and hasattr(widget, 'text') and widget.text == tag_name:
                tag_uuid = widget.tag_uuid
                break

        if tag_uuid:
            # Desmarcar na árvore
            self._uncheck_tree_item_by_uuid(tag_uuid)

    def _uncheck_tree_item_by_uuid(self, tag_uuid: str):
        """Desmarca um item na árvore pelo UUID."""
        from PyQt6.QtWidgets import QTreeWidgetItemIterator

        iterator = QTreeWidgetItemIterator(self.tag_tree_widget.tree)
        while iterator.value():
            item = iterator.value()
            item_uuid = item.data(0, Qt.ItemDataRole.UserRole)
            if item_uuid == tag_uuid:
                item.setCheckState(0, Qt.CheckState.Unchecked)
                break
            iterator += 1


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
            self.setWindowTitle("Tags Tab Test")
            self.setGeometry(100, 100, 800, 900)

            self.tags_tab = TagsTab(self)
            self.setCentralWidget(self.tags_tab)

            self.tags_tab.tags_changed.connect(lambda tags: print(f"Selected Tags UUIDs: {tags}"))

    window = TestMainWindow()
    window.show()
    sys.exit(app.exec())
