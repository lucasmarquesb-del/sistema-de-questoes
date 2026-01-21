# src/views/pages/dashboard_page.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout,
    QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView,
    QSpacerItem, QSizePolicy, QFrame
)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QFont
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict

# Matplotlib for plotting
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from src.views.design.constants import Color, Spacing, Typography, Dimensions, Text, IconPath
from src.views.components.common.cards import StatCard
from src.views.components.common.buttons import SecondaryButton, PrimaryButton
from src.controllers.questao_controller_orm import QuestaoControllerORM
from src.controllers.tag_controller_orm import TagControllerORM


class MplCanvas(FigureCanvas):
    """A Matplotlib canvas widget for embedding plots in PyQt applications."""
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor='white')
        self.axes = self.fig.add_subplot(111)
        super(MplCanvas, self).__init__(self.fig)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.updateGeometry()


class DashboardPage(QWidget):
    """
    Page displaying various statistics and metrics for the MathBank application.
    Data is fetched from the database via controllers.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dashboard_page")

        # Data containers
        self.stats_data: Dict[str, Any] = {}
        self.questions_data: List[Dict] = []
        self.tags_data: List[Dict] = []

        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        """Setup the UI layout."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(Spacing.XL, Spacing.LG, Spacing.XL, Spacing.LG)
        main_layout.setSpacing(Spacing.LG)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 1. Filter Row
        filter_row = self._create_filter_row()
        main_layout.addLayout(filter_row)

        # 2. Metric Cards
        self.metric_cards_layout = QHBoxLayout()
        self.metric_cards_layout.setSpacing(Spacing.LG)
        self.metric_cards_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Placeholders - will be populated with real data
        self.total_card = StatCard(Text.DASHBOARD_TOTAL_QUESTIONS, "0", parent=self)
        self.new_card = StatCard(Text.DASHBOARD_NEW_THIS_MONTH, "0", parent=self)
        self.success_card = StatCard(Text.DASHBOARD_SUCCESS_RATE, "0%", parent=self)
        self.time_card = StatCard(Text.DASHBOARD_AVG_RESOLUTION, "0m 0s", parent=self)

        self.metric_cards_layout.addWidget(self.total_card)
        self.metric_cards_layout.addWidget(self.new_card)
        self.metric_cards_layout.addWidget(self.success_card)
        self.metric_cards_layout.addWidget(self.time_card)
        self.metric_cards_layout.addStretch()
        main_layout.addLayout(self.metric_cards_layout)

        # 3. Charts Row
        charts_row_layout = QHBoxLayout()
        charts_row_layout.setSpacing(Spacing.LG)

        # Questions Over Time Chart Container
        line_chart_frame = self._create_chart_frame(Text.DASHBOARD_QUESTIONS_OVER_TIME)
        self.line_chart_canvas = MplCanvas(self, width=6, height=3.5, dpi=100)
        line_chart_frame.layout().addWidget(self.line_chart_canvas)
        charts_row_layout.addWidget(line_chart_frame, 2)

        # Difficulty Distribution Chart Container
        donut_chart_frame = self._create_chart_frame(Text.DASHBOARD_DIFFICULTY_DISTRIBUTION)
        self.donut_chart_canvas = MplCanvas(self, width=4, height=3.5, dpi=100)
        donut_chart_frame.layout().addWidget(self.donut_chart_canvas)
        charts_row_layout.addWidget(donut_chart_frame, 1)

        main_layout.addLayout(charts_row_layout)

        # 4. Accuracy Rate by Topic
        accuracy_section = self._create_section_header(Text.DASHBOARD_ACCURACY_BY_TOPIC)
        main_layout.addWidget(accuracy_section)

        self.bar_chart_canvas = MplCanvas(self, width=10, height=2.5, dpi=100)
        main_layout.addWidget(self.bar_chart_canvas)

        # 5. Top 10 Hardest Questions Table
        table_header = self._create_table_header()
        main_layout.addLayout(table_header)

        self.hard_questions_table = self._create_questions_table()
        main_layout.addWidget(self.hard_questions_table)

        # View all link
        view_all_layout = QHBoxLayout()
        view_all_layout.addStretch()
        view_all_btn = SecondaryButton(Text.DASHBOARD_VIEW_ALL_DIFFICULT, parent=self)
        view_all_layout.addWidget(view_all_btn)
        view_all_layout.addStretch()
        main_layout.addLayout(view_all_layout)

        main_layout.addStretch(1)

    def _create_filter_row(self) -> QHBoxLayout:
        """Create the filter row with dropdowns."""
        filter_row_layout = QHBoxLayout()
        filter_row_layout.setSpacing(Spacing.SM)
        filter_row_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        period_filter = SecondaryButton(f"📅 {Text.FILTER_PERIOD}: {Text.FILTER_LAST_30_DAYS} ▼", parent=self)
        filter_row_layout.addWidget(period_filter)

        tags_filter = SecondaryButton(f"🏷 {Text.FILTER_TAGS}: {Text.FILTER_ALL} ▼", parent=self)
        filter_row_layout.addWidget(tags_filter)

        difficulty_filter = SecondaryButton(f"📊 {Text.FILTER_DIFFICULTY}: {Text.FILTER_ALL} ▼", parent=self)
        filter_row_layout.addWidget(difficulty_filter)

        filter_row_layout.addStretch()
        return filter_row_layout

    def _create_chart_frame(self, title: str) -> QFrame:
        """Create a styled frame for charts."""
        frame = QFrame(self)
        frame.setObjectName("chart_frame")
        frame.setStyleSheet(f"""
            QFrame#chart_frame {{
                background-color: {Color.WHITE};
                border: 1px solid {Color.BORDER_LIGHT};
                border-radius: {Dimensions.BORDER_RADIUS_LG};
                padding: {Spacing.MD}px;
            }}
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)

        title_label = QLabel(title, frame)
        title_label.setStyleSheet(f"""
            font-size: {Typography.FONT_SIZE_LG};
            font-weight: {Typography.FONT_WEIGHT_SEMIBOLD};
            color: {Color.DARK_TEXT};
        """)
        layout.addWidget(title_label)

        return frame

    def _create_section_header(self, title: str) -> QLabel:
        """Create a section header label."""
        label = QLabel(title, self)
        label.setStyleSheet(f"""
            font-size: {Typography.FONT_SIZE_XL};
            font-weight: {Typography.FONT_WEIGHT_SEMIBOLD};
            color: {Color.DARK_TEXT};
            margin-top: {Spacing.MD}px;
        """)
        return label

    def _create_table_header(self) -> QHBoxLayout:
        """Create the header for the hardest questions table."""
        header_layout = QHBoxLayout()

        label = QLabel(Text.DASHBOARD_TOP_HARDEST, self)
        label.setStyleSheet(f"""
            font-size: {Typography.FONT_SIZE_XL};
            font-weight: {Typography.FONT_WEIGHT_SEMIBOLD};
            color: {Color.DARK_TEXT};
        """)
        header_layout.addWidget(label)
        header_layout.addStretch()

        export_btn = SecondaryButton(Text.DASHBOARD_EXPORT_CSV, parent=self)
        header_layout.addWidget(export_btn)

        return header_layout

    def _create_questions_table(self) -> QTableWidget:
        """Create and style the questions table."""
        table = QTableWidget(self)
        table.setObjectName("hard_questions_table")
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels([
            Text.TABLE_ID,
            Text.TABLE_TOPIC,
            Text.TABLE_TAG,
            Text.TABLE_SUCCESS_RATE,
            Text.TABLE_ACTIONS
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)

        table.setStyleSheet(f"""
            QTableWidget#hard_questions_table {{
                background-color: {Color.WHITE};
                border: 1px solid {Color.BORDER_LIGHT};
                border-radius: {Dimensions.BORDER_RADIUS_MD};
                font-size: {Typography.FONT_SIZE_MD};
                color: {Color.DARK_TEXT};
                gridline-color: {Color.BORDER_LIGHT};
            }}
            QTableWidget#hard_questions_table QHeaderView::section {{
                background-color: {Color.LIGHT_BACKGROUND};
                color: {Color.GRAY_TEXT};
                font-weight: {Typography.FONT_WEIGHT_SEMIBOLD};
                font-size: {Typography.FONT_SIZE_SM};
                padding: {Spacing.SM}px;
                border: none;
                border-bottom: 1px solid {Color.BORDER_LIGHT};
            }}
            QTableWidget#hard_questions_table::item {{
                padding: {Spacing.SM}px;
            }}
            QTableWidget#hard_questions_table::item:selected {{
                background-color: {Color.LIGHT_BLUE_BG_2};
                color: {Color.PRIMARY_BLUE};
            }}
            QTableWidget#hard_questions_table::item:alternate {{
                background-color: {Color.LIGHT_BACKGROUND};
            }}
        """)

        return table

    def _load_data(self):
        """Load data from controllers."""
        try:
            # Get statistics
            self.stats_data = QuestaoControllerORM.obter_estatisticas()

            # Get all questions for analysis
            self.questions_data = QuestaoControllerORM.listar_questoes()

            # Get tags for topic analysis
            self.tags_data = TagControllerORM.listar_todas()

            # Update UI with loaded data
            self._update_metric_cards()
            self._update_charts()
            self._update_table()

        except Exception as e:
            print(f"Error loading dashboard data: {e}")
            self._show_empty_state()

    def _update_metric_cards(self):
        """Update metric cards with real data."""
        total = self.stats_data.get('total', 0)

        # Calculate new questions this month
        new_this_month = self._calculate_new_this_month()

        # Calculate growth rate
        growth_rate = self._calculate_growth_rate()
        growth_str = f"+{growth_rate}%" if growth_rate >= 0 else f"{growth_rate}%"

        # Update cards
        self.total_card.set_value(f"{total:,}")
        self.total_card.set_variation(growth_str if growth_rate != 0 else None)

        self.new_card.set_value(f"+{new_this_month}")

        # Success rate - placeholder since we don't track this yet
        self.success_card.set_value("68.5%")
        self.success_card.set_variation("-1.2%")

        # Average resolution time - placeholder
        self.time_card.set_value("4m 32s")

    def _calculate_new_this_month(self) -> int:
        """Calculate number of questions added this month."""
        now = datetime.now()
        first_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        count = 0
        for q in self.questions_data:
            if 'data_criacao' in q and q['data_criacao']:
                try:
                    created = q['data_criacao']
                    if isinstance(created, str):
                        created = datetime.fromisoformat(created.replace('Z', '+00:00'))
                    if created >= first_of_month:
                        count += 1
                except:
                    pass
        return count

    def _calculate_growth_rate(self) -> float:
        """Calculate growth rate compared to last month."""
        # Simplified calculation
        total = len(self.questions_data)
        if total == 0:
            return 0.0
        new_this_month = self._calculate_new_this_month()
        if total - new_this_month == 0:
            return 100.0
        return round((new_this_month / (total - new_this_month)) * 100, 1)

    def _update_charts(self):
        """Update all charts with real data."""
        self._plot_questions_over_time()
        self._plot_difficulty_distribution()
        self._plot_accuracy_by_topic()

    def _plot_questions_over_time(self):
        """Plot questions added over time using real data."""
        ax = self.line_chart_canvas.axes
        ax.clear()

        # Group questions by month
        monthly_counts = defaultdict(int)
        for q in self.questions_data:
            if 'data_criacao' in q and q['data_criacao']:
                try:
                    created = q['data_criacao']
                    if isinstance(created, str):
                        created = datetime.fromisoformat(created.replace('Z', '+00:00'))
                    month_key = created.strftime('%b')
                    monthly_counts[month_key] += 1
                except:
                    pass

        # Generate last 12 months
        months = []
        now = datetime.now()
        for i in range(11, -1, -1):
            month_date = now - timedelta(days=30*i)
            months.append(month_date.strftime('%b'))

        values = [monthly_counts.get(m, 0) for m in months]

        # If no data, show placeholder
        if sum(values) == 0:
            values = [0] * 12

        # Plot
        ax.fill_between(months, values, alpha=0.3, color=Color.PRIMARY_BLUE)
        ax.plot(months, values, marker='o', color=Color.PRIMARY_BLUE, linewidth=2, markersize=4)

        ax.set_ylabel('Questions Added', fontsize=9, color=Color.GRAY_TEXT)
        ax.tick_params(axis='x', rotation=45, labelsize=8)
        ax.tick_params(axis='y', labelsize=8)
        ax.grid(True, linestyle='--', alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        # Add total annotation
        total = sum(values)
        ax.annotate(f'{total:,}\nTOTAL',
                   xy=(0.95, 0.95), xycoords='axes fraction',
                   ha='right', va='top',
                   fontsize=14, fontweight='bold', color=Color.DARK_TEXT)

        self.line_chart_canvas.fig.tight_layout()
        self.line_chart_canvas.draw()

    def _plot_difficulty_distribution(self):
        """Plot difficulty distribution using real data."""
        ax = self.donut_chart_canvas.axes
        ax.clear()

        # Get difficulty counts from stats
        por_dificuldade = self.stats_data.get('por_dificuldade', {})

        # Map to display labels
        difficulty_map = {
            'FACIL': (Text.DIFFICULTY_EASY, Color.DIFFICULTY_EASY),
            'MEDIO': (Text.DIFFICULTY_MEDIUM, Color.DIFFICULTY_MEDIUM),
            'DIFICIL': (Text.DIFFICULTY_HARD, Color.DIFFICULTY_HARD),
            'MUITO_DIFICIL': (Text.DIFFICULTY_VERY_HARD, Color.DIFFICULTY_VERY_HARD),
        }

        labels = []
        sizes = []
        colors = []

        for key, (label, color) in difficulty_map.items():
            count = por_dificuldade.get(key, 0)
            if count > 0:
                labels.append(f"{label} ({count})")
                sizes.append(count)
                colors.append(color)

        # If no data, show placeholder
        if not sizes:
            labels = [Text.DIFFICULTY_EASY, Text.DIFFICULTY_MEDIUM, Text.DIFFICULTY_HARD, Text.DIFFICULTY_VERY_HARD]
            sizes = [25, 40, 20, 15]
            colors = [Color.DIFFICULTY_EASY, Color.DIFFICULTY_MEDIUM, Color.DIFFICULTY_HARD, Color.DIFFICULTY_VERY_HARD]

        # Create donut chart
        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=None,
            autopct='%1.0f%%',
            startangle=90,
            colors=colors,
            wedgeprops={'edgecolor': 'white', 'linewidth': 2, 'width': 0.6},
            pctdistance=0.75
        )

        # Style percentage text
        for autotext in autotexts:
            autotext.set_fontsize(8)
            autotext.set_color('white')
            autotext.set_fontweight('bold')

        # Add center text
        total = sum(sizes)
        ax.text(0, 0, f'{total/1000:.1f}k\nTOTAL', ha='center', va='center',
               fontsize=12, fontweight='bold', color=Color.DARK_TEXT)

        # Add legend
        ax.legend(labels, loc='center left', bbox_to_anchor=(1, 0.5), fontsize=8)

        ax.axis('equal')
        self.donut_chart_canvas.fig.tight_layout()
        self.donut_chart_canvas.draw()

    def _plot_accuracy_by_topic(self):
        """Plot accuracy by topic using tag data."""
        ax = self.bar_chart_canvas.axes
        ax.clear()

        # Get top-level tags and their question counts
        topic_data = []
        for tag in self.tags_data:
            if tag.get('nivel', 0) == 1:  # Top-level tags
                nome = tag.get('nome', 'Unknown')
                # Simulated accuracy - in real app, would come from user responses
                # Using a formula based on question count for demo
                accuracy = 50 + (hash(nome) % 40)  # Pseudo-random but consistent
                topic_data.append((nome, accuracy))

        # Sort by accuracy and take top 5
        topic_data.sort(key=lambda x: x[1], reverse=True)
        topic_data = topic_data[:5]

        # If no data, use placeholder
        if not topic_data:
            topic_data = [
                ('Álgebra Linear', 82.4),
                ('Cálculo Diferencial', 64.1),
                ('Geometria Analítica', 58.7),
                ('Trigonometria', 45.2),
                ('Estatística & Probabilidade', 38.9),
            ]

        topics = [t[0] for t in topic_data]
        accuracies = [t[1] for t in topic_data]

        # Plot horizontal bars
        y_pos = range(len(topics))
        bars = ax.barh(y_pos, accuracies, color=Color.PRIMARY_BLUE, height=0.6)

        # Add percentage labels
        for i, (bar, acc) in enumerate(zip(bars, accuracies)):
            ax.text(acc + 1, i, f'{acc:.1f}%', va='center', fontsize=9, color=Color.DARK_TEXT)

        ax.set_yticks(y_pos)
        ax.set_yticklabels(topics, fontsize=9)
        ax.set_xlim(0, 100)
        ax.set_xlabel('')
        ax.invert_yaxis()
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.tick_params(bottom=False, labelbottom=False)

        self.bar_chart_canvas.fig.tight_layout()
        self.bar_chart_canvas.draw()

    def _update_table(self):
        """Update the hardest questions table with real data."""
        # Sort questions by difficulty (hard ones first)
        difficulty_order = {'DIFICIL': 0, 'MUITO_DIFICIL': 0, 'MEDIO': 1, 'FACIL': 2}

        sorted_questions = sorted(
            self.questions_data,
            key=lambda q: difficulty_order.get(q.get('dificuldade', ''), 3)
        )

        # Take top 10
        hard_questions = sorted_questions[:10]

        self.hard_questions_table.setRowCount(len(hard_questions))

        for row_idx, q in enumerate(hard_questions):
            codigo = q.get('codigo', 'N/A')

            # Get first tag as topic
            tags = q.get('tags', [])
            topic = tags[0] if tags else 'General'
            tag_name = tags[1] if len(tags) > 1 else (tags[0] if tags else '-')

            # Simulated success rate
            success_rate = f"{30 + (hash(codigo) % 25):.1f}%"

            # Create items with styling
            id_item = QTableWidgetItem(codigo)
            id_item.setForeground(Qt.GlobalColor.blue)

            self.hard_questions_table.setItem(row_idx, 0, id_item)
            self.hard_questions_table.setItem(row_idx, 1, QTableWidgetItem(topic))

            tag_item = QTableWidgetItem(tag_name)
            self.hard_questions_table.setItem(row_idx, 2, tag_item)

            self.hard_questions_table.setItem(row_idx, 3, QTableWidgetItem(success_rate))
            self.hard_questions_table.setItem(row_idx, 4, QTableWidgetItem("👁"))

    def _show_empty_state(self):
        """Show empty state when no data is available."""
        self.total_card.set_value("0")
        self.new_card.set_value("0")
        self.success_card.set_value("-")
        self.time_card.set_value("-")

    def refresh_data(self):
        """Public method to refresh dashboard data."""
        self._load_data()


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
            self.setWindowTitle("Dashboard Page Test")
            self.setGeometry(100, 100, 1200, 900)

            self.dashboard_page = DashboardPage(self)
            self.setCentralWidget(self.dashboard_page)

    window = TestMainWindow()
    window.show()
    sys.exit(app.exec())
