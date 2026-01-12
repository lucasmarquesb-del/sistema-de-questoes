"""
View: Search Panel
DESCRIÇÃO: Painel de busca e filtros de questões
RELACIONAMENTOS: QuestaoController, TagModel
COMPONENTES:
    - Campo de busca por título
    - Árvore de tags (checkboxes)
    - Filtros: Ano, Fonte, Dificuldade, Tipo
    - Contadores por tag
    - Lista de resultados (cards)
    - Botão: Limpar Filtros
RESULTADO:
    - Cards com preview da questão
    - Ações: Visualizar, Editar, Adicionar à Lista, Inativar
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QScrollArea, QFrame, QSpinBox,
    QGroupBox, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal
import logging

from src.controllers.questao_controller_refactored import criar_questao_controller
from src.application.dtos import FiltroQuestaoDTO

logger = logging.getLogger(__name__)


class SearchPanel(QWidget):
    """
    Painel de busca e filtros de questões.
    Permite buscar questões por diversos critérios.
    """

    questaoSelected = pyqtSignal(int)  # Emite ID da questão selecionada
    editQuestao = pyqtSignal(int)
    deleteQuestao = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Inicializar controller
        self.controller = criar_questao_controller()

        self.init_ui()
        logger.info("SearchPanel inicializado")

    def init_ui(self):
        """Configura a interface do painel de busca"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Splitter para dividir filtros e resultados
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Painel de filtros (esquerda)
        filters_panel = self.create_filters_panel()
        splitter.addWidget(filters_panel)

        # Painel de resultados (direita)
        results_panel = self.create_results_panel()
        splitter.addWidget(results_panel)

        # Proporções (30% filtros, 70% resultados)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 7)

        layout.addWidget(splitter)

    def create_filters_panel(self):
        """Cria painel de filtros"""
        panel = QWidget()
        panel.setMaximumWidth(400)
        panel.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

        layout = QVBoxLayout(panel)

        # Título
        title_label = QLabel("🔍 Filtros de Busca")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)

        # Campo de busca por título/enunciado
        search_group = QGroupBox("Busca por Texto")
        search_layout = QVBoxLayout(search_group)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Digite título ou parte do enunciado...")
        self.search_input.textChanged.connect(self.on_search_changed)
        search_layout.addWidget(self.search_input)

        layout.addWidget(search_group)

        # Filtro por Tipo
        tipo_group = QGroupBox("Tipo de Questão")
        tipo_layout = QVBoxLayout(tipo_group)

        self.tipo_combo = QComboBox()
        self.tipo_combo.addItems(["Todas", "Objetiva", "Discursiva"])
        self.tipo_combo.currentTextChanged.connect(self.on_filters_changed)
        tipo_layout.addWidget(self.tipo_combo)

        layout.addWidget(tipo_group)

        # Filtro por Dificuldade
        dif_group = QGroupBox("Dificuldade")
        dif_layout = QVBoxLayout(dif_group)

        self.dificuldade_combo = QComboBox()
        self.dificuldade_combo.addItems(["Todas", "FÁCIL", "MÉDIO", "DIFÍCIL"])
        self.dificuldade_combo.currentTextChanged.connect(self.on_filters_changed)
        dif_layout.addWidget(self.dificuldade_combo)

        layout.addWidget(dif_group)

        # Filtro por Ano
        ano_group = QGroupBox("Ano")
        ano_layout = QHBoxLayout(ano_group)

        ano_layout.addWidget(QLabel("De:"))
        self.ano_de_spin = QSpinBox()
        self.ano_de_spin.setRange(1900, 2100)
        self.ano_de_spin.setValue(2020)
        self.ano_de_spin.valueChanged.connect(self.on_filters_changed)
        ano_layout.addWidget(self.ano_de_spin)

        ano_layout.addWidget(QLabel("Até:"))
        self.ano_ate_spin = QSpinBox()
        self.ano_ate_spin.setRange(1900, 2100)
        self.ano_ate_spin.setValue(2026)
        self.ano_ate_spin.valueChanged.connect(self.on_filters_changed)
        ano_layout.addWidget(self.ano_ate_spin)

        layout.addWidget(ano_group)

        # Filtro por Fonte
        fonte_group = QGroupBox("Fonte/Banca")
        fonte_layout = QVBoxLayout(fonte_group)

        self.fonte_input = QLineEdit()
        self.fonte_input.setPlaceholderText("Ex: ENEM, FUVEST, AUTORAL...")
        self.fonte_input.textChanged.connect(self.on_filters_changed)
        fonte_layout.addWidget(self.fonte_input)

        layout.addWidget(fonte_group)

        # Tags (placeholder - será implementado depois)
        tags_group = QGroupBox("Tags")
        tags_layout = QVBoxLayout(tags_group)

        tags_info = QLabel("Seleção de tags será\nimplementada aqui")
        tags_info.setStyleSheet("color: #666; font-style: italic;")
        tags_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tags_layout.addWidget(tags_info)

        layout.addWidget(tags_group)

        # Botões de ação
        btn_layout = QHBoxLayout()

        btn_search = QPushButton("🔍 Buscar")
        btn_search.clicked.connect(self.perform_search)
        btn_search.setStyleSheet("""
            QPushButton {
                background-color: #1abc9c;
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #16a085;
            }
        """)
        btn_layout.addWidget(btn_search)

        btn_clear = QPushButton("🔄 Limpar")
        btn_clear.clicked.connect(self.clear_filters)
        btn_layout.addWidget(btn_clear)

        layout.addLayout(btn_layout)

        layout.addStretch()

        # Contador de resultados
        self.results_count_label = QLabel("Resultados: 0")
        self.results_count_label.setStyleSheet("font-weight: bold; color: #2c3e50; margin-top: 10px;")
        layout.addWidget(self.results_count_label)

        return panel

    def create_results_panel(self):
        """Cria painel de resultados"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        # Cabeçalho
        header_layout = QHBoxLayout()

        title_label = QLabel("📋 Resultados da Busca")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Ordenação
        header_layout.addWidget(QLabel("Ordenar por:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            "Mais Recentes",
            "Mais Antigas",
            "Título A-Z",
            "Título Z-A",
            "Fonte",
            "Ano"
        ])
        self.sort_combo.currentTextChanged.connect(self.on_sort_changed)
        header_layout.addWidget(self.sort_combo)

        layout.addLayout(header_layout)

        # Área de scroll com resultados
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #f5f5f5;
            }
        """)

        # Container de resultados
        self.results_container = QWidget()
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.results_layout.setSpacing(10)

        scroll.setWidget(self.results_container)
        layout.addWidget(scroll)

        # Mensagem inicial
        self.show_empty_state()

        return panel

    def show_empty_state(self):
        """Exibe mensagem quando não há resultados"""
        self.clear_results()

        empty_widget = QWidget()
        empty_layout = QVBoxLayout(empty_widget)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_label = QLabel("🔍")
        icon_label.setStyleSheet("font-size: 64px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(icon_label)

        msg_label = QLabel("Nenhuma questão encontrada")
        msg_label.setStyleSheet("font-size: 18px; color: #666; margin-top: 10px;")
        msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(msg_label)

        hint_label = QLabel("Ajuste os filtros e clique em Buscar")
        hint_label.setStyleSheet("font-size: 14px; color: #999; margin-top: 5px;")
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(hint_label)

        self.results_layout.addWidget(empty_widget)

    def clear_results(self):
        """Limpa os resultados exibidos"""
        while self.results_layout.count():
            child = self.results_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def on_search_changed(self, text):
        """Callback quando o texto de busca muda"""
        # Auto-busca ao digitar (com debounce seria melhor)
        pass

    def on_filters_changed(self):
        """Callback quando algum filtro muda"""
        pass

    def on_sort_changed(self, sort_type):
        """Callback quando a ordenação muda"""
        logger.info(f"Ordenação alterada para: {sort_type}")
        # TODO: Reordenar resultados

    def clear_filters(self):
        """Limpa todos os filtros"""
        logger.info("Limpando filtros")
        self.search_input.clear()
        self.tipo_combo.setCurrentIndex(0)
        self.dificuldade_combo.setCurrentIndex(0)
        self.ano_de_spin.setValue(2020)
        self.ano_ate_spin.setValue(2026)
        self.fonte_input.clear()
        self.show_empty_state()
        self.results_count_label.setText("Resultados: 0")

    def perform_search(self):
        """Executa a busca com os filtros atuais via controller"""
        logger.info("Executando busca")

        # Limpar resultados anteriores
        self.clear_results()

        try:
            # Coletar filtros
            filtro = self._get_filtros()

            # Buscar via controller
            questoes_dto = self.controller.buscar_questoes(filtro)

            # Exibir resultados
            for questao_dto in questoes_dto:
                # Converter DTO para dict para manter compatibilidade
                questao_data = {
                    'id': questao_dto.id,
                    'titulo': questao_dto.titulo or 'Sem título',
                    'enunciado': questao_dto.enunciado[:100] + '...' if len(questao_dto.enunciado) > 100 else questao_dto.enunciado,
                    'tipo': questao_dto.tipo,
                    'fonte': questao_dto.fonte or 'N/A',
                    'ano': questao_dto.ano or 'N/A',
                    'dificuldade': questao_dto.dificuldade_nome
                }
                card = self.create_questao_card(questao_data)
                self.results_layout.addWidget(card)

            self.results_count_label.setText(f"Resultados: {len(questoes_dto)}")

            logger.info(f"Busca concluída: {len(questoes_dto)} questões encontradas")

        except Exception as e:
            logger.error(f"Erro ao buscar questões: {e}", exc_info=True)
            self.results_count_label.setText("Erro ao buscar questões")

    def _get_filtros(self):
        """Coleta filtros atuais para busca"""
        # Obter valores dos filtros
        titulo = self.search_input.text().strip() or None
        tipo = self.tipo_combo.currentText() if self.tipo_combo.currentText() != "Todos" else None
        ano_value = self.ano_spin.value()
        ano = ano_value if ano_value > 1900 else None
        fonte = self.fonte_combo.currentText() if self.fonte_combo.currentText() != "Todas" else None

        # Mapear dificuldade selecionada
        dificuldade_texto = self.dificuldade_combo.currentText()
        dificuldade_map = {
            'Fácil': 1,
            'Médio': 2,
            'Difícil': 3
        }
        id_dificuldade = dificuldade_map.get(dificuldade_texto)

        # TODO: Obter tags selecionadas da árvore de tags
        tags = []

        # Criar DTO de filtro
        filtro = FiltroQuestaoDTO(
            titulo=titulo,
            tipo=tipo,
            ano=ano,
            fonte=fonte,
            id_dificuldade=id_dificuldade,
            tags=tags,
            ativa=True  # Buscar apenas questões ativas
        )

        return filtro

    def _exemplo_placeholder(self):
        """Método auxiliar com dados de exemplo (não usado mais)"""
        exemplo_questoes = [
            {
                'id': 1,
                'titulo': 'Função Quadrática - Vértice',
                'enunciado': 'Determine as coordenadas do vértice da parábola...',
                'tipo': 'OBJETIVA',
                'fonte': 'ENEM',
                'ano': 2023,
                'dificuldade': 'MÉDIO'
            },
            {
                'id': 2,
                'titulo': 'Geometria Espacial - Volume',
                'enunciado': 'Calcule o volume de um cilindro com raio 5cm...',
                'tipo': 'DISCURSIVA',
                'fonte': 'FUVEST',
                'ano': 2024,
                'dificuldade': 'DIFÍCIL'
            },
            {
                'id': 3,
                'titulo': None,
                'enunciado': 'Resolva a equação x² - 5x + 6 = 0...',
                'tipo': 'OBJETIVA',
                'fonte': 'UNICAMP',
                'ano': 2025,
                'dificuldade': 'FÁCIL'
            }
        ]

        # Criar cards de resultados
        for questao in exemplo_questoes:
            card = self.create_questao_card(questao)
            self.results_layout.addWidget(card)

        self.results_count_label.setText(f"Resultados: {len(exemplo_questoes)}")

    def create_questao_card(self, questao_data):
        """Cria um card de questão"""
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        card.setStyleSheet("""
            QFrame {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: white;
                padding: 15px;
            }
            QFrame:hover {
                border-color: #1abc9c;
                background-color: #f0fff4;
            }
        """)

        layout = QVBoxLayout(card)

        # Cabeçalho
        header_layout = QHBoxLayout()

        # Título
        titulo = questao_data.get('titulo') or 'Sem título'
        title_label = QLabel(titulo)
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #2c3e50;")
        title_label.setWordWrap(True)
        header_layout.addWidget(title_label, 1)

        # Badge de tipo
        tipo_label = QLabel(questao_data['tipo'])
        tipo_color = "#2196f3" if questao_data['tipo'] == 'OBJETIVA' else "#9c27b0"
        tipo_label.setStyleSheet(f"""
            QLabel {{
                background-color: {tipo_color};
                color: white;
                padding: 4px 10px;
                border-radius: 3px;
                font-size: 11px;
                font-weight: bold;
            }}
        """)
        header_layout.addWidget(tipo_label)

        layout.addLayout(header_layout)

        # Preview do enunciado
        enunciado_preview = questao_data['enunciado'][:150] + "..."
        enunciado_label = QLabel(enunciado_preview)
        enunciado_label.setStyleSheet("color: #555; margin-top: 8px; font-size: 12px;")
        enunciado_label.setWordWrap(True)
        layout.addWidget(enunciado_label)

        # Metadados
        meta_layout = QHBoxLayout()
        meta_layout.setContentsMargins(0, 10, 0, 5)

        meta_text = f"📚 {questao_data['fonte']} • 📅 {questao_data['ano']} • ⭐ {questao_data['dificuldade']}"
        meta_label = QLabel(meta_text)
        meta_label.setStyleSheet("color: #777; font-size: 11px;")
        meta_layout.addWidget(meta_label)

        meta_layout.addStretch()
        layout.addLayout(meta_layout)

        # Botões de ação
        btn_layout = QHBoxLayout()

        btn_visualizar = QPushButton("👁️ Visualizar")
        btn_visualizar.setMaximumWidth(100)
        btn_visualizar.clicked.connect(lambda: self.questaoSelected.emit(questao_data['id']))
        btn_layout.addWidget(btn_visualizar)

        btn_editar = QPushButton("✏️ Editar")
        btn_editar.setMaximumWidth(100)
        btn_editar.clicked.connect(lambda: self.editQuestao.emit(questao_data['id']))
        btn_layout.addWidget(btn_editar)

        btn_adicionar = QPushButton("➕ Adicionar à Lista")
        btn_adicionar.setMaximumWidth(150)
        btn_layout.addWidget(btn_adicionar)

        btn_layout.addStretch()

        btn_excluir = QPushButton("🗑️")
        btn_excluir.setMaximumWidth(40)
        btn_excluir.setStyleSheet("QPushButton { color: #e74c3c; }")
        btn_excluir.clicked.connect(lambda: self.deleteQuestao.emit(questao_data['id']))
        btn_layout.addWidget(btn_excluir)

        layout.addLayout(btn_layout)

        return card

    def load_questoes(self, questoes):
        """Carrega lista de questões nos resultados"""
        self.clear_results()

        if not questoes:
            self.show_empty_state()
            self.results_count_label.setText("Resultados: 0")
            return

        for questao in questoes:
            card = self.create_questao_card(questao)
            self.results_layout.addWidget(card)

        self.results_count_label.setText(f"Resultados: {len(questoes)}")


logger.info("SearchPanel carregado")
