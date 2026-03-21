from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableView, \
    QHeaderView
import qtawesome as fa

from table_model.model import TableModel


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
        main_layout.setContentsMargins(10, 8, 10, 8)
        main_layout.setSpacing(8)

        header_card = QFrame()
        header_card.setObjectName("HeaderCard")
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(4, 0, 4, 0)

        self.selected_formulation_label = QLabel("INDEX REF. - FORMULATION NO.: No Selection", objectName="card_header")
        self.selected_formulation_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        header_layout.addWidget(self.selected_formulation_label)

        header_layout.addStretch()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search Productions...")
        self.search_input.setFixedWidth(250)

        search_btn = QPushButton("Search", objectName="PrimaryButton")
        search_btn.setIcon(fa.icon('fa5s.search', color='white'))
        # TODO: create search function for production

        header_layout.addWidget(self.search_input)
        header_layout.addWidget(search_btn)

        main_layout.addWidget(header_card)

        records_card = QFrame()
        records_card.setObjectName("ContentCard")
        records_layout = QVBoxLayout(records_card)
        records_layout.setContentsMargins(8, 0, 8, 0)
        records_layout.setSpacing(10)

        self.table_records_label = QLabel("Poduction Records", objectName="table_label")
        self.table_records_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        records_layout.addWidget(self.table_records_label)

        # set of rows
        self.headers = ["Date", "Customer", "Product Code", "Product Color", "Lot No", "Qty Produced"]
        self.rows = [["0000-00-00", "SMYPC", "BA2322E", "BLUE", "LOT434", "3.88906"],
                     ["1100-00-00", "SMYPC", "BA2326E", "BLUE", "LOT432", "3.882906"]]

        self.table_records = QTableView()
        self.table_model = TableModel(self.rows, self.headers)
        self.table_records.setModel(self.table_model)
        self.table_records.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.table_records.setAlternatingRowColors(True)
        self.table_records.setSortingEnabled(True)

        records_layout.addWidget(self.table_records, stretch=1)

        main_layout.addWidget(records_card)



