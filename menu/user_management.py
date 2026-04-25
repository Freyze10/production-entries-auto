from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
                             QPushButton, QLineEdit, QComboBox, QTableView,
                             QHeaderView, QGroupBox, QGridLayout, QMessageBox,
                             QAbstractItemView, QTabWidget, QTableWidget, QTableWidgetItem, QCheckBox)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont
import qtawesome as fa

from css.styles import AppStyles
from table_model.model import TableModel
from db.read import get_user_management_list
from db.write import save_user_changes, log_audit_trail
from workstation.workstation_details import _get_workstation_info


class PermissionsManager(QWidget):
    def __init__(self):
        super().__init__()
        self.work_station = _get_workstation_info()
        self.setup_ui()

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        # Tab Widget
        self.tabs = QTabWidget()
        self.tabs.setObjectName("MainTabWidget")

        # Initialize Tabs
        self.user_tab = QWidget()
        self.role_tab = QWidget()

        self.setup_user_management_tab()
        self.setup_role_management_tab()

        self.tabs.addTab(self.user_tab, fa.icon('fa5s.users', color=AppStyles.TEAL_500), " User Management")
        self.tabs.addTab(self.role_tab, fa.icon('fa5s.user-shield', color=AppStyles.TEAL_500), " Role & Access")

        self.main_layout.addWidget(self.tabs)

    # =========================================================================
    # TAB 1: USER MANAGEMENT
    # =========================================================================
    def setup_user_management_tab(self):
        layout = QVBoxLayout(self.user_tab)

        # Reuse your existing logic here...
        content_layout = QHBoxLayout()

        # --- Left: Table ---
        table_container = QFrame(objectName="ContentCard")
        table_v = QVBoxLayout(table_container)

        search_layout = QHBoxLayout()
        self.user_search = QLineEdit(placeholderText="Search users...")
        search_icon = QLabel()
        search_icon.setPixmap(fa.icon('fa5s.search', color=AppStyles.SLATE_400).pixmap(16, 16))
        search_layout.addWidget(search_icon)
        search_layout.addWidget(self.user_search)
        table_v.addLayout(search_layout)

        self.user_table = QTableView()
        self.user_headers = ["ID", "Hostname", "Username", "IP", "MAC", "Role", "Dept"]
        self.user_model = TableModel([], self.user_headers)
        self.user_table.setModel(self.user_model)
        self.user_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.user_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.user_table.clicked.connect(self.load_user_to_form)

        table_v.addWidget(self.user_table)
        content_layout.addWidget(table_container, stretch=2)

        # --- Right: Form ---
        form_container = QFrame(objectName="ContentCard")
        form_container.setFixedWidth(350)
        form_v = QVBoxLayout(form_container)

        grid = QGridLayout()
        self.edit_user = QLineEdit()
        self.edit_pass = QLineEdit(echoMode=QLineEdit.EchoMode.Password)
        self.edit_host = QLineEdit()
        self.edit_role_combo = QComboBox()  # Populate this from DB roles

        grid.addWidget(QLabel("Username:"), 0, 0)
        grid.addWidget(self.edit_user, 0, 1)
        grid.addWidget(QLabel("Password:"), 1, 0)
        grid.addWidget(self.edit_pass, 1, 1)
        grid.addWidget(QLabel("Role:"), 2, 0)
        grid.addWidget(self.edit_role_combo, 2, 1)

        form_v.addLayout(grid)

        self.btn_save_user = QPushButton(" Save User", objectName="PrimaryButton")
        self.btn_save_user.clicked.connect(self.save_user_data)
        form_v.addWidget(self.btn_save_user)
        form_v.addStretch()

        content_layout.addWidget(form_container)
        layout.addLayout(content_layout)

        self.refresh_user_list()

    # =========================================================================
    # TAB 2: ROLE & ACCESS MANAGEMENT
    # =========================================================================
    def setup_role_management_tab(self):
        layout = QVBoxLayout(self.role_tab)
        layout.setSpacing(15)

        # --- Top Section: Add New Role ---
        add_role_group = QGroupBox("Add New System Role")
        add_role_layout = QHBoxLayout(add_role_group)

        self.new_role_name = QLineEdit(placeholderText="e.g., Quality Control")
        self.new_role_dept = QLineEdit(placeholderText="e.g., Production")
        btn_add_role = QPushButton(" Create Role", objectName="SuccessButton")
        btn_add_role.setIcon(fa.icon('fa5s.plus', color='white'))
        btn_add_role.clicked.connect(self.add_new_role)

        add_role_layout.addWidget(QLabel("Role Name:"))
        add_role_layout.addWidget(self.new_role_name)
        add_role_layout.addWidget(QLabel("Department:"))
        add_role_layout.addWidget(self.new_role_dept)
        add_role_layout.addWidget(btn_add_role)

        layout.addWidget(add_role_group)

        # --- Middle Section: Permission Matrix ---
        matrix_container = QFrame(objectName="ContentCard")
        matrix_v = QVBoxLayout(matrix_container)

        matrix_label = QLabel("Permission Access Matrix", objectName="table_label")
        matrix_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        matrix_v.addWidget(matrix_label)

        self.perm_table = QTableWidget()
        self.perm_table.setAlternatingRowColors(True)
        matrix_v.addWidget(self.perm_table)

        # Bottom Save
        self.btn_save_perms = QPushButton(" Save All Permission Changes", objectName="PrimaryButton")
        self.btn_save_perms.setIcon(fa.icon('fa5s.shield-alt', color='white'))
        self.btn_save_perms.clicked.connect(self.save_permissions)
        matrix_v.addWidget(self.btn_save_perms, alignment=Qt.AlignmentFlag.AlignRight)

        layout.addWidget(matrix_container)
        self.refresh_permission_matrix()

    def refresh_permission_matrix(self):
        """Loads the roles as columns and access items as rows."""
        try:
            # roles = get_roles_list()  # [(id, name, dept), ...]
            # access_items = get_all_access_permissions()  # [(id, name), ...]
            roles = [1, "admin", "prod", ]  # [(id, name, dept), ...]
            access_items = []  # [(id, name), ...]

            self.perm_table.setColumnCount(len(roles) + 1)
            self.perm_table.setRowCount(len(access_items))

            headers = ["Access Description"] + [r[1] for r in roles]
            self.perm_table.setHorizontalHeaderLabels(headers)
            self.perm_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            self.perm_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)

            for row_idx, access in enumerate(access_items):
                # Col 0: Access Name
                self.perm_table.setItem(row_idx, 0, QTableWidgetItem(access[1]))

                for col_idx, role in enumerate(roles):
                    # Checkbox for permission
                    container = QWidget()
                    check_layout = QHBoxLayout(container)
                    check = QCheckBox()
                    check.setAlignment(Qt.AlignmentFlag.AlignCenter)

                    # Logic: query if role has access
                    # is_enabled = check_role_access(role[0], access[0])
                    # check.setChecked(is_enabled)

                    # Store ID data in properties
                    check.setProperty("role_id", role[0])
                    check.setProperty("access_id", access[0])

                    check_layout.addWidget(check)
                    check_layout.setContentsMargins(0, 0, 0, 0)
                    self.perm_table.setCellWidget(row_idx, col_idx + 1, container)

        except Exception as e:
            print(f"Matrix Error: {e}")

    def add_new_role(self):
        name = self.new_role_name.text().strip()
        dept = self.new_role_dept.text().strip()

        if not name: return

        # if create_new_role(name, dept):
        #     QMessageBox.information(self, "Success", f"Role '{name}' created.")
        #     self.new_role_name.clear()
        #     self.new_role_dept.clear()
        #     self.refresh_permission_matrix()
        #     self.refresh_user_list()  # Update combo boxes

    def save_permissions(self):
        """Collects all checkbox states and saves to DB."""
        changes = []
        for row in range(self.perm_table.rowCount()):
            for col in range(1, self.perm_table.columnCount()):
                container = self.perm_table.cellWidget(row, col)
                checkbox = container.findChild(QCheckBox)

                changes.append({
                    "role_id": checkbox.property("role_id"),
                    "access_id": checkbox.property("access_id"),
                    "state": checkbox.isChecked()
                })

        # if save_role_permissions(changes):
        #     QMessageBox.information(self, "Saved", "System permissions updated successfully.")
        #     log_audit_trail(self.work_station['m'], "SECURITY", "Updated Role Access Matrix")

    # --- Utility methods for User Tab (stubs for context) ---
    def refresh_user_list(self):
        # Fetch users and roles for combo box
        pass

    def load_user_to_form(self, index):
        pass

    def save_user_data(self):
        pass