# src/views/components/layout/sidebar.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTreeWidget, QTreeWidgetItem, QApplication,
    QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QIcon, QFont
from typing import List, Dict, Any, Optional

from src.views.design.constants import Color, Spacing, Typography, Dimensions, Text, IconPath
from src.views.design.enums import ActionEnum
from src.views.components.common.buttons import IconButton, PrimaryButton, SecondaryButton
from src.controllers.tag_controller_orm import TagControllerORM


class TagTreeItem(QTreeWidgetItem):
    """Custom tree widget item for a tag, supporting expansion and optional checkbox."""

    def __init__(self, parent, name: str, uuid: str, numeracao: str = "", level: int = 0,
                 selectable: bool = True, is_checked: bool = False, question_count: int = 0):
        # Format display text with numbering
        display_text = f"{numeracao} {name}" if numeracao else name
        super().__init__(parent, [display_text])

        self.uuid = uuid
        self.name = name
        self.numeracao = numeracao
        self.level = level
        self.selectable = selectable
        self.question_count = question_count

        if selectable:
            self.setFlags(self.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsSelectable)
            self.setCheckState(0, Qt.CheckState.Checked if is_checked else Qt.CheckState.Unchecked)
        else:
            self.setFlags(self.flags() | Qt.ItemFlag.ItemIsSelectable)

        # Set font based on level
        font = self.font(0)
        if level == 0:
            font.setPointSize(11)
            font.setBold(True)
        elif level == 1:
            font.setPointSize(10)
            font.setBold(True)
        else:
            font.setPointSize(9)
        self.setFont(0, font)

        # Set icon based on level
        if level == 0:
            self.setIcon(0, QIcon())  # Root items can have category icons


