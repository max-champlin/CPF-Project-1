import sys
from PyQt5.QtWidgets import QApplication

from ui_main_window import MainWindow
from theme import apply_dark_theme


def main():
    app = QApplication(sys.argv)

    # Start the app in dark mode by default
    apply_dark_theme(app)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
