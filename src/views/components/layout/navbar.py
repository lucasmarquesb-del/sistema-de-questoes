# src/views/components/layout/navbar.py
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QVBoxLayout, QFrame
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from src.views.design.constants import Color, Spacing, Typography, Dimensions, Text
from src.views.design.enums import PageEnum, ActionEnum, ButtonTypeEnum
from src.views.components.common.buttons import IconButton, ContextualActionButton

class NavItem(QWidget):
    """
    Individual navigation item for the Navbar.
    """
    clicked = pyqtSignal(PageEnum)

    def __init__(self, page_enum: PageEnum, label: str, is_active: bool = False, parent=None):
        super().__init__(parent)
        self.page_enum = page_enum
        self.setObjectName("nav_item_container")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(Spacing.MD, Spacing.SM, Spacing.MD, Spacing.SM)
        self.layout.setSpacing(0)

        self.label = QLabel(label)
        self.label.setObjectName("nav_active" if is_active else "nav_link")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.label)

        self.setStyleSheet(f"""
            QWidget#nav_item_container {{
                background-color: transparent;
                padding: 0;
            }}
            QLabel#nav_link {{
                color: {Color.GRAY_TEXT};
                font-size: {Typography.FONT_SIZE_MD};
                font-weight: {Typography.FONT_WEIGHT_MEDIUM};
                border: none;
                background: transparent;
                padding: {Spacing.XS}px {Spacing.NONE}px;
            }}
            QLabel#nav_link:hover {{
                color: {Color.PRIMARY_BLUE};
            }}
            QLabel#nav_active {{
                color: {Color.PRIMARY_BLUE};
                font-size: {Typography.FONT_SIZE_MD};
                font-weight: {Typography.FONT_WEIGHT_SEMIBOLD};
                border: none;
                border-bottom: 2px solid {Color.PRIMARY_BLUE};
                background: transparent;
                padding: {Spacing.XS}px {Spacing.NONE}px;
            }}
        """)

    def mousePressEvent(self, event):
        self.clicked.emit(self.page_enum)
        super().mousePressEvent(event)

    def set_active(self, is_active: bool):
        self.label.setObjectName("nav_active" if is_active else "nav_link")
        self.label.style().polish(self.label) # Repolish to apply new objectName style


class NavMenu(QWidget):
    """
    Horizontal menu of NavItems.
    """
    page_changed = pyqtSignal(PageEnum)

    def __init__(self, current_page: PageEnum = PageEnum.DASHBOARD, parent=None):
        super().__init__(parent)
        self.current_page = current_page
        self.nav_items = {}

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(Spacing.LG)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self._add_nav_item(PageEnum.DASHBOARD, Text.NAV_DASHBOARD)
        self._add_nav_item(PageEnum.QUESTION_BANK, Text.NAV_QUESTION_BANK)
        self._add_nav_item(PageEnum.LISTS, Text.NAV_EXAMS)
        self._add_nav_item(PageEnum.TAXONOMY, Text.NAV_TAXONOMY)

        self.update_active_item(self.current_page)

    def _add_nav_item(self, page_enum: PageEnum, label: str):
        item = NavItem(page_enum, label, parent=self)
        item.clicked.connect(self._on_nav_item_clicked)
        self.layout.addWidget(item)
        self.nav_items[page_enum] = item

    def _on_nav_item_clicked(self, page_enum: PageEnum):
        self.update_active_item(page_enum)
        self.page_changed.emit(page_enum)

    def update_active_item(self, new_page: PageEnum):
        if self.current_page in self.nav_items:
            self.nav_items[self.current_page].set_active(False)
        if new_page in self.nav_items:
            self.nav_items[new_page].set_active(True)
        self.current_page = new_page


