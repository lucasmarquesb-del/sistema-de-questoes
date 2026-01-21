# src/views/pages/main_window.py
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QStatusBar, QLabel, QApplication
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from src.views.design.constants import Color, Spacing, Typography, Dimensions, Text
from src.views.design.enums import PageEnum, ActionEnum
from src.views.components.layout.navbar import Navbar
from src.views.components.layout.sidebar import Sidebar
from src.views.design.theme import ThemeManager
from src.views.components.common.feedback import Toast, LoadingSpinner # Added import

from src.views.pages.dashboard_page import DashboardPage
from src.views.pages.question_bank_page import QuestionBankPage
from src.views.pages.exam_list_page import ExamListPage
from src.views.pages.taxonomy_page import TaxonomyPage
from src.views.pages.question_editor_page import QuestionEditorPage


class MainWindow(QMainWindow):
    """
    The main application window (shell) managing navigation, sidebar, and page content.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(Text.APP_TITLE)
        self.setGeometry(100, 100, 1200, 800) # Initial window size

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_layout = QVBoxLayout(self.central_widget)
        self.central_layout.setContentsMargins(0, 0, 0, 0)
        self.central_layout.setSpacing(0)

        # 1. Navbar
        self.navbar = Navbar(current_page=PageEnum.DASHBOARD, parent=self)
        self.navbar.page_changed.connect(self._handle_page_change)
        self.navbar.action_clicked.connect(self._handle_action_clicked)
        self.central_layout.addWidget(self.navbar)

        # Content Area (Sidebar + Main Content)
        self.body_layout = QHBoxLayout()
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(0)

        # # 2. Sidebar
        # self.sidebar = Sidebar(self)
        # self.sidebar.tag_filter_changed.connect(self._handle_tag_filter_change)
        # self.body_layout.addWidget(self.sidebar)

        # 3. Content Area (QStackedWidget for pages)
        self.content_stacked_widget = QStackedWidget(self)
        self.content_stacked_widget.setObjectName("content_area")
        self.body_layout.addWidget(self.content_stacked_widget)

        self.central_layout.addLayout(self.body_layout)

        # 4. Status Bar
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(f"{Text.APP_TITLE} Initialized.")

        # Initialize Toast and LoadingSpinner (hidden by default)
        self.toast = Toast(parent=self) # Message will be set dynamically
        self.loading_spinner = LoadingSpinner(parent=self)
        self.loading_spinner.hide() # Initially hidden

        self._initialize_pages()
        self._set_current_page(PageEnum.DASHBOARD) # Set initial page

        # Apply global theme
        ThemeManager.apply_global_theme(QApplication.instance())


    def _initialize_pages(self):
        """Initializes and adds pages to the stacked widget (lazy loading can be implemented here)."""
        self.pages = {}
        # Pages that require sidebar: QuestionBank, Lists, Taxonomy
        # Pages that don't: Dashboard
        # Special pages: QuestionEditor (might be a dialog or full page)

        self.dashboard_page = DashboardPage(self)
        self.content_stacked_widget.addWidget(self.dashboard_page)
        self.pages[PageEnum.DASHBOARD] = self.dashboard_page

        self.question_bank_page = QuestionBankPage(self)
        self.content_stacked_widget.addWidget(self.question_bank_page)
        self.pages[PageEnum.QUESTION_BANK] = self.question_bank_page

        self.exam_list_page = ExamListPage(self)
        self.content_stacked_widget.addWidget(self.exam_list_page)
        self.pages[PageEnum.LISTS] = self.exam_list_page

        self.taxonomy_page = TaxonomyPage(self)
        self.content_stacked_widget.addWidget(self.taxonomy_page)
        self.pages[PageEnum.TAXONOMY] = self.taxonomy_page

        self.question_editor_page = QuestionEditorPage(self) # Can be shown via action
        self.content_stacked_widget.addWidget(self.question_editor_page)
        self.pages[PageEnum.QUESTION_EDITOR] = self.question_editor_page


    def _set_current_page(self, page_enum: PageEnum):
        """Switches the displayed page and updates UI components."""
        if page_enum in self.pages:
            self.content_stacked_widget.setCurrentWidget(self.pages[page_enum])
            self.navbar.update_navbar_for_page(page_enum)
            # self._update_sidebar_visibility(page_enum)
            self.toast.show_message(f"Showing page: {page_enum.value.replace('_', ' ').title()}", "info")
        else:
            self.toast.show_message(f"Error: Page '{page_enum.value}' not found.", "error")

    def _handle_page_change(self, page_enum: PageEnum):
        """Handler for page change requests from Navbar."""
        self._set_current_page(page_enum)

    def _handle_action_clicked(self, action_enum: ActionEnum):
        """Handler for actions from Navbar, e.g., 'Create New'."""
        self.loading_spinner.start_loading() # Show spinner for any action

        # Simulate a delay for the action
        QTimer.singleShot(1000, lambda: self._complete_action(action_enum))

    def _complete_action(self, action_enum: ActionEnum):
        self.loading_spinner.stop_loading() # Hide spinner after delay

        if action_enum == ActionEnum.CREATE_NEW:
            current_page_enum = self.navbar.nav_menu.current_page
            if current_page_enum == PageEnum.QUESTION_BANK:
                self._set_current_page(PageEnum.QUESTION_EDITOR)
                self.toast.show_message("Creating a new question...", "success")
            elif current_page_enum == PageEnum.LISTS:
                self.toast.show_message("Creating a new exam list...", "success")
                # self._set_current_page(PageEnum.EXAM_LIST_EDITOR) # Assuming a dedicated editor
            else:
                self.toast.show_message(f"Action '{action_enum.value}' not supported on this page.", "warning")
        else:
            self.toast.show_message(f"Action '{action_enum.value}' triggered.", "info")

    def _handle_tag_filter_change(self, tag_uuid: str, is_checked: bool):
        """Handler for tag filter changes from Sidebar."""
        self.toast.show_message(f"Tag '{tag_uuid}' filter changed: {'checked' if is_checked else 'unchecked'}", "info")
        # Here, actual filtering logic would be called for the current page


    # def _update_sidebar_visibility(self, page_enum: PageEnum):
    #     """Shows or hides the sidebar based on the current page."""
    #     pages_with_sidebar = [PageEnum.QUESTION_BANK, PageEnum.LISTS, PageEnum.TAXONOMY]
    #     if page_enum in pages_with_sidebar:
    #         self.sidebar.show()
    #     else:
    #         self.sidebar.hide()


if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())