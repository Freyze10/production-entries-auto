import sys
from datetime import datetime

import qtawesome as fa
from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QApplication, QVBoxLayout, QLabel, QFrame, QPushButton, \
    QStackedWidget, QStatusBar, QMessageBox

from css.styles import AppStyles
from db.read import get_all_user_mac, get_user_role
from db.write import create_current_user, log_audit_trail
from menu.audit_trail import AuditTrail
from menu.dc_auto_entry import DCAutoEntry
from menu.login import LoginWindow
from menu.mb_auto_entry import MBAutoEntry
from menu.mb_manual_entry import MBManualEntry
from menu.production_records import ProductionRecords
from util.absolute_path import resource_path
from workstation.workstation_details import _get_workstation_info
from db.schema import create_table


class AppController:
    def __init__(self):
        self.login_window = None
        self.main_window = None
        self.workstation_info = _get_workstation_info()

    def show_login(self):
        if self.main_window:
            self.main_window.close()

        self.login_window = LoginWindow(self.workstation_info)
        self.login_window.login_success.connect(self.show_main)
        self.login_window.show()

    def show_main(self, username, role):
        self.main_window = MainWindow(username, role)
        # Connect the logout button signal
        self.main_window.logout_requested.connect(self.show_login)
        self.main_window.show()


