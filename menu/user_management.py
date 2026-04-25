from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
                             QPushButton, QLineEdit, QComboBox, QTableView,
                             QHeaderView, QGroupBox, QGridLayout, QMessageBox,
                             QAbstractItemView, QTabWidget, QTableWidget, QCheckBox, QTableWidgetItem)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
import qtawesome as fa

from css.styles import AppStyles
from db.update import update_role_permissions
from table_model.model import TableModel
from db.read import (get_user_management_list, get_all_roles,
                     get_access_points, get_permission_matrix)
from db.write import (save_user_changes, log_audit_trail, add_new_role)
from workstation.workstation_details import _get_workstation_info


class PermissionsManager(QWidget):
    def __init__(self):
        super().__init__()
        self.work_station = _get_workstation_info()
        self.setup_ui()

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        # Main Tab Widget
        self.tabs = QTabWidget()
        self.tabs.setObjectName("MainTabs")

        # Add Tabs
        self.tabs.addTab(self.create_user_management_tab(), "User Management")
        self.tabs.addTab(self.create_role_management_tab(), "Role & Access Matrix")

        self.main_layout.addWidget(self.tabs)
        self.setStyleSheet(AppStyles.MAIN_WINDOW_STYLESHEET)

    # =========================================================================
    # TAB 1: USER MANAGEMENT
    # =========================================================================
    def create_user_management_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        content_container = QWidget()
        content_main_layout = QVBoxLayout(content_container)

        # Header Card
        header_card = QFrame(objectName="HeaderCard")
        header_layout = QHBoxLayout(header_card)
        title_container = QVBoxLayout()
        title_container.addWidget(QLabel("User Access Control", objectName="table_label"))
        title_container.addWidget(
            QLabel("Manage specific user credentials and workstation bindings", objectName="light_label"))
        header_layout.addLayout(title_container)
        header_layout.addStretch()
        self.btn_refresh = QPushButton(" Refresh List", objectName="SecondaryButton")
        self.btn_refresh.clicked.connect(self.refresh_data)
        header_layout.addWidget(self.btn_refresh)
        content_main_layout.addWidget(header_card)

        # Content Splitter
        content_split = QHBoxLayout()

        # Table (Left)
        table_container = QFrame(objectName="ContentCard")
        table_v = QVBoxLayout(table_container)
        self.search_input = QLineEdit(placeholderText="Search user...")
        self.search_input.textChanged.connect(self.filter_table)
        table_v.addWidget(self.search_input)

        self.user_table = QTableView()
        self.user_table.verticalHeader().setVisible(False)  # HIDE VERTICAL HEADER
        self.headers = ["ID", "Hostname", "Username", "IP Address", "MAC", "Role", "Department"]
        self.table_model = TableModel([], self.headers)
        self.user_table.setModel(self.table_model)
        self.user_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.user_table.clicked.connect(self.load_user_to_form)
        table_v.addWidget(self.user_table)
        content_split.addWidget(table_container, stretch=2)

        # Form (Right)
        form_container = QFrame(objectName="ContentCard")
        form_container.setFixedWidth(350)
        form_v = QVBoxLayout(form_container)
        self.edit_username = QLineEdit();
        self.edit_password = QLineEdit()
        self.edit_hostname = QLineEdit();
        self.edit_ip = QLineEdit();
        self.edit_mac = QLineEdit()
        self.role_combo = QComboBox()

        grid = QGridLayout()
        grid.addWidget(QLabel("Username:"), 0, 0);
        grid.addWidget(self.edit_username, 0, 1)
        grid.addWidget(QLabel("Password:"), 1, 0);
        grid.addWidget(self.edit_password, 1, 1)
        grid.addWidget(QLabel("Hostname:"), 2, 0);
        grid.addWidget(self.edit_hostname, 2, 1)
        grid.addWidget(QLabel("IP Address:"), 3, 0);
        grid.addWidget(self.edit_ip, 3, 1)
        grid.addWidget(QLabel("MAC Address:"), 4, 0);
        grid.addWidget(self.edit_mac, 4, 1)
        grid.addWidget(QLabel("Role:"), 5, 0);
        grid.addWidget(self.role_combo, 5, 1)
        form_v.addLayout(grid)

        self.btn_save = QPushButton(" Save Changes", objectName="PrimaryButton")
        self.btn_save.clicked.connect(self.save_data)
        form_v.addWidget(self.btn_save)
        form_v.addStretch()

        content_split.addWidget(form_container)
        content_main_layout.addLayout(content_split)
        layout.addWidget(content_container)

        self.refresh_data()
        return tab

    # =========================================================================
    # TAB 2: ROLE MANAGEMENT
    # =========================================================================
    def create_role_management_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # --- Top: Add New Role Group ---
        add_role_group = QGroupBox("Create New System Role")
        add_role_layout = QHBoxLayout(add_role_group)
        self.new_role_input = QLineEdit(placeholderText="Role Name")
        self.new_dept_input = QLineEdit(placeholderText="Department")
        btn_add_role = QPushButton(" Add Role", objectName="SuccessButton")
        btn_add_role.clicked.connect(self.handle_add_role)
        add_role_layout.addWidget(QLabel("Name:"));
        add_role_layout.addWidget(self.new_role_input)
        add_role_layout.addWidget(QLabel("Dept:"));
        add_role_layout.addWidget(self.new_dept_input)
        add_role_layout.addWidget(btn_add_role)
        layout.addWidget(add_role_group)

        # --- Middle: Permission Matrix ---
        matrix_group = QFrame(objectName="ContentCard")
        matrix_layout = QVBoxLayout(matrix_group)
        matrix_layout.addWidget(QLabel("Permission Access Matrix", objectName="table_label"))

        self.matrix_table = QTableWidget()
        self.matrix_table.verticalHeader().setVisible(False)  # HIDE VERTICAL HEADER
        self.matrix_table.setAlternatingRowColors(True)
        matrix_layout.addWidget(self.matrix_table)

        btn_footer = QHBoxLayout()
        btn_footer.addStretch()
        btn_refresh_matrix = QPushButton(" Reload Matrix", objectName="SecondaryButton")
        btn_refresh_matrix.clicked.connect(self.refresh_matrix)
        btn_save_matrix = QPushButton(" Save Permissions", objectName="PrimaryButton")
        btn_save_matrix.clicked.connect(self.save_permissions)
        btn_footer.addWidget(btn_refresh_matrix);
        btn_footer.addWidget(btn_save_matrix)
        layout.addWidget(matrix_group);
        layout.addLayout(btn_footer)

        self.refresh_matrix()
        return tab

    def refresh_matrix(self):
        """Fetches Roles and Access Points to build the toggle grid."""
        roles = get_all_roles()
        access_points = get_access_points()
        permissions = get_permission_matrix()

        self.matrix_table.setRowCount(len(access_points))
        self.matrix_table.setColumnCount(len(roles) + 1)  # Column 0 for names

        # Build Headers
        headers = ["ACCESS"] + [r[1] for r in roles]
        self.matrix_table.setHorizontalHeaderLabels(headers)
        self.matrix_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.matrix_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)

        self.checkbox_map = {}

        for a_idx, ap in enumerate(access_points):
            # 1. Set Access Name in Column 0
            name_item = QTableWidgetItem(ap[1])
            name_item.setFlags(name_item.flags() ^ Qt.ItemFlag.ItemIsEditable)  # Make read-only
            name_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            self.matrix_table.setItem(a_idx, 0, name_item)

            # 2. Set Checkboxes in remaining columns
            for r_idx, role in enumerate(roles):
                cb = QCheckBox()
                cb.setObjectName("RawMaterialCheck")
                state = permissions.get((role[0], ap[0]), False)
                cb.setChecked(state)

                # Column index is r_idx + 1 because column 0 is the name
                self.checkbox_map[(role[0], ap[0])] = cb

                cell_widget = QWidget()
                cell_layout = QHBoxLayout(cell_widget)
                cell_layout.addWidget(cb)
                cell_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                cell_layout.setContentsMargins(0, 0, 0, 0)
                self.matrix_table.setCellWidget(a_idx, r_idx + 1, cell_widget)

    # =========================================================================
    # (Rest of existing Logic remains the same)
    # =========================================================================
    def save_permissions(self):
        permission_data = []
        for (role_id, access_id), cb in self.checkbox_map.items():
            permission_data.append((role_id, access_id, cb.isChecked()))
        if update_role_permissions(permission_data):
            QMessageBox.information(self, "Success", "Permissions Matrix updated.")
            log_audit_trail(self.work_station['m'], "SECURITY", "Matrix Modified")
        else:
            QMessageBox.critical(self, "Error", "Failed to update.")

    def handle_add_role(self):
        name, dept = self.new_role_input.text().strip(), self.new_dept_input.text().strip()
        if name and dept and add_new_role(name, dept):
            QMessageBox.information(self, "Success", f"Role '{name}' created.")
            self.new_role_input.clear();
            self.new_dept_input.clear()
            self.refresh_matrix();
            self.refresh_data()

    def refresh_data(self):
        self.users_raw_data = get_user_management_list()
        self.table_model.set_data([row[:7] for row in self.users_raw_data])
        roles = get_all_roles()
        self.role_combo.clear()
        self.role_combo.addItems([r[1] for r in roles])

    def filter_table(self):
        self.table_model.filter_data(self.search_input.text().lower())

    def load_user_to_form(self, index):
        row_idx = index.row()
        user_id = self.table_model.data(self.table_model.index(row_idx, 0))
        user_data = next((u for u in self.users_raw_data if u[0] == user_id), None)
        if user_data:
            self.selected_user_id = user_data[0]
            self.edit_username.setText(user_data[2]);
            self.edit_hostname.setText(user_data[1])
            self.edit_ip.setText(user_data[3]);
            self.edit_mac.setText(user_data[4])
            self.edit_password.setText(user_data[7])
            self.role_combo.setCurrentText(user_data[5])

    def save_data(self):
        if not self.selected_user_id: return
        data = {
            "username": self.edit_username.text().strip(),
            "hostname": self.edit_hostname.text().strip(),
            "password": self.edit_password.text().strip(),
            "ip": self.edit_ip.text().strip(),
            "mac": self.edit_mac.text().strip(),
            # Find the actual role_id by looking it up in the raw roles data
            "role_id": next(r[0] for r in get_all_roles() if r[1] == self.role_combo.currentText())
        }
        if save_user_changes(self.selected_user_id, data):
            QMessageBox.information(self, "Success", "User details updated.")
            self.refresh_data()