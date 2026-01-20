"""
Page: Dashboard
Pagina inicial com estatisticas e acesso rapido as funcionalidades
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal
import logging

from src.controllers.adapters import criar_questao_controller, criar_lista_controller, criar_tag_controller
from src.utils import ErrorHandler

logger = logging.getLogger(__name__)


class StatCard(QFrame):
    """Card de estatistica individual."""
    clicked = pyqtSignal()

    def __init__(self, titulo: str, valor: str, descricao: str = "", cor: str = "#1abc9c", parent=None):
        super().__init__(parent)
        self.setObjectName("stat_card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QFrame#stat_card {{
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
                padding: 20px;
            }}
            QFrame#stat_card:hover {{
                border: 2px solid {cor};
                background-color: #fafafa;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Icone/indicador de cor
        indicador = QFrame()
        indicador.setFixedSize(8, 40)
        indicador.setStyleSheet(f"background-color: {cor}; border-radius: 4px;")

        header = QHBoxLayout()
        header.addWidget(indicador)

        # Valor grande
        valor_label = QLabel(valor)
        valor_label.setStyleSheet(f"font-size: 36px; font-weight: bold; color: {cor};")
        header.addWidget(valor_label)
        header.addStretch()

        layout.addLayout(header)

        # Titulo
        titulo_label = QLabel(titulo)
        titulo_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #2c3e50;")
        layout.addWidget(titulo_label)

        # Descricao
        if descricao:
            desc_label = QLabel(descricao)
            desc_label.setStyleSheet("font-size: 12px; color: #7f8c8d;")
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class QuickActionCard(QFrame):
    """Card de acao rapida."""
    clicked = pyqtSignal()

    def __init__(self, titulo: str, descricao: str, icone: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("action_card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QFrame#action_card {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
                padding: 16px;
            }
            QFrame#action_card:hover {
                border: 2px solid #1abc9c;
                background-color: #f8f9fa;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Icone
        if icone:
            icone_label = QLabel(icone)
            icone_label.setStyleSheet("font-size: 24px;")
            layout.addWidget(icone_label)

        # Titulo
        titulo_label = QLabel(titulo)
        titulo_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #2c3e50;")
        layout.addWidget(titulo_label)

        # Descricao
        desc_label = QLabel(descricao)
        desc_label.setStyleSheet("font-size: 12px; color: #7f8c8d;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class RecentActivityItem(QFrame):
    """Item de atividade recente."""

    def __init__(self, tipo: str, descricao: str, tempo: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 8px;
                padding: 12px;
                margin-bottom: 8px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # Icone do tipo
        icone_map = {
            'questao': 'Q',
            'lista': 'L',
            'tag': 'T',
            'export': 'E'
        }
        icone = icone_map.get(tipo, '?')

        icone_label = QLabel(icone)
        icone_label.setFixedSize(32, 32)
        icone_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icone_label.setStyleSheet("""
            background-color: #1abc9c;
            color: white;
            border-radius: 16px;
            font-weight: bold;
        """)
        layout.addWidget(icone_label)

        # Descricao
        desc_label = QLabel(descricao)
        desc_label.setStyleSheet("color: #2c3e50; font-size: 13px;")
        layout.addWidget(desc_label, 1)

        # Tempo
        tempo_label = QLabel(tempo)
        tempo_label.setStyleSheet("color: #95a5a6; font-size: 11px;")
        layout.addWidget(tempo_label)


class DashboardPage(QWidget):
    """Pagina de dashboard com estatisticas e acesso rapido."""

    # Sinais para navegacao
    novaQuestaoClicked = pyqtSignal()
    novaListaClicked = pyqtSignal()
    questoesClicked = pyqtSignal()
    listasClicked = pyqtSignal()
    tagsClicked = pyqtSignal()
    exportClicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.questao_controller = criar_questao_controller()
        self.lista_controller = criar_lista_controller()
        self.tag_controller = criar_tag_controller()

        self.init_ui()
        self.load_statistics()
        logger.info("DashboardPage inicializado")

    def init_ui(self):
        """Inicializa a interface do dashboard."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area para todo o conteudo
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #f5f6fa; }")

        content = QWidget()
        content.setStyleSheet("background-color: #f5f6fa;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)

        # Cabecalho
        header = self._create_header()
        layout.addLayout(header)

        # Cards de estatisticas
        stats_section = self._create_stats_section()
        layout.addWidget(stats_section)

        # Acoes rapidas
        actions_section = self._create_actions_section()
        layout.addWidget(actions_section)

        # Atividade recente (placeholder)
        activity_section = self._create_activity_section()
        layout.addWidget(activity_section)

        layout.addStretch()

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def _create_header(self) -> QHBoxLayout:
        """Cria o cabecalho do dashboard."""
        header = QHBoxLayout()

        # Titulo
        titulo = QLabel("Dashboard")
        titulo.setStyleSheet("font-size: 28px; font-weight: bold; color: #2c3e50;")
        header.addWidget(titulo)

        header.addStretch()

        # Botao de nova questao
        btn_nova = QPushButton("+ Nova Questao")
        btn_nova.setStyleSheet("""
            QPushButton {
                background-color: #1abc9c;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #16a085;
            }
        """)
        btn_nova.clicked.connect(self.novaQuestaoClicked.emit)
        header.addWidget(btn_nova)

        return header

    def _create_stats_section(self) -> QWidget:
        """Cria a secao de estatisticas."""
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)

        # Titulo da secao
        titulo = QLabel("Estatisticas")
        titulo.setStyleSheet("font-size: 18px; font-weight: 600; color: #2c3e50; margin-bottom: 8px;")
        layout.addWidget(titulo)

        # Grid de cards
        grid = QHBoxLayout()
        grid.setSpacing(16)

        # Card de questoes
        self.card_questoes = StatCard(
            "Total de Questoes",
            "0",
            "Questoes cadastradas no banco",
            "#3498db"
        )
        self.card_questoes.clicked.connect(self.questoesClicked.emit)
        grid.addWidget(self.card_questoes)

        # Card de listas
        self.card_listas = StatCard(
            "Listas Criadas",
            "0",
            "Listas de questoes",
            "#9b59b6"
        )
        self.card_listas.clicked.connect(self.listasClicked.emit)
        grid.addWidget(self.card_listas)

        # Card de tags
        self.card_tags = StatCard(
            "Tags de Conteudo",
            "0",
            "Categorias e assuntos",
            "#e67e22"
        )
        self.card_tags.clicked.connect(self.tagsClicked.emit)
        grid.addWidget(self.card_tags)

        # Card de objetivas vs discursivas
        self.card_tipos = StatCard(
            "Objetivas / Discursivas",
            "0 / 0",
            "Distribuicao por tipo",
            "#1abc9c"
        )
        grid.addWidget(self.card_tipos)

        layout.addLayout(grid)
        return section

    def _create_actions_section(self) -> QWidget:
        """Cria a secao de acoes rapidas."""
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)

        # Titulo da secao
        titulo = QLabel("Acoes Rapidas")
        titulo.setStyleSheet("font-size: 18px; font-weight: 600; color: #2c3e50; margin-bottom: 8px;")
        layout.addWidget(titulo)

        # Grid de acoes
        grid = QHBoxLayout()
        grid.setSpacing(16)

        # Nova questao
        action_questao = QuickActionCard(
            "Nova Questao",
            "Cadastrar uma nova questao objetiva ou discursiva",
            "+"
        )
        action_questao.clicked.connect(self.novaQuestaoClicked.emit)
        grid.addWidget(action_questao)

        # Nova lista
        action_lista = QuickActionCard(
            "Nova Lista",
            "Criar uma nova lista ou prova com questoes",
            "L"
        )
        action_lista.clicked.connect(self.novaListaClicked.emit)
        grid.addWidget(action_lista)

        # Buscar questoes
        action_buscar = QuickActionCard(
            "Buscar Questoes",
            "Encontrar questoes por filtros e tags",
            "?"
        )
        action_buscar.clicked.connect(self.questoesClicked.emit)
        grid.addWidget(action_buscar)

        # Exportar
        action_exportar = QuickActionCard(
            "Exportar Lista",
            "Gerar PDF ou LaTeX de uma lista",
            "E"
        )
        action_exportar.clicked.connect(self.exportClicked.emit)
        grid.addWidget(action_exportar)

        layout.addLayout(grid)
        return section

    def _create_activity_section(self) -> QWidget:
        """Cria a secao de atividade recente."""
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)

        # Titulo da secao
        titulo = QLabel("Atividade Recente")
        titulo.setStyleSheet("font-size: 18px; font-weight: 600; color: #2c3e50; margin-bottom: 8px;")
        layout.addWidget(titulo)

        # Container para itens
        self.activity_container = QWidget()
        self.activity_layout = QVBoxLayout(self.activity_container)
        self.activity_layout.setContentsMargins(0, 0, 0, 0)
        self.activity_layout.setSpacing(8)

        # Placeholder
        placeholder = QLabel("Nenhuma atividade recente registrada")
        placeholder.setStyleSheet("color: #95a5a6; font-style: italic; padding: 20px;")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.activity_layout.addWidget(placeholder)

        layout.addWidget(self.activity_container)
        return section

    def load_statistics(self):
        """Carrega as estatisticas do banco de dados."""
        try:
            # Total de questoes
            questoes = self.questao_controller.buscar_questoes({'ativa': True})
            total_questoes = len(questoes) if questoes else 0
            self.card_questoes.findChild(QLabel).setText(str(total_questoes))

            # Contar objetivas e discursivas
            objetivas = sum(1 for q in questoes if q.get('tipo') == 'OBJETIVA') if questoes else 0
            discursivas = total_questoes - objetivas

            # Total de listas
            listas = self.lista_controller.listar_todas_listas()
            total_listas = len(listas) if listas else 0

            # Total de tags
            tags = self.tag_controller.obter_arvore_tags_completa()
            total_tags = self._contar_tags(tags) if tags else 0

            # Atualizar cards
            self._update_card_value(self.card_questoes, str(total_questoes))
            self._update_card_value(self.card_listas, str(total_listas))
            self._update_card_value(self.card_tags, str(total_tags))
            self._update_card_value(self.card_tipos, f"{objetivas} / {discursivas}")

            logger.info(f"Estatisticas carregadas: {total_questoes} questoes, {total_listas} listas, {total_tags} tags")

        except Exception as e:
            logger.error(f"Erro ao carregar estatisticas: {e}")
            ErrorHandler.handle_exception(self, e, "Erro ao carregar estatisticas")

    def _contar_tags(self, tags_list) -> int:
        """Conta o total de tags recursivamente."""
        if not tags_list:
            return 0

        total = 0
        for tag in tags_list:
            total += 1
            filhos = tag.get('filhos', []) if isinstance(tag, dict) else getattr(tag, 'filhos', [])
            if filhos:
                total += self._contar_tags(filhos)
        return total

    def _update_card_value(self, card: StatCard, valor: str):
        """Atualiza o valor de um card de estatistica."""
        # Encontrar o QLabel com o valor (e maior fonte)
        for child in card.findChildren(QLabel):
            style = child.styleSheet()
            if 'font-size: 36px' in style:
                child.setText(valor)
                break

    def refresh(self):
        """Atualiza as estatisticas do dashboard."""
        self.load_statistics()


# Alias para compatibilidade
Dashboard = DashboardPage
