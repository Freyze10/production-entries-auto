from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QFrame, QHBoxLayout, QGroupBox, QGridLayout, QLineEdit, \
    QLabel, QComboBox

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
        left_column.setSpacing(6)

        # Production Information Card
        primary_card = QGroupBox("Production Information")
        primary_layout = QGridLayout(primary_card)
        primary_layout.setSpacing(4)
        primary_layout.setContentsMargins(8, 12, 8, 8)

        row = 0

        # WIP No (Production ID)
        self.wip_no_input = QLineEdit()
        self.wip_no_input.setStyleSheet("background-color: #e9ecef;")
        primary_layout.addWidget(QLabel("WIP No:"), row, 0)
        primary_layout.addWidget(self.wip_no_input, row, 1)
        row += 1

        # Production ID
        self.production_id_input = QLineEdit()
        self.production_id_input.setPlaceholderText("0098988")
        self.production_id_input.setStyleSheet("background-color: #fff9c4;")
        primary_layout.addWidget(QLabel("Production ID:"), row, 0)
        primary_layout.addWidget(self.production_id_input, row, 1)
        row += 1

        # Form Type
        self.form_type_combo = QComboBox()
        self.form_type_combo.addItems(["", "New", "Correction"])
        self.form_type_combo.setStyleSheet("background-color: #fff9c4;")
        primary_layout.addWidget(QLabel("Form Type:"), row, 0)
        primary_layout.addWidget(self.form_type_combo, row, 1)
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