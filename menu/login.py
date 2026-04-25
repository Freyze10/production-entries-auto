from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QLabel, QFrame, QHBoxLayout, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont
import qtawesome as fa
from css.styles import AppStyles
from db.read import get_all_user_mac, authenticate_user, get_user_info_by_mac
from db.schema import create_table
from db.write import create_current_user, update_user_workstation


# from db.read import authenticate_user

class LoginWindow(QDialog):
    login_success = pyqtSignal(str, str)  # Sends (username, role)

    def __init__(self, workstation_info):
        super().__init__()
        self.workstation = workstation_info
        self.setObjectName("LoginWindow")  # Matches CSS selector #LoginWindow
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)  # Clean look
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(AppStyles.LOGIN_STYLESHEET)

        create_table()
        self.init_ui()

        self.create_acccount()

    def init_ui(self):
        # Translucent container to allow for the shadow effect in CSS
        container_layout = QVBoxLayout(self)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # The White Card
        self.form_frame = QFrame(objectName="FormFrame")
        self.form_frame.setFixedSize(420, 550)
        form_layout = QVBoxLayout(self.form_frame)
        form_layout.setContentsMargins(40, 40, 40, 40)
        form_layout.setSpacing(20)

        # Header
        header_icon = QLabel()
        icon_size = 80
        header_icon.setPixmap(
            fa.icon('fa5s.user-shield', color=AppStyles.TEAL_500).pixmap(QSize(icon_size, icon_size)))

        header_icon.setFixedSize(icon_size, icon_size)

        title = QLabel("Welcome Back", objectName="LoginTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Please enter your credentials", objectName="light_label")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Input Helper to create the structure expected by CSS (#InputFrame)
        def create_input_field(placeholder, icon_name, is_password=False):
            frame = QFrame(objectName="InputFrame")
            layout = QHBoxLayout(frame)
            layout.setContentsMargins(10, 0, 10, 0)

            icon = QLabel()
            icon.setPixmap(fa.icon(icon_name, color=AppStyles.SLATE_400).pixmap(18, 18))

            edit = QLineEdit()
            edit.setPlaceholderText(placeholder)
            if is_password:
                edit.setEchoMode(QLineEdit.EchoMode.Password)

            layout.addWidget(icon)
            layout.addWidget(edit)
            return frame, edit

        user_frame, self.username_input = create_input_field("Username", "fa5s.user")
        pass_frame, self.password_input = create_input_field("Password", "fa5s.lock", True)
        self.password_input.returnPressed.connect(self.handle_login)

        # Error Label
        self.status_label = QLabel("", objectName="StatusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Button
        self.btn_login = QPushButton("Sign In", objectName="PrimaryButton")
        self.btn_login.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_login.clicked.connect(self.handle_login)

        # Exit Button
        self.btn_exit = QPushButton("Close Application")
        self.btn_exit.setStyleSheet("border: none; color: gray; font-size: 11px;")
        self.btn_exit.clicked.connect(self.close)

        # Assemble
        form_layout.addWidget(header_icon, alignment=Qt.AlignmentFlag.AlignCenter)
        form_layout.addSpacing(20)
        form_layout.addWidget(title)
        form_layout.addWidget(subtitle)
        form_layout.addSpacing(20)
        form_layout.addWidget(user_frame)
        form_layout.addWidget(pass_frame)
        form_layout.addWidget(self.status_label)
        form_layout.addWidget(self.btn_login)
        form_layout.addWidget(self.btn_exit, alignment=Qt.AlignmentFlag.AlignCenter)

        container_layout.addWidget(self.form_frame)

    def create_acccount(self):
        all_user_mac = get_all_user_mac()
        current_mac = self.workstation['m']

        if current_mac not in all_user_mac:
            # MAC is new: create the user
            create_current_user(self.workstation)
        else:
            # MAC exists: check if Hostname or IP has changed
            existing_data = get_user_info_by_mac(current_mac)

            if existing_data:
                db_host = existing_data[0]  # hostname from DB
                db_ip = existing_data[1]  # ip_address from DB

                # Compare with current workstation data
                if db_host != self.workstation['h'] or db_ip != self.workstation['i']:
                    print("Workstation details changed. Updating record...")
                    update_user_workstation(current_mac, self.workstation['h'], self.workstation['i'])

    def handle_login(self):
        actual_username = self.username_input.text().strip()
        pw = self.password_input.text().strip()

        if not actual_username:
            QMessageBox.warning(self, "Invalid Input", "Please enter your username.")
            return

        # Perform authentication
        success, role = authenticate_user(actual_username, pw)

        if success:
            self.login_success.emit(actual_username, role)
            self.accept()
        else:
            self.status_label.setText("Invalid username or password")
            self.password_input.clear()
