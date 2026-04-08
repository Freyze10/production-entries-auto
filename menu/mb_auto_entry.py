from datetime import datetime

from PyQt6.QtCore import Qt, QThread, QDate
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QFrame, QHBoxLayout, QGroupBox, QGridLayout, QLineEdit, \
    QLabel, QComboBox, QTextEdit, QTableWidget, QHeaderView, QAbstractItemView, QPushButton, QMessageBox, \
    QTableWidgetItem, QCompleter, QDialog
import qtawesome as fa

from db.legacy import SyncRM
from db.read import get_latest_prod_id, get_formula_select, get_formula_materials, \
    get_all_completer_data, get_single_production_details, get_single_production_data
from table_model import table_spacing
from print.print_preview import ProductionPrintPreview
from table_model.table_auto_compute import process_formulation_to_table
from util.field_format import format_to_float, SmartDateEdit, production_mixing_time, NumericTableWidgetItem
from util.loading import LoadingDialog
from workstation.workstation_details import _get_workstation_info


class MBAutoEntry(QWidget):
    def __init__(self, prod_id=0):  # , username, user_role, log_audit_trail
        super().__init__()
        self.prod_id = prod_id
        self.prod_results = None
        self.prod_materials = None
        self.work_station = _get_workstation_info()
        # self.user_id = f"{self.work_station['h']} # {self.user_role}"
        # Track current production for edit/view
        self.current_production_id = None
        self.formulation_details = None

        self.setup_ui()
        self.setup_auto_completers()

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

        primary_card = QGroupBox("Production Information  -  Masterbatch")
        primary_layout = QGridLayout(primary_card)
        primary_layout.setSpacing(6)
        primary_layout.setContentsMargins(10, 18, 10, 12)

        self.production_id_input = QLineEdit(objectName='required')
        self.production_id_input.setPlaceholderText("000000")

        self.select_formula_btn = QPushButton()
        self.select_formula_btn.setIcon(
            fa.icon('mdi.newspaper-variant-multiple-outline', color='#0078d4', scale_factor=1.5))
        self.select_formula_btn.setFixedSize(36, 36)
        self.select_formula_btn.clicked.connect(self.show_formulation_selector)
        self.select_formula_btn.setToolTip("Select Formula")

        self.form_type_combo = QComboBox()
        self.form_type_combo.addItems(["", "New", "Correction"])
        self.form_type_combo.setStyleSheet("background-color: #FDECCE;")

        select_formula_layout = QHBoxLayout()

        self.product_code_input = QLineEdit(objectName='required')
        self.product_code_input.setPlaceholderText("Enter product code")
        primary_layout.addWidget(QLabel("Product Code:"), 0, 0)
        select_formula_layout.addWidget(self.product_code_input)
        select_formula_layout.addWidget(self.select_formula_btn)
        primary_layout.addLayout(select_formula_layout, 0, 1)

        self.product_color_input = QLineEdit()
        self.product_color_input.setPlaceholderText("Enter product color")
        primary_layout.addWidget(QLabel("Product Color:"), 1, 0)
        primary_layout.addWidget(self.product_color_input, 1, 1)

        dosage_layout = QHBoxLayout()
        self.dosage_input = QLineEdit(objectName='required')
        self.dosage_input.setPlaceholderText("0.000000")
        self.dosage_input.focusOutEvent = lambda event: format_to_float(self, event, self.dosage_input)
        dosage_layout.addWidget(self.dosage_input)
        dosage_layout.addWidget(QLabel("LD (%)"))
        self.ld_percent_input = QLineEdit()
        self.ld_percent_input.setPlaceholderText("0.000000")
        self.ld_percent_input.focusOutEvent = lambda event: format_to_float(self, event, self.ld_percent_input)
        dosage_layout.addWidget(self.ld_percent_input)
        primary_layout.addWidget(QLabel("Dosage:"), 2, 0)
        primary_layout.addLayout(dosage_layout, 2, 1)

        self.customer_input = QLineEdit(objectName='required')
        self.customer_input.setPlaceholderText("Enter customer")
        primary_layout.addWidget(QLabel("Customer:"), 3, 0)
        primary_layout.addWidget(self.customer_input, 3, 1)

        self.lot_no_input = QLineEdit(objectName='required')
        self.lot_no_input.setPlaceholderText("Enter lot number")
        primary_layout.addWidget(QLabel("Lot No:"), 4, 0)
        primary_layout.addWidget(self.lot_no_input, 4, 1)

        self.production_date_input = SmartDateEdit()
        self.production_date_input.setText(QDate.currentDate().toString("MM/dd/yyyy"))
        self.production_date_input.setStyleSheet("background-color: #FDECCE;")
        primary_layout.addWidget(QLabel("Tentative Production Date:"), 5, 0)
        primary_layout.addWidget(self.production_date_input, 5, 1)

        self.confirmation_date_input = SmartDateEdit()
        primary_layout.addWidget(QLabel("Confirmation Date \n(For Inventory Only):"), 6, 0)
        primary_layout.addWidget(self.confirmation_date_input, 6, 1)

        self.order_form_no_combo = QComboBox()
        self.order_form_no_combo.setEditable(True)
        self.order_form_no_combo.setPlaceholderText("Enter order form number")
        self.order_form_no_combo.setStyleSheet("background-color: #FDECCE;")
        primary_layout.addWidget(QLabel("Order Form No:"), 7, 0)
        primary_layout.addWidget(self.order_form_no_combo, 7, 1)

        self.colormatch_no_input = QLineEdit()
        self.colormatch_no_input.setPlaceholderText("Enter colormatch number")
        primary_layout.addWidget(QLabel("Colormatch No:"), 8, 0)
        primary_layout.addWidget(self.colormatch_no_input, 8, 1)

        self.matched_date_input = SmartDateEdit()
        primary_layout.addWidget(QLabel("Matched Date:"), 9, 0)
        primary_layout.addWidget(self.matched_date_input, 9, 1)

        self.formulation_id_input = QLineEdit(objectName='gray_bg')
        self.formulation_index = QLineEdit()
        self.formulation_id_input.setPlaceholderText("0")
        self.formulation_id_input.setReadOnly(True)
        primary_layout.addWidget(QLabel("Formulation ID:"), 10, 0)
        primary_layout.addWidget(self.formulation_id_input, 10, 1)

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

        primary_layout.addWidget(QLabel("Mixing Time:"), 11, 0)
        primary_layout.addLayout(mixing_machine_layout, 11, 1)

        qty_layout = QHBoxLayout()
        qty_layout.setSpacing(9)

        self.qty_required_input = QLineEdit(objectName='required')
        self.qty_required_input.setPlaceholderText("0.000000")
        self.qty_required_input.focusOutEvent = lambda event: format_to_float(self, event, self.qty_required_input)
        qty_layout.addWidget(self.qty_required_input)

        qty_batch_label = QLabel("Qty. Per Batch:")
        qty_layout.addWidget(qty_batch_label)

        self.qty_per_batch_input = QLineEdit(objectName='required')
        self.qty_per_batch_input.setPlaceholderText("0.000000")
        self.qty_per_batch_input.focusOutEvent = lambda event: format_to_float(self, event, self.qty_per_batch_input)
        qty_layout.addWidget(self.qty_per_batch_input)

        primary_layout.addWidget(QLabel("Qty. Req:"), 12, 0)
        primary_layout.addLayout(qty_layout, 12, 1)

        self.prepared_by_input = QLineEdit(objectName='required')
        self.prepared_by_input.setPlaceholderText("Enter preparer name")
        primary_layout.addWidget(QLabel("Prepared By:"), 13, 0)
        primary_layout.addWidget(self.prepared_by_input, 13, 1)

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Enter any notes...")
        self.notes_input.setMinimumHeight(30)
        self.notes_input.setMaximumHeight(50)
        primary_layout.addWidget(QLabel("Notes:"), 14, 0)
        primary_layout.addWidget(self.notes_input, 14, 1)

        left_column.addWidget(primary_card)

        scroll_layout.addLayout(left_column, stretch=1)

        right_column = QVBoxLayout()
        right_column.setSpacing(8)

        material_card = QGroupBox("Material Composition")
        material_layout = QVBoxLayout(material_card)
        material_layout.setContentsMargins(10, 18, 10, 12)
        material_layout.setSpacing(8)

        # Add Production ID and Form Type before the table
        header_layout = QGridLayout()
        header_layout.addWidget(QLabel("Production ID:"), 0, 0)
        header_layout.addWidget(self.production_id_input, 0, 1)
        header_layout.addWidget(QLabel("Form Type:"), 1, 0)
        header_layout.addWidget(self.form_type_combo, 1, 1)
        material_layout.addLayout(header_layout)

        self.materials_table = QTableWidget()
        self.materials_table.setColumnCount(4)
        self.materials_table.setHorizontalHeaderLabels([
            "Material Name", "Large Scale (KG)", "Small Scale (G)", "Total Weight (KG)"
        ])
        self.materials_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.materials_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.materials_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.materials_table.verticalHeader().setVisible(False)
        self.materials_table.setAlternatingRowColors(True)
        self.materials_table.setMinimumHeight(300)
        self.materials_table.setStyleSheet("""
                   color: #343a40; background-color: transparent;
               """)
        self.materials_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.materials_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        material_layout.addWidget(self.materials_table)

        total_layout = QHBoxLayout()
        total_layout.addWidget(QLabel("No. of Items:"))
        self.no_items_label = QLabel("0")
        self.no_items_label.setStyleSheet("font-weight: bold; color: #0078d4;")
        total_layout.addWidget(self.no_items_label)
        total_layout.addStretch()
        total_layout.addWidget(QLabel("Total Weight:"))
        self.total_weight_label = QLabel("0.000000")
        self.total_weight_label.setStyleSheet("font-weight: bold; color: #0078d4;")
        total_layout.addWidget(self.total_weight_label)

        material_layout.addLayout(total_layout)

        # Encoding Information
        encoding_layout = QGridLayout()
        encoding_layout.setSpacing(6)

        self.encoded_by_display = QLineEdit(objectName='gray_bg')
        self.encoded_by_display.setReadOnly(True)
        self.encoded_by_display.setText(self.work_station['u'])

        encoding_layout.addWidget(QLabel("Encoded By:"), 0, 0)
        encoding_layout.addWidget(self.encoded_by_display, 0, 1)

        self.production_confirmation_display = QLineEdit(objectName='required')
        self.production_confirmation_display.setPlaceholderText("mm/dd/yyyy h:m:s")
        self.production_confirmation_display.setReadOnly(True)
        encoding_layout.addWidget(QLabel("Production Confirmation Encoded On:"), 1, 0)
        encoding_layout.addWidget(self.production_confirmation_display, 1, 1)

        self.production_encoded_display = QLineEdit(objectName='gray_bg')
        self.production_encoded_display.setText(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.production_encoded_display.setReadOnly(True)
        encoding_layout.addWidget(QLabel("Production Encoded On:"), 2, 0)
        encoding_layout.addWidget(self.production_encoded_display, 2, 1)

        material_layout.addLayout(encoding_layout)

        right_column.addWidget(material_card)
        scroll_layout.addLayout(right_column, stretch=1)

        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        generate_btn = QPushButton("Generate", objectName="SuccessButton")
        generate_btn.setIcon(fa.icon('fa5s.cogs', color='white'))
        generate_btn.clicked.connect(self.generate_production)
        button_layout.addWidget(generate_btn)

        tumbler_btn = QPushButton("Tumbler", objectName="InfoButton")
        tumbler_btn.setIcon(fa.icon('fa5s.recycle', color='white'))
        # tumbler_btn.clicked.connect(self.tumbler_function)
        button_layout.addWidget(tumbler_btn)


        print_btn = QPushButton("Print", objectName="SecondaryButton")
        print_btn.setIcon(fa.icon('fa5s.print', color='white'))
        print_btn.clicked.connect(self.print_production)
        button_layout.addWidget(print_btn)

        new_btn = QPushButton("New", objectName="PrimaryButton")
        new_btn.setIcon(fa.icon('fa5s.file', color='white'))
        new_btn.clicked.connect(self.new_production)
        button_layout.addWidget(new_btn)

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

    def setup_auto_completers(self):
        data = get_all_completer_data()

        def setup_comp(widget, items):
            # Convert all items to strings (in case order_no is int)
            str_items = [str(i) for i in items if i]
            completer = QCompleter(str_items)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            completer.setFilterMode(Qt.MatchFlag.MatchStartsWith)
            widget.setCompleter(completer)

        def setup_combo_comp(combo, items):
            if not items: items = []
            # 1. Create list with empty string at the first index
            str_items = [""] + [str(i) for i in items if i]

            # 2. Add items to the ComboBox dropdown
            combo.clear()
            combo.addItems(str_items)
            completer = combo.completer()
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            completer.setFilterMode(Qt.MatchFlag.MatchStartsWith)
            completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)

            # 4. Set default to the empty string (Index 0)
            combo.setCurrentIndex(0)

        setup_comp(self.customer_input, data['customers'])
        setup_comp(self.product_code_input, data['prod_codes'])
        setup_comp(self.lot_no_input, data['lots'])
        setup_combo_comp(self.order_form_no_combo, data.get('orders'))



    def show_formulation_selector(self):
        """Show dialog to select a formulation and populate its materials."""
        try:
            if not self.product_code_input.text().strip():
                QMessageBox.warning(self, "No Product Code",
                                    "Please enter a product code and try again.")
                return

            dialog = QDialog(self)
            dialog.setWindowTitle("Select Formula")
            dialog.setMinimumSize(900, 640)

            layout = QVBoxLayout(dialog)

            product_code = self.product_code_input.text().strip()
            header = QLabel(f"Product Code: {product_code}")
            header.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            header.setStyleSheet("color: #0078d4; background-color: #e3f2fd; padding: 8px;")
            layout.addWidget(header)

            self.formula_table = QTableWidget()
            self.formula_table.setColumnCount(7)
            self.formula_table.setHorizontalHeaderLabels([
                "Index No.", "Formula No.", "Customer", "Product Code",
                "Product Color", "Dosage", "LD (%)"
            ])

            try:
                formula_data = get_formula_select(product_code)
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"Failed to fetch formulas: {e}")
                return

            self.formula_table.setRowCount(len(formula_data))

            for r, row in enumerate(formula_data):
                row = list(row) + [""] * (7 - len(row))
                for c, value in enumerate(row[:7]):
                    item = QTableWidgetItem(str(value))
                    if r == 2:
                        item.setBackground(Qt.GlobalColor.cyan)
                    self.formula_table.setItem(r, c, item)

            self.formula_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            self.formula_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            self.formula_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
            self.formula_table.verticalHeader().setVisible(False)
            self.formula_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            self.formula_table.setAlternatingRowColors(True)
            self.formula_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            self.formula_table.itemSelectionChanged.connect(self.show_formulation_selected)
            self.formula_table.itemDoubleClicked.connect(
                lambda item: self._on_formula_double_clicked(dialog, item)
            )

            layout.addWidget(self.formula_table)

            materials_lbl = QLabel("Materials:")
            materials_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            layout.addWidget(materials_lbl)

            self.materials_table_selector = QTableWidget()
            self.materials_table_selector.setColumnCount(2)
            self.materials_table_selector.setHorizontalHeaderLabels(["Material Code", "Concentration"])
            self.materials_table_selector.setRowCount(0)
            self.materials_table_selector.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            self.materials_table_selector.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
            self.materials_table_selector.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            self.materials_table_selector.verticalHeader().setVisible(False)
            self.materials_table_selector.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            self.materials_table_selector.setAlternatingRowColors(True)
            self.materials_table_selector.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            layout.addWidget(self.materials_table_selector)

            btn_layout = QHBoxLayout()
            btn_layout.addStretch()

            ok_btn = QPushButton("OK")
            ok_btn.setObjectName("SuccessButton")
            # ok_btn.clicked.connect(
            #     lambda: self.load_selected_formula(dialog, self.formula_table, self.materials_table_selector))
            btn_layout.addWidget(ok_btn)

            cancel_btn = QPushButton("CANCEL")
            cancel_btn.setObjectName("DangerButton")
            cancel_btn.clicked.connect(dialog.reject)
            btn_layout.addWidget(cancel_btn)

            layout.addLayout(btn_layout)

            if formula_data:
                self.formula_table.selectRow(0)

            dialog.exec()
        except Exception as e:
            print(e)

    def show_formulation_selected(self):
        """Fill the materials table for the currently selected formula."""
        rows = self.formula_table.selectionModel().selectedRows()
        if not rows:
            return

        row_idx = rows[0].row()
        formula_no_item = self.formula_table.item(row_idx, 1)
        if not formula_no_item:
            return
        formula_no = formula_no_item.text().strip()

        try:
            materials = get_formula_materials(formula_no)
        except Exception as e:
            QMessageBox.critical(self, "Database Error",
                                 f"Could not load materials for formula {formula_no}: {e}")
            materials = []

        self.materials_table_selector.setRowCount(len(materials))
        for r, (mat_code, conc) in enumerate(materials):
            self.materials_table_selector.setItem(r, 0, QTableWidgetItem(str(mat_code)))
            self.materials_table_selector.setItem(r, 1, QTableWidgetItem(str(conc)))

    def _on_formula_double_clicked(self, dialog, item):
        """Called when user double-clicks a row in the formula selector."""
        row = item.row()
        # Ensure the row is selected (in case double-click happens before selection)
        self.formula_table.selectRow(row)
        # Trigger the same logic as the OK button
        self.load_selected_formula(dialog, self.formula_table, self.materials_table_selector)

    def load_selected_formula(self, dialog, formula_table, materials_table):
        """Copy the selected formula + materials into the main production form."""
        sel = formula_table.selectionModel().selectedRows()
        if not sel:
            QMessageBox.warning(dialog, "No Selection", "Please select a formula first.")
            return

        row = sel[0].row()

        self.formulation_index.setText(formula_table.item(row, 0).text())
        self.formulation_id_input.setText(formula_table.item(row, 1).text())
        self.customer_input.setText(formula_table.item(row, 2).text())
        self.product_code_input.setText(formula_table.item(row, 3).text())
        self.product_color_input.setText(formula_table.item(row, 4).text())
        self.dosage_input.setText(formula_table.item(row, 5).text())
        self.ld_percent_input.setText(formula_table.item(row, 6).text())

        self.formulation_details = materials_table

        self.select_formula_btn.setIcon(
            fa.icon('mdi.check-underline', color='#0078d4', scale_factor=1.5))

        self.materials_table.setRowCount(0)

        # for mat_row in range(materials_table.rowCount()):
        #     mat_code = materials_table.item(mat_row, 0).text()
        #     conc_str = materials_table.item(mat_row, 1).text()
        #     try:
        #         concentration = float(conc_str.replace("%", "").strip())
        #     except ValueError:
        #         concentration = 0.0
        #
        #     dosage = float(self.dosage_input.text())
        #     masterbatch = 100
        #     large_scale = concentration * 0.1
        #     small_scale = concentration * 10
        #     total_weight = large_scale + (small_scale / 1000)
        #     total_loss = total_weight * 0.02
        #     total_consumption = total_weight + total_loss
        #
        #     new_row = self.materials_table.rowCount()
        #     self.materials_table.insertRow(new_row)
        #
        #     self.materials_table.setItem(new_row, 0, QTableWidgetItem(mat_code))
        #     self.materials_table.setItem(new_row, 1, NumericTableWidgetItem(large_scale, is_float=True))
        #     self.materials_table.setItem(new_row, 2, NumericTableWidgetItem(small_scale, is_float=True))
        #     self.materials_table.setItem(new_row, 3, NumericTableWidgetItem(total_weight, is_float=True))
        #     self.materials_table.setItem(new_row, 4, NumericTableWidgetItem(total_loss, is_float=True))
        #     self.materials_table.setItem(new_row, 5, NumericTableWidgetItem(total_consumption, is_float=True))
        #
        # self.update_totals()
        dialog.accept()
        QMessageBox.information(self, "Success", "Formula loaded successfully!")

    def display_details(self):
        self.production_id_input.setText(str(self.prod_results['prod_id']))
        self.form_type_combo.setCurrentText(str(self.prod_results['form_type']))
        self.product_code_input.setText(str(self.prod_results['prod_code']))
        self.product_color_input.setText(str(self.prod_results['prod_color']))
        self.formulation_id_input.setText(str(self.prod_results['form_id']))
        self.dosage_input.setText(f"{self.prod_results['dosage']:.6f}")
        self.ld_percent_input.setText(f"{self.prod_results['ld']:.6f}")
        self.customer_input.setText(str(self.prod_results['customer']))
        self.lot_no_input.setText(str(self.prod_results['lot_no']))
        self.order_form_no_combo.setCurrentText(str(self.prod_results['order_no']))
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
        self.total_weight_label.setText(f"{self.prod_results['quantity_prod']:.6f}")

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

    def new_production(self):
        """Initialize a new production entry."""
        self.current_production_id = None
        try:
            latest_prod = get_latest_prod_id()
            self.production_id_input.setText(str(latest_prod + 1))
        except Exception as e:
            self.production_id_input.setText("1")

        self.form_type_combo.setCurrentIndex(0)
        self.product_code_input.clear()
        self.product_color_input.clear()
        self.formulation_id_input.clear()
        self.dosage_input.clear()
        self.ld_percent_input.clear()
        self.customer_input.clear()
        self.lot_no_input.clear()
        self.production_date_input.setText(QDate.currentDate().toString("MM/dd/yyyy"))
        self.confirmation_date_input.setText("")
        self.order_form_no_combo.clear()
        self.colormatch_no_input.clear()
        self.matched_date_input.setText("")
        self.mixing_time_input.clear()
        self.machine_no_input.clear()
        self.qty_required_input.clear()
        self.qty_per_batch_input.clear()
        self.prepared_by_input.clear()
        self.notes_input.clear()

        self.encoded_by_display.setText(self.work_station['u'])
        self.production_encoded_display.setText(datetime.now().strftime("%m/%d/%Y %I:%M:%S %p"))
        self.production_confirmation_display.clear()

        self.select_formula_btn.setIcon(
            fa.icon('mdi.newspaper-variant-multiple-outline', color='#0078d4', scale_factor=1.5))

        if self.prod_results:
            self.prod_results = None

        self.materials_table.setRowCount(0)
        self.update_totals()

    def generate_production(self):
        # Get the input values as text first
        qty_req_text = self.qty_required_input.text().strip()
        qty_batch_text = self.qty_per_batch_input.text().strip()

        if not qty_req_text or not qty_batch_text:
            QMessageBox.warning(
                self,
                "Missing Information",
                "Please fill out both 'Quantity Required' and 'Quantity per Batch' fields before proceeding.",
                QMessageBox.Ok
            )
            return
        try:
            quantity_req = float(qty_req_text)
            quantity_batch = float(qty_batch_text)

            if quantity_batch == 0:
                QMessageBox.warning(
                    self,
                    "Invalid Value",
                    "Quantity per Batch cannot be zero.",
                    QMessageBox.Ok
                )
                return

            batch_size = quantity_req / quantity_batch

            process_formulation_to_table(
                source_table=self.formulation_details,
                target_table=self.materials_table,
                total_weight=quantity_req,
                batch_divisor=float(batch_size),
                base_divisor=100.0
            )

            self.update_totals()

        except ValueError:
            QMessageBox.warning(
                self,
                "Invalid Input",
                "Please enter valid numbers for Quantity Required and Quantity per Batch.",
                QMessageBox.Ok
            )

    def print_production(self):
        if not self.production_id_input.text().strip():
            QMessageBox.warning(self, "No Data", "Please create or load a production record first.")
            return

        try:
            production_date = ''

            # Check if self.result exists and contains the key
            if self.prod_results and self.prod_results.get('production_date'):
                production_date = self.prod_results['production_date'].strftime("%m/%d/%y")
            else:
                # Handle the case where it's missing or None
                text_date = self.production_date_input.text().strip()

                # Check if text_date is already in "MM/dd/yyyy" or "yyyy-MM-dd"
                if "-" in text_date:
                    production_date = datetime.strptime(text_date, "%Y-%m-%d").strftime("%m/%d/%y")
                else:
                    production_date = datetime.strptime(text_date, "%m/%d/%Y").strftime("%m/%d/%y")

        except Exception as e:
            print("Error:", e)
            production_date = ""
        # === Collect Data ===
        production_data = {
            'prod_id': self.production_id_input.text().strip(),
            'form_type': self.form_type_combo.currentText(),
            'production_date': production_date,
            'order_form_no': self.order_form_no_combo.currentText().strip(),
            'formulation_id': self.formulation_id_input.text().strip(),
            'product_code': self.product_code_input.text().strip(),
            'product_color': self.product_color_input.text().strip(),
            'dosage': self.dosage_input.text().strip(),
            'customer': self.customer_input.text().strip(),
            'lot_number': self.lot_no_input.text().strip(),
            'mixing_time': self.mixing_time_input.text().strip(),
            'machine_no': self.machine_no_input.text().strip(),
            'qty_required': self.qty_required_input.text().strip(),
            'qty_per_batch': self.qty_per_batch_input.text().strip(),
            'qty_produced': self.total_weight_label.text().strip(),
            'prepared_by': self.prepared_by_input.text().strip(),
            'notes': self.notes_input.toPlainText().strip(),
            'approved_by': 'M. VERDE'
        }

        materials_data = []
        for row in range(self.materials_table.rowCount()):
            it0 = self.materials_table.item(row, 0)
            it1 = self.materials_table.item(row, 1)
            it2 = self.materials_table.item(row, 2)
            it3 = self.materials_table.item(row, 3)

            # If the first column is empty, we treat this as a blank separator row
            m_code = it0.text().strip() if it0 else ""

            materials_data.append({
                'material_code': m_code,  # Keep it as "" if empty
                'large_scale': it1.text().strip() if it1 else '0',
                'small_scale': it2.text().strip() if it2 else '0',
                'total_weight': it3.text().strip() if it3 else '0'
            })

        # === Open Preview with exec()===
        preview = ProductionPrintPreview(production_data, materials_data, self)

        # Connect audit log
        # def on_printed(prod_id):
        #     self.log_audit_trail(
        #         "Print Production",
        #         f"(Manual) Prod ID: {prod_id} | Production Date: {production_data['production_date']}"
        #     )

        # preview.printed.connect(on_printed)

        # This blocks until user closes or prints
        preview.exec()

    def clear_material_table(self):
        self.materials_table.setRowCount(0)
        self.clear_material_inputs()
        self.update_totals()

    def update_totals(self):
        total_weight = 0.0
        item_count = self.get_valid_row_count()

        for row in range(self.materials_table.rowCount()):
            item = self.materials_table.item(row, 3)  # Check column 3 (Weight)

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