import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QFontDatabase
from dashboard_window import DashboardWindow

def main():
    app = QApplication(sys.argv)
    
    # Set application-wide font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # Apply stylesheet
    with open("styles.qss", "r") as f:
        app.setStyleSheet(f.read())
    
    window = DashboardWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
