from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QScrollArea)
from PyQt6.QtCore import Qt

class SidebarWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("sidebar")
        self.setFixedWidth(288)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)
        
        # Header
        header_layout = QHBoxLayout()
        
        header_info = QVBoxLayout()
        header_info.setSpacing(4)
        
        title = QLabel("MATH CONTENT")
        title.setObjectName("sidebar_title")
        
        subtitle = QLabel("Hierarchical Tags")
        subtitle.setObjectName("sidebar_subtitle")
        
        header_info.addWidget(title)
        header_info.addWidget(subtitle)
        
        header_layout.addLayout(header_info)
        header_layout.addStretch()
        
        expand_btn = QLabel("⋮")
        expand_btn.setObjectName("sidebar_icon")
        header_layout.addWidget(expand_btn)
        
        layout.addLayout(header_layout)
        
        # Navigation tree
        tree = self.create_tree()
        layout.addWidget(tree, 1)
        
        # Export button
        export_btn = QPushButton("📄 Export to PDF")
        export_btn.setObjectName("export_button")
        export_btn.setMinimumHeight(40)
        
        layout.addWidget(export_btn)
    
    def create_tree(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        tree_widget = QWidget()
        tree_layout = QVBoxLayout(tree_widget)
        tree_layout.setSpacing(4)
        tree_layout.setContentsMargins(0, 0, 0, 0)
        
        # Active item (Algebra)
        algebra_item = QFrame()
        algebra_item.setObjectName("tree_item_active")
        algebra_layout = QHBoxLayout(algebra_item)
        algebra_layout.setContentsMargins(12, 8, 12, 8)
        algebra_layout.setSpacing(8)
        
        algebra_arrow = QLabel("▼")
        algebra_icon = QLabel("≈")
        algebra_text = QLabel("1. Algebra")
        algebra_text.setObjectName("tree_item_text")
        
        algebra_layout.addWidget(algebra_arrow)
        algebra_layout.addWidget(algebra_icon)
        algebra_layout.addWidget(algebra_text)
        algebra_layout.addStretch()
        
        tree_layout.addWidget(algebra_item)
        
        # Sub-items
        sub_layout = QVBoxLayout()
        sub_layout.setSpacing(4)
        sub_layout.setContentsMargins(24, 0, 0, 8)
        
        # Functions (active)
        functions_item = QFrame()
        functions_item.setObjectName("tree_subitem_active")
        functions_layout = QHBoxLayout(functions_item)
        functions_layout.setContentsMargins(12, 6, 12, 6)
        
        functions_text = QLabel("1.1 Functions")
        functions_text.setObjectName("tree_subitem_text")
        functions_layout.addWidget(functions_text)
        
        sub_layout.addWidget(functions_item)
        
        # Other sub-items
        for name in ["1.2 Quadratic Equations", "1.3 Logarithms"]:
            item = QFrame()
            item.setObjectName("tree_subitem")
            item_layout = QHBoxLayout(item)
            item_layout.setContentsMargins(12, 6, 12, 6)
            
            text = QLabel(name)
            text.setObjectName("tree_subitem_text_inactive")
            item_layout.addWidget(text)
            
            sub_layout.addWidget(item)
        
        tree_layout.addLayout(sub_layout)
        
        # Other main items
        items = [
            ("▶", "▦", "2. Geometry"),
            ("▶", "📈", "3. Calculus"),
            ("▶", "📊", "4. Statistics"),
            ("▶", "△", "5. Trigonometry"),
        ]
        
        for arrow, icon, text in items:
            item = QFrame()
            item.setObjectName("tree_item")
            item_layout = QHBoxLayout(item)
            item_layout.setContentsMargins(12, 8, 12, 8)
            item_layout.setSpacing(8)
            
            arrow_label = QLabel(arrow)
            icon_label = QLabel(icon)
            text_label = QLabel(text)
            text_label.setObjectName("tree_item_text_inactive")
            
            item_layout.addWidget(arrow_label)
            item_layout.addWidget(icon_label)
            item_layout.addWidget(text_label)
            item_layout.addStretch()
            
            tree_layout.addWidget(item)
        
        tree_layout.addStretch()
        
        scroll.setWidget(tree_widget)
        return scroll