class TagTreeView(QTreeWidget):
    """Hierarchical tree view for tags loaded from database."""

    tag_selected = pyqtSignal(str, str, bool)  # (tag_uuid, tag_path, is_checked)
    item_expanded = pyqtSignal(str)
    item_collapsed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("tag_tree_view")
        self.setHeaderHidden(True)
        self.setRootIsDecorated(True)
        self.setIndentation(Spacing.LG)
        self.setAnimated(True)

        self.itemChanged.connect(self._on_item_changed)
        self.itemClicked.connect(self._on_item_clicked)
        self.itemExpanded.connect(lambda item: self.item_expanded.emit(item.uuid))
        self.itemCollapsed.connect(lambda item: self.item_collapsed.emit(item.uuid))

        self._apply_styles()

    def _apply_styles(self):
        """Apply QSS styles to the tree view."""
        self.setStyleSheet(f"""
            QTreeWidget#tag_tree_view {{
                background-color: transparent;
                border: none;
                font-size: {Typography.FONT_SIZE_MD};
                color: {Color.DARK_TEXT};
                show-decoration-selected: 1;
            }}
            QTreeWidget#tag_tree_view::item {{
                padding: {Spacing.XS}px 0;
                margin: {Spacing.XXS}px 0;
                border-radius: {Dimensions.BORDER_RADIUS_SM};
            }}
            QTreeWidget#tag_tree_view::item:selected {{
                background-color: {Color.LIGHT_BLUE_BG_2};
                color: {Color.PRIMARY_BLUE};
            }}
            QTreeWidget#tag_tree_view::item:hover {{
                background-color: {Color.BORDER_LIGHT};
            }}
            QTreeWidget#tag_tree_view::branch {{
                background: transparent;
            }}
            QTreeWidget#tag_tree_view::branch:open:has-children {{
                image: url({IconPath.ARROW_DOWN});
            }}
            QTreeWidget#tag_tree_view::branch:closed:has-children {{
                image: url({IconPath.ARROW_RIGHT});
            }}
        """)

    def load_tags_from_database(self):
        """Load tags from database using controller."""
        self.clear()

        try:
            # Get hierarchical tree from controller
            tree_data = TagControllerORM.obter_arvore_conteudos()

            if not tree_data:
                # Show empty state
                empty_item = QTreeWidgetItem(self, [Text.EMPTY_NO_TAGS])
                empty_item.setFlags(Qt.ItemFlag.NoItemFlags)
                return

            # Convert DTOs to tree items
            for root_dto in tree_data:
                self._add_tag_item(self, root_dto, level=0)

            # Expand first level by default
            for i in range(self.topLevelItemCount()):
                item = self.topLevelItem(i)
                if item:
                    self.expandItem(item)

        except Exception as e:
            print(f"Error loading tags: {e}")
            error_item = QTreeWidgetItem(self, ["Erro ao carregar tags"])
            error_item.setFlags(Qt.ItemFlag.NoItemFlags)

    def _add_tag_item(self, parent, tag_dto, level: int = 0) -> TagTreeItem:
        """Recursively add tag items to the tree."""
        item = TagTreeItem(
            parent,
            name=tag_dto.nome,
            uuid=tag_dto.uuid,
            numeracao=tag_dto.numeracao if hasattr(tag_dto, 'numeracao') else "",
            level=level,
            selectable=True,
            is_checked=False
        )

        # Add children recursively
        if hasattr(tag_dto, 'filhos') and tag_dto.filhos:
            for child_dto in tag_dto.filhos:
                self._add_tag_item(item, child_dto, level + 1)

        return item

    def set_tags(self, tags_data: List[Dict]):
        """Set tags from a list of dictionaries (alternative to database loading)."""
        self.clear()
        self._add_tags_to_tree(self, tags_data, level=0)

    def _add_tags_to_tree(self, parent_item, tags_data: List[Dict], level: int = 0):
        """Recursively add tags from dict data."""
        for tag in tags_data:
            item = TagTreeItem(
                parent_item,
                name=tag.get('nome', tag.get('name', '')),
                uuid=tag.get('uuid', ''),
                numeracao=tag.get('numeracao', ''),
                level=level,
                selectable=tag.get('selectable', True),
                is_checked=tag.get('is_checked', False)
            )
            if 'children' in tag and tag['children']:
                self._add_tags_to_tree(item, tag['children'], level + 1)
            elif 'filhas' in tag and tag['filhas']:
                self._add_tags_to_tree(item, tag['filhas'], level + 1)

    def _on_item_changed(self, item: TagTreeItem, column: int):
        """Handle item checkbox state change."""
        if hasattr(item, 'selectable') and item.selectable and column == 0:
            is_checked = item.checkState(column) == Qt.CheckState.Checked
            tag_path = self._get_tag_path(item)
            self.tag_selected.emit(item.uuid, tag_path, is_checked)

    def _on_item_clicked(self, item: TagTreeItem, column: int):
        """Handle item click."""
        if hasattr(item, 'selectable') and not item.selectable:
            # Toggle expansion for non-selectable items
            if item.isExpanded():
                self.collapseItem(item)
            else:
                self.expandItem(item)

    def _get_tag_path(self, item: TagTreeItem) -> str:
        """Get the full path of a tag (e.g., 'Algebra / Functions / Linear')."""
        path_parts = []
        current = item
        while current:
            if hasattr(current, 'name'):
                path_parts.insert(0, current.name)
            if current.parent():
                current = current.parent()
            else:
                break
        return " / ".join(path_parts)


