from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QFrame, QHBoxLayout, QGroupBox, QGridLayout, QLineEdit, \
    QLabel, QComboBox, QTextEdit

from util.field_format import format_to_float, SmartDateEdit, production_mixing_time
from workstation.workstation_details import _get_workstation_info


class MBManualEntry(QWidget):
    def __init__(self):  # , username, user_role, log_audit_trail
        super().__init__()
        # self.username = username
        # self.user_role = user_role
        # self.log_audit_trail = log_audit_trail
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
        left_column.setSpacing(8)

        # Production Information Card
        primary_card = QGroupBox("Production Information")
        primary_layout = QGridLayout(primary_card)
        primary_layout.setSpacing(4)
        primary_layout.setContentsMargins(8, 12, 8, 8)

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
        right_column.setSpacing(6)

        # Materials Card
        material_card = QGroupBox("Material Composition")
        material_layout = QVBoxLayout(material_card)
        material_layout.setContentsMargins(8, 12, 8, 8)
        material_layout.setSpacing(6)




        right_column.addWidget(material_card)
        scroll_layout.addLayout(right_column, stretch=1)

        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)