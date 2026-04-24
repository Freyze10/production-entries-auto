from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
                             QPushButton, QLineEdit, QComboBox, QTableView,
                             QHeaderView, QGroupBox, QGridLayout, QMessageBox, QAbstractItemView)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
import qtawesome as fa

from css.styles import AppStyles
from table_model.model import TableModel
from db.read import get_user_management_list
from db.write import save_user_changes, log_audit_trail
from workstation.workstation_details import _get_workstation_info


class UserManagement(QWidget):
    def __init__(self):
        super().__init__()
        self.users_raw_data = []
        self.selected_user_id = None
        self.work_station = _get_workstation_info()
        self.setup_ui()
        self.refresh_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # === Header Card ===
        header_card = QFrame(objectName="HeaderCard")
        header_layout = QHBoxLayout(header_card)

        title_container = QVBoxLayout()
        title_label = QLabel("User Management", objectName="table_label")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        subtitle_label = QLabel("Configure system access, roles, and workstation mapping", objectName="light_label")
        title_container.addWidget(title_label)
        title_container.addWidget(subtitle_label)

        header_layout.addLayout(title_container)
        header_layout.addStretch()

        self.btn_refresh = QPushButton(" Refresh List", objectName="SecondaryButton")
        self.btn_refresh.setIcon(fa.icon('fa5s.sync-alt', color='white'))
        self.btn_refresh.clicked.connect(self.refresh_data)
        header_layout.addWidget(self.btn_refresh)

        main_layout.addWidget(header_card)

        # === Content Splitter (Table Left, Form Right) ===
        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)

        # --- LEFT: User List Table ---
        table_container = QFrame(objectName="ContentCard")
        table_v_layout = QVBoxLayout(table_container)

        search_layout = QHBoxLayout()
        self.search_input = QLineEdit(placeholderText="Search username or hostname...")
        self.search_input.textChanged.connect(self.filter_table)
        search_icon_label = QLabel()
        search_icon_label.setPixmap(fa.icon('fa5s.search', color=AppStyles.SLATE_400).pixmap(16, 16))
        search_layout.addWidget(search_icon_label)
        search_layout.addWidget(self.search_input)
        table_v_layout.addLayout(search_layout)

        self.user_table = QTableView()
        self.headers = ["ID", "Hostname", "Username", "IP Address", "MAC", "Role", "Department"]
        self.table_model = TableModel([], self.headers)
        self.user_table.setModel(self.table_model)
        self.user_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.user_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.user_table.clicked.connect(self.load_user_to_form)

        # Table Styling
        header = self.user_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.user_table.setColumnHidden(0, True)  # Hide User ID
        self.user_table.verticalHeader().setVisible(False)

        table_v_layout.addWidget(self.user_table)
        content_layout.addWidget(table_container, stretch=2)

        # --- RIGHT: Editor Form ---
        form_container = QFrame(objectName="ContentCard")
        form_container.setFixedWidth(400)
        form_v_layout = QVBoxLayout(form_container)

        self.form_group = QGroupBox("User Details Editor")
        grid = QGridLayout(self.form_group)
        grid.setSpacing(10)
        grid.setContentsMargins(10, 20, 10, 10)

        # Form Fields
        self.edit_username = QLineEdit()
        self.edit_password = QLineEdit()

        self.edit_hostname = QLineEdit()
        self.edit_ip = QLineEdit()
        self.edit_mac = QLineEdit()

        self.role_combo = QComboBox()
        self.role_combo.addItems(["Admin", "Editor", "Viewer"])
        # Note: Map Admin=1, Editor=2, Viewer=3 based on your DB

        grid.addWidget(QLabel("Username:"), 0, 0)
        grid.addWidget(self.edit_username, 0, 1)
        grid.addWidget(QLabel("Password:"), 1, 0)
        grid.addWidget(self.edit_password, 1, 1)
        grid.addWidget(QLabel("Hostname:"), 2, 0)
        grid.addWidget(self.edit_hostname, 2, 1)
        grid.addWidget(QLabel("IP Address:"), 3, 0)
        grid.addWidget(self.edit_ip, 3, 1)
        grid.addWidget(QLabel("MAC Address:"), 4, 0)
        grid.addWidget(self.edit_mac, 4, 1)
        grid.addWidget(QLabel("System Role:"), 5, 0)
        grid.addWidget(self.role_combo, 5, 1)

        form_v_layout.addWidget(self.form_group)

        # Form Buttons
        btn_layout = QHBoxLayout()
        self.btn_clear = QPushButton(" Clear", objectName="TertiaryButton")
        self.btn_clear.clicked.connect(self.clear_form)

        self.btn_save = QPushButton(" Save Changes", objectName="PrimaryButton")
        self.btn_save.setIcon(fa.icon('fa5s.save', color='white'))
        self.btn_save.clicked.connect(self.save_data)

        btn_layout.addWidget(self.btn_clear)
        btn_layout.addWidget(self.btn_save)
        form_v_layout.addLayout(btn_layout)
        form_v_layout.addStretch()

        content_layout.addWidget(form_container)
        main_layout.addLayout(content_layout)

    def refresh_data(self):
        # Fetch from DB: returns [(id, user, host, ip, mac, role_name, pass, role_id), ...]
        self.users_raw_data = get_user_management_list()

        # Prepare table display (strip out password and role_id for the view)
        display_rows = [row[:7] for row in self.users_raw_data]
        self.table_model.set_data(display_rows)
        self.clear_form()

    def filter_table(self):
        text = self.search_input.text().lower()
        self.table_model.filter_data(text)

    def load_user_to_form(self, index):
        # Find the full row data from the raw data using ID
        row_idx = index.row()
        user_id = self.table_model.data(self.table_model.index(row_idx, 0))

        user_data = next((u for u in self.users_raw_data if u[0] == user_id), None)

        if user_data:
            self.selected_user_id = user_data[0]
            self.edit_username.setText(user_data[2])
            self.edit_hostname.setText(user_data[1])
            self.edit_ip.setText(user_data[3])
            self.edit_mac.setText(user_data[4])
            self.edit_password.setText(user_data[7])

            # Set combo box based on role_id (1=Admin, 2=Editor, 3=Viewer)
            self.role_combo.setCurrentIndex(user_data[8] - 1)

    def clear_form(self):
        self.selected_user_id = None
        self.edit_username.clear()
        self.edit_password.clear()
        self.edit_hostname.clear()
        self.edit_ip.clear()
        self.edit_mac.clear()
        self.role_combo.setCurrentIndex(2)  # Default to Viewer

    def save_data(self):
        if not self.selected_user_id:
            QMessageBox.warning(self, "Selection Required", "Please select a user from the list first.")
            return

        data = {
            "username": self.edit_username.text().strip(),
            "hostname": self.edit_hostname.text().strip(),
            "password": self.edit_password.text().strip(),
            "ip": self.edit_ip.text().strip(),
            "mac": self.edit_mac.text().strip(),
            "role_id": self.role_combo.currentIndex() + 1
        }

        # Validation
        if not data["username"] or not data["password"]:
            QMessageBox.critical(self, "Invalid Data", "Username and Password cannot be empty.")
            return

        success = save_user_changes(self.selected_user_id, data)
        if success:
            QMessageBox.information(self, "Success", "User details updated successfully.")

            audit_details = f"Hostname: {data["hostname"]}\\{data["username"]} has been successfully Updated"
            log_audit_trail(self.work_station['m'], "UPDATE", audit_details)

            self.refresh_data()
