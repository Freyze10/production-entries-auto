from datetime import datetime

from PyQt6.QtCore import Qt, QThread
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QFrame, QHBoxLayout, QGroupBox, QGridLayout, QLineEdit, \
    QLabel, QComboBox, QTextEdit, QCheckBox, QTableWidget, QHeaderView, QAbstractItemView, QPushButton, QMessageBox, \
    QTableWidgetItem, QCompleter
import qtawesome as fa

from db.legacy import SyncRM
from db.read import get_single_production_data, get_single_production_details, get_rm_code_lists
from table_model import table_spacing
from util.field_format import format_to_float, SmartDateEdit, production_mixing_time, NumericTableWidgetItem
from util.loading import LoadingDialog
from workstation.workstation_details import _get_workstation_info


class MBManualEntry(QWidget):
    def __init__(self, prod_id=0):  # , username, user_role, log_audit_trail
        super().__init__()
        self.prod_id = prod_id
        self.prod_results = None
        self.prod_materials = None
        self.work_station = _get_workstation_info()
        # self.user_id = f"{self.work_station['h']} # {self.user_role}"
        # Track current production for edit/view
        self.current_production_id = None

        self.setup_ui()

    def setup_ui(self):

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        scroll_widget = QWidget()
        scroll_layout = QHBoxLayout(scroll_widget)
        scroll_layout.setSpacing(12)

        # Left Column - Production Information
        left_column = QVBoxLayout()
        left_column.setSpacing(6)

        # Production Information Card
        primary_card = QGroupBox("Production Information")
        primary_layout = QGridLayout(primary_card)
        primary_layout.setSpacing(4)
        primary_layout.setContentsMargins(8, 12, 8, 4)

        row = 0

        # WIP No (Production ID)
        self.wip_no_input = QLineEdit(objectName='gray_bg')
        primary_layout.addWidget(QLabel("WIP No:"), row, 0)
        primary_layout.addWidget(self.wip_no_input, row, 1)
        row += 1

        # Production ID
        self.production_id_input = QLineEdit(objectName='required')
        self.production_id_input.setPlaceholderText("0098988")
        primary_layout.addWidget(QLabel("Production ID:"), row, 0)
        primary_layout.addWidget(self.production_id_input, row, 1)
        row += 1

        # Form Type
        self.form_type_combo = QComboBox()
        self.form_type_combo.addItems(["", "New", "Correction"])
        self.form_type_combo.setStyleSheet("background-color: #FDECCE;")
        primary_layout.addWidget(QLabel("Form Type:"), row, 0)
        primary_layout.addWidget(self.form_type_combo, row, 1)
        row += 1

        # Product Code
        self.product_code_input = QLineEdit(objectName='required')
        self.product_code_input.setPlaceholderText("Enter product code")
        primary_layout.addWidget(QLabel("Product Code:"), row, 0)
        primary_layout.addWidget(self.product_code_input, row, 1)
        row += 1

        # Product Color
        self.product_color_input = QLineEdit()
        self.product_color_input.setPlaceholderText("Enter product color")
        primary_layout.addWidget(QLabel("Product Color:"), row, 0)
        primary_layout.addWidget(self.product_color_input, row, 1)
        row += 1

        # Formula
        self.formula_input = QLineEdit()
        self.formula_input.setPlaceholderText("0")
        primary_layout.addWidget(QLabel("Formula:"), row, 0)
        primary_layout.addWidget(self.formula_input, row, 1)
        row += 1

        # Sum of Cons and Dosage in one row
        sum_dosage_layout = QHBoxLayout()
        sum_dosage_layout.setSpacing(9)

        self.sum_cons_input = QLineEdit()
        self.sum_cons_input.setPlaceholderText("0.00000")
        self.sum_cons_input.focusOutEvent = lambda event: format_to_float(self, event, self.sum_cons_input)
        sum_dosage_layout.addWidget(self.sum_cons_input)

        dosage_label = QLabel("Dosage:")
        sum_dosage_layout.addWidget(dosage_label)

        self.dosage_input = QLineEdit(objectName='required')
        self.dosage_input.setPlaceholderText("0.000000")
        self.dosage_input.focusOutEvent = lambda event: format_to_float(self, event, self.dosage_input)
        sum_dosage_layout.addWidget(self.dosage_input)

        primary_layout.addWidget(QLabel("Sum of Cons:"), row, 0)
        primary_layout.addLayout(sum_dosage_layout, row, 1)
        row += 1

        # Customer
        self.customer_input = QLineEdit(objectName='required')
        self.customer_input.setPlaceholderText("Enter customer")
        primary_layout.addWidget(QLabel("Customer:"), row, 0)
        primary_layout.addWidget(self.customer_input, row, 1)
        row += 1

        # Lot No
        self.lot_no_input = QLineEdit(objectName='required')
        self.lot_no_input.setPlaceholderText("Enter lot number")
        primary_layout.addWidget(QLabel("Lot No:"), row, 0)
        primary_layout.addWidget(self.lot_no_input, row, 1)
        row += 1

        # Production Date
        self.production_date_input = SmartDateEdit()
        self.production_date_input.setStyleSheet("background-color: #FDECCE;")
        primary_layout.addWidget(QLabel("Production Date:"), row, 0)
        primary_layout.addWidget(self.production_date_input, row, 1)
        row += 1

        # Confirmation Date
        self.confirmation_date_input = SmartDateEdit()
        primary_layout.addWidget(QLabel("Confirmation Date:  <br><span style='font-size: 10px;'>(For Inventory Only)</span>"), row, 0)
        primary_layout.addWidget(self.confirmation_date_input, row, 1)
        row += 1

        # Order Form No
        self.order_form_no_input = QLineEdit(objectName='required')
        self.order_form_no_input.setPlaceholderText("Enter order form number")
        primary_layout.addWidget(QLabel("Order Form No:"), row, 0)
        primary_layout.addWidget(self.order_form_no_input, row, 1)
        row += 1

        # Colormatch No
        self.colormatch_no_input = QLineEdit()
        self.colormatch_no_input.setPlaceholderText("Enter colormatch number")
        primary_layout.addWidget(QLabel("Colormatch No:"), row, 0)
        primary_layout.addWidget(self.colormatch_no_input, row, 1)
        row += 1

        # Matched Date
        self.matched_date_input = SmartDateEdit()
        primary_layout.addWidget(QLabel("Matched Date:"), row, 0)
        primary_layout.addWidget(self.matched_date_input, row, 1)
        row += 1

        # Mixing Time and Machine No in one row
        mixing_machine_layout = QHBoxLayout()
        mixing_machine_layout.setSpacing(9)

        self.mixing_time_input = QLineEdit()
        self.mixing_time_input.setPlaceholderText("Enter mixing time")
        self.mixing_time_input.focusOutEvent = lambda event: production_mixing_time(event, self.mixing_time_input)
        mixing_machine_layout.addWidget(self.mixing_time_input)

        machine_no_label = QLabel("Machine No:")
        mixing_machine_layout.addWidget(machine_no_label)

        self.machine_no_input = QLineEdit()
        self.machine_no_input.setPlaceholderText("Enter machine number")
        mixing_machine_layout.addWidget(self.machine_no_input)

        primary_layout.addWidget(QLabel("Mixing Time:"), row, 0)
        primary_layout.addLayout(mixing_machine_layout, row, 1)
        row += 1

        # Qty Required and Qty Per Batch in one row
        qty_layout = QHBoxLayout()
        qty_layout.setSpacing(9)

        self.qty_required_input = QLineEdit(objectName='required')
        self.qty_required_input.setPlaceholderText("0.0000000")
        self.qty_required_input.focusOutEvent = lambda event: format_to_float(self, event, self.qty_required_input)
        qty_layout.addWidget(self.qty_required_input)

        qty_batch_label = QLabel("Qty. Per Batch:")
        qty_layout.addWidget(qty_batch_label)

        self.qty_per_batch_input = QLineEdit(objectName='required')
        self.qty_per_batch_input.setPlaceholderText("0.0000000")
        self.qty_per_batch_input.focusOutEvent = lambda event: format_to_float(self, event, self.qty_per_batch_input)
        qty_layout.addWidget(self.qty_per_batch_input)

        primary_layout.addWidget(QLabel("Qty. Required:"), row, 0)
        primary_layout.addLayout(qty_layout, row, 1)
        row += 1

        # Prepared By
        self.prepared_by_input = QLineEdit(objectName='required')
        self.prepared_by_input.setPlaceholderText("Enter preparer name")
        primary_layout.addWidget(QLabel("Prepared By:"), row, 0)
        primary_layout.addWidget(self.prepared_by_input, row, 1)
        row += 1

        # Notes
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Enter any notes...")
        self.notes_input.setMinimumHeight(30)
        self.notes_input.setMaximumHeight(50)
        primary_layout.addWidget(QLabel("Notes:"), row, 0)
        primary_layout.addWidget(self.notes_input, row, 1)
        row += 1

        left_column.addWidget(primary_card)
        scroll_layout.addLayout(left_column, stretch=1)

        # Right Column - Materials
        right_column = QVBoxLayout()
        right_column.setSpacing(4)

        # Materials Card
        material_card = QGroupBox("Material Composition")
        material_layout = QVBoxLayout(material_card)
        material_layout.setContentsMargins(8, 12, 8, 4)
        material_layout.setSpacing(6)

        # Material Type Selection (Radio-button behavior)
        material_type_layout = QHBoxLayout()
        material_type_layout.addWidget(QLabel("Material Used:"))
        self.raw_material_check = QCheckBox("RAW MATERIAL")
        self.raw_material_check.setObjectName("RawMaterialCheck")
        self.raw_material_check.setChecked(True)
        self.non_raw_material_check = QCheckBox("NON-RAW MATERIAL")
        self.non_raw_material_check.setObjectName("NonRawMaterialCheck")

        # Make checkboxes behave like radio buttons
        self.raw_material_check.toggled.connect(lambda checked: self.on_material_type_changed(checked, True))
        self.non_raw_material_check.toggled.connect(lambda checked: self.on_material_type_changed(checked, False))

        material_type_layout.addWidget(self.raw_material_check)
        material_type_layout.addWidget(self.non_raw_material_check)
        material_type_layout.addStretch()
        material_layout.addLayout(material_type_layout)

        # Material Input Section
        input_card = QFrame()
        input_layout = QGridLayout(input_card)
        input_layout.setSpacing(6)

        # Material Code - Create both QComboBox and QLineEdit
        self.material_code_combo = QComboBox()
        self.material_code_combo.setEditable(True)
        self.material_code_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.material_code_combo.setPlaceholderText("Enter material code")
        self.material_code_combo.setStyleSheet("background-color: #FDECCE;")
        self.material_code_combo.lineEdit().editingFinished.connect(self.validate_rm_code)
        self.setup_rm_code_completer()
        self.material_code_combo.setCurrentIndex(0)

        self.material_code_lineedit = QLineEdit()
        self.material_code_lineedit.setPlaceholderText("Enter material code")
        self.material_code_lineedit.setStyleSheet("background-color: #FDECCE;")
        self.material_code_lineedit.setVisible(False)  # Hidden by default

        btn_sync_rm = QPushButton("Sync")
        btn_sync_rm.setObjectName("SuccessButton")
        btn_sync_rm.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_sync_rm.clicked.connect(self.sync_rm)

        # Add label
        input_layout.addWidget(QLabel("Material Code:"), 0, 0)
        # Add both widgets to the same position (only one will be visible at a time)
        input_layout.addWidget(self.material_code_combo, 0, 1, 1, 2)
        input_layout.addWidget(self.material_code_lineedit, 0, 1, 1, 2)
        input_layout.addWidget(btn_sync_rm, 0, 3)

        # Large Scale
        self.large_scale_input = QLineEdit()
        self.large_scale_input.setPlaceholderText("0.0000000")
        self.large_scale_input.setStyleSheet("background-color: #fff9c4;")
        input_layout.addWidget(QLabel("Large Scale (KG):"), 1, 0)
        input_layout.addWidget(self.large_scale_input, 1, 1, 1, 3)

        # Small Scale
        self.small_scale_input = QLineEdit()
        self.small_scale_input.setPlaceholderText("0.0000000")
        self.small_scale_input.setStyleSheet("background-color: #fff9c4;")
        input_layout.addWidget(QLabel("Small Scale (G):"), 2, 0)
        input_layout.addWidget(self.small_scale_input, 2, 1, 1, 3)

        # Total Weight
        self.total_weight_input = QLineEdit()
        self.total_weight_input.setPlaceholderText("0.0000000")
        self.total_weight_input.setStyleSheet("background-color: #fff9c4;")
        self.total_weight_input.returnPressed.connect(self.add_material)
        self.total_weight_input.installEventFilter(self)
        input_layout.addWidget(QLabel("Total Weight (KG):"), 3, 0)
        input_layout.addWidget(self.total_weight_input, 3, 1, 1, 3)

        # Action Buttons
        action_layout = QHBoxLayout()
        action_layout.addStretch()

        add_btn = QPushButton("Add")
        add_btn.setObjectName("SuccessButton")
        add_btn.clicked.connect(self.add_material)
        action_layout.addWidget(add_btn)

        remove_btn = QPushButton("Remove")
        remove_btn.setObjectName("DangerButton")
        remove_btn.clicked.connect(self.remove_material)
        action_layout.addWidget(remove_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("SecondaryButton")
        clear_btn.clicked.connect(self.clear_material_table)
        action_layout.addWidget(clear_btn)

        remove_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        clear_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        input_layout.addLayout(action_layout, 4, 0, 1, 4)
        material_layout.addWidget(input_card)

        # Materials Table
        self.materials_table = QTableWidget()
        self.materials_table.setColumnCount(4)
        self.materials_table.setHorizontalHeaderLabels([
            "Material Name", "Large Scale (KG)", "Small Scale (G)",
            "Total Weight (KG)"
        ])
        self.materials_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.materials_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.materials_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.materials_table.verticalHeader().setVisible(False)
        self.materials_table.setAlternatingRowColors(True)
        self.materials_table.setMinimumHeight(200)
        self.materials_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.materials_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.materials_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        material_layout.addWidget(self.materials_table)

        # Totals Display
        total_layout = QHBoxLayout()
        total_layout.addWidget(QLabel("No. of Item(s):"))
        self.no_items_label = QLabel("0")
        self.no_items_label.setStyleSheet("font-weight: bold; color: #0078d4;")
        total_layout.addWidget(self.no_items_label)
        total_layout.addStretch()
        total_layout.addWidget(QLabel("Total Weight:"))
        self.total_weight_label = QLabel("0.0000000")
        self.total_weight_label.setStyleSheet("font-weight: bold; color: #0078d4;")
        total_layout.addWidget(self.total_weight_label)
        material_layout.addLayout(total_layout)

        # Encoding Information
        encoding_layout = QGridLayout()
        encoding_layout.setSpacing(6)

        self.encoded_by_display = QLineEdit()
        self.encoded_by_display.setReadOnly(True)
        self.encoded_by_display.setText(self.work_station['u'])
        self.encoded_by_display.setStyleSheet("background-color: #e9ecef;")

        encoding_layout.addWidget(QLabel("Encoded By:"), 0, 0)
        encoding_layout.addWidget(self.encoded_by_display, 0, 1)

        self.production_confirmation_display = QLineEdit()
        self.production_confirmation_display.setPlaceholderText("mm/dd/yyyy h:m:s")
        self.production_confirmation_display.setStyleSheet("background-color: #fff9c4;")
        self.production_confirmation_display.setReadOnly(True)
        encoding_layout.addWidget(QLabel("Production Confirmation Encoded On:"), 1, 0)
        encoding_layout.addWidget(self.production_confirmation_display, 1, 1)

        self.production_encoded_display = QLineEdit()
        self.production_encoded_display.setText(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.production_encoded_display.setReadOnly(True)
        self.production_encoded_display.setStyleSheet("background-color: #e9ecef;")
        encoding_layout.addWidget(QLabel("Production Encoded On:"), 2, 0)
        encoding_layout.addWidget(self.production_encoded_display, 2, 1)

        material_layout.addLayout(encoding_layout)

        right_column.addWidget(material_card)
        scroll_layout.addLayout(right_column, stretch=1)

        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)

        # Bottom Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.print_wip_btn = QPushButton("Print with WIP", objectName="InfoButton")
        self.print_wip_btn.setIcon(fa.icon('fa5s.print', color='white'))
        # self.print_wip_btn.clicked.connect(self.print_with_wip)
        button_layout.addWidget(self.print_wip_btn)

        self.print_btn = QPushButton("Print", objectName="SecondaryButton")
        self.print_btn.setIcon(fa.icon('fa5s.print', color='white'))
        # self.print_btn.clicked.connect(self.print_production)
        button_layout.addWidget(self.print_btn)

        self.new_btn = QPushButton("New", objectName="PrimaryButton")
        self.new_btn.setIcon(fa.icon('fa5s.file', color='white'))
        # self.new_btn.clicked.connect(self.new_production)
        button_layout.addWidget(self.new_btn)

        self.save_btn = QPushButton("Save", objectName="SuccessButton")
        self.save_btn.setIcon(fa.icon('fa5s.save', color='white'))
        # self.save_btn.clicked.connect(self.save_production)
        button_layout.addWidget(self.save_btn)

        main_layout.addLayout(button_layout)

        if self.prod_id != 0:
            try:
                self.prod_results = get_single_production_data(self.prod_id)
                self.prod_materials = get_single_production_details(self.prod_id)
                if not self.prod_results:
                    QMessageBox.warning(self, "Not Found",
                                        f"Production {self.prod_id} not found.")
                    return False
                self.display_details()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load: {e}")
                return False

    def on_material_type_changed(self, checked, is_raw):
        """Handle material type selection like radio buttons and switch input fields."""
        if is_raw:
            if checked:
                self.non_raw_material_check.setChecked(False)
                # self.material_code_combo.setVisible(True)
                # self.material_code_lineedit.setVisible(False)
            else:
                if not self.non_raw_material_check.isChecked():
                    self.raw_material_check.setChecked(True)
        else:
            if checked:
                self.raw_material_check.setChecked(False)
                # self.material_code_combo.setVisible(False)
                # self.material_code_lineedit.setVisible(True)
            else:
                if not self.raw_material_check.isChecked():
                    self.non_raw_material_check.setChecked(True)

    def display_details(self, prod_id = 0):
        self.wip_no_input.setText(str(self.prod_results['index_no']))
        self.production_id_input.setText(str(self.prod_results['prod_id']))
        self.form_type_combo.setCurrentText(str(self.prod_results['form_type']))
        self.product_code_input.setText(str(self.prod_results['prod_code']))
        self.product_color_input.setText(str(self.prod_results['prod_color']))
        self.formula_input.setText(str(self.prod_results['form_id']))
        self.sum_cons_input.setText(f"{self.prod_results['dosage']:.6f}")
        self.dosage_input.setText(f"{self.prod_results['ld']:.6f}")
        self.customer_input.setText(str(self.prod_results['customer']))
        self.lot_no_input.setText(str(self.prod_results['lot_no']))
        self.order_form_no_input.setText(str(self.prod_results['order_no']))
        self.colormatch_no_input.setText(str(self.prod_results['colormatch_no']))
        self.prepared_by_input.setText(str(self.prod_results['prepared_by']))
        self.notes_input.setPlainText(str(self.prod_results['note']))

        def _set_date(widget, date_obj):
            if date_obj:
                widget.setText(date_obj.strftime("%m/%d/%Y"))
            else:
                widget.clear()

        qty_req = float(self.prod_results['quantity_req'])
        qty_batch = float(self.prod_results['quantity_batch'])

        _set_date(self.production_date_input, self.prod_results.get('prod_date'))
        _set_date(self.confirmation_date_input, self.prod_results.get('inventory_c_date'))
        _set_date(self.matched_date_input, self.prod_results.get('colormatch_date'))

        self.mixing_time_input.setText(str(self.prod_results['mix_time']))
        self.machine_no_input.setText(str(self.prod_results['machine_no']))
        self.qty_required_input.setText(f"{qty_req:.6f}")
        self.qty_per_batch_input.setText(f"{qty_batch:.6f}")
        self.total_weight_label.setText(f"{self.prod_results['quantity_prod']:.7f}")

        self.encoded_by_display.setText(str(self.prod_results['encoded_by']))
        if self.prod_results.get('encoded_on'):
            self.production_encoded_display.setText(
                self.prod_results['encoded_on'].strftime("%m/%d/%Y %I:%M:%S %p"))
        if self.prod_results.get('confirmation_encoded_on'):
            self.production_confirmation_display.setText(
                self.prod_results['confirmation_encoded_on'].strftime("%m/%d/%Y %I:%M:%S %p"))

        self.materials_table.setRowCount(0)

        batches = qty_req / qty_batch if qty_batch > 0 else 1.0
        for mat in self.prod_materials:
            # Tuple indexing: (id, material_code, large_scale, small_scale, total_weight)
            mat_code = str(mat[1])
            large_scale = float(mat[2])
            small_scale = float(mat[3])
            total_weight = float(mat[4])

            table_spacing.handle_batch_break_manual(self.materials_table, weight=total_weight, batches=batches , limit=25.0)

            row = self.materials_table.rowCount()
            self.materials_table.insertRow(row)

            self.materials_table.setItem(row, 0, QTableWidgetItem(mat_code))
            self.materials_table.setItem(row, 1, NumericTableWidgetItem(large_scale, is_float=True))
            self.materials_table.setItem(row, 2, NumericTableWidgetItem(small_scale, is_float=True))
            self.materials_table.setItem(row, 3, NumericTableWidgetItem(total_weight, is_float=True))

        item_count = self.materials_table.rowCount()
        self.no_items_label.setText(str(item_count))
        return True

    def add_material(self):
        """Add material to the table."""
        material_code = self.get_material_code().strip()

        if not material_code:
            QMessageBox.warning(self, "Missing Input", "Please enter a material code.")
            return

        if self.raw_material_check.isChecked():
            if material_code not in self.rm_list:
                QMessageBox.warning(self, "Invalid Material",
                                    "Please select a valid raw material code from the list.")
                return

        large_scale_text = self.large_scale_input.text().strip()
        small_scale_text = self.small_scale_input.text().strip()
        total_weight_text = self.total_weight_input.text().strip()

        if not large_scale_text or not small_scale_text or not total_weight_text:
            QMessageBox.warning(self, "Missing Input", "Please fill in all scale and weight fields.")
            return

        try:
            large_scale = float(large_scale_text)
            small_scale = float(small_scale_text)
            total_weight = float(total_weight_text)
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter valid numbers for scales and weight.")
            return
        batches = float(str(self.qty_required_input.text())) / float(str(self.qty_per_batch_input.text()))
        table_spacing.handle_batch_break_manual(self.materials_table, weight=total_weight, batches=batches, limit=25.0)

        row_position = self.materials_table.rowCount()
        self.materials_table.insertRow(row_position)

        self.materials_table.setItem(row_position, 0, QTableWidgetItem(material_code))
        self.materials_table.setItem(row_position, 1, NumericTableWidgetItem(large_scale, is_float=True))
        self.materials_table.setItem(row_position, 2, NumericTableWidgetItem(small_scale, is_float=True))
        self.materials_table.setItem(row_position, 3, NumericTableWidgetItem(total_weight, is_float=True))

        self.clear_material_inputs()
        self.update_totals()
        self.material_code_combo.setFocus()

    def remove_material(self):
        current_row = self.materials_table.currentRow()
        if current_row >= 0:
            self.materials_table.removeRow(current_row)
            self.update_totals()
        else:
            QMessageBox.warning(self, "No Selection", "Please select a material to remove.")

    def clear_material_table(self):
        self.materials_table.setRowCount(0)
        self.clear_material_inputs()
        self.update_totals()

    def update_totals(self):
        total_weight = 0.0
        item_count = self.get_valid_row_count()

        for row in range(self.materials_table.rowCount()):
            item = self.materials_table.item(row, 3) # Check column 3 (Weight)

            if item:
                if hasattr(item, 'value'):
                    total_weight += float(item.value)
                else:
                    # skip if text is empty
                    text_val = item.text().strip()
                    if text_val:  # This avoids ValueError on empty strings ""
                        try:
                            # Remove commas if any exist (e.g., "1,200.00")
                            clean_text = text_val.replace(',', '')
                            total_weight += float(clean_text)
                        except ValueError:
                            pass

        self.no_items_label.setText(str(item_count))
        self.total_weight_label.setText(f"{total_weight:.7f}")

    def get_valid_row_count(self):
        valid_count = 0
        for row in range(self.materials_table.rowCount()):
            item = self.materials_table.item(row, 0)  # Check the first column
            if item:  # check if may value ung first item, count if meron
                if item.text().strip():
                    valid_count += 1
        return valid_count

    def setup_rm_code_completer(self):
        self.rm_list = get_rm_code_lists()
        self.material_code_combo.clear()
        self.material_code_combo.addItems(self.rm_list)

        rm_completer = QCompleter(self.rm_list, self.material_code_combo)
        rm_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        rm_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.material_code_combo.setCompleter(rm_completer)

    def validate_rm_code(self):
        """Prevent invalid input."""
        current_text = self.material_code_combo.currentText()
        if current_text not in self.rm_list:
            self.material_code_combo.setCurrentIndex(0)

    def clear_material_inputs(self):
        self.material_code_combo.setCurrentIndex(0)
        self.material_code_lineedit.clear()
        self.large_scale_input.clear()
        self.small_scale_input.clear()
        self.total_weight_input.clear()

    def get_material_code(self):
        if self.raw_material_check.isChecked():
            return self.material_code_combo.currentText().strip()
        else:
            return self.material_code_lineedit.text().strip()

    def eventFilter(self, watched, event):
        # Check if the event is a key press and specifically the Tab key
        if watched == self.total_weight_input and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Tab:
                # Decide which Material widget to focus based on which is visible
                if self.material_code_lineedit.isVisible():
                    self.material_code_lineedit.setFocus()
                else:
                    # For editable combos, we focus the internal lineEdit
                    self.material_code_combo.setFocus()
                    self.material_code_combo.lineEdit().selectAll()

                return True  # This "consumes" the event so focus doesn't move elsewhere

        return super().eventFilter(watched, event)

    def sync_rm(self):
        thread = QThread()
        worker = SyncRM()
        worker.moveToThread(thread)

        loading_dialog = LoadingDialog("Syncing Production Data", self)

        worker.progress.connect(loading_dialog.update_progress)
        worker.finished.connect(
            lambda success, message: self.on_sync_finished(success, message, thread, loading_dialog)
        )

        thread.started.connect(worker.run)
        worker.finished.connect(thread.quit)
        thread.finished.connect(lambda: worker.deleteLater())
        thread.finished.connect(thread.deleteLater)

        thread.start()
        loading_dialog.exec()

    def on_sync_finished(self, success, message, thread, loading_dialog, sync_type=None):
        try:
            if loading_dialog.isVisible():
                loading_dialog.accept()

            if success:
                QMessageBox.information(self, "Sync Complete", message)
            else:
                QMessageBox.critical(self, "Sync Error", message)

        except Exception as e:
            print(f"Error in on_sync_finished: {e}")