
from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import QApplication

# -----------------------------
#   Dark Theme
# -----------------------------
def apply_dark_theme(app: QApplication):
    dark_palette = QPalette()

    dark_color = QColor(45, 45, 45)
    nearly_black = QColor(30, 30, 30)
    light_gray = QColor(200, 200, 200)
    white = QColor(255, 255, 255)
    accent = QColor(42, 130, 218)

    dark_palette.setColor(QPalette.Window, dark_color)
    dark_palette.setColor(QPalette.WindowText, white)
    dark_palette.setColor(QPalette.Base, nearly_black)
    dark_palette.setColor(QPalette.AlternateBase, dark_color)
    dark_palette.setColor(QPalette.Text, white)
    dark_palette.setColor(QPalette.Button, dark_color)
    dark_palette.setColor(QPalette.ButtonText, white)
    dark_palette.setColor(QPalette.Highlight, accent)
    dark_palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))

    app.setPalette(dark_palette)

    app.setStyleSheet("""
        QWidget {
            color: #FFFFFF;
            background-color: #2D2D2D;
        }
        QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox {
            background-color: #1E1E1E;
            border: 1px solid #555;
            color: #FFFFFF;
        }
        QPushButton {
            background-color: #3C3C3C;
            border: 1px solid #555;
            padding: 5px;
        }
        QPushButton:hover {
            background-color: #505050;
        }
        QTableWidget, QTableView {
            background-color: #1E1E1E;
            alternate-background-color: #2A2A2A;
            gridline-color: #444;
            color: #FFFFFF;
        }
        QHeaderView::section {
            background-color: #3C3C3C;
            color: white;
            padding: 4px;
            border: 1px solid #555;
        }
        QListWidget {
            background-color: #2D2D2D;
            color: #FFFFFF;
        }
        /* Tabs */
        QTabWidget::pane {
            border: 1px solid #555;
            background-color: #2D2D2D;
        }
        QTabBar::tab {
            background-color: #3C3C3C;
            color: #FFFFFF;
            padding: 6px 10px;
            border: 1px solid #555;
            border-bottom: none;
            margin-right: 1px;
        }
        QTabBar::tab:selected {
            background-color: #2D2D2D;
        }
        QTabBar::tab:hover {
            background-color: #505050;
        }
    """)


# -----------------------------
#   Light Theme
# -----------------------------
def apply_light_theme(app: QApplication):
    light_palette = QPalette()

    light_palette.setColor(QPalette.Window, QColor(240, 240, 240))
    light_palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
    light_palette.setColor(QPalette.Base, QColor(255, 255, 255))
    light_palette.setColor(QPalette.AlternateBase, QColor(245, 245, 245))
    light_palette.setColor(QPalette.Text, QColor(0, 0, 0))
    light_palette.setColor(QPalette.Button, QColor(240, 240, 240))
    light_palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))
    light_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    light_palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))

    app.setPalette(light_palette)

    app.setStyleSheet("""
        QWidget {
            color: #000000;
            background-color: #F0F0F0;
        }
        QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox {
            background-color: #FFFFFF;
            border: 1px solid #AAA;
            color: #000000;
        }
        QPushButton {
            background-color: #E0E0E0;
            border: 1px solid #888;
            padding: 5px;
        }
        QPushButton:hover {
            background-color: #CCCCCC;
        }
        QTableWidget, QTableView {
            background-color: #FFFFFF;
            alternate-background-color: #F0F0F0;
            gridline-color: #AAA;
            color: #000000;
        }
        QHeaderView::section {
            background-color: #E0E0E0;
            color: black;
            padding: 4px;
            border: 1px solid #AAA;
        }
        QListWidget {
            background-color: #FFFFFF;
            color: #000000;
        }
        /* Tabs */
        QTabWidget::pane {
            border: 1px solid #AAA;
            background-color: #F0F0F0;
        }
        QTabBar::tab {
            background-color: #E0E0E0;
            color: #000000;
            padding: 6px 10px;
            border: 1px solid #AAA;
            border-bottom: none;
            margin-right: 1px;
        }
        QTabBar::tab:selected {
            background-color: #FFFFFF;
        }
        QTabBar::tab:hover {
            background-color: #DDDDDD;
        }
    """)
