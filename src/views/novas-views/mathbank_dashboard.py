from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QLineEdit, QScrollArea, QFrame)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QPixmap
from sidebar_widget import SidebarWidget
from question_card import QuestionCard

class DashboardWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MathBank - Question Bank Dashboard")
        self.setMinimumSize(1400, 800)
        
        # Main widget
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Content area (sidebar + main content)
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Sidebar
        sidebar = SidebarWidget()
        content_layout.addWidget(sidebar)
        
        # Main content
        main_content = self.create_main_content()
        content_layout.addWidget(main_content, 1)
        
        content_widget = QWidget()
        content_widget.setLayout(content_layout)
        main_layout.addWidget(content_widget, 1)
        
        self.setCentralWidget(main_widget)
    
    def create_header(self):
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(60)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(40, 0, 40, 0)
        
        # Left section
        left_layout = QHBoxLayout()
        left_layout.setSpacing(32)
        
        # Logo and title
        logo_layout = QHBoxLayout()
        logo_layout.setSpacing(12)
        
        logo_label = QLabel("ƒ")
        logo_label.setObjectName("logo")
        logo_label.setFixedSize(32, 32)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title_label = QLabel("MathBank")
        title_label.setObjectName("title")
        
        logo_layout.addWidget(logo_label)
        logo_layout.addWidget(title_label)
        
        left_layout.addLayout(logo_layout)
        
        # Navigation
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(24)
        
        dashboard_btn = QPushButton("Dashboard")
        dashboard_btn.setObjectName("nav_active")
        
        exams_btn = QPushButton("Exams")
        exams_btn.setObjectName("nav_link")
        
        reports_btn = QPushButton("Reports")
        reports_btn.setObjectName("nav_link")
        
        nav_layout.addWidget(dashboard_btn)
        nav_layout.addWidget(exams_btn)
        nav_layout.addWidget(reports_btn)
        
        left_layout.addLayout(nav_layout)
        
        layout.addLayout(left_layout)
        layout.addStretch()
        
        # Right section
        right_layout = QHBoxLayout()
        right_layout.setSpacing(16)
        
        create_btn = QPushButton("+ Create Question")
        create_btn.setObjectName("create_button")
        create_btn.setMinimumWidth(140)
        
        # Profile avatar
        avatar_label = QLabel()
        avatar_label.setObjectName("avatar")
        avatar_label.setFixedSize(40, 40)
        avatar_label.setScaledContents(True)
        
        right_layout.addWidget(create_btn)
        right_layout.addWidget(avatar_label)
        
        layout.addLayout(right_layout)
        
        return header
    
    def create_main_content(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("main_scroll")
        
        content = QWidget()
        content.setObjectName("main_content")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)
        
        # Breadcrumbs and title
        breadcrumbs = QHBoxLayout()
        breadcrumbs.setSpacing(8)
        
        algebra_link = QLabel('<a href="#" style="color: #616f89;">Algebra</a>')
        algebra_link.setTextFormat(Qt.TextFormat.RichText)
        algebra_link.setOpenExternalLinks(False)
        
        separator = QLabel("/")
        separator.setStyleSheet("color: #616f89;")
        
        functions_label = QLabel("Functions")
        functions_label.setStyleSheet("color: #111318; font-weight: 500;")
        
        breadcrumbs.addWidget(algebra_link)
        breadcrumbs.addWidget(separator)
        breadcrumbs.addWidget(functions_label)
        breadcrumbs.addStretch()
        
        layout.addLayout(breadcrumbs)
        
        # Title and results count
        title_layout = QHBoxLayout()
        
        title = QLabel("Question Explorer")
        title.setObjectName("page_title")
        
        results = QLabel("Showing 24 of 1,240 results")
        results.setObjectName("results_count")
        
        title_layout.addWidget(title)
        title_layout.addStretch()
        title_layout.addWidget(results)
        
        layout.addLayout(title_layout)
        
        # Filters
        filters = self.create_filters()
        layout.addWidget(filters)
        
        # Questions grid
        grid_scroll = QScrollArea()
        grid_scroll.setWidgetResizable(True)
        grid_scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        grid_widget = QWidget()
        grid_layout = QVBoxLayout(grid_widget)
        grid_layout.setSpacing(24)
        
        # Mock questions data
        questions = [
            {"id": "#Q-1042", "title": "Function Limits at Infinity", 
             "formula": "f(x) = lim(x→∞) (x² + 2x + 1) / (3x² - 5)", 
             "tags": ["ENEM", "Easy", "Functions"], "type": "objective"},
            {"id": "#Q-2051", "title": "Quadratic Roots Properties", 
             "formula": "ax² + bx + c = 0, Δ = b² - 4ac", 
             "tags": ["Hard", "UTFPR", "Algebra"], "type": "discursive"},
            {"id": "#Q-4592", "title": "Definite Integral Areas", 
             "formula": "∫ₐᵇ x² dx = [x³/3]ₐᵇ", 
             "tags": ["Calculus", "Hard", "Review Needed"], "type": "objective"},
            {"id": "#Q-1102", "title": "Set Intersections", 
             "formula": "A ∩ (B ∪ C) = (A ∩ B) ∪ (A ∩ C)", 
             "tags": ["Basic", "Set Theory"], "type": "objective"},
            {"id": "#Q-3304", "title": "Matrix Determinants", 
             "formula": "det(A · B) = det(A) · det(B)", 
             "tags": ["Medium", "Matrices"], "type": "objective"},
            {"id": "#Q-5521", "title": "Complex Polar Forms", 
             "formula": "z = r(cos θ + i sin θ) = re^(iθ)", 
             "tags": ["ENEM", "Hard", "Complex Num"], "type": "discursive"},
        ]
        
        # Create rows of 3 cards
        row_layout = None
        for i, q in enumerate(questions):
            if i % 3 == 0:
                row_layout = QHBoxLayout()
                row_layout.setSpacing(24)
                grid_layout.addLayout(row_layout)
            
            card = QuestionCard(q["id"], q["title"], q["formula"], q["tags"], q["type"])
            row_layout.addWidget(card)
        
        # Fill remaining space in last row
        if len(questions) % 3 != 0:
            for _ in range(3 - (len(questions) % 3)):
                row_layout.addStretch()
        
        grid_layout.addStretch()
        
        grid_scroll.setWidget(grid_widget)
        layout.addWidget(grid_scroll, 1)
        
        scroll.setWidget(content)
        return scroll
    
    def create_filters(self):
        filters = QFrame()
        filters.setObjectName("filters")
        
        layout = QHBoxLayout(filters)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Search bar
        search = QLineEdit()
        search.setPlaceholderText("Search by ID, statement snippet, or tags...")
        search.setObjectName("search_bar")
        search.setMinimumHeight(40)
        
        layout.addWidget(search, 1)
        
        # Filter buttons
        enem_btn = QPushButton("ENEM ▼")
        enem_btn.setObjectName("filter_button")
        
        easy_btn = QPushButton("Easy ✕")
        easy_btn.setObjectName("filter_button_active")
        
        type_btn = QPushButton("Type ▼")
        type_btn.setObjectName("filter_button")
        
        filters_btn = QPushButton("⚙ Filters")
        filters_btn.setObjectName("filter_button_dark")
        
        layout.addWidget(enem_btn)
        layout.addWidget(easy_btn)
        layout.addWidget(type_btn)
        layout.addWidget(filters_btn)
        
        return filters
