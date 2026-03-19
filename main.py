import sys
from datetime import datetime

import qtawesome as fa
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QApplication, QVBoxLayout, QLabel, QFrame, QPushButton, \
    QStackedWidget

from css.styles import AppStyles


class MainWindow(QMainWindow):
    def __init__(self): # , username, user_role, login_window
        super().__init__()
        # self.username = username
        # self.user_role = user_role
        # self.login_window = login_window
        self.icon_db_ok, self.icon_db_fail = (fa.icon('fa5s.check-circle', color='#4CAF50'),
                                              fa.icon('fa5s.times-circle', color='#D32F2F'))
        self.setWindowTitle("Production Entry")
        self.setWindowIcon(fa.icon('mdi.upload-network-outline', color='gray'))
        self.setMinimumSize(1400, 720)
        self.setGeometry(100, 100, 1366, 768)

        # self.workstation_info = _get_workstation_info()
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

        sep = QFrame(frameShape=QFrame.Shape.HLine, objectName="Separator")
        sep.setContentsMargins(0, 10, 0, 10)

        self.btn_production_records = self.create_menu_button(" Production Records", "ph.stack", 0)
        self.btn_manual_entry = self.create_menu_button(" Manual Entry", "msc.tools", 1)
        self.btn_auto_entry = self.create_menu_button(" Auto Entry", "mdi.head-cog-outline", 2)
        self.btn_manual_entry_dc = self.create_menu_button(" Manual Entry - DC", "msc.wrench", 3)
        self.btn_auto_entry_dc = self.create_menu_button(" Auto Entry - DC", "mdi.application-cog", 3)

        self.btn_logout = QPushButton("  Logout", icon=fa.icon('fa5s.sign-out-alt', color=AppStyles.RED_500))
        # self.btn_logout.clicked.connect(self.logout)

        layout.addWidget(sep)
        layout.addWidget(QLabel("Production Entry", objectName="MenuLabel"))
        layout.addWidget(self.btn_production_records)
        layout.addWidget(self.btn_manual_entry)
        layout.addWidget(self.btn_auto_entry)
        layout.addWidget(self.btn_manual_entry_dc)
        layout.addWidget(self.btn_auto_entry_dc)
        layout.addStretch(1)
        layout.addWidget(self.btn_logout)

        return menu

    def set_page(self, index):
        self.stacked_widget.setCurrentIndex(index)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()