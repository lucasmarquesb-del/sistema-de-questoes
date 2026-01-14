from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt

class QuestionCard(QFrame):
    def __init__(self, qid, title, formula, tags, qtype):
        super().__init__()
        self.setObjectName("question_card")
        self.setMinimumHeight(280)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Header (ID and type)
        header = QHBoxLayout()
        
        id_label = QLabel(qid)
        id_label.setObjectName("card_id")
        
        header.addWidget(id_label)
        header.addStretch()
        
        type_icon = "○" if qtype == "objective" else "✎"
        type_label = QLabel(type_icon)
        type_label.setObjectName("card_type")
        
        menu_label = QLabel("⋮")
        menu_label.setObjectName("card_menu")
        
        header.addWidget(type_label)
        header.addWidget(menu_label)
        
        layout.addLayout(header)
        
        # Title
        title_label = QLabel(title)
        title_label.setObjectName("card_title")
        title_label.setWordWrap(True)
        layout.addWidget(title_label)
        
        # Formula box
        formula_frame = QFrame()
        formula_frame.setObjectName("formula_box")
        formula_frame.setMinimumHeight(80)
        
        formula_layout = QVBoxLayout(formula_frame)
        formula_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        formula_label = QLabel(formula)
        formula_label.setObjectName("formula_text")
        formula_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        formula_label.setWordWrap(True)
        
        formula_layout.addWidget(formula_label)
        
        layout.addWidget(formula_frame, 1)
        
        # Tags
        tags_layout = QHBoxLayout()
        tags_layout.setSpacing(8)
        
        tag_styles = {
            "ENEM": "tag_blue",
            "Easy": "tag_green",
            "Hard": "tag_red",
            "Medium": "tag_yellow",
            "UTFPR": "tag_purple",
            "Review Needed": "tag_orange",
            "Basic": "tag_green",
        }
        
        for tag_text in tags:
            tag = QLabel(tag_text.upper())
            tag_style = tag_styles.get(tag_text, "tag_gray")
            tag.setObjectName(tag_style)
            tags_layout.addWidget(tag)
        
        tags_layout.addStretch()
        
        layout.addLayout(tags_layout)
