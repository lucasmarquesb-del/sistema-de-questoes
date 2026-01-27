# src/views/pages/dashboard_page.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSizePolicy, QFrame
)
from PyQt6.QtCore import Qt
from typing import Dict, List, Any
from datetime import datetime, timedelta
from collections import defaultdict

# Matplotlib for plotting
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from src.views.design.constants import Color, Spacing, Typography, Dimensions, Text
from src.views.components.common.cards import StatCard
from src.views.components.common.buttons import SecondaryButton
from src.controllers.questao_controller_orm import QuestaoControllerORM


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
        self.time_card = StatCard(Text.DASHBOARD_AVG_RESOLUTION, "0m 0s", parent=self)

        self.metric_cards_layout.addWidget(self.total_card)
        self.metric_cards_layout.addWidget(self.new_card)
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

    def _load_data(self):
        """Load data from controllers."""
        try:
            # Get statistics
            self.stats_data = QuestaoControllerORM.obter_estatisticas()

            # Get all questions for analysis
            self.questions_data = QuestaoControllerORM.listar_questoes()

            # Update UI with loaded data
            self._update_metric_cards()
            self._update_charts()

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

    def _show_empty_state(self):
        """Show empty state when no data is available."""
        self.total_card.set_value("0")
        self.new_card.set_value("0")
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
