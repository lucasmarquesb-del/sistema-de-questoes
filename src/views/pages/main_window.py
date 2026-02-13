# src/views/pages/main_window.py
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QStatusBar, QLabel, QApplication
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from src.views.design.constants import Color, Spacing, Typography, Dimensions, Text
from src.views.design.enums import PageEnum, ActionEnum
from src.views.components.layout.navbar import Navbar
from src.views.components.layout.sidebar import Sidebar
from src.views.design.theme import ThemeManager
from src.views.components.common.feedback import Toast, LoadingSpinner

from src.views.pages.dashboard_page import DashboardPage
from src.views.pages.question_bank_page import QuestionBankPage
from src.views.pages.exam_list_page import ExamListPage
from src.views.pages.taxonomy_page import TaxonomyPage
from src.views.pages.question_editor_page import QuestionEditorPage
from src.controllers.adapters import criar_questao_controller
from src.application.dtos import QuestaoCreateDTO, AlternativaDTO


class MainWindow(QMainWindow):
    """
    The main application window (shell) managing navigation, sidebar, and page content.
    """
    logout_requested = pyqtSignal()

    def __init__(self, user_data: dict = None, auth_service=None, parent=None):
        super().__init__(parent)
        self._user_data = user_data or {}
        self._auth_service = auth_service
        self._is_admin = self._user_data.get("role") == "admin"

        self.setWindowTitle(Text.APP_TITLE)
        self.setGeometry(100, 100, 1200, 800)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_layout = QVBoxLayout(self.central_widget)
        self.central_layout.setContentsMargins(0, 0, 0, 0)
        self.central_layout.setSpacing(0)

        # 1. Navbar (passa user_data para exibir nome e menu admin)
        self.navbar = Navbar(current_page=PageEnum.QUESTION_BANK, user_data=self._user_data, parent=self)
        self.navbar.page_changed.connect(self._handle_page_change)
        self.navbar.action_clicked.connect(self._handle_action_clicked)
        self.navbar.logout_clicked.connect(self._handle_logout)
        self.central_layout.addWidget(self.navbar)

        # Content Area (Sidebar + Main Content)
        self.body_layout = QHBoxLayout()
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(0)

        # 3. Content Area (QStackedWidget for pages)
        self.content_stacked_widget = QStackedWidget(self)
        self.content_stacked_widget.setObjectName("content_area")
        self.body_layout.addWidget(self.content_stacked_widget)

        self.central_layout.addLayout(self.body_layout)

        # 4. Status Bar
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        user_email = self._user_data.get("email", "")
        self.status_bar.showMessage(f"{Text.APP_TITLE} - {user_email}" if user_email else f"{Text.APP_TITLE}")

        # Initialize Toast and LoadingSpinner (hidden by default)
        self.toast = Toast(parent=self)
        self.loading_spinner = LoadingSpinner(parent=self)
        self.loading_spinner.hide()

        self._initialize_pages()
        self._set_current_page(PageEnum.QUESTION_BANK)

        # Apply global theme
        ThemeManager.apply_global_theme(QApplication.instance())


    def _initialize_pages(self):
        """Initializes and adds pages to the stacked widget."""
        self.pages = {}

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

        self.question_editor_page = QuestionEditorPage(self)
        self.content_stacked_widget.addWidget(self.question_editor_page)
        self.pages[PageEnum.QUESTION_EDITOR] = self.question_editor_page

        # Página de gerenciamento de usuários (somente admin)
        if self._is_admin and self._auth_service:
            from src.views.pages.user_management_page import UserManagementPage
            self.user_management_page = UserManagementPage(
                api_client=self._auth_service.api_client, parent=self
            )
            self.content_stacked_widget.addWidget(self.user_management_page)
            self.pages[PageEnum.USER_MANAGEMENT] = self.user_management_page

        # Conectar sinais do editor de questões
        self.question_editor_page.cancel_requested.connect(self._on_question_editor_cancel)
        self.question_editor_page.back_to_questions_requested.connect(self._on_question_editor_cancel)
        self.question_editor_page.save_requested.connect(self._on_question_save_requested)

        # Conectar sinal de edição do banco de questões
        self.question_bank_page.edit_question_requested.connect(self._on_edit_question_requested)

        # Conectar sinal de criar variante do banco de questões
        self.question_bank_page.create_variant_requested.connect(self._on_create_variant_requested)

        # Inicializar controller de questões
        self.questao_controller = criar_questao_controller()


    def _set_current_page(self, page_enum: PageEnum):
        """Switches the displayed page and updates UI components."""
        if page_enum in self.pages:
            self.content_stacked_widget.setCurrentWidget(self.pages[page_enum])
            self.navbar.update_navbar_for_page(page_enum)
            self.toast.show_message(f"Showing page: {page_enum.value.replace('_', ' ').title()}", "info")
        else:
            self.toast.show_message(f"Error: Page '{page_enum.value}' not found.", "error")

    def _handle_page_change(self, page_enum: PageEnum):
        """Handler for page change requests from Navbar."""
        self._set_current_page(page_enum)

    def _handle_action_clicked(self, action_enum: ActionEnum):
        """Handler for actions from Navbar, e.g., 'Create New'."""
        self.loading_spinner.start_loading()
        QTimer.singleShot(1000, lambda: self._complete_action(action_enum))

    def _complete_action(self, action_enum: ActionEnum):
        self.loading_spinner.stop_loading()

        if action_enum == ActionEnum.CREATE_NEW:
            current_page_enum = self.navbar.nav_menu.current_page
            if current_page_enum == PageEnum.QUESTION_BANK:
                self.question_editor_page.clear_form()
                self._set_current_page(PageEnum.QUESTION_EDITOR)
                self.toast.show_message("Criando nova questão...", "success")
            elif current_page_enum == PageEnum.LISTS:
                self.toast.show_message("Creating a new exam list...", "success")
            else:
                self.toast.show_message(f"Action '{action_enum.value}' not supported on this page.", "warning")
        else:
            self.toast.show_message(f"Action '{action_enum.value}' triggered.", "info")

    def _handle_logout(self):
        """Handler para logout — emite signal para main.py."""
        self.logout_requested.emit()

    def _handle_tag_filter_change(self, tag_uuid: str, is_checked: bool):
        """Handler for tag filter changes from Sidebar."""
        self.toast.show_message(f"Tag '{tag_uuid}' filter changed: {'checked' if is_checked else 'unchecked'}", "info")

    def _on_question_editor_cancel(self):
        """Handler para cancelar/voltar do editor de questões."""
        self.question_editor_page.clear_form()
        self._set_current_page(PageEnum.QUESTION_BANK)

    def _on_question_save_requested(self, question_data: dict):
        """Handler para salvar questão do editor (criação, edição ou variante)."""
        try:
            # Se é variante, o salvamento já foi feito no editor
            if question_data.get('is_variant'):
                codigo_variante = question_data.get('codigo_variante', 'N/A')
                if question_data.get('is_editing'):
                    self.toast.show_message(f"Variante {codigo_variante} atualizada com sucesso!", "success")
                else:
                    self.toast.show_message(f"Variante {codigo_variante} criada com sucesso!", "success")
                self.question_editor_page.clear_form()
                if hasattr(self.question_bank_page, 'refresh_data'):
                    self.question_bank_page.refresh_data()
                self._set_current_page(PageEnum.QUESTION_BANK)
                return

            # Verificar se é edição ou criação
            is_editing = self.question_editor_page.is_editing
            editing_id = self.question_editor_page.editing_question_id

            # Converter dados do editor para o formato do DTO
            tipo = 'OBJETIVA' if question_data.get('question_type') == 'objective' else 'DISCURSIVA'

            alternativas_dto = []
            if tipo == 'OBJETIVA':
                for i, alt in enumerate(question_data.get('alternatives', [])):
                    letra = chr(ord('A') + i)
                    alternativas_dto.append(AlternativaDTO(
                        letra=letra,
                        texto=alt.get('text', ''),
                        correta=alt.get('is_correct', False)
                    ))

            # Converter fonte para maiuscula
            fonte_raw = question_data.get('origin', '').strip()
            fonte = fonte_raw.upper() if fonte_raw else None

            # Converter dificuldade (1=FACIL, 2=MEDIO, 3=DIFICIL)
            id_dificuldade = question_data.get('difficulty')
            if id_dificuldade and id_dificuldade < 1:
                id_dificuldade = None

            # Montar lista de niveis escolares
            school_level_uuid = question_data.get('school_level_uuid')
            niveis_escolares = [school_level_uuid] if school_level_uuid else []

            if is_editing and editing_id:
                # Modo edição - usar QuestaoUpdateDTO
                from src.application.dtos import QuestaoUpdateDTO
                dto = QuestaoUpdateDTO(
                    id_questao=editing_id,
                    enunciado=question_data.get('statement', ''),
                    tipo=tipo,
                    titulo=question_data.get('titulo'),
                    ano=int(question_data.get('academic_year', 2026)) if question_data.get('academic_year') else 2026,
                    id_dificuldade=id_dificuldade,
                    alternativas=alternativas_dto,
                    tags=question_data.get('tags', []),
                    niveis_escolares=niveis_escolares,
                    observacoes=None
                )
                sucesso = self.questao_controller.atualizar_questao_completa(dto)
                if sucesso:
                    self.toast.show_message(f"Questão {editing_id} atualizada com sucesso!", "success")
                    self.question_editor_page.clear_form()
                    if hasattr(self.question_bank_page, 'refresh_data'):
                        self.question_bank_page.refresh_data()
                    self._set_current_page(PageEnum.QUESTION_BANK)
                else:
                    self.toast.show_message("Erro ao atualizar a questão.", "error")
            else:
                # Modo criação - usar QuestaoCreateDTO
                dto = QuestaoCreateDTO(
                    enunciado=question_data.get('statement', ''),
                    tipo=tipo,
                    titulo=question_data.get('titulo'),
                    ano=int(question_data.get('academic_year', 2026)) if question_data.get('academic_year') else 2026,
                    fonte=fonte,
                    id_dificuldade=id_dificuldade,
                    alternativas=alternativas_dto,
                    tags=question_data.get('tags', []),
                    niveis_escolares=niveis_escolares,
                    observacoes=None
                )

                resultado = self.questao_controller.criar_questao_completa(dto)

                if resultado:
                    codigo = resultado.get('codigo') if isinstance(resultado, dict) else resultado
                    self.toast.show_message(f"Questão criada com sucesso! Código: {codigo}", "success")
                    self.question_editor_page.clear_form()
                    if hasattr(self.question_bank_page, 'refresh_data'):
                        self.question_bank_page.refresh_data()
                    self._set_current_page(PageEnum.QUESTION_BANK)
                else:
                    self.toast.show_message("Erro ao salvar a questão.", "error")

        except Exception as e:
            self.toast.show_message(f"Erro ao salvar: {str(e)}", "error")

    def _on_edit_question_requested(self, questao_data: dict):
        """Handler para abrir formulário de edição de questão."""
        try:
            self.question_editor_page.load_question_for_editing(questao_data)
            self._set_current_page(PageEnum.QUESTION_EDITOR)
        except Exception as e:
            self.toast.show_message(f"Erro ao abrir editor: {str(e)}", "error")

    def _on_create_variant_requested(self, questao_data: dict):
        """Handler para abrir editor para criação de variante."""
        try:
            self.question_editor_page.load_question_for_variant(questao_data)
            self._set_current_page(PageEnum.QUESTION_EDITOR)
        except Exception as e:
            self.toast.show_message(f"Erro ao abrir editor de variante: {str(e)}", "error")
