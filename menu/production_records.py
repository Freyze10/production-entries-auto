from PyQt6.QtCore import Qt, QThread
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableView, \
    QHeaderView, QMenu, QMessageBox, QComboBox
import qtawesome as fa
from PyQt6.QtCore import pyqtSignal

from db.legacy import Sync
from db import read
from table_model.model import TableModel
from util.debounce import finished_typing
from util.loading import LoadingDialog


class ProductionRecords(QWidget):
    go_to_manual_entry = pyqtSignal(int)
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

        self.selected_production_label = QLabel("INDEX REF. - FORMULATION NO.: No Selection", objectName="card_header")
        self.selected_production_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        header_layout.addWidget(self.selected_production_label)

        header_layout.addStretch()

        self.search_column_combo = QComboBox()
        self.search_column_combo.setFixedWidth(170)
        self.search_column_combo.addItems([
            "All Columns",
            "Prod ID",
            "Date",
            "Customer",
            "Product Code",
            "Product Color",
            "Lot No",
            "Qty Produced",
        ])
        self.search_column_combo.setCurrentIndex(0)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search Productions...")
        self.search_input.setFixedWidth(250)
        self.search_input.returnPressed.connect(self.filter_production)
        self.production_search_timer = finished_typing(self.search_input, self.filter_production, delay=700)

        search_btn = QPushButton("Search", objectName="PrimaryButton")
        search_btn.setIcon(fa.icon('fa5s.search', color='white'))
        search_btn.clicked.connect(self.filter_production)

        header_layout.addWidget(self.search_column_combo)
        header_layout.addWidget(self.search_input)
        header_layout.addWidget(search_btn)

        main_layout.addWidget(header_card)

        records_card = QFrame()
        records_card.setObjectName("ContentCard")
        records_layout = QVBoxLayout(records_card)
        records_layout.setContentsMargins(8, 0, 8, 0)
        records_layout.setSpacing(8)

        self.table_records_label = QLabel("Poduction Records", objectName="table_label")
        self.table_records_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        records_layout.addWidget(self.table_records_label)

        # set of rows
        self.headers = ["prod_id", "Date", "Customer", "Product Code", "Product Color", "Lot No", "Qty Produced"]
        self.rows = read.get_all_production_data()

        self.table_records = QTableView()
        self.table_model = TableModel(self.rows, self.headers)
        self.table_records.setModel(self.table_model)
        self.table_records.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_records.verticalHeader().setVisible(False)  # hide row numbers
        self.table_records.setColumnHidden(0, True)
        self.table_records.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_records.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table_records.setAlternatingRowColors(True)
        self.table_records.setSortingEnabled(True)
        self.table_records.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table_records.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_records.sortByColumn(1, Qt.SortOrder.DescendingOrder)
        self.table_records.customContextMenuRequested.connect(self.show_context_menu)
        # Connect to row selection change
        self.table_records.selectionModel().selectionChanged.connect(self.on_row_selected)

        records_layout.addWidget(self.table_records, stretch=1)
        main_layout.addWidget(records_card, stretch=3)

        details_card = QFrame()
        details_card.setObjectName("ContentCard")
        details_card.setStyleSheet("""
            QFrame#ContentCard {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 6px;
            }
        """)
        details_layout = QVBoxLayout(details_card)
        details_layout.setContentsMargins(15, 0, 15, 0)
        details_layout.setSpacing(8)

        details_label = QLabel("Production Materials Details", objectName="table_label")
        details_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        details_layout.addWidget(details_label)

        self.details_header = ["prod_id", "Material Name", "Large Scale(kg)", "Small Scale(g)", "Total Weight(kg)"]
        self.details_row = [["0", "--", "0.00", "0.00", "0.00"]        ]
        self.details_table = QTableView()
        self.details_table_model = TableModel(self.details_row, self.details_header)
        self.details_table.setModel(self.details_table_model)
        self.details_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.details_table.verticalHeader().setVisible(False)  # hide row numbers
        self.details_table.setColumnHidden(0, True)
        self.details_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.details_table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.details_table.setAlternatingRowColors(True)
        self.details_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        details_layout.addWidget(self.details_table, stretch=1)
        main_layout.addWidget(details_card, stretch=3)

        controls_layout =QHBoxLayout()
        controls_layout.setSpacing(10)

        self.btn_cancelled = QPushButton("Cancelled", objectName="DangerButton")
        self.btn_cancelled.setIcon(fa.icon('mdi.cancel', color='white'))
        controls_layout.addWidget(self.btn_cancelled)

        controls_layout.addStretch()

        self.btn_sync = QPushButton("Sync", objectName="SuccessButton")
        self.btn_sync.setIcon(fa.icon('fa5s.sync-alt', color='white'))
        self.btn_sync.clicked.connect(self.run_production_sync)
        controls_layout.addWidget(self.btn_sync)

        self.btn_refresh = QPushButton("Refresh", objectName="TertiaryButton")
        self.btn_refresh.setIcon(fa.icon('fa5s.redo', color='white'))
        controls_layout.addWidget(self.btn_refresh)

        self.btn_view = QPushButton("View", objectName="InfoButton")
        self.btn_view.setIcon(fa.icon('fa5s.eye', color='white'))
        controls_layout.addWidget(self.btn_view)

        main_layout.addLayout(controls_layout)

    def filter_production(self):
        PRODUCTION_COL_MAP = {
            "All Columns": None,
            "Prod ID": 0,
            "Date": 1,
            "Customer": 2,
            "Product Code": 3,
            "Product Color": 4,
            "Lot No": 5,
            "Qty Produced": 6,
        }

        search_text = self.search_input.text().lower()
        col_label = self.search_column_combo.currentText()
        col_index = PRODUCTION_COL_MAP.get(col_label, None)
        self.table_model.filter_data(search_text, col_index)

    def on_row_selected(self):
        index = self.table_records.selectionModel().selectedRows()
        if not index:
            return

        row = index[0].row()

        try:
            prod_id = self.rows[row][0]  # prod_id
            customer = self.rows[row][2]  # customer
            lot_no = self.rows[row][5]  # lot_number

            self.selected_production_label.setText(f"LOT NO: {lot_no} - {customer}")
            self.load_production_details(prod_id)

        except IndexError:
            print("Error: Could not read row data")

    def load_production_details(self, prod_id):
        try:
            if not prod_id:
                self.details_table_model.clear_data()
                return

            details = read.get_single_production_details(prod_id)
            if not details:
                self.details_table_model.clear_data()
                return

            data = []
            for row in details:
                row_list = []
                for col, value in enumerate(row):
                    if col == 0:
                        try:
                            row_list.append(int(value) if value is not None else 0)
                        except (ValueError, TypeError):
                            row_list.append(0)
                    elif col == 1:  # Material name/code
                        row_list.append(str(value) if value else "")
                    else:  # Numeric values
                        try:
                            row_list.append(float(value) if value is not None else 0.0)
                        except (ValueError, TypeError):
                            row_list.append(0.0)
                data.append(row_list)

            self.details_table_model.set_data(data)
        except Exception as e:
            print(e)

    def get_selected_row_id(self):
        index = self.table_records.selectionModel().currentIndex()

        if not index.isValid():
            return None

        value = self.table_model.data(
            self.table_model.index(index.row(), 0),
            Qt.ItemDataRole.DisplayRole
        )

        return int(value) if value else 0

    def show_context_menu(self, position):
        index = self.table_records.indexAt(position)

        if not index.isValid():
            return

        # Select the row
        self.table_records.selectRow(index.row())

        # Get selected row ID (hidden column 0)
        prod_id = self.get_selected_row_id()

        menu = QMenu()

        view_manual_mb = menu.addAction(fa.icon('msc.wrench-subaction'), " Manual - MB")
        view_auto_mb = menu.addAction(fa.icon('ph.eye-light'), " Auto - MB")
        view_manual_dc = menu.addAction(fa.icon('msc.tools'), " Manual - DC")
        view_auto_dc = menu.addAction(fa.icon('mdi.monitor-eye'), " Auto - DC")

        action = menu.exec(self.table_records.viewport().mapToGlobal(position))

        if action == view_auto_mb:
            self.view_auto(prod_id)
        elif action == view_manual_mb:
            self.view_manual(prod_id)
        elif action == view_auto_dc:
            self.view_auto_dc(prod_id)
        elif action == view_manual_dc:
            self.view_manual_dc(prod_id)


    def view_manual(self, prod_id):
        self.go_to_manual_entry.emit(prod_id)
    def view_auto(self, prod_id):
        self.go_to_manual_entry.emit(prod_id)

    def view_manual_dc(self, prod_id):
        print("Delete row ID:", prod_id)

    def view_auto_dc(self, prod_id):
        print("Delete row ID:", prod_id)

    def run_production_sync(self):
        thread = QThread()
        worker = Sync()
        worker.moveToThread(thread)

        loading_dialog = LoadingDialog("Syncing Production Data", self)

        worker.progress.connect(loading_dialog.update_progress)
        worker.finished.connect(
            lambda success, message: self.on_sync_finished(success, message, thread, loading_dialog)
        )

        thread.started.connect(worker.run)
        worker.finished.connect(thread.quit)
        thread.finished.connect(lambda: worker.deleteLater())
        thread.finished.connect(thread.deleteLater)

        thread.start()
        loading_dialog.exec()

    def on_sync_finished(self, success, message, thread, loading_dialog, sync_type=None):
        try:
            if loading_dialog.isVisible():
                loading_dialog.accept()

            if success:
                QMessageBox.information(self, "Sync Complete", message)
            else:
                QMessageBox.critical(self, "Sync Error", message)

        except Exception as e:
            print(f"Error in on_sync_finished: {e}")