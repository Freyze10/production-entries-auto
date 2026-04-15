import csv
from datetime import datetime

from PyQt6.QtCore import Qt, QDate
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
                             QAbstractItemView, QHeaderView, QMessageBox, QHBoxLayout, QLabel,
                             QPushButton, QDateEdit, QLineEdit, QFileDialog, QFrame, QGridLayout)
from PyQt6.QtGui import QFont
import qtawesome as fa


class AuditTrailPage(QWidget):
    """A modern page to view, filter, and export audit trail records."""

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 10, 15, 15)
        main_layout.setSpacing(12)

        # === Header Section ===
        header_card = QFrame()
        header_card.setObjectName("HeaderCard")
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(20, 15, 20, 15)

        title_label = QLabel("Audit Trail")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #111827;")
        header_layout.addWidget(title_label)

        subtitle_label = QLabel("Track all system activities and user actions")
        subtitle_label.setFont(QFont("Segoe UI", 9))
        subtitle_label.setStyleSheet("color: #6B7280;")
        header_layout.addWidget(subtitle_label)

        header_layout.addStretch()

        # Export button in header
        self.export_btn = QPushButton(" Export to CSV", objectName="InfoButton")
        self.export_btn.setIcon(fa.icon('fa5s.file-export', color='white'))
        self.export_btn.clicked.connect(self.export_to_csv)
        header_layout.addWidget(self.export_btn)

        main_layout.addWidget(header_card)

        # === Filter Card ===
        filter_card = QFrame()
        filter_card.setObjectName("ContentCard")
        filter_layout = QVBoxLayout(filter_card)
        filter_layout.setContentsMargins(20, 20, 20, 20)
        filter_layout.setSpacing(15)

        filter_title = QLabel("Filters")
        filter_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        filter_title.setStyleSheet("color: #111827;")
        filter_layout.addWidget(filter_title)

        # Grid layout for filters
        grid_layout = QGridLayout()
        grid_layout.setHorizontalSpacing(15)
        grid_layout.setVerticalSpacing(12)

        # Date Range
        date_label = QLabel("Date Range:")
        date_label.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        grid_layout.addWidget(date_label, 0, 0)

        date_container = QWidget()
        date_hlayout = QHBoxLayout(date_container)
        date_hlayout.setContentsMargins(0, 0, 0, 0)
        date_hlayout.setSpacing(8)

        self.start_date_edit = QDateEdit(calendarPopup=True, displayFormat="yyyy-MM-dd")
        self.start_date_edit.setMinimumWidth(140)
        date_hlayout.addWidget(self.start_date_edit)

        date_hlayout.addWidget(QLabel("to"))

        self.end_date_edit = QDateEdit(calendarPopup=True, displayFormat="yyyy-MM-dd")
        self.end_date_edit.setMinimumWidth(140)
        date_hlayout.addWidget(self.end_date_edit)
        date_hlayout.addStretch()

        grid_layout.addWidget(date_container, 0, 1, 1, 3)

        # Username Filter
        username_label = QLabel("Username:")
        username_label.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        grid_layout.addWidget(username_label, 1, 0)

        self.username_filter = QLineEdit(placeholderText="Filter by username...")
        grid_layout.addWidget(self.username_filter, 1, 1)

        # Action Type Filter
        action_label = QLabel("Action Type:")
        action_label.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        grid_layout.addWidget(action_label, 1, 2)

        self.action_filter = QLineEdit(placeholderText="e.g., LOGIN, DELETE...")
        grid_layout.addWidget(self.action_filter, 1, 3)

        # Details Search
        details_label = QLabel("Details:")
        details_label.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        grid_layout.addWidget(details_label, 2, 0)

        self.details_filter = QLineEdit(placeholderText="Search in details...")
        grid_layout.addWidget(self.details_filter, 2, 1, 1, 3)

        filter_layout.addLayout(grid_layout)

        # Filter Buttons
        filter_btn_layout = QHBoxLayout()
        filter_btn_layout.addStretch()

        self.reset_btn = QPushButton(" Reset Filters", objectName="SecondaryButton")
        self.reset_btn.setIcon(fa.icon('fa5s.redo', color='white'))
        self.reset_btn.clicked.connect(self.refresh_page)
        filter_btn_layout.addWidget(self.reset_btn)

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

