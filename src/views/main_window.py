"""
View: Main Window
DESCRIÇÃO: Janela principal da aplicação
RELACIONAMENTOS: PyQt6, todos os controllers
COMPONENTES:
    - Menu superior (Arquivo, Editar, Visualizar, Ajuda)
    - Barra de ferramentas (ações rápidas)
    - Painel lateral (navegação)
    - Área central (conteúdo dinâmico)
    - Barra de status (informações)
MENUS:
    Arquivo: Nova Questão, Nova Lista, Backup, Restaurar, Sair
    Editar: Gerenciar Tags, Configurações
    Visualizar: Questões, Listas, Estatísticas
    Ajuda: Sobre, Documentação
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMenuBar, QMenu, QToolBar, QStatusBar, QLabel,
    QPushButton, QStackedWidget, QListWidget, QMessageBox,
    QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QIcon, QKeySequence
import logging

from src.utils import ErrorHandler

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Janela principal da aplicação.
    Gerencia navegação entre diferentes telas e funcionalidades.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Banco de Questões Educacionais")
        self.setGeometry(100, 100, 1400, 800)
        self.setMinimumSize(1000, 600)

        # Inicializar componentes
        self.setup_ui()
        self.create_menu_bar()
        self.create_toolbar()
        self.create_status_bar()
        self.setup_connections()

        # Exibir tela inicial
        self.show_questoes_view()

        # Iniciar maximizada
        self.showMaximized()

        logger.info("MainWindow inicializada")

    def setup_ui(self):
        """Configura a interface principal"""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal (horizontal)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Splitter para dividir sidebar e conteúdo
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Painel lateral (Sidebar)
        self.sidebar = self.create_sidebar()
        splitter.addWidget(self.sidebar)

        # Área central com stack de telas
        self.stacked_widget = QStackedWidget()
        splitter.addWidget(self.stacked_widget)

        # Proporções do splitter (20% sidebar, 80% conteúdo)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 4)

        main_layout.addWidget(splitter)

    def create_sidebar(self):
        """Cria painel lateral de navegação"""
        sidebar = QWidget()
        sidebar.setMaximumWidth(250)
        sidebar.setMinimumWidth(200)
        sidebar.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
                color: white;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 15px;
                text-align: left;
                color: white;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
            QPushButton:pressed {
                background-color: #1abc9c;
            }
        """)

        layout = QVBoxLayout(sidebar)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 20, 0, 0)

        # Logo/Título
        title_label = QLabel("📚 Banco de Questões")
        title_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            padding: 20px;
            background-color: #1abc9c;
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Botões de navegação
        nav_buttons = [
            ("🔍 Buscar Questões", self.show_questoes_view),
            ("➕ Nova Questão", self.show_nova_questao),
            ("📋 Listas", self.show_listas_view),
            ("➕ Nova Lista", self.show_nova_lista),
            ("🏷️ Gerenciar Tags", self.show_tag_manager),
            ("📊 Estatísticas", self.show_estatisticas),
        ]

        self.nav_buttons = {}
        for text, callback in nav_buttons:
            btn = QPushButton(text)
            btn.clicked.connect(callback)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            layout.addWidget(btn)
            self.nav_buttons[text] = btn

        layout.addStretch()

        # Informações na parte inferior
        info_label = QLabel("Versão 1.0.1")
        info_label.setStyleSheet("padding: 10px; font-size: 10px; color: #95a5a6;")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)

        return sidebar

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

    def create_toolbar(self):
        """Cria barra de ferramentas"""
        toolbar = QToolBar("Barra de Ferramentas Principal")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Ações rápidas
        action_nova_questao = QAction("➕ Nova Questão", self)
        action_nova_questao.triggered.connect(self.show_nova_questao)
        toolbar.addAction(action_nova_questao)

        action_nova_lista = QAction("📋 Nova Lista", self)
        action_nova_lista.triggered.connect(self.show_nova_lista)
        toolbar.addAction(action_nova_lista)

        toolbar.addSeparator()

        action_buscar = QAction("🔍 Buscar", self)
        action_buscar.triggered.connect(self.show_questoes_view)
        toolbar.addAction(action_buscar)

        action_tags = QAction("🏷️ Tags", self)
        action_tags.triggered.connect(self.show_tag_manager)
        toolbar.addAction(action_tags)

        toolbar.addSeparator()

        action_backup = QAction("💾 Backup", self)
        action_backup.triggered.connect(self.fazer_backup)
        toolbar.addAction(action_backup)

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

    def setup_connections(self):
        """Configura conexões de sinais"""
        # TODO: Conectar sinais quando os widgets forem implementados
        pass

    # ========== Métodos de Navegação ==========

    def show_questoes_view(self):
        """Exibe tela de busca de questões"""
        logger.info("Navegando para: Buscar Questões")
        self.status_label.setText("Visualizando questões")

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

        # Cria o painel de listas na primeira vez que é acessado
        if not hasattr(self, 'lista_panel'):
            from src.views.lista_panel import ListaPanel
            self.lista_panel = ListaPanel(self)
            self.stacked_widget.addWidget(self.lista_panel)

        # Garante que a lista esteja sempre atualizada ao exibir a tela
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
        dialog.exec()

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

        title_label = QLabel("📚 Sistema de Banco de Questões Educacionais")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        info_text = """
        <div style='text-align: center; font-size: 14px; line-height: 1.8;'>
            <p><b>Versão:</b> 1.0.1</p>
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

        # Buscar listas disponiveis
        listas = controller.listar_todas()
        if not listas:
            QMessageBox.warning(self, 'Aviso', 'Nenhuma lista cadastrada. Crie uma lista primeiro.')
            return

        # Dialogo para selecionar lista
        from PyQt6.QtWidgets import QInputDialog
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
                # Extrair codigo da lista selecionada
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
        # TODO: Implementar lógica de backup
        self.show_placeholder("💾 Backup",
                             "Interface de backup do banco de dados será exibida aqui")

    def restaurar_backup(self):
        """Restaura backup do banco de dados"""
        logger.info("Navegando para: Restaurar Backup")
        self.status_label.setText("Restaurando backup")
        # TODO: Implementar lógica de restauração
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

        # Adicionar ao stack se ainda não existe
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
