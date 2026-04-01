import sys
from datetime import datetime

import qtawesome as fa
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QApplication, QVBoxLayout, QLabel, QFrame, QPushButton, \
    QStackedWidget, QStatusBar

from css.styles import AppStyles
from menu.mb_auto_entry import MBAutoEntry
from menu.mb_manual_entry import MBManualEntry
from menu.production_records import ProductionRecords
from workstation.workstation_details import _get_workstation_info
from db.schema import create_table


class MainWindow(QMainWindow):
    def __init__(self):  # , username, user_role, login_window
        super().__init__()
        # self.username = username
        # self.user_role = user_role
        self.username = "Brant"
        self.user_role = "Admin"
        # self.login_window = login_window
        self.workstation_info = _get_workstation_info()

        self.icon_db_ok, self.icon_db_fail = (fa.icon('fa5s.check-circle', color='#4CAF50'),
                                              fa.icon('fa5s.times-circle', color='#D32F2F'))
        self.setWindowTitle("Production Entry")
        self.setWindowIcon(fa.icon('mdi.upload-network-outline', color='gray'))
        self.setMinimumSize(1400, 720)
        self.setGeometry(100, 100, 1366, 768)

        self.production_records = None
        self.production_manual_entry = None
        self.production_auto_entry = None
        self.production_manual_entry_dc = None
        self.production_auto_entry_dc = None
        self.audit_trail = None

        self.init_ui()

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
        create_table()
        self.set_status_bar()
        self._init_pages()

    def _init_pages(self):
        self.production_records = ProductionRecords(self.username, self.user_role)
        self.mb_manual_entry = MBManualEntry()
        self.mb_auto_entry = MBAutoEntry()

        self.stacked_widget.addWidget(self.production_records)  # 0
        self.stacked_widget.addWidget(self.mb_manual_entry)   # 1
        self.stacked_widget.addWidget(self.mb_auto_entry)   # 2

        self.production_records.go_to_manual_entry.connect(self.switch_to_manual_entry)

        self.btn_production_records.setChecked(True)

    def switch_to_manual_entry(self, prod_id: int):
        self.mb_manual_entry = MBManualEntry(prod_id)  # Pass prod_id in constructor
        self.stacked_widget.removeWidget(self.stacked_widget.widget(1))  # remove old one
        self.stacked_widget.insertWidget(1, self.mb_manual_entry)  # add new one with same index
        self.btn_manual_entry.setChecked(True)
        self.stacked_widget.setCurrentIndex(1)

    def switch_to_auto_entry(self, prod_id: int):
        self.mb_manual_entry = MBManualEntry(prod_id)  # Pass prod_id in constructor
        self.stacked_widget.removeWidget(self.stacked_widget.widget(1))  # remove old one
        self.stacked_widget.insertWidget(1, self.mb_manual_entry)  # add new one with same index
        self.btn_manual_entry.setChecked(True)
        self.stacked_widget.setCurrentIndex(1)

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
        self.btn_auto_entry = self.create_menu_button(" Auto Entry", "mdi.head-cog-outline", 2)
        self.btn_manual_entry_dc = self.create_menu_button(" Manual Entry - DC", "msc.wrench", 3)
        self.btn_auto_entry_dc = self.create_menu_button(" Auto Entry - DC", "mdi.application-cog", 4)

        self.btn_audit_trail = self.create_menu_button("  Audit Trail", 'fa5s.history', 5)

        self.btn_logout = QPushButton("  Logout", icon=fa.icon('fa5s.sign-out-alt', color=AppStyles.RED_500))
        self.btn_logout.setStyleSheet(f"""QPushButton {{ color: {AppStyles.RED_500};}}""")
        # self.btn_logout.clicked.connect(self.logout)

        layout.addWidget(profile)
        layout.addWidget(sep)
        layout.addWidget(QLabel("Production Entry", objectName="MenuLabel"))
        layout.addWidget(self.btn_production_records)
        layout.addWidget(self.btn_manual_entry)
        layout.addWidget(self.btn_auto_entry)
        layout.addWidget(self.btn_manual_entry_dc)
        layout.addWidget(self.btn_auto_entry_dc)
        layout.addWidget(QLabel("System", objectName="MenuLabel"))
        layout.addWidget(self.btn_audit_trail)
        layout.addStretch(1)
        layout.addWidget(self.btn_logout)

        return menu

    def show_page(self, index):
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


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()