class Navbar(QFrame):
    """
    Main navigation bar for the application.
    """
    page_changed = pyqtSignal(PageEnum)
    action_clicked = pyqtSignal(ActionEnum)
    notifications_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()
    profile_clicked = pyqtSignal()

    def __init__(self, current_page: PageEnum = PageEnum.DASHBOARD, parent=None):
        super().__init__(parent)
        self.setObjectName("header")
        self.setFixedHeight(Dimensions.NAVBAR_HEIGHT)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(Spacing.XL, 0, Spacing.XL, 0)
        main_layout.setSpacing(Spacing.XL)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # 1. Logo
        logo_container = QHBoxLayout()
        logo_container.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.logo_label = QLabel(self)
        self.logo_label.setObjectName("logo")
        # Placeholder for actual Sigma icon + text
        self.logo_label.setText(f"Σ {Text.APP_TITLE}") # Assuming Σ is part of the text or an icon
        self.logo_label.setFixedSize(QSize(120, 30)) # Example size
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_container.addWidget(self.logo_label)
        main_layout.addLayout(logo_container)

        # 2. Navigation Menu
        self.nav_menu = NavMenu(current_page, self)
        self.nav_menu.page_changed.connect(self.page_changed.emit)
        main_layout.addWidget(self.nav_menu)

        main_layout.addStretch() # Pushes action items to the right

        # 3. Action Area (Contextual Button, Notifications, Settings, User Avatar)
        action_area_layout = QHBoxLayout()
        action_area_layout.setSpacing(Spacing.SM)
        action_area_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.contextual_button = ContextualActionButton(Text.BUTTON_CREATE, action_type=ActionEnum.CREATE_NEW, parent=self)
        self.contextual_button.clicked.connect(lambda: self.action_clicked.emit(self.contextual_button.action_type))
        action_area_layout.addWidget(self.contextual_button)

        # Placeholder icons
        self.notification_icon = IconButton(icon_path="images/icons/bell.png", size=QSize(20,20), parent=self)
        self.notification_icon.setToolTip("Notifications")
        self.notification_icon.clicked.connect(self.notifications_clicked.emit)
        action_area_layout.addWidget(self.notification_icon)

        self.settings_icon = IconButton(icon_path="images/icons/settings.png", size=QSize(20,20), parent=self)
        self.settings_icon.setToolTip("Settings")
        self.settings_icon.clicked.connect(self.settings_clicked.emit)
        action_area_layout.addWidget(self.settings_icon)

        self.user_avatar = IconButton(icon_path="images/icons/user.png", size=QSize(30,30), parent=self) # Bigger for avatar
        self.user_avatar.setToolTip("User Profile")
        self.user_avatar.clicked.connect(self.profile_clicked.emit)
        self.user_avatar.setObjectName("avatar") # Uses specific avatar style
        self.user_avatar.setFixedSize(QSize(40,40)) # Override fixed size for avatar
        self.user_avatar.setStyleSheet(f"""
            QPushButton#avatar {{
                border-radius: {Dimensions.BORDER_RADIUS_CIRCLE};
                border: 1px solid {Color.BORDER_MEDIUM};
                background-color: {Color.BORDER_MEDIUM};
            }}
            QPushButton#avatar:hover {{
                border: 1px solid {Color.PRIMARY_BLUE};
            }}
        """)
        action_area_layout.addWidget(self.user_avatar)

        main_layout.addLayout(action_area_layout)
        self.setLayout(main_layout)

    def update_navbar_for_page(self, new_page: PageEnum):
        self.nav_menu.update_active_item(new_page)
        # Logic to update contextual button based on page
        if new_page == PageEnum.QUESTION_BANK:
            self.contextual_button.setText(Text.BUTTON_CREATE)
            self.contextual_button.action_type = ActionEnum.CREATE_NEW
        elif new_page == PageEnum.LISTS:
            self.contextual_button.setText("Criar Nova Lista")
            self.contextual_button.action_type = ActionEnum.CREATE_NEW
        else:
            self.contextual_button.hide() # Hide for other pages by default
        self.contextual_button.setVisible(new_page in [PageEnum.QUESTION_BANK, PageEnum.LISTS])


if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    from src.views.design.theme import ThemeManager
    ThemeManager.apply_global_theme(app)

    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Navbar Test")
            self.setGeometry(100, 100, 1000, 100)

            self.navbar = Navbar(current_page=PageEnum.DASHBOARD, parent=self)
            self.setCentralWidget(self.navbar)

            self.navbar.page_changed.connect(self.on_page_changed)
            self.navbar.action_clicked.connect(self.on_action_clicked)
            self.navbar.notifications_clicked.connect(lambda: print("Notifications Clicked"))
            self.navbar.settings_clicked.connect(lambda: print("Settings Clicked"))
            self.navbar.profile_clicked.connect(lambda: print("Profile Clicked"))

        def on_page_changed(self, page_enum: PageEnum):
            print(f"Page Changed to: {page_enum.value}")
            self.navbar.update_navbar_for_page(page_enum)

        def on_action_clicked(self, action_enum: ActionEnum):
            print(f"Action Clicked: {action_enum.value}")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
