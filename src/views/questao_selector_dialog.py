"""
View: Questao Selector Dialog
DESCRICAO: Dialogo para selecionar questoes para adicionar a uma lista
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QScrollArea, QFrame, QGroupBox, QSplitter, QWidget,
    QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal
import logging
from typing import List, Set, Dict

from src.controllers.adapters import criar_questao_controller, criar_tag_controller
from src.utils import ErrorHandler
from src.views.widgets import TagTreeWidget

logger = logging.getLogger(__name__)


class QuestaoSelectorCard(QFrame):
    """Card com checkbox para selecao de questao"""
    checkChanged = pyqtSignal(object, bool)  # Emite (questao_dto, checked)

    def __init__(self, questao_dto, ja_adicionada=False, parent=None):
        super().__init__(parent)
        self.questao_dto = questao_dto
        self.ja_adicionada = ja_adicionada
        self._get_id()
        self.init_ui()

    def _get_id(self):
        """Obtem ID da questao (suporta dict e objeto) - prioriza codigo"""
        if isinstance(self.questao_dto, dict):
            self.questao_id = self.questao_dto.get('codigo') or self.questao_dto.get('uuid')
        else:
            self.questao_id = getattr(self.questao_dto, 'codigo', None) or getattr(self.questao_dto, 'uuid', None)

    def _get_attr(self, attr, default=None):
        """Helper para obter atributo tanto de dict quanto de objeto"""
        if isinstance(self.questao_dto, dict):
            return self.questao_dto.get(attr, default)
        return getattr(self.questao_dto, attr, default)

    def init_ui(self):
        if self.ja_adicionada:
            self.setStyleSheet("""
                QFrame {
                    border: 2px solid #27ae60;
                    border-radius: 5px;
                    background-color: #e8f8f5;
                    padding: 10px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    background-color: white;
                    padding: 10px;
                }
                QFrame:hover {
                    border-color: #3498db;
                    background-color: #ebf5fb;
                }
            """)

        layout = QVBoxLayout(self)
        layout.setSpacing(5)

        # Primeira linha: Checkbox + Titulo + Badge tipo
        header_layout = QHBoxLayout()

        # Checkbox
        self.checkbox = QCheckBox()
        if self.ja_adicionada:
            self.checkbox.setChecked(True)
            self.checkbox.setEnabled(False)
        self.checkbox.stateChanged.connect(self._on_check_changed)
        header_layout.addWidget(self.checkbox)

        titulo = self._get_attr('titulo') or 'Sem titulo'
        title_label = QLabel(titulo)
        title_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #2c3e50;")
        title_label.setWordWrap(True)
        header_layout.addWidget(title_label, 1)

        tipo = self._get_attr('tipo', 'N/A')
        tipo_color = "#2196f3" if tipo == 'OBJETIVA' else "#9c27b0"
        tipo_label = QLabel(tipo)
        tipo_label.setStyleSheet(f"""
            QLabel {{
                background-color: {tipo_color};
                color: white;
                padding: 3px 8px;
                border-radius: 3px;
                font-size: 10px;
                font-weight: bold;
            }}
        """)
        header_layout.addWidget(tipo_label)

        if self.ja_adicionada:
            added_label = QLabel("JA NA LISTA")
            added_label.setStyleSheet("""
                QLabel {
                    background-color: #27ae60;
                    color: white;
                    padding: 3px 8px;
                    border-radius: 3px;
                    font-size: 10px;
                    font-weight: bold;
                }
            """)
            header_layout.addWidget(added_label)

        layout.addLayout(header_layout)

        # Preview do enunciado
        enunciado = self._get_attr('enunciado', '')
        enunciado_preview = (enunciado[:120] + "...") if len(enunciado) > 120 else enunciado
        enunciado_label = QLabel(enunciado_preview)
        enunciado_label.setStyleSheet("color: #555; font-size: 11px; margin-left: 25px;")
        enunciado_label.setWordWrap(True)
        layout.addWidget(enunciado_label)

        # Tags (se disponiveis)
        tags = self._get_attr('tags', [])
        if tags:
            tags_text = ", ".join(
                t.get('nome', t) if isinstance(t, dict) else getattr(t, 'nome', str(t))
                for t in tags[:5]
            )
            if len(tags) > 5:
                tags_text += f" (+{len(tags)-5})"
            tags_label = QLabel(f"Tags: {tags_text}")
            tags_label.setStyleSheet("color: #7f8c8d; font-size: 10px; font-style: italic; margin-left: 25px;")
            layout.addWidget(tags_label)

        # Metadados
        fonte = self._get_attr('fonte') or 'N/A'
        ano = self._get_attr('ano') or 'N/A'
        dificuldade = self._get_attr('dificuldade_nome') or self._get_attr('dificuldade') or 'N/A'
        meta_label = QLabel(f"{fonte} | {ano} | {dificuldade}")
        meta_label.setStyleSheet("color: #95a5a6; font-size: 10px; margin-left: 25px;")
        layout.addWidget(meta_label)

    def _on_check_changed(self, state):
        if not self.ja_adicionada:
            self.checkChanged.emit(self.questao_dto, state == Qt.CheckState.Checked.value)

    def is_checked(self):
        return self.checkbox.isChecked() and not self.ja_adicionada

    def set_checked(self, checked):
        if not self.ja_adicionada:
            self.checkbox.setChecked(checked)


class QuestaoSelectorDialog(QDialog):
    """Dialogo para selecionar questoes com filtros e checkboxes"""
    questoesAdicionadas = pyqtSignal(list)  # Emite lista de questao_dto quando confirmar

    def __init__(self, questoes_ja_na_lista: List = None, parent=None):
        super().__init__(parent)
        self.questoes_ja_na_lista = questoes_ja_na_lista or []
        self.ids_na_lista: Set = self._extrair_ids(self.questoes_ja_na_lista)
        self.questoes_selecionadas: Dict = {}  # {id: questao_dto}
        self.cards: List[QuestaoSelectorCard] = []

        self.controller = criar_questao_controller()
        self.tag_controller = criar_tag_controller()

        self.setWindowTitle("Selecionar Questoes")
        self.setMinimumSize(900, 600)
        self.init_ui()
        self.load_tags()

        logger.info("QuestaoSelectorDialog inicializado")

    def _extrair_ids(self, questoes) -> Set:
        """Extrai IDs das questoes (suporta dict e objeto) - prioriza codigo"""
        ids = set()
        for q in questoes:
            if isinstance(q, dict):
                qid = q.get('codigo') or q.get('uuid')
            else:
                qid = getattr(q, 'codigo', None) or getattr(q, 'uuid', None)
            if qid:
                ids.add(qid)
        return ids

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Titulo
        header = QLabel("Selecionar Questoes para Adicionar")
        header.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 5px;")
        layout.addWidget(header)

        hint = QLabel("Marque as questoes desejadas e clique em 'Adicionar Selecionadas'")
        hint.setStyleSheet("color: #666; font-size: 11px; margin-bottom: 10px;")
        layout.addWidget(hint)

        # Splitter: Filtros | Resultados
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Painel de filtros
        filters_panel = self._create_filters_panel()
        splitter.addWidget(filters_panel)

        # Painel de resultados
        results_panel = self._create_results_panel()
        splitter.addWidget(results_panel)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 7)
        layout.addWidget(splitter)

        # Rodape com contadores e botoes
        footer_layout = QHBoxLayout()

        self.results_count_label = QLabel("Clique em 'Buscar' para ver questoes")
        self.results_count_label.setStyleSheet("color: #666;")
        footer_layout.addWidget(self.results_count_label)

        self.selected_count_label = QLabel("0 selecionadas")
        self.selected_count_label.setStyleSheet("color: #3498db; font-weight: bold;")
        footer_layout.addWidget(self.selected_count_label)

        footer_layout.addStretch()

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        footer_layout.addWidget(btn_cancel)

        self.btn_add = QPushButton("Adicionar Selecionadas")
        self.btn_add.setStyleSheet("background-color: #1abc9c; color: white; padding: 8px 20px; font-weight: bold; border-radius: 4px;")
        self.btn_add.clicked.connect(self._on_adicionar_clicked)
        self.btn_add.setEnabled(False)
        footer_layout.addWidget(self.btn_add)

        layout.addLayout(footer_layout)

    def _create_filters_panel(self):
        panel = QWidget()
        panel.setMaximumWidth(350)
        layout = QVBoxLayout(panel)

        # Busca por texto
        search_group = QGroupBox("Busca")
        search_layout = QVBoxLayout(search_group)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar em titulo e enunciado...")
        self.search_input.returnPressed.connect(self.perform_search)
        search_layout.addWidget(self.search_input)
        layout.addWidget(search_group)

        # Filtro por tags
        tags_group = QGroupBox("Filtrar por Tags")
        tags_layout = QVBoxLayout(tags_group)
        self.tag_tree_widget = TagTreeWidget()
        tags_layout.addWidget(self.tag_tree_widget)
        layout.addWidget(tags_group)

        layout.addStretch()

        # Botoes de acao
        btn_layout = QHBoxLayout()
        btn_search = QPushButton("Buscar")
        btn_search.setStyleSheet("background-color: #3498db; color: white; padding: 6px 15px; font-weight: bold; border-radius: 4px;")
        btn_search.clicked.connect(self.perform_search)
        btn_layout.addWidget(btn_search)

        btn_clear = QPushButton("Limpar")
        btn_clear.clicked.connect(self.clear_filters)
        btn_layout.addWidget(btn_clear)
        layout.addLayout(btn_layout)

        return panel

    def _create_results_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        # Barra de selecao rapida
        select_bar = QHBoxLayout()
        btn_select_all = QPushButton("Selecionar Todas")
        btn_select_all.clicked.connect(self._select_all)
        select_bar.addWidget(btn_select_all)

        btn_deselect_all = QPushButton("Desmarcar Todas")
        btn_deselect_all.clicked.connect(self._deselect_all)
        select_bar.addWidget(btn_deselect_all)

        select_bar.addStretch()
        layout.addLayout(select_bar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #f5f5f5; }")

        self.results_container = QWidget()
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.results_layout.setSpacing(8)

        scroll.setWidget(self.results_container)
        layout.addWidget(scroll)

        self._show_empty_state()
        return panel

    def load_tags(self):
        try:
            tags_arvore = self.tag_controller.obter_arvore_tags_completa()
            if tags_arvore:
                self.tag_tree_widget.load_tags(tags_arvore)
        except Exception as e:
            logger.warning(f"Erro ao carregar tags: {e}")

    def _show_empty_state(self):
        self._clear_results()
        empty_label = QLabel("Use os filtros e clique em 'Buscar'")
        empty_label.setStyleSheet("color: #999; font-size: 14px; padding: 40px;")
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.results_layout.addWidget(empty_label)

    def _clear_results(self):
        self.cards.clear()
        while self.results_layout.count():
            child = self.results_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def clear_filters(self):
        self.search_input.clear()
        self.tag_tree_widget.clear_selection()
        self._show_empty_state()
        self.results_count_label.setText("Filtros limpos")

    def perform_search(self):
        self._clear_results()
        try:
            filtro = self._get_filtros()
            questoes = self.controller.buscar_questoes(filtro)

            if not questoes:
                no_results = QLabel("Nenhuma questao encontrada")
                no_results.setStyleSheet("color: #999; font-size: 14px; padding: 40px;")
                no_results.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.results_layout.addWidget(no_results)
                self.results_count_label.setText("0 questoes encontradas")
            else:
                for q in questoes:
                    # Verificar se ja esta na lista - usar codigo
                    if isinstance(q, dict):
                        qid = q.get('codigo') or q.get('uuid')
                    else:
                        qid = getattr(q, 'codigo', None) or getattr(q, 'uuid', None)

                    ja_adicionada = qid in self.ids_na_lista

                    card = QuestaoSelectorCard(q, ja_adicionada=ja_adicionada)
                    card.checkChanged.connect(self._on_check_changed)

                    # Restaurar estado se ja estava selecionada
                    if qid in self.questoes_selecionadas:
                        card.set_checked(True)

                    self.cards.append(card)
                    self.results_layout.addWidget(card)

                self.results_count_label.setText(f"{len(questoes)} questoes encontradas")

            logger.info(f"Busca concluida: {len(questoes) if questoes else 0} questoes")
        except Exception as e:
            ErrorHandler.handle_exception(self, e, "Erro ao buscar questoes")

    def _get_filtros(self):
        titulo = self.search_input.text().strip() or None
        tags = self.tag_tree_widget.get_selected_tag_ids()

        return {
            'titulo': titulo,
            'tags': tags if tags else None,
            'ativa': True
        }

    def _on_check_changed(self, questao_dto, checked):
        """Chamado quando um checkbox muda de estado"""
        if isinstance(questao_dto, dict):
            qid = questao_dto.get('codigo') or questao_dto.get('uuid')
        else:
            qid = getattr(questao_dto, 'codigo', None) or getattr(questao_dto, 'uuid', None)

        if checked:
            self.questoes_selecionadas[qid] = questao_dto
        else:
            self.questoes_selecionadas.pop(qid, None)

        self._update_selection_count()

    def _update_selection_count(self):
        count = len(self.questoes_selecionadas)
        self.selected_count_label.setText(f"{count} selecionada{'s' if count != 1 else ''}")
        self.btn_add.setEnabled(count > 0)

    def _select_all(self):
        for card in self.cards:
            if not card.ja_adicionada:
                card.set_checked(True)

    def _deselect_all(self):
        for card in self.cards:
            card.set_checked(False)
        self.questoes_selecionadas.clear()
        self._update_selection_count()

    def _on_adicionar_clicked(self):
        """Adiciona todas as questoes selecionadas"""
        if not self.questoes_selecionadas:
            return

        # Obter questoes completas
        questoes_completas = []
        for qid, q_dto in self.questoes_selecionadas.items():
            questao_completa = self.controller.obter_questao_completa(qid)
            if questao_completa:
                questoes_completas.append(questao_completa)

        if questoes_completas:
            self.questoesAdicionadas.emit(questoes_completas)
            logger.info(f"{len(questoes_completas)} questoes adicionadas")

        self.accept()