class Sidebar(QFrame):
    """Main sidebar component for navigation and filtering."""

    export_clicked = pyqtSignal()
    help_clicked = pyqtSignal()
    tag_filter_changed = pyqtSignal(str, str, bool)  # (tag_uuid, tag_path, is_checked)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(Dimensions.SIDEBAR_WIDTH)

        self._setup_ui()
        self._load_tags()

    def _setup_ui(self):
        """Setup the sidebar UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        main_layout.setSpacing(Spacing.LG)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Header
        header_layout = QHBoxLayout()

        header_title = QLabel(Text.SIDEBAR_MATH_CONTENT, self)
        header_title.setObjectName("sidebar_title")
        header_title.setStyleSheet(f"""
            QLabel#sidebar_title {{
                font-size: {Typography.FONT_SIZE_SM};
                font-weight: {Typography.FONT_WEIGHT_BOLD};
                color: {Color.DARK_TEXT};
                letter-spacing: 1px;
            }}
        """)
        header_layout.addWidget(header_title)
        header_layout.addStretch()

        # Expand/Collapse toggle
        self.expand_btn = IconButton(icon_path=IconPath.COLLAPSE, size=QSize(16, 16), parent=self)
        self.expand_btn.setToolTip("Expand/Collapse")
        self.expand_btn.clicked.connect(self._toggle_all_items)
        header_layout.addWidget(self.expand_btn)

        main_layout.addLayout(header_layout)

        # Subtitle
        tags_subtitle = QLabel(Text.SIDEBAR_HIERARCHICAL_TAGS, self)
        tags_subtitle.setObjectName("sidebar_subtitle")
        tags_subtitle.setStyleSheet(f"""
            QLabel#sidebar_subtitle {{
                font-size: {Typography.FONT_SIZE_XS};
                color: {Color.GRAY_TEXT};
            }}
        """)
        main_layout.addWidget(tags_subtitle)

        # Tag Tree View
        self.tag_tree_view = TagTreeView(self)
        self.tag_tree_view.tag_selected.connect(self.tag_filter_changed.emit)
        main_layout.addWidget(self.tag_tree_view)

        # Footer Actions
        footer_frame = QFrame(self)
        footer_frame.setObjectName("sidebar_footer")
        footer_frame.setStyleSheet(f"""
            QFrame#sidebar_footer {{
                border-top: 1px solid {Color.BORDER_LIGHT};
                padding-top: {Spacing.MD}px;
            }}
        """)

        footer_layout = QVBoxLayout(footer_frame)
        footer_layout.setContentsMargins(0, Spacing.MD, 0, 0)
        footer_layout.setSpacing(Spacing.SM)
        footer_layout.setAlignment(Qt.AlignmentFlag.AlignBottom)

        export_button = PrimaryButton(Text.BUTTON_EXPORT_PDF, icon=IconPath.PDF, parent=self)
        export_button.clicked.connect(self.export_clicked.emit)
        footer_layout.addWidget(export_button)

        help_button = SecondaryButton(Text.SIDEBAR_HELP_CENTER, icon=IconPath.HELP, parent=self)
        help_button.clicked.connect(self.help_clicked.emit)
        footer_layout.addWidget(help_button)

        main_layout.addWidget(footer_frame)
        main_layout.addStretch()

    def _load_tags(self):
        """Load tags from database."""
        self.tag_tree_view.load_tags_from_database()

    def _toggle_all_items(self):
        """Toggle expand/collapse all items."""
        # Check if any items are expanded
        any_expanded = False
        for i in range(self.tag_tree_view.topLevelItemCount()):
            item = self.tag_tree_view.topLevelItem(i)
            if item and item.isExpanded():
                any_expanded = True
                break

        # Toggle all items
        for i in range(self.tag_tree_view.topLevelItemCount()):
            item = self.tag_tree_view.topLevelItem(i)
            if item:
                if any_expanded:
                    self.tag_tree_view.collapseItem(item)
                else:
                    self.tag_tree_view.expandItem(item)

    def refresh_tags(self):
        """Public method to refresh tags from database."""
        self._load_tags()

    def set_tags(self, tags_data: List[Dict]):
        """Set tags programmatically (alternative to database)."""
        self.tag_tree_view.set_tags(tags_data)


if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QMainWindow

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    from src.views.design.theme import ThemeManager
    ThemeManager.apply_global_theme(app)

    class TestMainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Sidebar Test")
            self.setGeometry(100, 100, 400, 800)

            self.sidebar = Sidebar(self)
            self.setCentralWidget(self.sidebar)

            self.sidebar.export_clicked.connect(lambda: print("Export button clicked!"))
            self.sidebar.help_clicked.connect(lambda: print("Help button clicked!"))
            self.sidebar.tag_filter_changed.connect(
                lambda uuid, path, checked: print(f"Tag: {path} ({uuid}), Checked: {checked}")
            )

    window = TestMainWindow()
    window.show()
    sys.exit(app.exec())
