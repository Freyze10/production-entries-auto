import csv
from datetime import datetime

from PyQt6.QtCore import Qt, QDate
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
                             QAbstractItemView, QHeaderView, QMessageBox, QHBoxLayout, QLabel,
                             QPushButton, QDateEdit, QLineEdit, QFileDialog, QFrame, QGridLayout, QComboBox)
from PyQt6.QtGui import QFont
import qtawesome as fa


class AuditTrail(QWidget):

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 10, 15, 10)
        main_layout.setSpacing(8)

        # === Header Section ===
        header_card = QFrame()
        header_card.setObjectName("HeaderCard")
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(20, 2, 15, 2)

        title_label = QLabel("Audit Trail", objectName="table_label")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header_layout.addWidget(title_label)

        subtitle_label = QLabel("Track all system activities and user actions", objectName="light_label")
        subtitle_label.setFont(QFont("Segoe UI", 9))
        header_layout.addWidget(subtitle_label)

        header_layout.addStretch()

        # Export button in header
        self.export_btn = QPushButton(" Export to CSV", objectName="PrimaryButton")
        self.export_btn.setIcon(fa.icon('fa5s.file-export', color='white'))
        # self.export_btn.clicked.connect(self.export_to_csv)
        header_layout.addWidget(self.export_btn)

        main_layout.addWidget(header_card)

        # === Filter Card ===
        filter_card = QFrame()
        filter_card.setObjectName("ContentCard")
        filter_layout = QVBoxLayout(filter_card)
        filter_layout.setContentsMargins(20, 0, 10, 0)
        filter_layout.setSpacing(5)

        fields_layout = QHBoxLayout()

        self.audit_column_combo = QComboBox()
        self.audit_column_combo.setFixedWidth(170)
        self.audit_column_combo.addItems([
            "All Columns",
            "Hostname",
            "Action Type",
            "Details",
        ])
        self.audit_column_combo.setCurrentIndex(0)

        search_label = QLabel("Search Record:")
        search_label.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))

        self.search_filter = QLineEdit(placeholderText="Enter Text...")


        self.reset_btn = QPushButton(" Reset Filters", objectName="InfoButton")
        self.reset_btn.setIcon(fa.icon('fa5s.redo', color='white'))
        # self.reset_btn.clicked.connect(self.refresh_page)

        fields_layout.addWidget(search_label)
        fields_layout.addWidget(self.audit_column_combo)
        fields_layout.addWidget(self.search_filter)
        fields_layout.addWidget(self.reset_btn)

        filter_layout.addLayout(fields_layout)

        # Filter Buttons
        filter_btn_layout = QHBoxLayout()
        filter_btn_layout.addStretch()


        filter_layout.addLayout(filter_btn_layout)

        main_layout.addWidget(filter_card)

        # === Results Card ===
        results_card = QFrame()
        results_card.setObjectName("ContentCard")
        results_layout = QVBoxLayout(results_card)
        results_layout.setContentsMargins(20, 20, 20, 20)
        results_layout.setSpacing(12)

        results_header = QHBoxLayout()
        results_title = QLabel("Audit Records")
        results_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        results_title.setStyleSheet("color: #111827;")
        results_header.addWidget(results_title)

        self.record_count_label = QLabel("0 records")
        self.record_count_label.setFont(QFont("Segoe UI", 9))
        self.record_count_label.setStyleSheet("color: #6B7280;")
        results_header.addWidget(self.record_count_label)
        results_header.addStretch()

        results_layout.addLayout(results_header)

        # Table
        self.audit_table = QTableWidget(
            editTriggers=QAbstractItemView.EditTrigger.NoEditTriggers,
            selectionBehavior=QAbstractItemView.SelectionBehavior.SelectRows,
            alternatingRowColors=True
        )
        self.audit_table.verticalHeader().setVisible(False)
        self.audit_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        results_layout.addWidget(self.audit_table)

        main_layout.addWidget(results_card, stretch=1)

