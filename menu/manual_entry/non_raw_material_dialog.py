from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QDoubleValidator
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QPushButton, QTabWidget, QTableWidget, QHeaderView, QAbstractItemView,
    QFrame, QMessageBox, QWidget, QSplitter, QTableWidgetItem, QStackedWidget
)
import json


class NonRawMaterialWizard(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Non-Raw Material Composition Setup")

        # Start smaller for Step 1
        self.resize(500, 300)

        # Data container to store the final compiled output
        self.final_result_data = None
        self.step1_data = {}

        # Main layout using a Stacked Widget to cleanly handle pages/steps
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.stacked_widget = QStackedWidget()
        # Listen to step/page changes to dynamically resize the dialog window
        self.stacked_widget.currentChanged.connect(self.on_step_changed)

        main_layout.addWidget(self.stacked_widget)

        # Build steps
        self.init_step_one_ui()
        self.init_step_two_ui()

        # Start on Step 1
        self.stacked_widget.setCurrentIndex(0)

    def on_step_changed(self, index):
        """Dynamically resize the dialog depending on which step is active"""
        if index == 0:
            # Step 1: Compact size for simple form inputs
            self.resize(500, 300)
            self.setMinimumSize(450, 280)
            self.setMaximumSize(600, 350)
        else:
            # Step 2: Large size for side-by-side tables and dual containers
            self.setMinimumSize(900, 500)
            self.setMaximumSize(16777215, 16777215)  # Remove maximum limits
            self.resize(1100, 650)

        # Center the window nicely whenever size adjusts
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

        # Title/Info Label
        info_label = QLabel("Write what to display in the production material name")
        info_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        info_label.setStyleSheet("color: #333;")
        layout.addWidget(info_label)

        form_layout = QGridLayout()
        form_layout.setSpacing(10)

        # Display Material Code input
        self.display_mat_code_input = QLineEdit()
        self.display_mat_code_input.setPlaceholderText("Enter display material code...")
        form_layout.addWidget(QLabel("Display Material Code:"), 0, 0)
        form_layout.addWidget(self.display_mat_code_input, 0, 1)

        # Float validator for numbers only
        double_validator = QDoubleValidator(0.0, 99999999.999999, 6)
        double_validator.setNotation(QDoubleValidator.Notation.StandardNotation)

        # Large Scale (kg)
        self.large_scale_input = QLineEdit()
        self.large_scale_input.setPlaceholderText("0.000000")
        self.large_scale_input.setValidator(double_validator)
        form_layout.addWidget(QLabel("Large Scale (kg):"), 1, 0)
        form_layout.addWidget(self.large_scale_input, 1, 1)

        # Small Scale (grm.)
        self.small_scale_input = QLineEdit()
        self.small_scale_input.setPlaceholderText("0.000000")
        self.small_scale_input.setValidator(double_validator)
        form_layout.addWidget(QLabel("Small Scale (grm.):"), 2, 0)
        form_layout.addWidget(self.small_scale_input, 2, 1)

        # Total Weight (kg)
        self.total_weight_input = QLineEdit()
        self.total_weight_input.setPlaceholderText("0.000000")
        self.total_weight_input.setValidator(double_validator)
        form_layout.addWidget(QLabel("Total Weight (kg):"), 3, 0)
        form_layout.addWidget(self.total_weight_input, 3, 1)

        layout.addLayout(form_layout)
        layout.addStretch()

        # Bottom Next Button Layout
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.next_btn = QPushButton("Next")
        self.next_btn.setObjectName("PrimaryButton")
        self.next_btn.setFixedWidth(120)
        self.next_btn.clicked.connect(self.validate_and_go_to_step_two)
        btn_layout.addWidget(self.next_btn)

        layout.addLayout(btn_layout)

        # Add to Stacked Widget (Index 0)
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

        # Switch to Step 2 smoothly using the Stacked Widget
        self.stacked_widget.setCurrentIndex(1)
        self.update_validation_display(0.0)

    # ==========================================
    # STEP 2: DUAL CONTAINER SELECTION WIZARD
    # ==========================================
    def init_step_two_ui(self):
        self.step_two_widget = QWidget()
        step2_layout = QVBoxLayout(self.step_two_widget)
        step2_layout.setContentsMargins(15, 15, 15, 15)

        # Big Splitter for Left and Right Containers Side-by-Side
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # -----------------------------------------
        # LEFT CONTAINER
        # -----------------------------------------
        left_frame = QFrame()
        left_frame.setObjectName("ContentCard")
        left_layout = QVBoxLayout(left_frame)

        # Tabs for Pass and Failed
        self.tab_widget = QTabWidget()
        self.pass_tab = QWidget()
        self.fail_tab = QWidget()
        self.tab_widget.addTab(self.pass_tab, "Pass Records")
        self.tab_widget.addTab(self.fail_tab, "Failed Records")

        self.setup_left_tab_content(self.pass_tab, "pass")
        self.setup_left_tab_content(self.fail_tab, "fail")

        left_layout.addWidget(self.tab_widget)

        # Select Button at the bottom of Left Container
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

        # Right Table: Product code, Qty, total deduction
        self.right_table = QTableWidget()
        self.right_table.setColumnCount(3)
        self.right_table.setHorizontalHeaderLabels(["Product code", "Qty", "Total Deduction"])
        self.right_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.right_table.verticalHeader().setVisible(False)
        self.right_table.setAlternatingRowColors(True)
        self.right_table.itemChanged.connect(self.validate_total_deductions_match)
        right_layout.addWidget(self.right_table)

        # Remove Selected button for Right Table
        remove_right_btn = QPushButton("Remove Selected")
        remove_right_btn.setObjectName("DangerButton")
        remove_right_btn.clicked.connect(self.remove_from_right_table)
        right_layout.addWidget(remove_right_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        # Validation Message Label (Total Weight vs Current Total Deduction)
        self.validation_status_label = QLabel()
        self.validation_status_label.setStyleSheet("font-weight: bold; color: red;")
        right_layout.addWidget(self.validation_status_label)

        # Final Add Button
        self.final_add_btn = QPushButton("Add Composition")
        self.final_add_btn.setObjectName("PrimaryButton")
        self.final_add_btn.setEnabled(False)
        self.final_add_btn.clicked.connect(self.finalize_and_save)
        right_layout.addWidget(self.final_add_btn)

        splitter.addWidget(right_frame)
        splitter.setSizes([600, 500])

        step2_layout.addWidget(splitter)

        # Add to Stacked Widget (Index 1)
        self.stacked_widget.addWidget(self.step_two_widget)

    def setup_left_tab_content(self, tab_widget, status_type):
        layout = QVBoxLayout(tab_widget)

        search_input = QLineEdit()
        search_input.setPlaceholderText(f"Search {status_type} records...")
        layout.addWidget(search_input)

        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Product code", "Lot no", "Qty", "Warehouse #", "Status"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        if status_type == "pass":
            self.pass_table = table
        else:
            self.fail_table = table

        layout.addWidget(table)

    def move_selected_record_to_right(self):
        current_tab_idx = self.tab_widget.currentIndex()
        active_table = self.pass_table if current_tab_idx == 0 else self.fail_table

        selected_rows = active_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a record from the table first.")
            return

        row = selected_rows[0].row()
        prod_code = active_table.item(row, 0).text() if active_table.item(row, 0) else ""
        lot_no = active_table.item(row, 1).text() if active_table.item(row, 1) else ""
        qty_str = active_table.item(row, 2).text() if active_table.item(row, 2) else "0"

        try:
            max_qty = float(qty_str)
        except ValueError:
            max_qty = 0.0

        for r in range(self.right_table.rowCount()):
            existing_code = self.right_table.item(r, 0).text()
            if prod_code in existing_code:
                QMessageBox.warning(self, "Duplicate", "This item is already included in the deduction list.")
                return

        right_row = self.right_table.rowCount()
        self.right_table.insertRow(right_row)

        self.right_table.setItem(right_row, 0, QTableWidgetItem(f"{prod_code} (Lot: {lot_no})"))

        qty_item = QTableWidgetItem(str(max_qty))
        qty_item.setFlags(qty_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.right_table.setItem(right_row, 1, qty_item)

        deduction_item = QTableWidgetItem("0.00")
        self.right_table.setItem(right_row, 2, deduction_item)

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

        for row in range(self.right_table.rowCount()):
            qty_val = float(self.right_table.item(row, 1).text())
            deduction_cell = self.right_table.item(row, 2)

            deduction_text = deduction_cell.text().strip() if deduction_cell else "0"
            try:
                deduction_val = float(deduction_text)
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
        deductions_list = []
        for row in range(self.right_table.rowCount()):
            prod_info = self.right_table.item(row, 0).text()
            deduction_val = float(self.right_table.item(row, 2).text())
            deductions_list.append({
                "product_info": prod_info,
                "deduction_qty": deduction_val
            })

        complete_payload = {
            "composition_info": self.step1_data,
            "source_deductions": deductions_list
        }

        self.final_result_data = complete_payload

        with open("non_raw_material_payload.json", "w") as f:
            json.dump(complete_payload, f, indent=4)

        QMessageBox.information(self, "Success", "Non-raw material composition compiled successfully!")
        self.accept()