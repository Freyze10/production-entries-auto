import os

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QDoubleValidator, QColor
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QPushButton, QTabWidget, QTableWidget, QHeaderView, QAbstractItemView,
    QFrame, QMessageBox, QWidget, QSplitter, QTableWidgetItem, QStackedWidget,
    QStyledItemDelegate, QStyle
)
import json
from db.read import get_fginv_passed_records, get_fginv_failed_records


class RowColorDelegate(QStyledItemDelegate):
    """Paints each cell's BackgroundRole itself, so global stylesheets can't override it."""

    def paint(self, painter, option, index):
        bg = index.data(Qt.ItemDataRole.BackgroundRole)
        if bg is None or (option.state & QStyle.StateFlag.State_Selected):
            super().paint(painter, option, index)
            return

        painter.save()
        painter.fillRect(option.rect, bg)

        fg = index.data(Qt.ItemDataRole.ForegroundRole)
        painter.setPen(fg.color() if fg is not None and hasattr(fg, "color") else QColor("black"))

        font = index.data(Qt.ItemDataRole.FontRole)
        painter.setFont(font if font is not None else option.font)

        align = index.data(Qt.ItemDataRole.TextAlignmentRole)
        if align is None:
            align = (Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter).value
        elif not isinstance(align, int):
            align = align.value

        text = str(index.data(Qt.ItemDataRole.DisplayRole) or "")
        painter.drawText(option.rect.adjusted(8, 0, -8, 0), int(align), text)
        painter.restore()