class MainWindow(QMainWindow):
    logout_requested = pyqtSignal()  # Add this signal

    def __init__(self, username, user_role):
        super().__init__()
        self.workstation_info = _get_workstation_info()
        self.username = username
        self.user_role = user_role

        self.icon_db_ok, self.icon_db_fail = (fa.icon('fa5s.check-circle', color='#4CAF50'),
                                              fa.icon('fa5s.times-circle', color='#D32F2F'))
        self.setWindowTitle("Production Entry")
        icon_path = resource_path("css/img/production_icon.ico")
        self.setWindowIcon(QIcon(icon_path))
        self.setGeometry(100, 100, 1320, 668)
        self.showMaximized()

        self.production_records = None
        self.production_manual_entry = None
        self.production_auto_entry = None
        # self.production_manual_entry_dc = None
        self.production_auto_entry_dc = None
        self.audit_trail = None

        create_table()
        self.create_acccount()
        self.username = self.workstation_info['h']
        self.user_role = get_user_role(self.workstation_info['m'])
        self.init_ui()
        self.log_audit_trail()

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        main_layout.addWidget(self.create_side_menu())

        self.setStyleSheet(AppStyles.MAIN_WINDOW_STYLESHEET)
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        self.setCentralWidget(main_widget)
        self.set_status_bar()
        self._init_pages()

    def _init_pages(self):
        for _ in range(5):
            self.stacked_widget.addWidget(QWidget())

            # Load the first page immediately (Production Records)
        self.show_page(0)
        self.btn_production_records.setChecked(True)

    def switch_to_manual_entry(self, prod_id: int):
        self.mb_manual_entry = MBManualEntry(prod_id)  # Pass prod_id in constructor
        self.stacked_widget.removeWidget(self.stacked_widget.widget(1))  # remove old one
        self.stacked_widget.insertWidget(1, self.mb_manual_entry)  # add new one with same index
        self.btn_manual_entry.setChecked(True)
        self.stacked_widget.setCurrentIndex(1)

    def switch_to_auto_entry(self, prod_id: int):
        self.mb_auto_entry = MBAutoEntry(prod_id)  # Pass prod_id in constructor
        self.stacked_widget.removeWidget(self.stacked_widget.widget(2))  # remove old one
        self.stacked_widget.insertWidget(2, self.mb_auto_entry)  # add new one with same index
        self.btn_auto_entry.setChecked(True)
        self.stacked_widget.setCurrentIndex(2)

    def switch_to_dc_auto(self, prod_id: int):
        self.dc_auto_entry = DCAutoEntry(prod_id)  # Pass prod_id in constructor
        self.stacked_widget.removeWidget(self.stacked_widget.widget(3))  # remove old one
        self.stacked_widget.insertWidget(3, self.dc_auto_entry)  # add new one with same index
        self.btn_auto_entry_dc.setChecked(True)
        self.stacked_widget.setCurrentIndex(3)

    def log_audit_trail(self):
        log_audit_trail(
            mac_address=self.workstation_info['m'],
            action_type="LOGIN",
            details="User logged in successfully"
        )


    def create_menu_button(self, text, icon, page_index):
        btn = QPushButton(text, icon=fa.icon(icon, color='#ecf0f1'), checkable=True, autoExclusive=True)
        if page_index is not None:
            btn.clicked.connect(lambda: self.show_page(page_index))
        return btn

    def create_side_menu(self):
        menu = QWidget(objectName="SideMenu")
        layout = QVBoxLayout(menu)
        layout.setContentsMargins(5, 20, 5, 10)
        layout.setSpacing(5)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        profile = QWidget()
        user_profile = QHBoxLayout(profile)
        user_profile.setContentsMargins(15, 0, 0, 5)
        user_profile.setAlignment(Qt.AlignmentFlag.AlignLeft)
        user_profile.addWidget(QLabel(pixmap=fa.icon('fa5s.user-circle', color="#ecf0f1").pixmap(QSize(40, 40))))
        user_profile.addWidget(QLabel(f"<b>{self.username}</b><br><font color='#bdc3c7'>{self.user_role}</font>"))

        sep = QFrame(frameShape=QFrame.Shape.HLine, objectName="Separator")
        sep.setContentsMargins(0, 10, 0, 10)

        self.btn_production_records = self.create_menu_button(" Production Records", "ph.stack", 0)
        self.btn_manual_entry = self.create_menu_button(" Manual Entry", "msc.tools", 1)
        self.btn_auto_entry = self.create_menu_button(" Auto Entry - MB", "mdi.head-cog-outline", 2)
        # self.btn_manual_entry_dc = self.create_menu_button(" Manual Entry - DC", "msc.wrench", 3)
        self.btn_auto_entry_dc = self.create_menu_button(" Auto Entry - DC", "mdi.application-cog", 3)

        self.btn_audit_trail = self.create_menu_button("  Audit Trail", 'fa5s.history', 4)

        self.btn_logout = QPushButton("  Logout", icon=fa.icon('fa5s.sign-out-alt', color=AppStyles.RED_500))
        self.btn_logout.setStyleSheet(f"""QPushButton {{ color: {AppStyles.RED_500};}}""")
        self.btn_logout.clicked.connect(self.handle_logout)

        layout.addWidget(profile)
        layout.addWidget(sep)
        layout.addWidget(QLabel("Production Entry", objectName="MenuLabel"))
        layout.addWidget(self.btn_production_records)
        layout.addWidget(self.btn_manual_entry)
        layout.addWidget(self.btn_auto_entry)
        # layout.addWidget(self.btn_manual_entry_dc)
        layout.addWidget(self.btn_auto_entry_dc)
        layout.addWidget(QLabel("System", objectName="MenuLabel"))
        layout.addWidget(self.btn_audit_trail)
        layout.addStretch(1)
        layout.addWidget(self.btn_logout)

        return menu

    def show_page(self, index):
        # Check if the page is already loaded
        current_widget = self.stacked_widget.widget(index)

        # If it's a plain QWidget, it hasn't been initialized yet
        if type(current_widget) == QWidget:
            if index == 0:
                self.production_records = ProductionRecords(self.workstation_info['m'])
                # Connect the signals for the first page
                self.production_records.go_to_manual_entry.connect(self.switch_to_manual_entry)
                self.production_records.go_to_auto_entry.connect(self.switch_to_auto_entry)
                self.production_records.go_to_dc_auto.connect(self.switch_to_dc_auto)
                new_widget = self.production_records

            elif index == 1:
                self.mb_manual_entry = MBManualEntry()
                new_widget = self.mb_manual_entry

            elif index == 2:
                self.mb_auto_entry = MBAutoEntry()
                new_widget = self.mb_auto_entry

            elif index == 3:
                self.dc_auto_entry = DCAutoEntry()
                new_widget = self.dc_auto_entry

            elif index == 4:
                self.audit_trail = AuditTrail()
                new_widget = self.audit_trail

            # Replace the placeholder with the actual loaded page
            self.stacked_widget.removeWidget(current_widget)
            self.stacked_widget.insertWidget(index, new_widget)

        # Now show the page
        self.stacked_widget.setCurrentIndex(index)

    def set_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.time_label = QLabel()

        for status in [self.time_label,
                  QLabel(f" PC: {self.workstation_info['h']}"),
                  QLabel(f" IP: {self.workstation_info['i']}"),
                  QLabel(f" MAC: {self.workstation_info['m']}")]:
            self.status_bar.addPermanentWidget(status)

        self.time_timer = QTimer(self, timeout=self.update_time)
        self.time_timer.start(1000)
        self.update_time()

    def update_time(self):
        self.time_label.setText(f" {datetime.now().strftime('%b %d, %Y  %I:%M:%S %p')}")

    def create_acccount(self):
        all_user_mac = get_all_user_mac()
        if self.workstation_info['m'] not in all_user_mac:
            create_current_user(self.workstation_info)

    def handle_logout(self):
        msg = QMessageBox.question(self, "Logout", "Are you sure you want to logout?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if msg == QMessageBox.StandardButton.Yes:
            log_audit_trail(self.workstation_info['m'], "LOGOUT", "User logged out")
            self.logout_requested.emit()  # Notify controller to show login again


def main():
    app = QApplication(sys.argv)

    # Crucial: Prevent app from closing when switching windows
    app.setQuitOnLastWindowClosed(False)

    controller = AppController()
    controller.show_login()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()