from PyQt5.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QListWidget,
    QPushButton,
    QStackedWidget,
    QApplication,
)
from PyQt5.QtGui import QIcon

from ui_pages import (
    DashboardPage,
    SpoolsPage,
    PartsPage,
    ProductsPage,
    PrintJobsPage,
    InvoicesPage,
    AnalyticsPage,
    CreditsPage,
)
from theme import apply_dark_theme, apply_light_theme


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PrintForge Desktop")
        self.setMinimumSize(1200, 750)

        self.setWindowIcon(QIcon("assets/cpf_logo.png"))

        main_layout = QHBoxLayout(self)
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        # Sidebar
        self.nav = QListWidget()
        self.nav.addItems(
            [
                "Dashboard",
                "Spools",
                "Parts",
                "Products",
                "Print Jobs",
                "Invoices",
                "Analytics",
                "Credits",
            ]
        )
        self.nav.currentRowChanged.connect(self.change_page)
        self.nav.setFixedWidth(200)

        # Pages
        self.pages = QStackedWidget()
        self.dashboard_page = DashboardPage()
        self.spools_page = SpoolsPage()
        self.parts_page = PartsPage()
        self.products_page = ProductsPage()
        self.print_jobs_page = PrintJobsPage()
        self.invoices_page = InvoicesPage()
        self.analytics_page = AnalyticsPage()
        self.credits_page = CreditsPage()

        self.pages.addWidget(self.dashboard_page)
        self.pages.addWidget(self.spools_page)
        self.pages.addWidget(self.parts_page)
        self.pages.addWidget(self.products_page)
        self.pages.addWidget(self.print_jobs_page)
        self.pages.addWidget(self.invoices_page)
        self.pages.addWidget(self.analytics_page)
        self.pages.addWidget(self.credits_page)

        # Theme toggle
        self.theme_button = QPushButton("Switch to Light Theme")
        self.theme_button.clicked.connect(self.toggle_theme)
        self.is_dark = True  # start in dark (set in main.py)

        left_layout.addWidget(self.nav)
        left_layout.addWidget(self.theme_button)

        right_layout.addWidget(self.pages)

        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)

        self.nav.setCurrentRow(0)

    def change_page(self, index: int):
        self.pages.setCurrentIndex(index)
        current = self.pages.currentWidget()

        # Let pages refresh themselves when you switch to them
        if hasattr(current, "refresh_data"):
            try:
                current.refresh_data()
            except Exception:
                pass

        if hasattr(current, "refresh_table"):
            try:
                current.refresh_table()
            except Exception:
                pass

        if hasattr(current, "refresh_spools"):
            try:
                current.refresh_spools()
            except Exception:
                pass

    def toggle_theme(self):
        app = QApplication.instance()
        if app is None:
            return

        if self.is_dark:
            apply_light_theme(app)
            self.theme_button.setText("Switch to Dark Theme")
            self.is_dark = False
        else:
            apply_dark_theme(app)
            self.theme_button.setText("Switch to Light Theme")
            self.is_dark = True