class NonRawMaterialWizard(QDialog):
    PASS_BG = QColor(212, 237, 218)  # Soft green (#d4edda)
    FAIL_BG = QColor(248, 215, 218)  # Soft red (#f8d7da)

    def __init__(self, parent=None, edit_data=None):
        super().__init__(parent)
        self.setWindowTitle("Non-Raw Material Composition Setup")

        # Start smaller for Step 1
        self.resize(500, 300)

        # Data container to store the final compiled output
        self.final_result_data = None
        self.step1_data = {}
        self.initial_edit_deductions = []  # Track pre-loaded rows for editing

        # Main layout using a Stacked Widget to cleanly handle pages/steps
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.currentChanged.connect(self.on_step_changed)

        main_layout.addWidget(self.stacked_widget)

        self.init_step_one_ui()
        self.init_step_two_ui()

        # --- PRE-LOAD DATA IF WE ARE EDITING ---
        if edit_data:
            self.step1_data = edit_data.get("composition_info", {})
            self.display_mat_code_input.setText(self.step1_data.get("display_material_code", ""))
            self.large_scale_input.setText(str(self.step1_data.get("large_scale", "")))
            self.small_scale_input.setText(str(self.step1_data.get("small_scale", "")))
            self.total_weight_input.setText(str(self.step1_data.get("total_weight", "")))

            # Store source deductions to be loaded after left tables are populated
            self.initial_edit_deductions = edit_data.get("source_deductions", [])

        self.stacked_widget.setCurrentIndex(0)

    def on_step_changed(self, index):
        """Dynamically resize the dialog depending on which step is active"""
        if index == 0:
            self.resize(500, 300)
            self.setMinimumSize(450, 280)
            self.setMaximumSize(600, 350)
        else:
            self.setMinimumSize(1000, 600)
            self.setMaximumSize(16777215, 16777215)
            self.resize(1350, 750)

        if self.parent():
            self.move(
                self.parent().geometry().center() - self.rect().center()
            )

    # ==========================================
    # STEP 1: INITIAL INPUT DIALOG
    # ==========================================
    def init_step_one_ui(self):
        self.step_one_widget = QWidget()
        layout = QVBoxLayout(self.step_one_widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        info_label = QLabel("Write what to display in the production material name")
        info_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        info_label.setStyleSheet("color: #333;")
        layout.addWidget(info_label)

        form_layout = QGridLayout()
        form_layout.setSpacing(10)

        self.display_mat_code_input = QLineEdit()
        self.display_mat_code_input.setPlaceholderText("Enter display material code...")
        form_layout.addWidget(QLabel("Display Material Code:"), 0, 0)
        form_layout.addWidget(self.display_mat_code_input, 0, 1)

        double_validator = QDoubleValidator(0.0, 99999999.999999, 6)
        double_validator.setNotation(QDoubleValidator.Notation.StandardNotation)

        self.large_scale_input = QLineEdit()
        self.large_scale_input.setPlaceholderText("0.000000")
        self.large_scale_input.setValidator(double_validator)
        form_layout.addWidget(QLabel("Large Scale (kg):"), 1, 0)
        form_layout.addWidget(self.large_scale_input, 1, 1)

        self.small_scale_input = QLineEdit()
        self.small_scale_input.setPlaceholderText("0.000000")
        self.small_scale_input.setValidator(double_validator)
        form_layout.addWidget(QLabel("Small Scale (grm.):"), 2, 0)
        form_layout.addWidget(self.small_scale_input, 2, 1)

        self.total_weight_input = QLineEdit()
        self.total_weight_input.setPlaceholderText("0.000000")
        self.total_weight_input.setValidator(double_validator)
        form_layout.addWidget(QLabel("Total Weight (kg):"), 3, 0)
        form_layout.addWidget(self.total_weight_input, 3, 1)

        layout.addLayout(form_layout)
        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.next_btn = QPushButton("Next")
        self.next_btn.setObjectName("PrimaryButton")
        self.next_btn.setFixedWidth(120)
        self.next_btn.clicked.connect(self.validate_and_go_to_step_two)
        btn_layout.addWidget(self.next_btn)

        layout.addLayout(btn_layout)
        self.stacked_widget.addWidget(self.step_one_widget)

    def validate_and_go_to_step_two(self):
        mat_code = self.display_mat_code_input.text().strip()
        large_txt = self.large_scale_input.text().strip()
        small_txt = self.small_scale_input.text().strip()
        total_txt = self.total_weight_input.text().strip()

        if not mat_code or not large_txt or not small_txt or not total_txt:
            QMessageBox.warning(self, "Validation Error", "Please fill in all required fields before proceeding.")
            return

        try:
            self.step1_data = {
                "display_material_code": mat_code,
                "large_scale": float(large_txt),
                "small_scale": float(small_txt),
                "total_weight": float(total_txt)
            }
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Scale and weight inputs must be valid numbers.")
            return

        self.stacked_widget.setCurrentIndex(1)
        self.load_inventory_data()

        # --- POPULATE RIGHT TABLE IF EDITING ---
        if self.initial_edit_deductions:
            self.load_existing_deductions_to_right_table(self.initial_edit_deductions)

        self.update_validation_display(0.0)

    def load_existing_deductions_to_right_table(self, deductions):
        """Populates the right table with previous deductions and highlights left table rows"""
        self.right_table.blockSignals(True)
        try:
            for item_info in deductions:
                prod_info_str = item_info.get("product_info", "")
                deduction_qty = item_info.get("deduction_qty", 0.0)
                saved_status = item_info.get("status", "Passed")  # Read status from payload

                right_row = self.right_table.rowCount()
                self.right_table.insertRow(right_row)

                # --- Column 0: Product Code (NON-EDITABLE) ---
                code_item = QTableWidgetItem(prod_info_str)
                code_item.setFlags(code_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                code_item.setData(Qt.ItemDataRole.UserRole, saved_status)  # Store status in UserRole

                # Determine background color based on saved status
                is_pass_status = (saved_status.lower() == "passed")
                bg_col = self.PASS_BG if is_pass_status else self.FAIL_BG

                code_item.setData(Qt.ItemDataRole.BackgroundRole, bg_col)
                self.right_table.setItem(right_row, 0, code_item)

                # Match against left inventory tables to find max quantity limit
                found_max_qty = deduction_qty
                for tbl in [self.pass_table, self.fail_table]:
                    for r in range(tbl.rowCount()):
                        p_code = tbl.item(r, 0).text() if tbl.item(r, 0) else ""
                        l_no = tbl.item(r, 1).text() if tbl.item(r, 1) else ""
                        if p_code in prod_info_str and l_no in prod_info_str:
                            q_str = tbl.item(r, 2).text() if tbl.item(r, 2) else "0"
                            try:
                                found_max_qty = float(q_str)
                            except ValueError:
                                pass
                            break

                # --- Column 1: Qty (NON-EDITABLE) ---
                qty_item = QTableWidgetItem(f"{found_max_qty:.6f}")
                qty_item.setFlags(qty_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                qty_item.setData(Qt.ItemDataRole.BackgroundRole, bg_col)
                self.right_table.setItem(right_row, 1, qty_item)

                # --- Column 2: Total Deduction (EDITABLE) ---
                deduction_item = QTableWidgetItem(f"{deduction_qty:.6f}")
                deduction_item.setData(Qt.ItemDataRole.BackgroundRole, bg_col)
                self.right_table.setItem(right_row, 2, deduction_item)

        finally:
            self.right_table.blockSignals(False)

        self.validate_total_deductions_match()

    # ==========================================
    # STEP 2: DUAL CONTAINER SELECTION WIZARD
    # ==========================================
    def init_step_two_ui(self):
        self.step_two_widget = QWidget()
        step2_layout = QVBoxLayout(self.step_two_widget)
        step2_layout.setContentsMargins(15, 15, 15, 15)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # -----------------------------------------
        # LEFT CONTAINER
        # -----------------------------------------
        left_frame = QFrame()
        left_frame.setObjectName("ContentCard")
        left_layout = QVBoxLayout(left_frame)

        self.tab_widget = QTabWidget()
        self.pass_tab = QWidget()
        self.fail_tab = QWidget()
        self.tab_widget.addTab(self.pass_tab, "Pass Records")
        self.tab_widget.addTab(self.fail_tab, "Failed Records")

        self.setup_left_tab_content(self.pass_tab, "pass")
        self.setup_left_tab_content(self.fail_tab, "fail")

        left_layout.addWidget(self.tab_widget)

        self.select_row_btn = QPushButton("Select Record >>")
        self.select_row_btn.setObjectName("SuccessButton")
        self.select_row_btn.clicked.connect(self.move_selected_record_to_right)
        left_layout.addWidget(self.select_row_btn, alignment=Qt.AlignmentFlag.AlignRight)

        splitter.addWidget(left_frame)

        # -----------------------------------------
        # RIGHT CONTAINER
        # -----------------------------------------
        right_frame = QFrame()
        right_frame.setObjectName("ContentCard")
        right_layout = QVBoxLayout(right_frame)

        right_layout.addWidget(QLabel("<b>Selected Deductions Allocation</b>"))

        self.right_table = QTableWidget()
        self.right_table.setColumnCount(3)
        self.right_table.setHorizontalHeaderLabels(["Product code", "Qty", "Total Deduction"])

        right_header = self.right_table.horizontalHeader()
        right_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        right_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        right_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        self.right_table.verticalHeader().setVisible(False)
        self.right_table.setAlternatingRowColors(False)
        self.right_table.setItemDelegate(RowColorDelegate(self.right_table))
        self.right_table.itemChanged.connect(self.validate_total_deductions_match)
        right_layout.addWidget(self.right_table)

        remove_right_btn = QPushButton("Remove Selected")
        remove_right_btn.setObjectName("DangerButton")
        remove_right_btn.clicked.connect(self.remove_from_right_table)
        right_layout.addWidget(remove_right_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        self.validation_status_label = QLabel()
        self.validation_status_label.setStyleSheet("font-weight: bold; color: red;")
        right_layout.addWidget(self.validation_status_label)

        step2_btn_layout = QHBoxLayout()

        self.back_btn = QPushButton("<< Back")
        self.back_btn.setObjectName("SecondaryButton")
        self.back_btn.setFixedWidth(100)
        self.back_btn.clicked.connect(self.go_back_to_step_one)
        step2_btn_layout.addWidget(self.back_btn)

        step2_btn_layout.addStretch()

        self.final_add_btn = QPushButton("Add Composition")
        self.final_add_btn.setObjectName("PrimaryButton")
        self.final_add_btn.setEnabled(False)
        self.final_add_btn.clicked.connect(self.finalize_and_save)
        step2_btn_layout.addWidget(self.final_add_btn)

        right_layout.addLayout(step2_btn_layout)

        splitter.addWidget(right_frame)
        splitter.setSizes([750, 600])

        step2_layout.addWidget(splitter)
        self.stacked_widget.addWidget(self.step_two_widget)

    def setup_left_tab_content(self, tab_widget, status_type):
        layout = QVBoxLayout(tab_widget)

        search_input = QLineEdit()
        search_input.setPlaceholderText(f"Search {status_type} records...")
        search_input.textChanged.connect(lambda text, st=status_type: self.filter_left_table(text, st))
        layout.addWidget(search_input)

        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(["Product code", "Lot no", "Qty", "Warehouse #", "Bag No.", "Status"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(False)
        table.setItemDelegate(RowColorDelegate(table))

        if status_type == "pass":
            self.pass_search_input = search_input
            self.pass_table = table
        else:
            self.fail_search_input = search_input
            self.fail_table = table

        layout.addWidget(table)

    def filter_left_table(self, query, status_type):
        table = self.pass_table if status_type == "pass" else self.fail_table
        query = query.lower().strip()

        for row in range(table.rowCount()):
            match_found = False
            for col in range(table.columnCount()):
                item = table.item(row, col)
                if item and query in item.text().lower():
                    match_found = True
                    break
            table.setRowHidden(row, not match_found)

    def load_inventory_data(self):
        """Loads data from schema_fg views into Pass and Fail tables with status-based row shading"""

        def populate_table(table, data, is_passed):
            table.setRowCount(0)
            bg_color = self.PASS_BG if is_passed else self.FAIL_BG

            for row_idx, row_data in enumerate(data):
                table.insertRow(row_idx)

                table.setItem(row_idx, 0, QTableWidgetItem(str(row_data[0] or "")))
                table.setItem(row_idx, 1, QTableWidgetItem(str(row_data[1] or "")))
                table.setItem(row_idx, 2, QTableWidgetItem(str(row_data[2] or "0")))
                table.setItem(row_idx, 3, QTableWidgetItem(str(row_data[3] or "")))
                table.setItem(row_idx, 4, QTableWidgetItem(str(row_data[4] or "")))

                status_item = QTableWidgetItem("Passed" if is_passed else "Failed")
                status_item.setForeground(QColor("green" if is_passed else "red"))
                status_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                table.setItem(row_idx, 5, status_item)

                for col in range(table.columnCount()):
                    table.item(row_idx, col).setBackground(bg_color)

        populate_table(self.pass_table, get_fginv_passed_records(), is_passed=True)
        populate_table(self.fail_table, get_fginv_failed_records(), is_passed=False)

    def go_back_to_step_one(self):
        self.stacked_widget.setCurrentIndex(0)

    def move_selected_record_to_right(self):
        current_tab_idx = self.tab_widget.currentIndex()
        is_passed = (current_tab_idx == 0) # Tab 0 is Pass Records, Tab 1 is Failed Records
        active_table = self.pass_table if is_passed else self.fail_table

        row = active_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a record from the table first.")
            return

        def cell_text(col, default=""):
            item = active_table.item(row, col)
            return item.text() if item else default

        prod_code = cell_text(0)
        lot_no = cell_text(1)
        qty_str = cell_text(2, "0")
        bag_no = cell_text(4)

        try:
            max_qty = float(qty_str)
        except ValueError:
            max_qty = 0.0

        for r in range(self.right_table.rowCount()):
            existing_item = self.right_table.item(r, 0)
            if existing_item and prod_code in existing_item.text() and lot_no in existing_item.text():
                QMessageBox.warning(self, "Duplicate", "This specific product and lot is already included in the deduction list.")
                return

        bg_color = self.PASS_BG if is_passed else self.FAIL_BG

        self.right_table.blockSignals(True)
        try:
            right_row = self.right_table.rowCount()
            self.right_table.insertRow(right_row)

            display_text = f"{prod_code} (Lot: {lot_no} | Bag: {bag_no})"
            code_item = QTableWidgetItem(display_text)
            code_item.setFlags(code_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

            qty_item = QTableWidgetItem(f"{max_qty:.6f}")
            qty_item.setFlags(qty_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

            deduction_item = QTableWidgetItem("0.00")

            # Store the status context directly inside the row's item data using UserRole!
            status_context = "Passed" if is_passed else "Failed"
            code_item.setData(Qt.ItemDataRole.UserRole, status_context)

            for col, item in enumerate((code_item, qty_item, deduction_item)):
                item.setBackground(bg_color)
                self.right_table.setItem(right_row, col, item)
        finally:
            self.right_table.blockSignals(False)

        self.validate_total_deductions_match()

    def remove_from_right_table(self):
        current_row = self.right_table.currentRow()
        if current_row >= 0:
            self.right_table.removeRow(current_row)
            self.validate_total_deductions_match()
        else:
            QMessageBox.warning(self, "No Selection", "Please select an item from the deduction table to remove.")

    def validate_total_deductions_match(self):
        total_deduction_sum = 0.0
        self.right_table.blockSignals(True)
        try:
            for row in range(self.right_table.rowCount()):
                qty_cell = self.right_table.item(row, 1)
                deduction_cell = self.right_table.item(row, 2)
                if qty_cell is None or deduction_cell is None:
                    continue

                qty_val = float(qty_cell.text())

                try:
                    deduction_val = float(deduction_cell.text().strip() or "0")
                except ValueError:
                    deduction_val = 0.0
                    deduction_cell.setText("0.00")

                if deduction_val > qty_val:
                    QMessageBox.warning(self, "Exceeds Quantity",
                                        f"Deduction cannot exceed available quantity ({qty_val}).")
                    deduction_val = qty_val
                    deduction_cell.setText(f"{qty_val:.6f}")
                elif deduction_val < 0:
                    deduction_val = 0.0
                    deduction_cell.setText("0.00")

                total_deduction_sum += deduction_val
        finally:
            self.right_table.blockSignals(False)

        target_weight = self.step1_data.get("total_weight", 0.0)
        self.update_validation_display(total_deduction_sum)

        if abs(total_deduction_sum - target_weight) < 0.000001 and self.right_table.rowCount() > 0:
            self.final_add_btn.setEnabled(True)
            self.validation_status_label.setStyleSheet("font-weight: bold; color: green;")
        else:
            self.final_add_btn.setEnabled(False)
            self.validation_status_label.setStyleSheet("font-weight: bold; color: red;")

    def update_validation_display(self, current_sum):
        target = self.step1_data.get("total_weight", 0.0)
        text_msg = (f"Target Weight Required: {target:.6f} kg\n"
                    f"Current Total Deductions: {current_sum:.6f} kg")
        self.validation_status_label.setText(text_msg)

    def finalize_and_save(self):
        """Compiles everything into a clean dictionary payload in-memory and closes dialog"""
        deductions_list = []
        for row in range(self.right_table.rowCount()):
            code_item = self.right_table.item(row, 0)
            prod_info = code_item.text() if code_item else ""

            # Retrieve the Pass/Fail status we stored in UserRole
            status_val = code_item.data(Qt.ItemDataRole.UserRole) if code_item else "Passed"

            deduction_val = float(self.right_table.item(row, 2).text() or 0.0)

            deductions_list.append({
                "product_info": prod_info,
                "deduction_qty": deduction_val,
                "status": status_val  # <-- Included in payload!
            })

        self.final_result_data = {
            "composition_info": self.step1_data,
            "source_deductions": deductions_list
        }

        QMessageBox.information(self, "Success", "Non-raw material composition compiled successfully!")
        self.accept()