from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QFrame,
    QComboBox,
    QDoubleSpinBox,
    QPushButton,
    QTabWidget,
    QDialog,
    QLineEdit,
    QFormLayout,
    QDialogButtonBox,
    QMessageBox,
    QAbstractItemView,
    QPlainTextEdit,)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

import db

# Optional charts (requires matplotlib)
try:
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    HAS_MPL = True
except ImportError:
    HAS_MPL = False


# ======================================================================
# DASHBOARD
# ======================================================================
class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout(self)

        # ----- Header with logo ----------------------------------------------
        header_layout = QHBoxLayout()

        title = QLabel("Dashboard")
        title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        title.setStyleSheet("font-size: 20pt; font-weight: bold; margin-bottom: 8px;")

        logo_label = QLabel()
        pix = QPixmap("assets/cpf_logo.png")
        if not pix.isNull():
            logo_label.setPixmap(
                pix.scaled(72, 72, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        logo_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(logo_label)

        main_layout.addLayout(header_layout)

        # ----- Top stat cards -------------------------------------------------
        stats_layout = QHBoxLayout()

        self.total_spools_card, self.total_spools_value = self._create_stat_card(
            "Total Spools"
        )
        self.total_weight_card, self.total_weight_value = self._create_stat_card(
            "Total Filament"
        )
        self.total_value_card, self.total_value_value = self._create_stat_card(
            "Total Spool Value"
        )

        stats_layout.addWidget(self.total_spools_card)
        stats_layout.addWidget(self.total_weight_card)
        stats_layout.addWidget(self.total_value_card)

        main_layout.addLayout(stats_layout)

        # ----- Chart (if matplotlib is available) ----------------------------
        if HAS_MPL:
            chart_label = QLabel("Filament by Brand (kg)")
            chart_label.setStyleSheet("font-weight: bold; margin-top: 16px;")
            main_layout.addWidget(chart_label)

            self.figure = Figure(figsize=(4, 2))
            self.canvas = FigureCanvas(self.figure)
            main_layout.addWidget(self.canvas)
        else:
            info = QLabel(
                "Install 'matplotlib' to see charts:\n"
                "pip install matplotlib"
            )
            info.setAlignment(Qt.AlignLeft)
            info.setStyleSheet("margin-top: 16px; font-style: italic;")
            main_layout.addWidget(info)

        # ----- Top spools table ----------------------------------------------
        table_title = QLabel("Top Spools by Remaining Value")
        table_title.setStyleSheet("font-weight: bold; margin-top: 16px;")
        main_layout.addWidget(table_title)

        self.top_spools_table = QTableWidget()
        self.top_spools_table.setColumnCount(5)
        self.top_spools_table.setHorizontalHeaderLabels(
            ["Brand", "Color", "Remaining (g)", "Cost/G", "Est. Value"]
        )
        self.top_spools_table.horizontalHeader().setStretchLastSection(True)
        main_layout.addWidget(self.top_spools_table)

        self.refresh_data()

    def _create_stat_card(self, title: str):
        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card.setFrameShadow(QFrame.Raised)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 8, 12, 8)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 9pt; font-weight: bold;")
        value_label = QLabel("--")
        value_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        value_label.setStyleSheet("font-size: 16pt; font-weight: bold;")

        card_layout.addWidget(title_label)
        card_layout.addWidget(value_label)

        return card, value_label

    def refresh_data(self):
        spools = db.get_all_spools()

        if not spools:
            self.total_spools_value.setText("0")
            self.total_weight_value.setText("0.00 kg")
            self.total_value_value.setText("$0.00")

            self.top_spools_table.setRowCount(0)

            if HAS_MPL:
                self.figure.clear()
                self.canvas.draw()
            return

        total_spools = len(spools)
        total_weight_g = sum(row[4] for row in spools)
        total_weight_kg = total_weight_g / 1000.0
        total_value = sum(row[3] * row[4] for row in spools)

        self.total_spools_value.setText(str(total_spools))
        self.total_weight_value.setText(f"{total_weight_kg:.2f} kg")
        self.total_value_value.setText(f"${total_value:,.2f}")

        enriched = []
        for _, brand, color, cost_per_g, weight_g in spools:
            value = cost_per_g * weight_g
            enriched.append((brand, color, weight_g, cost_per_g, value))

        enriched.sort(key=lambda x: x[-1], reverse=True)
        top_n = enriched[:10]

        self.top_spools_table.setRowCount(len(top_n))
        for row_idx, (brand, color, weight_g, cost_per_g, value) in enumerate(top_n):
            for col_idx, val in enumerate(
                [
                    brand,
                    color,
                    f"{weight_g:.0f}",
                    f"{cost_per_g:.4f}",
                    f"{value:,.2f}",
                ]
            ):
                item = QTableWidgetItem(str(val))
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                self.top_spools_table.setItem(row_idx, col_idx, item)

        if HAS_MPL:
            self._update_brand_chart(spools)

    def _update_brand_chart(self, spools):
        brand_totals = {}
        for _, brand, _, _, weight_g in spools:
            if not brand:
                continue
            brand_totals.setdefault(brand, 0.0)
            brand_totals[brand] += weight_g / 1000.0

        if not brand_totals:
            self.figure.clear()
            self.canvas.draw()
            return

        sorted_items = sorted(
            brand_totals.items(), key=lambda kv: kv[1], reverse=True
        )
        top_items = sorted_items[:5]

        names = [name for name, _ in top_items]
        values = [val for _, val in top_items]

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.bar(names, values)
        ax.set_ylabel("kg remaining")
        ax.set_xlabel("Brand")
        ax.set_title("Filament by Brand (kg)")
        ax.tick_params(axis="x", rotation=30)

        self.figure.tight_layout()
        self.canvas.draw()


# ======================================================================
# SPOOL EDITOR DIALOG
# ======================================================================
class SpoolEditorDialog(QDialog):
    def __init__(self, parent=None, spool_row=None):
        super().__init__(parent)

        self.setWindowTitle("Edit Spool" if spool_row is not None else "Add Spool")

        main_layout = QVBoxLayout(self)
        form = QFormLayout()

        self.brand_edit = QLineEdit()
        self.spool_type_edit = QLineEdit()
        self.color_edit = QLineEdit()

        self.cost_per_kg_spin = QDoubleSpinBox()
        self.cost_per_kg_spin.setRange(0.0, 10000.0)
        self.cost_per_kg_spin.setDecimals(2)
        self.cost_per_kg_spin.setSuffix(" /kg")

        self.current_weight_spin = QDoubleSpinBox()
        self.current_weight_spin.setRange(0.0, 100000.0)
        self.current_weight_spin.setDecimals(1)
        self.current_weight_spin.setSuffix(" g")

        self.empty_weight_spin = QDoubleSpinBox()
        self.empty_weight_spin.setRange(0.0, 100000.0)
        self.empty_weight_spin.setDecimals(1)
        self.empty_weight_spin.setSuffix(" g")

        form.addRow("Brand:", self.brand_edit)
        form.addRow("Spool type:", self.spool_type_edit)
        form.addRow("Color:", self.color_edit)
        form.addRow("Cost per kg:", self.cost_per_kg_spin)
        form.addRow("Current weight:", self.current_weight_spin)
        form.addRow("Empty spool weight:", self.empty_weight_spin)

        main_layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

        if spool_row is not None:
            self.brand_edit.setText(spool_row["brand"] or "")
            self.spool_type_edit.setText(spool_row["spool_type"] or "")
            self.color_edit.setText(spool_row["color"] or "")

            self.cost_per_kg_spin.setValue(float(spool_row["cost_per_kg"] or 0.0))
            self.current_weight_spin.setValue(float(spool_row["current_weight_g"] or 0.0))
            self.empty_weight_spin.setValue(float(spool_row["weight_no_spool_g"] or 0.0))

    def get_values(self):
        return (
            self.brand_edit.text().strip(),
            self.spool_type_edit.text().strip(),
            self.color_edit.text().strip(),
            float(self.cost_per_kg_spin.value()),
            float(self.current_weight_spin.value()),
            float(self.empty_weight_spin.value()),
        )


# ======================================================================
# SPOOLS PAGE – TABLE + CRUD BUTTONS
# ======================================================================
class SpoolsPage(QWidget):
    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout(self)

        title = QLabel("Spools")
        title.setStyleSheet("font-size: 16pt; font-weight: bold;")
        main_layout.addWidget(title)

        buttons_layout = QHBoxLayout()
        self.add_button = QPushButton("Add")
        self.edit_button = QPushButton("Edit Selected")
        self.delete_button = QPushButton("Delete Selected")
        self.refresh_button = QPushButton("Refresh")

        self.add_button.clicked.connect(self.add_spool)
        self.edit_button.clicked.connect(self.edit_spool)
        self.delete_button.clicked.connect(self.delete_spool)
        self.refresh_button.clicked.connect(self.refresh_table)

        buttons_layout.addWidget(self.add_button)
        buttons_layout.addWidget(self.edit_button)
        buttons_layout.addWidget(self.delete_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.refresh_button)

        main_layout.addLayout(buttons_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Brand", "Type", "Color", "Cost/kg", "Cost/G", "Remaining (g)"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        main_layout.addWidget(self.table)

        self.refresh_table()

    def refresh_table(self):
        conn = db.get_connection()
        rows = conn.execute("SELECT * FROM spools ORDER BY id").fetchall()
        conn.close()

        self.table.setRowCount(len(rows))

        for row_idx, r in enumerate(rows):
            data = [
                r["id"],
                r["brand"],
                r["spool_type"],
                r["color"],
                f"{(r['cost_per_kg'] or 0):.2f}",
                f"{(r['cost_per_g'] or 0):.4f}",
                f"{(r['current_weight_g'] or 0):.0f}",
            ]
            for col_idx, value in enumerate(data):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                self.table.setItem(row_idx, col_idx, item)

        self.table.resizeColumnsToContents()

    def _get_selected_spool_id(self):
        selected = self.table.selectedItems()
        if not selected:
            return None
        row = selected[0].row()
        item = self.table.item(row, 0)
        try:
            return int(item.text())
        except (TypeError, ValueError):
            return None

    def add_spool(self):
        dlg = SpoolEditorDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            brand, spool_type, color, cost_per_kg, current_weight, empty_weight = (
                dlg.get_values()
            )
            if not brand:
                QMessageBox.warning(
                    self, "Missing brand", "Please enter at least a brand name."
                )
                return
            db.create_spool(
                brand, spool_type, color, cost_per_kg, current_weight, empty_weight
            )
            self.refresh_table()

    def edit_spool(self):
        spool_id = self._get_selected_spool_id()
        if spool_id is None:
            QMessageBox.information(
                self, "No selection", "Select a spool to edit."
            )
            return

        spool_row = db.get_spool_by_id(spool_id)
        if spool_row is None:
            QMessageBox.warning(
                self, "Not found", "Selected spool no longer exists."
            )
            self.refresh_table()
            return

        dlg = SpoolEditorDialog(self, spool_row=spool_row)
        if dlg.exec_() == QDialog.Accepted:
            brand, spool_type, color, cost_per_kg, current_weight, empty_weight = (
                dlg.get_values()
            )
            if not brand:
                QMessageBox.warning(
                    self, "Missing brand", "Please enter at least a brand name."
                )
                return
            db.update_spool(
                spool_id, brand, spool_type, color, cost_per_kg, current_weight, empty_weight
            )
            self.refresh_table()

    def delete_spool(self):
        spool_id = self._get_selected_spool_id()
        if spool_id is None:
            QMessageBox.information(
                self, "No selection", "Select a spool to delete."
            )
            return

        reply = QMessageBox.question(
            self,
            "Delete spool",
            "Are you sure you want to delete this spool?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        db.delete_spool(spool_id)
        self.refresh_table()


# ======================================================================
# PARTS EDITOR DIALOG
# ======================================================================
class PartEditorDialog(QDialog):
    def __init__(self, parent=None, part_row=None):
        super().__init__(parent)

        self.setWindowTitle("Edit Part" if part_row is not None else "Add Part")

        main_layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_edit = QLineEdit()
        self.category_edit = QLineEdit()
        self.unit_edit = QLineEdit()

        self.unit_cost_spin = QDoubleSpinBox()
        self.unit_cost_spin.setRange(0.0, 10000.0)
        self.unit_cost_spin.setDecimals(4)
        self.unit_cost_spin.setPrefix("$ ")

        self.quantity_spin = QDoubleSpinBox()
        self.quantity_spin.setRange(0.0, 1000000.0)
        self.quantity_spin.setDecimals(2)

        self.notes_edit = QPlainTextEdit()

        form.addRow("Name:", self.name_edit)
        form.addRow("Category:", self.category_edit)
        form.addRow("Unit (pcs, set, etc.):", self.unit_edit)
        form.addRow("Unit cost:", self.unit_cost_spin)
        form.addRow("Quantity on hand:", self.quantity_spin)
        form.addRow("Notes:", self.notes_edit)

        main_layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

        if part_row is not None:
            self.name_edit.setText(part_row["name"] or "")
            self.category_edit.setText(part_row["category"] or "")
            self.unit_edit.setText(part_row["unit"] or "")
            self.unit_cost_spin.setValue(float(part_row["unit_cost"] or 0.0))
            self.quantity_spin.setValue(float(part_row["quantity_on_hand"] or 0.0))
            self.notes_edit.setPlainText(part_row["notes"] or "")

    def get_values(self):
        return (
            self.name_edit.text().strip(),
            self.category_edit.text().strip(),
            self.unit_edit.text().strip(),
            float(self.unit_cost_spin.value()),
            float(self.quantity_spin.value()),
            self.notes_edit.toPlainText().strip(),
        )


# ======================================================================
# PARTS PAGE – TABLE + CRUD
# ======================================================================
class PartsPage(QWidget):
    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout(self)

        title = QLabel("Parts (Non-Printed)")
        title.setStyleSheet("font-size: 16pt; font-weight: bold;")
        main_layout.addWidget(title)

        buttons_layout = QHBoxLayout()
        self.add_button = QPushButton("Add")
        self.edit_button = QPushButton("Edit Selected")
        self.delete_button = QPushButton("Delete Selected")
        self.refresh_button = QPushButton("Refresh")

        self.add_button.clicked.connect(self.add_part)
        self.edit_button.clicked.connect(self.edit_part)
        self.delete_button.clicked.connect(self.delete_part)
        self.refresh_button.clicked.connect(self.refresh_table)

        buttons_layout.addWidget(self.add_button)
        buttons_layout.addWidget(self.edit_button)
        buttons_layout.addWidget(self.delete_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.refresh_button)

        main_layout.addLayout(buttons_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            [
                "ID",
                "Name",
                "Category",
                "Unit",
                "Qty on hand",
                "Unit cost",
                "Total value",
            ]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        main_layout.addWidget(self.table)

        self.refresh_table()

    def refresh_table(self):
        rows = db.get_all_parts()
        self.table.setRowCount(len(rows))

        for row_idx, r in enumerate(rows):
            unit_cost = r["unit_cost"] or 0.0
            qty = r["quantity_on_hand"] or 0.0
            total_value = unit_cost * qty

            data = [
                r["id"],
                r["name"],
                r["category"],
                r["unit"],
                f"{qty:.2f}",
                f"{unit_cost:.4f}",
                f"{total_value:,.2f}",
            ]
            for col_idx, value in enumerate(data):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                self.table.setItem(row_idx, col_idx, item)

        self.table.resizeColumnsToContents()

    def _get_selected_part_id(self):
        selected = self.table.selectedItems()
        if not selected:
            return None
        row = selected[0].row()
        item = self.table.item(row, 0)
        try:
            return int(item.text())
        except (TypeError, ValueError):
            return None

    def add_part(self):
        dlg = PartEditorDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            name, category, unit, unit_cost, qty, notes = dlg.get_values()
            if not name:
                QMessageBox.warning(
                    self, "Missing name", "Please enter at least a part name."
                )
                return
            db.create_part(name, category, unit, unit_cost, qty, notes)
            self.refresh_table()

    def edit_part(self):
        part_id = self._get_selected_part_id()
        if part_id is None:
            QMessageBox.information(
                self, "No selection", "Select a part to edit."
            )
            return

        part_row = db.get_part_by_id(part_id)
        if part_row is None:
            QMessageBox.warning(
                self, "Not found", "Selected part no longer exists."
            )
            self.refresh_table()
            return

        dlg = PartEditorDialog(self, part_row=part_row)
        if dlg.exec_() == QDialog.Accepted:
            name, category, unit, unit_cost, qty, notes = dlg.get_values()
            if not name:
                QMessageBox.warning(
                    self, "Missing name", "Please enter at least a part name."
                )
                return
            db.update_part(part_id, name, category, unit, unit_cost, qty, notes)
            self.refresh_table()

    def delete_part(self):
        part_id = self._get_selected_part_id()
        if part_id is None:
            QMessageBox.information(
                self, "No selection", "Select a part to delete."
            )
            return

        reply = QMessageBox.question(
            self,
            "Delete part",
            "Are you sure you want to delete this part?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        db.delete_part(part_id)
        self.refresh_table()


# ======================================================================
# PRODUCTS PAGE (simple view for now)
# ======================================================================
class ProductsPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        title = QLabel("Products")
        title.setStyleSheet("font-size: 16pt; font-weight: bold;")
        layout.addWidget(title)

        table = QTableWidget()
        data = db.get_all_products()

        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["ID", "Name"])
        table.setRowCount(len(data))

        for row_idx, row in enumerate(data):
            for col_idx, value in enumerate(row):
                table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))

        table.horizontalHeader().setStretchLastSection(True)

        layout.addWidget(table)
        self.setLayout(layout)


# ======================================================================
# CAN I PRINT THIS? – QUICK CALCULATOR
# ======================================================================
class CanIPrintPage(QWidget):
    """
    Spool-centric helper page.

    - Original behaviour: given a spool and required weight, tell you if it's enough.
    - New behaviour: optionally pick a product/variant and see how many units
      you can make from the selected spool, then send that into the By Product tab.
    """
    def __init__(self, send_to_by_product_callback=None):
        super().__init__()

        self._send_to_by_product_cb = send_to_by_product_callback

        main_layout = QVBoxLayout(self)

        # Title
        title = QLabel("Can I Print This?")
        title.setStyleSheet("font-size: 16pt; font-weight: bold;")
        main_layout.addWidget(title)

        # ------------------------------------------------
        # Basic "is this spool enough?" calculator
        # ------------------------------------------------
        form_layout = QVBoxLayout()

        # Spool row
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Spool:"))
        self.spool_combo = QComboBox()
        row1.addWidget(self.spool_combo, stretch=1)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setToolTip("Reload spools from the database")
        self.refresh_button.clicked.connect(self.refresh_spools)
        row1.addWidget(self.refresh_button)

        form_layout.addLayout(row1)

        # Required weight + margin
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Required weight:"))
        self.weight_input = QDoubleSpinBox()
        self.weight_input.setRange(0.0, 100000.0)
        self.weight_input.setDecimals(1)
        self.weight_input.setSuffix(" g")
        self.weight_input.setValue(100.0)
        row2.addWidget(self.weight_input)

        row2.addWidget(QLabel("Safety margin:"))
        self.margin_input = QDoubleSpinBox()
        self.margin_input.setRange(0.0, 100.0)
        self.margin_input.setDecimals(1)
        self.margin_input.setSuffix(" %")
        self.margin_input.setValue(10.0)
        row2.addWidget(self.margin_input)

        form_layout.addLayout(row2)

        # Check button
        row3 = QHBoxLayout()
        self.check_button = QPushButton("Check spool")
        self.check_button.clicked.connect(self.check_print)
        row3.addWidget(self.check_button)
        row3.addStretch()
        form_layout.addLayout(row3)

        main_layout.addLayout(form_layout)

        # Result label for spool check
        self.result_label = QLabel("")
        self.result_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.result_label.setWordWrap(True)
        self.result_label.setStyleSheet("margin-top: 12px;")
        main_layout.addWidget(self.result_label)

        # ------------------------------------------------
        # New: product/variant view for this spool
        # ------------------------------------------------
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(divider)

        sub_title = QLabel("Plan by Product using this spool")
        sub_title.setStyleSheet("font-weight: bold; margin-top: 8px;")
        main_layout.addWidget(sub_title)

        # Product + variant row
        prod_row = QHBoxLayout()
        prod_row.addWidget(QLabel("Product:"))
        self.spool_product_combo = QComboBox()
        prod_row.addWidget(self.spool_product_combo)

        prod_row.addWidget(QLabel("Variant:"))
        self.spool_variant_combo = QComboBox()
        prod_row.addWidget(self.spool_variant_combo)

        main_layout.addLayout(prod_row)

        # Max units + actions
        actions_row = QHBoxLayout()
        self.max_units_label = QLabel("Max units from this spool: —")
        actions_row.addWidget(self.max_units_label)
        actions_row.addStretch()

        self.compute_units_button = QPushButton("Compute Max Units")
        self.compute_units_button.setToolTip(
            "Use the BOM + selected spool to estimate how many units you can print."
        )
        self.compute_units_button.clicked.connect(self._on_compute_max_units)
        actions_row.addWidget(self.compute_units_button)

        self.send_to_by_product_button = QPushButton("Send to By Product")
        self.send_to_by_product_button.setToolTip(
            "Send the max units for the selected product/variant into the By Product tab."
        )
        if self._send_to_by_product_cb is None:
            self.send_to_by_product_button.setEnabled(False)
        self.send_to_by_product_button.clicked.connect(self._on_send_to_by_product)
        actions_row.addWidget(self.send_to_by_product_button)

        main_layout.addLayout(actions_row)

        # Caches
        self.spools_cache = []
        self.spool_products = []
        self.spool_variants = []

        # Wiring
        self.spool_product_combo.currentIndexChanged.connect(
            self._on_spool_product_changed
        )

        # Initial data
        self.refresh_spools()
        self._refresh_products_for_spool()

    # ------------------------------------------------
    # Data loading
    # ------------------------------------------------
    def refresh_spools(self):
        """Load spools into the spool combo box."""
        self.spools_cache = db.get_all_spools()
        self.spool_combo.clear()

        if not self.spools_cache:
            self.spool_combo.addItem("No spools available")
            self.spool_combo.setEnabled(False)
            self.result_label.setText(
                "No spools in the database. Run the Excel import to add spools."
            )
            return

        self.spool_combo.setEnabled(True)
        for sid, brand, color, cost_per_g, weight_g in self.spools_cache:
            label = f"{brand} — {color} ({weight_g:.0f} g left)"
            self.spool_combo.addItem(label, sid)

    def _refresh_products_for_spool(self):
        """Load products/variants for the product-on-spool controls."""
        self.spool_products = db.get_all_products()
        self.spool_product_combo.blockSignals(True)
        self.spool_product_combo.clear()

        if not self.spool_products:
            self.spool_product_combo.addItem("No products in database", None)
            self.spool_variant_combo.clear()
            self.spool_variant_combo.addItem("—", None)
            self.spool_product_combo.blockSignals(False)
            return

        for pid, name in self.spool_products:
            self.spool_product_combo.addItem(name, pid)

        self.spool_product_combo.blockSignals(False)
        self._on_spool_product_changed(self.spool_product_combo.currentIndex())

    def _on_spool_product_changed(self, index):
        """Refresh variants when the product selection changes (spool section)."""
        self.spool_variants = []
        self.spool_variant_combo.clear()

        pid = self.spool_product_combo.itemData(index)
        if pid is None:
            self.spool_variant_combo.addItem("—", None)
            return

        try:
            product, variants = db.get_product_detail(pid)
        except Exception:
            self.spool_variant_combo.addItem("—", None)
            return

        self.spool_variants = list(variants)
        self.spool_variant_combo.addItem("No specific variant", None)
        for row in self.spool_variants:
            label = row["variant_name"] or f"Variant #{row['id']}"
            if row["color"]:
                label = f"{label} ({row['color']})"
            self.spool_variant_combo.addItem(label, row["id"])

    # ------------------------------------------------
    # Behaviour
    # ------------------------------------------------
    def check_print(self):
        """Original spool check: is this spool enough for the required weight?"""
        if not self.spools_cache:
            self.result_label.setText(
                "No spools in the database. Run the Excel import to add spools."
            )
            return

        idx = self.spool_combo.currentIndex()
        if idx < 0 or idx >= len(self.spools_cache):
            self.result_label.setText("Please select a spool.")
            return

        sid, brand, color, cost_per_g, weight_g = self.spools_cache[idx]

        required = self.weight_input.value()
        margin_pct = self.margin_input.value()

        if required <= 0:
            self.result_label.setText("Enter a required weight greater than 0 g.")
            return

        required_with_margin = required * (1.0 + margin_pct / 100.0)
        cost_per_g = float(cost_per_g or 0.0)
        estimated_cost = required * cost_per_g

        if weight_g >= required_with_margin:
            leftover = weight_g - required_with_margin
            msg = (
                f"<b>Yes</b>, this spool is enough.<br><br>"
                f"<b>Spool:</b> {brand} — {color}<br>"
                f"<b>Available:</b> {weight_g:.0f} g<br>"
                f"<b>Required:</b> {required:.1f} g "
                f"(+{margin_pct:.1f}% margin → {required_with_margin:.1f} g)<br>"
                f"<b>Estimated filament cost:</b> ${estimated_cost:,.2f}<br>"
                f"<b>Estimated leftover after print:</b> {leftover:.1f} g"
            )
        else:
            short = required_with_margin - weight_g
            msg = (
                f"<b>No</b>, this spool is <b>not</b> enough.<br><br>"
                f"<b>Spool:</b> {brand} — {color}<br>"
                f"<b>Available:</b> {weight_g:.0f} g<br>"
                f"<b>Required with margin:</b> {required_with_margin:.1f} g<br>"
                f"You are short by about <b>{short:.1f} g</b>."
            )

        self.result_label.setText(msg)

    def _compute_max_units_internal(self):
        """
        Helper: compute max units from the selected spool for the selected
        product/variant, using the BOM.
        """
        if not self.spools_cache:
            QMessageBox.information(
                self,
                "No spools",
                "There are no spools in the database.",
            )
            return None

        spool_index = self.spool_combo.currentIndex()
        if spool_index < 0 or spool_index >= len(self.spools_cache):
            QMessageBox.information(
                self,
                "No spool selected",
                "Select a spool first.",
            )
            return None

        sid, brand, color, cost_per_g, weight_g = self.spools_cache[spool_index]

        product_index = self.spool_product_combo.currentIndex()
        product_id = self.spool_product_combo.itemData(product_index)
        if product_id is None:
            QMessageBox.information(
                self,
                "No product selected",
                "Select a product to plan from this spool.",
            )
            return None

        variant_index = self.spool_variant_combo.currentIndex()
        variant_id = self.spool_variant_combo.itemData(variant_index)

        try:
            bom_rows = db.get_effective_bom_for_product(product_id, variant_id)
        except Exception as e:
            QMessageBox.warning(
                self,
                "BOM error",
                f"Could not load BOM for this product/variant: {e}",
            )
            return None

        # Sum grams-per-unit for this specific spool in the BOM
        grams_per_unit = 0.0
        for row in bom_rows:
            if row["item_type"] != "filament":
                continue
            if row["spool_id"] != sid:
                continue
            grams = row["grams"] or 0.0
            try:
                grams = float(grams)
            except (TypeError, ValueError):
                grams = 0.0
            if grams > 0:
                grams_per_unit += grams

        if grams_per_unit <= 0.0:
            QMessageBox.information(
                self,
                "No matching filament",
                "The BOM for this product/variant does not use the selected spool.",
            )
            self.max_units_label.setText("Max units from this spool: —")
            return None

        margin_pct = self.margin_input.value()
        grams_per_unit_with_margin = grams_per_unit * (1.0 + margin_pct / 100.0)
        if grams_per_unit_with_margin <= 0.0:
            QMessageBox.information(
                self,
                "Invalid BOM",
                "The grams-per-unit from the BOM is not usable.",
            )
            self.max_units_label.setText("Max units from this spool: —")
            return None

        max_units = int(weight_g // grams_per_unit_with_margin)
        self.max_units_label.setText(
            f"Max units from this spool: {max_units} unit(s) "
            f"(with {margin_pct:.1f}% margin)"
        )

        if max_units <= 0:
            QMessageBox.information(
                self,
                "Spool too small",
                "With the current safety margin, this spool cannot produce a full unit.",
            )
            return None

        return product_id, variant_id, max_units

    def _on_compute_max_units(self):
        """Slot for the 'Compute Max Units' button."""
        self._compute_max_units_internal()

    def _on_send_to_by_product(self):
        """Compute max units and send them into the By Product tab if possible."""
        if self._send_to_by_product_cb is None:
            return

        result = self._compute_max_units_internal()
        if result is None:
            return

        product_id, variant_id, max_units = result
        self._send_to_by_product_cb(product_id, variant_id, max_units)
# ANALYTICS + CREDITS
# ======================================================================

# ======================================================================

# ======================================================================
# PRINT JOBS PAGE (tabs)
# ======================================================================
class PrintJobsPage(QWidget):
    """Print job tools, with tabs.

    - By Product: plan a print job from a product/variant, apply overhead,
      and generate internal/customer invoices.
    - By Spool: reuse the existing "Can I Print This?" calculator.
    """
    def __init__(self):
        super().__init__()

        self.current_products = []
        self.current_variants = []
        self.last_costs = None
        self.last_job_info = None

        main_layout = QVBoxLayout(self)

        title = QLabel("Print Jobs")
        title.setStyleSheet("font-size: 16pt; font-weight: bold;")
        main_layout.addWidget(title)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self._init_by_product_tab()
        self._init_by_spool_tab()

    # -----------------------------
    # By Spool tab (wraps CanIPrintPage)
    # -----------------------------
    def _init_by_spool_tab(self):
        """Use CanIPrintPage as the 'By Spool' tab, with a bridge into By Product."""
        self.by_spool_page = CanIPrintPage(
            send_to_by_product_callback=self._receive_spool_job
        )
        self.tabs.addTab(self.by_spool_page, "By Spool")

    def _receive_spool_job(self, product_id, variant_id, quantity):
        """
        Receive a job suggestion from the By Spool tab and pre-fill
        the By Product tab with product, variant, and quantity.
        """
        # Switch to the By Product tab if it exists
        try:
            by_product_index = self.tabs.indexOf(self.by_product_tab)
        except AttributeError:
            by_product_index = -1

        if by_product_index != -1:
            self.tabs.setCurrentIndex(by_product_index)

        # Ensure products are loaded
        if not getattr(self, "current_products", None):
            try:
                self._refresh_products()
            except Exception:
                pass

        # Select the product
        if product_id is not None:
            for i in range(self.product_combo.count()):
                if self.product_combo.itemData(i) == product_id:
                    self.product_combo.setCurrentIndex(i)
                    break

        # After changing the product, variants should be refreshed
        # Now try to select the variant (if provided)
        if variant_id is not None:
            for i in range(self.variant_combo.count()):
                if self.variant_combo.itemData(i) == variant_id:
                    self.variant_combo.setCurrentIndex(i)
                    break

        # Quantity
        if quantity is not None and quantity > 0:
            try:
                self.quantity_spin.setValue(float(quantity))
            except Exception:
                pass

        # Optionally, auto-fill material cost from BOM
        try:
            self._on_fill_material_from_bom()
        except Exception:
            # If anything goes wrong, just leave the manual material cost field as-is.
            pass# -----------------------------
    # By Product tab (job costing + invoices)
    # -----------------------------
    def _init_by_product_tab(self):
        self.by_product_tab = QWidget()
        layout = QVBoxLayout(self.by_product_tab)

        header = QLabel("By Product – Costing & Invoices")
        header.setStyleSheet("font-weight: bold;")
        layout.addWidget(header)

        # --- Product / variant / quantity row ---
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Product:"))
        self.product_combo = QComboBox()
        row1.addWidget(self.product_combo)

        row1.addWidget(QLabel("Variant:"))
        self.variant_combo = QComboBox()
        row1.addWidget(self.variant_combo)

        row1.addWidget(QLabel("Quantity:"))
        self.quantity_spin = QDoubleSpinBox()
        self.quantity_spin.setRange(1.0, 100000.0)
        self.quantity_spin.setDecimals(0)
        self.quantity_spin.setValue(1.0)
        self.quantity_spin.setSuffix(" units")
        row1.addWidget(self.quantity_spin)

        layout.addLayout(row1)

        # --- Material cost per unit ---
        mat_row = QHBoxLayout()
        mat_row.addWidget(QLabel("Material cost per unit ($, filament + parts):"))
        self.material_cost_spin = QDoubleSpinBox()
        self.material_cost_spin.setRange(0.0, 10000.0)
        self.material_cost_spin.setDecimals(2)
        self.material_cost_spin.setSingleStep(0.10)
        mat_row.addWidget(self.material_cost_spin)

        # New: button to pull cost from BOM
        self.material_from_bom_button = QPushButton("From BOM")
        self.material_from_bom_button.setToolTip(
            "Calculate material cost per unit from the BOM for the selected product/variant."
        )
        mat_row.addWidget(self.material_from_bom_button)

        mat_row.addStretch()
        layout.addLayout(mat_row)

        # --- Overhead panel ---
        overhead_frame = QFrame()
        overhead_frame.setFrameShape(QFrame.StyledPanel)
        overhead_layout = QFormLayout(overhead_frame)

        self.labor_rate_spin = QDoubleSpinBox()
        self.labor_rate_spin.setRange(0.0, 1000.0)
        self.labor_rate_spin.setDecimals(2)
        self.labor_rate_spin.setValue(20.0)

        self.labor_hours_spin = QDoubleSpinBox()
        self.labor_hours_spin.setRange(0.0, 1000.0)
        self.labor_hours_spin.setDecimals(2)
        self.labor_hours_spin.setSingleStep(0.10)
        self.labor_hours_spin.setValue(0.25)  # 15 min

        self.machine_power_spin = QDoubleSpinBox()
        self.machine_power_spin.setRange(0.0, 5000.0)
        self.machine_power_spin.setDecimals(0)
        self.machine_power_spin.setValue(250.0)
        self.machine_power_spin.setSuffix(" W")

        self.print_time_hours_spin = QDoubleSpinBox()
        self.print_time_hours_spin.setRange(0.0, 1000.0)
        self.print_time_hours_spin.setDecimals(2)
        self.print_time_hours_spin.setSingleStep(0.10)
        self.print_time_hours_spin.setValue(1.0)
        self.print_time_hours_spin.setSuffix(" h")

        self.electric_rate_spin = QDoubleSpinBox()
        self.electric_rate_spin.setRange(0.0, 10.0)
        self.electric_rate_spin.setDecimals(4)
        self.electric_rate_spin.setValue(0.15)  # $/kWh

        self.wear_tear_spin = QDoubleSpinBox()
        self.wear_tear_spin.setRange(0.0, 100.0)
        self.wear_tear_spin.setDecimals(2)
        self.wear_tear_spin.setValue(0.10)

        self.extra_overhead_spin = QDoubleSpinBox()
        self.extra_overhead_spin.setRange(0.0, 10000.0)
        self.extra_overhead_spin.setDecimals(2)
        self.extra_overhead_spin.setValue(0.0)

        self.margin_spin = QDoubleSpinBox()
        self.margin_spin.setRange(0.0, 1000.0)
        self.margin_spin.setDecimals(1)
        self.margin_spin.setValue(30.0)
        self.margin_spin.setSuffix(" %")

        overhead_layout.addRow("Labor rate ($/hr):", self.labor_rate_spin)
        overhead_layout.addRow("Labor hours per unit:", self.labor_hours_spin)
        overhead_layout.addRow("Machine power (W):", self.machine_power_spin)
        overhead_layout.addRow("Print time per unit (h):", self.print_time_hours_spin)
        overhead_layout.addRow("Electricity rate ($/kWh):", self.electric_rate_spin)
        overhead_layout.addRow("Wear & tear per unit ($):", self.wear_tear_spin)
        overhead_layout.addRow("Extra overhead per job ($):", self.extra_overhead_spin)
        overhead_layout.addRow("Margin (% markup):", self.margin_spin)

        layout.addWidget(overhead_frame)

        # --- Invoice / job info panel ---
        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.StyledPanel)
        info_layout = QFormLayout(info_frame)

        self.job_name_edit = QLineEdit()
        self.customer_name_edit = QLineEdit()
        self.customer_email_edit = QLineEdit()
        self.notes_edit = QPlainTextEdit()
        self.recommendation_edit = QPlainTextEdit()

        info_layout.addRow("Job name:", self.job_name_edit)
        info_layout.addRow("Customer name:", self.customer_name_edit)
        info_layout.addRow("Customer email:", self.customer_email_edit)
        info_layout.addRow("Notes:", self.notes_edit)
        info_layout.addRow("Recommendations:", self.recommendation_edit)

        layout.addWidget(info_frame)

        # --- Action buttons ---
        btn_row = QHBoxLayout()
        self.calc_button = QPushButton("Calculate Job")
        self.internal_invoice_button = QPushButton("Internal Invoice")
        self.customer_invoice_button = QPushButton("Customer Invoice")

        btn_row.addWidget(self.calc_button)
        btn_row.addStretch()
        btn_row.addWidget(self.internal_invoice_button)
        btn_row.addWidget(self.customer_invoice_button)

        layout.addLayout(btn_row)

        # --- Result area ---
        self.job_result_label = QLabel("")
        self.job_result_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.job_result_label.setWordWrap(True)
        self.job_result_label.setStyleSheet("margin-top: 8px;")
        layout.addWidget(self.job_result_label)

        layout.addStretch()

        # Connections
        self.product_combo.currentIndexChanged.connect(self._on_product_changed)
        self.calc_button.clicked.connect(self._on_calculate_job)
        self.internal_invoice_button.clicked.connect(lambda: self._show_invoice(True))
        self.customer_invoice_button.clicked.connect(lambda: self._show_invoice(False))
        self.material_from_bom_button.clicked.connect(self._on_fill_material_from_bom)

        # Load products from DB
        self._refresh_products()

        self.tabs.addTab(self.by_product_tab, "By Product")

    # -----------------------------
    # Data loading
    # -----------------------------
    def _refresh_products(self):
        """Load products into the combo box from the database."""
        self.current_products = db.get_all_products()
        self.product_combo.blockSignals(True)
        self.product_combo.clear()

        if not self.current_products:
            self.product_combo.addItem("No products in database", None)
            self.variant_combo.clear()
            self.variant_combo.addItem("—", None)
            self.product_combo.blockSignals(False)
            return

        for pid, name in self.current_products:
            self.product_combo.addItem(name, pid)

        self.product_combo.blockSignals(False)
        # Trigger variant loading for the first product
        self._on_product_changed(self.product_combo.currentIndex())

    def _on_product_changed(self, index):
        """Refresh variants when the product selection changes."""
        self.variant_combo.clear()
        self.current_variants = []

        pid = self.product_combo.itemData(index)
        if pid is None:
            self.variant_combo.addItem("—", None)
            return

        try:
            product, variants = db.get_product_detail(pid)
        except Exception:
            self.variant_combo.addItem("—", None)
            return

        self.current_variants = list(variants)
        self.variant_combo.addItem("No specific variant", None)
        for row in self.current_variants:
            label = row["variant_name"] or f"Variant #{row['id']}"
            if row["color"]:
                label = f"{label} ({row['color']})"
            self.variant_combo.addItem(label, row["id"])

    def _on_fill_material_from_bom(self):
        """
        Fill the 'material cost per unit' spinbox using the BOM for the
        currently selected product and variant.
        """
        if not getattr(self, "current_products", None):
            QMessageBox.information(
                self,
                "No products",
                "There are no products in the database. "
                "Run the Excel import or add a product first.",
            )
            return

        product_index = self.product_combo.currentIndex()
        product_id = self.product_combo.itemData(product_index)
        if product_id is None:
            QMessageBox.information(
                self,
                "No product selected",
                "Please select a product first.",
            )
            return

        variant_index = self.variant_combo.currentIndex()
        variant_id = self.variant_combo.itemData(variant_index)

        try:
            total_cost, breakdown = db.calculate_material_cost_per_unit(
                product_id, variant_id
            )
        except Exception as e:
            QMessageBox.warning(
                self,
                "BOM cost error",
                f"Could not calculate material cost from BOM:\n{e}",
            )
            return

        if total_cost <= 0.0:
            QMessageBox.information(
                self,
                "No BOM items",
                "No BOM items were found for this product/variant.\n"
                "Use the BOM editor to add filament and parts first.",
            )
            return

        self.material_cost_spin.setValue(total_cost)
        self.job_result_label.setText(
            f"Material cost per unit from BOM: ${total_cost:.2f}"
        )


    # -----------------------------
    # Cost calculation helpers
    # -----------------------------
    @staticmethod
    def _calculate_job_cost(
        qty,
        material_cost_per_unit,
        labor_hours_per_unit,
        labor_rate_per_hour,
        machine_hours_per_unit,
        machine_power_watts,
        electricity_rate_per_kwh,
        wear_tear_per_unit,
        extra_overhead_per_job,
        margin_percent,
    ):
        """
        Return a dict with a detailed breakdown of material, overhead,
        and final price for a job.
        """
        qty = float(qty) or 0.0
        material_cost_per_unit = float(material_cost_per_unit) or 0.0
        labor_hours_per_unit = float(labor_hours_per_unit) or 0.0
        labor_rate_per_hour = float(labor_rate_per_hour) or 0.0
        machine_hours_per_unit = float(machine_hours_per_unit) or 0.0
        machine_power_watts = float(machine_power_watts) or 0.0
        electricity_rate_per_kwh = float(electricity_rate_per_kwh) or 0.0
        wear_tear_per_unit = float(wear_tear_per_unit) or 0.0
        extra_overhead_per_job = float(extra_overhead_per_job) or 0.0
        margin_percent = float(margin_percent) or 0.0

        material_total = material_cost_per_unit * qty

        labor_cost_per_unit = labor_hours_per_unit * labor_rate_per_hour
        labor_total = labor_cost_per_unit * qty

        kwh_per_unit = machine_hours_per_unit * machine_power_watts / 1000.0
        electricity_cost_per_unit = kwh_per_unit * electricity_rate_per_kwh
        electricity_total = electricity_cost_per_unit * qty

        wear_total = wear_tear_per_unit * qty

        overhead_total = labor_total + electricity_total + wear_total + extra_overhead_per_job
        cost_total_before_margin = material_total + overhead_total
        cost_per_unit_before_margin = cost_total_before_margin / qty if qty > 0 else 0.0

        margin_multiplier = 1.0 + (margin_percent / 100.0)
        price_per_unit = cost_per_unit_before_margin * margin_multiplier
        price_total = price_per_unit * qty

        return {
            "qty": qty,
            "material_total": material_total,
            "labor_total": labor_total,
            "electricity_total": electricity_total,
            "wear_total": wear_total,
            "extra_overhead_per_job": extra_overhead_per_job,
            "overhead_total": overhead_total,
            "cost_total_before_margin": cost_total_before_margin,
            "cost_per_unit_before_margin": cost_per_unit_before_margin,
            "price_per_unit": price_per_unit,
            "price_total": price_total,
            "kwh_per_unit": kwh_per_unit,
        }

    @staticmethod
    def _build_invoice_text(job_info, costs, internal=False):
        """Build a plain-text invoice or internal breakdown."""
        from datetime import datetime

        lines = []
        lines.append("PrintForge Desktop Invoice")
        lines.append("=" * 32)
        lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        if job_info.get("job_name"):
            lines.append(f"Job: {job_info['job_name']}")
        lines.append("")

        if job_info.get("customer_name") or job_info.get("customer_email"):
            lines.append("Bill To:")
            if job_info.get("customer_name"):
                lines.append(f"  {job_info['customer_name']}")
            if job_info.get("customer_email"):
                lines.append(f"  {job_info['customer_email']}")
            lines.append("")

        item_line = job_info.get("product_name", "Unknown product")
        if job_info.get("variant_name"):
            item_line += f" — {job_info['variant_name']}"
        lines.append(f"Item: {item_line}")
        lines.append(f"Quantity: {costs['qty']:.0f}")
        lines.append("")
        lines.append(f"Price per unit: ${costs['price_per_unit']:.2f}")
        lines.append(f"Total price:    ${costs['price_total']:.2f}")
        lines.append("")

        if internal:
            lines.append("Internal cost breakdown:")
            lines.append(f"  Material total:    ${costs['material_total']:.2f}")
            lines.append(f"  Labor total:       ${costs['labor_total']:.2f}")
            lines.append(f"  Electricity total: ${costs['electricity_total']:.2f}")
            lines.append(f"  Wear & tear:       ${costs['wear_total']:.2f}")
            lines.append(f"  Extra overhead:    ${costs['extra_overhead_per_job']:.2f}")
            lines.append("  -------------------------------")
            lines.append(f"  Cost before margin:${costs['cost_total_before_margin']:.2f}")
            lines.append("")

        if job_info.get("notes"):
            lines.append("Notes:")
            lines.append(job_info["notes"])
            lines.append("")

        if job_info.get("recommendation"):
            lines.append("Recommendations:")
            lines.append(job_info["recommendation"])
            lines.append("")

        lines.append("Thank you for your business!")
        return "\n".join(lines)

    # -----------------------------
    # UI callbacks
    # -----------------------------
    def _on_calculate_job(self):
        """Calculate job cost and show a human-friendly summary."""
        if not self.current_products:
            self.job_result_label.setText(
                "No products in the database. Run the Excel import or add a product first."
            )
            return

        idx = self.product_combo.currentIndex()
        product_id = self.product_combo.itemData(idx)
        if product_id is None:
            self.job_result_label.setText("Please select a product.")
            return

        product_name = self.product_combo.currentText()

        v_idx = self.variant_combo.currentIndex()
        variant_id = self.variant_combo.itemData(v_idx)
        variant_name = ""
        if variant_id is not None:
            variant_name = self.variant_combo.currentText()

        qty = int(self.quantity_spin.value())
        if qty <= 0:
            self.job_result_label.setText("Quantity must be at least 1.")
            return

        material_cost_per_unit = self.material_cost_spin.value()
        if material_cost_per_unit < 0:
            material_cost_per_unit = 0.0

        costs = self._calculate_job_cost(
            qty=qty,
            material_cost_per_unit=material_cost_per_unit,
            labor_hours_per_unit=self.labor_hours_spin.value(),
            labor_rate_per_hour=self.labor_rate_spin.value(),
            machine_hours_per_unit=self.print_time_hours_spin.value(),
            machine_power_watts=self.machine_power_spin.value(),
            electricity_rate_per_kwh=self.electric_rate_spin.value(),
            wear_tear_per_unit=self.wear_tear_spin.value(),
            extra_overhead_per_job=self.extra_overhead_spin.value(),
            margin_percent=self.margin_spin.value(),
        )

        self.last_costs = costs
        self.last_job_info = {
            "job_name": self.job_name_edit.text().strip(),
            "customer_name": self.customer_name_edit.text().strip(),
            "customer_email": self.customer_email_edit.text().strip(),
            "product_name": product_name,
            "variant_name": variant_name,
            "notes": self.notes_edit.toPlainText().strip(),
            "recommendation": self.recommendation_edit.toPlainText().strip(),
        }

        html = (
            f"<b>Job summary</b><br>"
            f"Product: {product_name}"
        )
        if variant_name:
            html += f" — {variant_name}"
        html += "<br>"
        html += f"Quantity: {qty:d}<br><br>"

        html += (
            f"<b>Material total:</b> ${costs['material_total']:.2f}<br>"
            f"<b>Labor total:</b> ${costs['labor_total']:.2f}<br>"
            f"<b>Electricity total:</b> ${costs['electricity_total']:.2f}<br>"
            f"<b>Wear &amp; tear:</b> ${costs['wear_total']:.2f}<br>"
            f"<b>Extra overhead (job):</b> ${costs['extra_overhead_per_job']:.2f}<br>"
            f"<b>Overhead total:</b> ${costs['overhead_total']:.2f}<br><br>"
            f"<b>Cost per unit before margin:</b> ${costs['cost_per_unit_before_margin']:.2f}<br>"
            f"<b>Recommended price per unit:</b> ${costs['price_per_unit']:.2f}<br>"
            f"<b>Recommended total price:</b> ${costs['price_total']:.2f}"
        )

        self.job_result_label.setText(html)

    def _show_invoice(self, internal: bool):
        """Show either an internal or customer invoice dialog."""
        if not self.last_costs or not self.last_job_info:
            QMessageBox.information(
                self,
                "No job calculated",
                "Calculate a job first, then generate an invoice.",
            )
            return

        text = self._build_invoice_text(self.last_job_info, self.last_costs, internal=internal)

        dlg = QDialog(self)
        dlg.setWindowTitle("Internal Invoice" if internal else "Customer Invoice")
        layout = QVBoxLayout(dlg)

        edit = QPlainTextEdit()
        edit.setPlainText(text)
        layout.addWidget(edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(dlg.reject)
        buttons.accepted.connect(dlg.accept)
        layout.addWidget(buttons)

        dlg.resize(600, 500)
        dlg.exec_()

class AnalyticsPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Analytics"))
        self.setLayout(layout)


class CreditsPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        logo_label = QLabel()
        pix = QPixmap("assets/cpf_logo.png")
        if not pix.isNull():
            logo_label.setPixmap(
                pix.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        logo_label.setAlignment(Qt.AlignCenter)

        text_label = QLabel("PrintForge Desktop\nCreated by Max & ChatGPT (roughly 50/50)")
        text_label.setAlignment(Qt.AlignCenter)
        text_label.setStyleSheet("font-size: 12pt;")

        layout.addStretch()
        layout.addWidget(logo_label)
        layout.addWidget(text_label)
        layout.addStretch()

        self.setLayout(layout)
