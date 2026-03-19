from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFrame, QHBoxLayout, QLabel, QLineEdit


class ProductionRecords(QWidget):
    def __init__(self, username, user_role):
        super().__init__()
        self.username = username
        self.user_role = user_role

        self.init_ui()

    def init_ui(self):
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 10, 15, 15)
        main_layout.setSpacing(10)

        header_card = QFrame()
        header_card.setObjectName("HeaderCard")
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(10, 0, 10, 0)

        self.selected_formulation_label = QLabel("INDEX REF. - FORMULATION NO.: No Selection", objectName="card_header")
        self.selected_formulation_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        header_layout.addWidget(self.selected_formulation_label)

        header_layout.addStretch()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search Productions...")
        self.search_input.setFixedWidth(250)

        header_layout.addWidget(self.search_input)


        main_layout.addWidget(header_card)