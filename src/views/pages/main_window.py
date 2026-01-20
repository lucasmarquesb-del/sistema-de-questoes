"""
Page: Main Window
Janela principal da aplicação com novo design MathBank

COMPONENTES:
    - Header: Logo, navegação e ações rápidas
    - Sidebar: Árvore de tags hierárquica
    - Área central: Conteúdo dinâmico (stacked widget)
    - StatusBar: Informações de status
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMenuBar, QMenu, QToolBar, QStatusBar, QLabel,
    QPushButton, QStackedWidget, QMessageBox, QSplitter,
    QInputDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence
import logging

from src.utils import ErrorHandler
from src.views.components.layout.header import Header
from src.views.components.layout.sidebar import Sidebar
from src.views.styles import load_stylesheet

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Janela principal da aplicação.
    Gerencia navegação entre diferentes telas e funcionalidades.
    Design baseado no MathBank.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MathBank - Sistema de Banco de Questões")
        self.setGeometry(100, 100, 1400, 800)
        self.setMinimumSize(1000, 600)

        # Aplicar estilos do MathBank
        self._apply_styles()

        # Inicializar componentes
        self.setup_ui()
        self.create_menu_bar()
        self.create_status_bar()
        self.setup_connections()

        # Carregar tags na sidebar
        self._load_sidebar_tags()

        # Exibir tela inicial
        self.show_questoes_view()

        # Iniciar maximizada
        self.showMaximized()

        logger.info("MainWindow inicializada com novo design")

    def _apply_styles(self):
        """Aplica stylesheet do MathBank"""
        stylesheet = load_stylesheet("mathbank")
        if stylesheet:
            self.setStyleSheet(stylesheet)

    def setup_ui(self):
        """Configura a interface principal"""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal (vertical: header + conteúdo)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        self.header = Header()
        main_layout.addWidget(self.header)

        # Área de conteúdo (horizontal: sidebar + área principal)
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Sidebar
        self.sidebar = Sidebar()
        content_layout.addWidget(self.sidebar)

        # Área central com stack de telas
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setObjectName("main_content")
        content_layout.addWidget(self.stacked_widget)

        main_layout.addLayout(content_layout)

    def setup_connections(self):
        """Configura conexões de sinais"""
        # Conexões do Header
        self.header.dashboardClicked.connect(self.show_dashboard)
        self.header.questoesClicked.connect(self.show_questoes_view)
        self.header.listasClicked.connect(self.show_listas_view)
        self.header.novaQuestaoClicked.connect(self.show_nova_questao)

        # Conexões da Sidebar
        self.sidebar.tagSelected.connect(self._on_tag_selected)
        self.sidebar.exportClicked.connect(self._on_export_clicked)

    def _load_sidebar_tags(self):
        """Carrega tags na sidebar"""
        try:
            from src.controllers.adapters import criar_tag_controller
            controller = criar_tag_controller()
            tags_arvore = controller.obter_arvore_tags_completa()
            if tags_arvore:
                self.sidebar.load_tags(tags_arvore)
        except Exception as e:
            logger.warning(f"Erro ao carregar tags na sidebar: {e}")

    def create_menu_bar(self):
        """Cria barra de menus"""
        menubar = self.menuBar()

        # Menu Arquivo
        menu_arquivo = menubar.addMenu("&Arquivo")

        action_nova_questao = QAction("&Nova Questão", self)
        action_nova_questao.setShortcut(QKeySequence("Ctrl+N"))
        action_nova_questao.triggered.connect(self.show_nova_questao)
        menu_arquivo.addAction(action_nova_questao)

        action_nova_lista = QAction("Nova &Lista", self)
        action_nova_lista.setShortcut(QKeySequence("Ctrl+L"))
        action_nova_lista.triggered.connect(self.show_nova_lista)
        menu_arquivo.addAction(action_nova_lista)

        menu_arquivo.addSeparator()

        action_backup = QAction("&Backup", self)
        action_backup.setShortcut(QKeySequence("Ctrl+B"))
        action_backup.triggered.connect(self.fazer_backup)
        menu_arquivo.addAction(action_backup)

        action_restaurar = QAction("&Restaurar", self)
        action_restaurar.triggered.connect(self.restaurar_backup)
        menu_arquivo.addAction(action_restaurar)

        menu_arquivo.addSeparator()

        action_sair = QAction("&Sair", self)
        action_sair.setShortcut(QKeySequence("Ctrl+Q"))
        action_sair.triggered.connect(self.close)
        menu_arquivo.addAction(action_sair)

        # Menu Editar
        menu_editar = menubar.addMenu("&Editar")

        action_tags = QAction("Gerenciar &Tags", self)
        action_tags.setShortcut(QKeySequence("Ctrl+T"))
        action_tags.triggered.connect(self.show_tag_manager)
        menu_editar.addAction(action_tags)

        menu_editar.addSeparator()

        action_config = QAction("&Configurações", self)
        action_config.setShortcut(QKeySequence("Ctrl+,"))
        action_config.triggered.connect(self.show_configuracoes)
        menu_editar.addAction(action_config)

        # Menu Visualizar
        menu_visualizar = menubar.addMenu("&Visualizar")

        action_dashboard = QAction("&Dashboard", self)
        action_dashboard.setShortcut(QKeySequence("Ctrl+D"))
        action_dashboard.triggered.connect(self.show_dashboard)
        menu_visualizar.addAction(action_dashboard)

        action_questoes = QAction("&Questões", self)
        action_questoes.setShortcut(QKeySequence("Ctrl+1"))
        action_questoes.triggered.connect(self.show_questoes_view)
        menu_visualizar.addAction(action_questoes)

        action_listas = QAction("&Listas", self)
        action_listas.setShortcut(QKeySequence("Ctrl+2"))
        action_listas.triggered.connect(self.show_listas_view)
        menu_visualizar.addAction(action_listas)

        action_estatisticas = QAction("&Estatísticas", self)
        action_estatisticas.setShortcut(QKeySequence("Ctrl+3"))
        action_estatisticas.triggered.connect(self.show_estatisticas)
        menu_visualizar.addAction(action_estatisticas)

        # Menu Ajuda
        menu_ajuda = menubar.addMenu("A&juda")

        action_sobre = QAction("&Sobre", self)
        action_sobre.triggered.connect(self.show_sobre)
        menu_ajuda.addAction(action_sobre)

        action_doc = QAction("&Documentação", self)
        action_doc.setShortcut(QKeySequence("F1"))
        action_doc.triggered.connect(self.show_documentacao)
        menu_ajuda.addAction(action_doc)

    def create_status_bar(self):
        """Cria barra de status"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Label de status
        self.status_label = QLabel("Pronto")
        self.status_bar.addPermanentWidget(self.status_label)

        # Contador de questões
        self.questoes_count_label = QLabel("Questões: 0")
        self.status_bar.addPermanentWidget(self.questoes_count_label)

    # ========== Métodos de Navegação ==========

    def show_dashboard(self):
        """Exibe tela de dashboard"""
        logger.info("Navegando para: Dashboard")
        self.status_label.setText("Dashboard")
        self.header.set_active_nav("dashboard")

        if not hasattr(self, 'dashboard_page'):
            from src.views.pages.dashboard_page import DashboardPage
            self.dashboard_page = DashboardPage()
            self.stacked_widget.addWidget(self.dashboard_page)

            # Conectar sinais do Dashboard
            self.dashboard_page.novaQuestaoClicked.connect(self.show_nova_questao)
            self.dashboard_page.novaListaClicked.connect(self.show_nova_lista)
            self.dashboard_page.questoesClicked.connect(self.show_questoes_view)
            self.dashboard_page.listasClicked.connect(self.show_listas_view)
            self.dashboard_page.tagsClicked.connect(self.show_tag_manager)
            self.dashboard_page.exportClicked.connect(self._on_export_clicked)

        # Atualizar estatisticas
        self.dashboard_page.refresh()
        self.stacked_widget.setCurrentWidget(self.dashboard_page)

    def show_questoes_view(self):
        """Exibe tela de busca de questões"""
        logger.info("Navegando para: Buscar Questões")
        self.status_label.setText("Visualizando questões")
        self.header.set_active_nav("questoes")

        if not hasattr(self, 'search_panel'):
            from src.views.search_panel import SearchPanel
            self.search_panel = SearchPanel()
            self.stacked_widget.addWidget(self.search_panel)

            # Conectar sinais do SearchPanel
            self.search_panel.questaoSelected.connect(self._on_questao_visualizar)
            self.search_panel.editQuestao.connect(self._on_questao_editar)
            self.search_panel.inactivateQuestao.connect(self._on_questao_inativar)
            self.search_panel.reactivateQuestao.connect(self._on_questao_reativar)
            self.search_panel.addToListQuestao.connect(self._on_questao_adicionar_lista)

        self.stacked_widget.setCurrentWidget(self.search_panel)

    def show_nova_questao(self):
        """Abre formulário de nova questão"""
        logger.info("Abrindo diálogo: Nova Questão")
        self.status_label.setText("Criando nova questão")

        from src.views.questao_form import QuestaoForm
        dialog = QuestaoForm(parent=self)
        dialog.exec()

    def show_listas_view(self):
        """Exibe a tela de gerenciamento de listas."""
        logger.info("Navegando para: Listas")
        self.status_label.setText("Visualizando listas")
        self.header.set_active_nav("listas")

        if not hasattr(self, 'lista_panel'):
            from src.views.lista_panel import ListaPanel
            self.lista_panel = ListaPanel(self)
            self.stacked_widget.addWidget(self.lista_panel)

        self.lista_panel.load_listas()
        self.stacked_widget.setCurrentWidget(self.lista_panel)

    def show_nova_lista(self):
        """Abre formulário de nova lista"""
        logger.info("Abrindo diálogo: Nova Lista")
        self.status_label.setText("Criando nova lista")

        from src.views.lista_form import ListaForm
        dialog = ListaForm(parent=self)
        dialog.exec()

    def show_tag_manager(self):
        """Abre gerenciador de tags"""
        logger.info("Abrindo diálogo: Gerenciador de Tags")
        self.status_label.setText("Gerenciando tags")

        from src.views.tag_manager import TagManager
        dialog = TagManager(parent=self)
        result = dialog.exec()

        # Recarregar tags na sidebar após fechar
        if result:
            self._load_sidebar_tags()

    def show_estatisticas(self):
        """Exibe tela de estatísticas"""
        logger.info("Navegando para: Estatísticas")
        self.status_label.setText("Visualizando estatísticas")
        self.show_placeholder("📊 Tela de Estatísticas",
                             "Aqui você verá estatísticas do banco de questões")

    def show_configuracoes(self):
        """Abre tela de configurações"""
        logger.info("Navegando para: Configurações")
        self.status_label.setText("Configurações do sistema")
        self.show_placeholder("⚙️ Configurações",
                             "Painel de configurações do sistema será exibido aqui")

    def show_sobre(self):
        """Exibe tela sobre"""
        logger.info("Navegando para: Sobre")
        self.status_label.setText("Sobre o sistema")

        sobre_widget = QWidget()
        layout = QVBoxLayout(sobre_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel("📚 MathBank - Sistema de Banco de Questões")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        info_text = """
        <div style='text-align: center; font-size: 14px; line-height: 1.8;'>
            <p><b>Versão:</b> 2.0.0</p>
            <p><b>Data:</b> Janeiro 2026</p>
            <p style='margin-top: 20px;'>
                Sistema desenvolvido para gerenciar questões educacionais<br>
                com suporte a LaTeX, tags hierárquicas e exportação de listas.
            </p>
            <p style='margin-top: 30px; color: #666;'>
                <b>Recursos principais:</b><br>
                • Cadastro de questões objetivas e discursivas<br>
                • Sistema de tags hierárquicas<br>
                • Criação e exportação de listas em LaTeX<br>
                • Busca avançada com múltiplos filtros<br>
                • Backup automático do banco de dados
            </p>
        </div>
        """

        info_label = QLabel(info_text)
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #333; max-width: 600px;")
        layout.addWidget(info_label)

        if not hasattr(self, 'sobre_widget'):
            self.sobre_widget = sobre_widget
            self.stacked_widget.addWidget(sobre_widget)

        self.stacked_widget.setCurrentWidget(sobre_widget)

    def show_documentacao(self):
        """Abre tela de documentação"""
        logger.info("Navegando para: Documentação")
        self.status_label.setText("Documentação")
        self.show_placeholder("📖 Documentação",
                             "Documentação completa do sistema estará disponível em breve")

    # ========== Handlers de Sidebar ==========

    def _on_tag_selected(self, tag_uuid: str, tag_nome: str):
        """Filtra questões pela tag selecionada na sidebar"""
        logger.info(f"Tag selecionada na sidebar: {tag_nome} ({tag_uuid})")
        self.status_label.setText(f"Filtrando por: {tag_nome}")

        # Navegar para questões e aplicar filtro
        self.show_questoes_view()

        # Aplicar filtro de tag no search panel
        if hasattr(self, 'search_panel'):
            self.search_panel.filter_by_tag(tag_uuid)

    def _on_export_clicked(self):
        """Abre diálogo de exportação"""
        logger.info("Botão exportar clicado na sidebar")

        # Verificar se há uma lista selecionada ou abrir seleção
        from src.controllers.adapters import criar_lista_controller
        controller = criar_lista_controller()

        listas = controller.listar_todas()
        if not listas:
            QMessageBox.warning(self, 'Aviso', 'Nenhuma lista cadastrada. Crie uma lista primeiro.')
            return

        # Diálogo para selecionar lista
        lista_nomes = [f"{l.get('codigo', '')} - {l.get('titulo', 'Sem titulo')}" for l in listas]
        escolha, ok = QInputDialog.getItem(
            self,
            'Exportar Lista',
            'Selecione a lista para exportar:',
            lista_nomes,
            0,
            False
        )

        if ok and escolha:
            codigo_lista = escolha.split(' - ')[0]
            from src.views.export_dialog import ExportDialog
            dialog = ExportDialog(codigo_lista, parent=self)
            dialog.exec()

    # ========== Handlers de Questao ==========

    def _on_questao_visualizar(self, codigo_questao: str):
        """Abre preview da questao"""
        logger.info(f"Visualizando questao: {codigo_questao}")
        try:
            from src.controllers.adapters import criar_questao_controller
            controller = criar_questao_controller()
            questao_data = controller.buscar_por_id(codigo_questao)
            if not questao_data:
                QMessageBox.warning(self, 'Aviso', f'Questao {codigo_questao} nao encontrada.')
                return

            from src.views.questao_preview import QuestaoPreview
            dialog = QuestaoPreview(questao_data, parent=self)
            dialog.exec()
        except Exception as e:
            ErrorHandler.handle_exception(self, e, 'Erro ao visualizar questao')

    def _on_questao_editar(self, codigo_questao: str):
        """Abre formulario de edicao da questao"""
        logger.info(f"Editando questao: {codigo_questao}")
        from src.views.questao_form import QuestaoForm
        dialog = QuestaoForm(questao_id=codigo_questao, parent=self)
        dialog.questaoSaved.connect(self._refresh_search)
        dialog.exec()

    def _on_questao_inativar(self, codigo_questao: str):
        """Inativa uma questao (soft delete)"""
        logger.info(f"Inativando questao: {codigo_questao}")
        reply = QMessageBox.question(
            self,
            'Confirmar Inativacao',
            f'Tem certeza que deseja inativar a questao {codigo_questao}?\n\nA questao nao sera excluida, apenas ficara inativa.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                from src.controllers.adapters import criar_questao_controller
                controller = criar_questao_controller()
                controller.deletar_questao(codigo_questao)
                QMessageBox.information(self, 'Sucesso', 'Questao inativada com sucesso!')
                self._refresh_search()
            except Exception as e:
                ErrorHandler.handle_exception(self, e, 'Erro ao inativar questao')

    def _on_questao_reativar(self, codigo_questao: str):
        """Reativa uma questao inativa"""
        logger.info(f"Reativando questao: {codigo_questao}")
        reply = QMessageBox.question(
            self,
            'Confirmar Reativacao',
            f'Tem certeza que deseja reativar a questao {codigo_questao}?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                from src.controllers.adapters import criar_questao_controller
                controller = criar_questao_controller()
                controller.reativar_questao(codigo_questao)
                QMessageBox.information(self, 'Sucesso', 'Questao reativada com sucesso!')
                self._refresh_search()
            except Exception as e:
                ErrorHandler.handle_exception(self, e, 'Erro ao reativar questao')

    def _on_questao_adicionar_lista(self, codigo_questao: str):
        """Adiciona questao a uma lista existente"""
        logger.info(f"Adicionando questao {codigo_questao} a uma lista")
        from src.controllers.adapters import criar_lista_controller
        controller = criar_lista_controller()

        listas = controller.listar_todas()
        if not listas:
            QMessageBox.warning(self, 'Aviso', 'Nenhuma lista cadastrada. Crie uma lista primeiro.')
            return

        lista_nomes = [f"{l.get('codigo', '')} - {l.get('titulo', 'Sem titulo')}" for l in listas]
        escolha, ok = QInputDialog.getItem(
            self,
            'Adicionar a Lista',
            'Selecione a lista:',
            lista_nomes,
            0,
            False
        )

        if ok and escolha:
            try:
                codigo_lista = escolha.split(' - ')[0]
                controller.adicionar_questao(codigo_lista, codigo_questao)
                QMessageBox.information(self, 'Sucesso', f'Questao adicionada a lista {codigo_lista}!')
            except Exception as e:
                ErrorHandler.handle_exception(self, e, 'Erro ao adicionar questao a lista')

    def _refresh_search(self):
        """Atualiza resultados da busca"""
        if hasattr(self, 'search_panel'):
            self.search_panel.perform_search()

    # ========== Métodos de Funcionalidade ==========

    def fazer_backup(self):
        """Cria backup do banco de dados"""
        logger.info("Navegando para: Backup")
        self.status_label.setText("Gerenciando backups")
        self.show_placeholder("💾 Backup",
                             "Interface de backup do banco de dados será exibida aqui")

    def restaurar_backup(self):
        """Restaura backup do banco de dados"""
        logger.info("Navegando para: Restaurar Backup")
        self.status_label.setText("Restaurando backup")
        self.show_placeholder("♻️ Restaurar Backup",
                             "Interface de restauração de backup será exibida aqui")

    def update_status_counts(self, questoes_count=0, listas_count=0):
        """Atualiza contadores na barra de status"""
        self.questoes_count_label.setText(f"Questões: {questoes_count}")

    # ========== Método Auxiliar ==========

    def show_placeholder(self, title, description):
        """Exibe placeholder para tela não implementada"""
        placeholder = QWidget()
        layout = QVBoxLayout(placeholder)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        desc_label = QLabel(description)
        desc_label.setStyleSheet("font-size: 14px; color: #666; margin-top: 10px;")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_label)

        placeholder_name = f"placeholder_{title}"
        if not hasattr(self, placeholder_name):
            setattr(self, placeholder_name, placeholder)
            self.stacked_widget.addWidget(placeholder)

        self.stacked_widget.setCurrentWidget(placeholder)

    def closeEvent(self, event):
        """Evento de fechamento da janela"""
        reply = QMessageBox.question(
            self,
            'Sair',
            'Tem certeza que deseja sair?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            logger.info("Aplicação fechada pelo usuário")
            event.accept()
        else:
            event.ignore()


logger.info("MainWindow carregado")
