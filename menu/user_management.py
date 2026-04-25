from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
                             QPushButton, QLineEdit, QComboBox, QTableView,
                             QHeaderView, QGroupBox, QGridLayout, QMessageBox,
                             QAbstractItemView, QTabWidget, QTableWidget, QCheckBox)
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
    # TAB 1: USER MANAGEMENT (Your existing logic)
    # =========================================================================
    def create_user_management_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # --- (Existing Header, Table, and Form Logic) ---
        # Note: I am wrapping your existing code here
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
        self.role_combo.addItems(["Admin", "Editor", "Viewer"])

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
    # TAB 2: ROLE MANAGEMENT (Matrix & New Roles)
    # =========================================================================
    def create_role_management_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # --- Top: Add New Role Group ---
        add_role_group = QGroupBox("Create New System Role")
        add_role_layout = QHBoxLayout(add_role_group)

        self.new_role_input = QLineEdit(placeholderText="Role Name (e.g., Supervisor)")
        self.new_dept_input = QLineEdit(placeholderText="Department (e.g., Production)")
        btn_add_role = QPushButton(" Add Role", objectName="SuccessButton")
        btn_add_role.setIcon(fa.icon('fa5s.plus', color='white'))
        btn_add_role.clicked.connect(self.handle_add_role)

        add_role_layout.addWidget(QLabel("Name:"))
        add_role_layout.addWidget(self.new_role_input)
        add_role_layout.addWidget(QLabel("Dept:"))
        add_role_layout.addWidget(self.new_dept_input)
        add_role_layout.addWidget(btn_add_role)
        layout.addWidget(add_role_group)

        # --- Middle: Permission Matrix ---
        matrix_group = QFrame(objectName="ContentCard")
        matrix_layout = QVBoxLayout(matrix_group)
        matrix_layout.addWidget(QLabel("Permission Access Matrix", objectName="table_label"))

        self.matrix_table = QTableWidget()
        self.matrix_table.setAlternatingRowColors(True)
        self.matrix_table.setStyleSheet("QCheckBox { margin-left: 50%; }")  # Center checkboxes
        matrix_layout.addWidget(self.matrix_table)

        # --- Bottom: Action Buttons ---
        btn_footer = QHBoxLayout()
        btn_footer.addStretch()

        btn_refresh_matrix = QPushButton(" Reload Matrix", objectName="SecondaryButton")
        btn_refresh_matrix.clicked.connect(self.refresh_matrix)

        btn_save_matrix = QPushButton(" Save Permissions", objectName="PrimaryButton")
        btn_save_matrix.setIcon(fa.icon('fa5s.shield-alt', color='white'))
        btn_save_matrix.clicked.connect(self.save_permissions)

        btn_footer.addWidget(btn_refresh_matrix)
        btn_footer.addWidget(btn_save_matrix)
        layout.addWidget(matrix_group)
        layout.addLayout(btn_footer)

        self.refresh_matrix()
        return tab

    # =========================================================================
    # LOGIC: ROLE MANAGEMENT
    # =========================================================================
    def refresh_matrix(self):
        """Fetches Roles and Access Points to build the toggle grid."""
        roles = get_all_roles()  # [(1, 'Admin'), (2, 'Editor')...]
        access_points = get_access_points()  # [(1, 'Manual Entry'), (2, 'Audit Trail')...]
        permissions = get_permission_matrix()  # Dictionary {(role_id, access_id): True/False}

        self.matrix_table.setRowCount(len(access_points))
        self.matrix_table.setColumnCount(len(roles))

        # Headers
        self.matrix_table.setVerticalHeaderLabels([ap[1] for ap in access_points])
        self.matrix_table.setHorizontalHeaderLabels([r[1] for r in roles])
        self.matrix_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.checkbox_map = {}  # Store refs to checkboxes

        for r_idx, role in enumerate(roles):
            for a_idx, ap in enumerate(access_points):
                cb = QCheckBox()
                cb.setObjectName("RawMaterialCheck")  # Use your teal theme

                # Set initial state from DB
                state = permissions.get((role[0], ap[0]), False)
                cb.setChecked(state)

                # Store indices for saving later
                self.checkbox_map[(role[0], ap[0])] = cb

                # Add to table
                cell_widget = QWidget()
                cell_layout = QHBoxLayout(cell_widget)
                cell_layout.addWidget(cb)
                cell_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                cell_layout.setContentsMargins(0, 0, 0, 0)
                self.matrix_table.setCellWidget(a_idx, r_idx, cell_widget)

    def save_permissions(self):
        """Iterates through checkboxes and updates the database."""
        permission_data = []
        for (role_id, access_id), cb in self.checkbox_map.items():
            permission_data.append((role_id, access_id, cb.isChecked()))

        if update_role_permissions(permission_data):
            QMessageBox.information(self, "Success", "Permissions Matrix updated successfully.")
            log_audit_trail(self.work_station['m'], "SECURITY", "Role Permission Matrix Modified")
        else:
            QMessageBox.critical(self, "Error", "Failed to update permissions.")

    def handle_add_role(self):
        name = self.new_role_input.text().strip()
        dept = self.new_dept_input.text().strip()

        if not name or not dept:
            QMessageBox.warning(self, "Input Error", "Please provide Role Name and Department.")
            return

        if add_new_role(name, dept):
            QMessageBox.information(self, "Success", f"Role '{name}' created.")
            self.new_role_input.clear()
            self.new_dept_input.clear()
            self.refresh_matrix()  # Update table headers
            self.refresh_data()  # Update user form combo box
        else:
            QMessageBox.critical(self, "Error", "Failed to create role.")

    # =========================================================================
    # LOGIC: USER MANAGEMENT (Keep your existing functions)
    # =========================================================================
    def refresh_data(self):
        self.users_raw_data = get_user_management_list()
        display_rows = [row[:7] for row in self.users_raw_data]
        self.table_model.set_data(display_rows)
        # Update Role Combo Box if new roles were added
        roles = get_all_roles()
        self.role_combo.clear()
        self.role_combo.addItems([r[1] for r in roles])

    def filter_table(self):
        text = self.search_input.text().lower()
        self.table_model.filter_data(text)

    def load_user_to_form(self, index):
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
            # Match role by name in combo
            role_name = user_data[5]
            self.role_combo.setCurrentText(role_name)

    def save_data(self):
        # ... (Your existing save_data logic) ...
        pass