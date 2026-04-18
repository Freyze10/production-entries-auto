import csv
from datetime import datetime

from PyQt6.QtCore import Qt, QDate
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
                             QAbstractItemView, QHeaderView, QMessageBox, QHBoxLayout, QLabel,
                             QPushButton, QDateEdit, QLineEdit, QFileDialog, QFrame, QGridLayout, QComboBox, QTableView)
from PyQt6.QtGui import QFont
import qtawesome as fa

from db.read import get_audit_trail_report
from table_model.model import TableModel
from util.debounce import finished_typing


class AuditTrail(QWidget):

    def __init__(self):
        super().__init__()
        self.rows = []
        self.setup_ui()
        self.refresh_records()

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

        self.date_start = QDateEdit()
        self.date_start.setCalendarPopup(True)
        self.date_start.setDisplayFormat("MM-dd-yyyy")
        self.date_start.setMinimumWidth(130)
        header_layout.addWidget(self.date_start)

        dash = QLabel(" - ", objectName="table_label")
        dash.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header_layout.addWidget(dash)

        self.date_end = QDateEdit()
        self.date_end.setCalendarPopup(True)
        self.date_end.setDisplayFormat("MM-dd-yyyy")
        self.date_end.setMinimumWidth(130)
        header_layout.addWidget(self.date_end)

        # Export button in header
        self.export_btn = QPushButton(" Export to CSV", objectName="PrimaryButton")
        self.export_btn.setIcon(fa.icon('fa5s.file-export', color='white'))
        self.export_btn.clicked.connect(self.export_to_csv)
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
        self.search_filter.returnPressed.connect(self.filter_audit_trail)
        self.production_search_timer = finished_typing(self.search_filter, self.filter_audit_trail, delay=700)


        self.reset_btn = QPushButton(" Refresh", objectName="InfoButton")
        self.reset_btn.setIcon(fa.icon('fa5s.redo', color='white'))
        self.reset_btn.clicked.connect(self.refresh_records)

        fields_layout.addWidget(search_label)
        fields_layout.addWidget(self.audit_column_combo)
        fields_layout.addWidget(self.search_filter)
        fields_layout.addWidget(self.reset_btn)

        filter_layout.addLayout(fields_layout)

        main_layout.addWidget(filter_card)

        # === Results Card ===
        results_card = QFrame()
        results_card.setObjectName("ContentCard")
        results_layout = QVBoxLayout(results_card)
        results_layout.setContentsMargins(20, 2, 20, 2)
        results_layout.setSpacing(12)

        results_header = QHBoxLayout()
        results_title = QLabel("Audit Records", objectName="table_label")
        results_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        results_title.setStyleSheet("color: #111827;")
        results_header.addWidget(results_title)

        self.record_count_label = QLabel("0 records", objectName="light_label")
        self.record_count_label.setFont(QFont("Segoe UI", 9))
        results_header.addWidget(self.record_count_label)
        results_header.addStretch()

        results_layout.addLayout(results_header)

        self.headers = ["Timestamp", "Hostname", "Action", "Details", "IP Address", "MAC Address"]

        # Table
        self.table_audit_records = QTableView()
        self.table_model = TableModel(self.rows, self.headers)
        self.table_audit_records.setModel(self.table_model)
        self.table_audit_records.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        # Force the "Details" column (index 3) to stretch and fill empty space
        self.table_audit_records.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table_audit_records.setColumnWidth(0, 140)
        self.table_audit_records.setColumnWidth(5, 110)
        self.table_audit_records.verticalHeader().setVisible(False)  # hide row numbers
        # self.table_audit_records.setColumnHidden(0, True)
        self.table_audit_records.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_audit_records.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table_audit_records.setAlternatingRowColors(True)
        self.table_audit_records.setSortingEnabled(True)
        self.table_audit_records.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table_audit_records.sortByColumn(0, Qt.SortOrder.DescendingOrder)

        results_layout.addWidget(self.table_audit_records)

        main_layout.addWidget(results_card, stretch=1)

    def refresh_records(self):
        try:
            self.rows = get_audit_trail_report()
            self.table_model.set_data(self.rows)

            total_count = len(self.rows)
            self.record_count_label.setText(f"{total_count} records")

            # Reset the selection in the UI
            self.table_audit_records.clearSelection()
            self.table_audit_records.sortByColumn(0, Qt.SortOrder.DescendingOrder)
            self.table_audit_records.scrollToTop()

            # Clear search bar if text was entered
            self.search_filter.clear()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to refresh data: {e}")

    def filter_audit_trail(self):
        AUDIT_COL_MAP = {
            "All Columns": None,
            "Hostname": 1,
            "Action Type": 2,
            "Details": 3
        }

        search_text = self.search_filter.text().lower()
        col_label = self.audit_column_combo.currentText()
        col_index = AUDIT_COL_MAP.get(col_label, None)
        self.table_model.filter_data(search_text, col_index)

        current_count = self.table_model.rowCount()
        self.record_count_label.setText(f"{current_count} records")

    def export_to_csv(self):
        # 1. Check if there is data to export
        if self.table_model.rowCount() == 0:
            QMessageBox.warning(self, "Export Error", "No records found to export.")
            return

        # 2. Open File Dialog
        # This ensures the file is saved as .csv, which Excel opens perfectly
        default_name = f"Audit_Trail_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Audit Trail",
            default_name,
            "CSV Files (*.csv);;All Files (*)"
        )

        if not file_path:
            return  # User cancelled

        try:
            # 3. Write to CSV
            with open(file_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)

                # Write the Headers
                writer.writerow(self.headers)

                # Write the Data from the Model (this respects the current filter)
                # We access self.table_model._data directly
                for row_index in range(self.table_model.rowCount()):
                    row_data = []
                    for col_index in range(self.table_model.columnCount()):
                        # Get value from the model
                        val = self.table_model.data(self.table_model.index(row_index, col_index))
                        row_data.append(val)
                    writer.writerow(row_data)

            QMessageBox.information(self, "Export Successful", f"Data exported successfully to:\n{file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"An error occurred while exporting: {e}")