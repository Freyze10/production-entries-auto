from PyQt6.QtCore import Qt, QThread
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableView, \
    QHeaderView, QMenu, QMessageBox, QComboBox, QSizePolicy
import qtawesome as fa
from PyQt6.QtCore import pyqtSignal

from db.legacy import Sync
from db.read import get_cancelled_production_data, get_all_production_data, get_single_production_details
from table_model.model import TableModel
from util.debounce import finished_typing
from util.field_format import setup_auto_completers
from util.loading import LoadingDialog


class ProductionRecords(QWidget):
    go_to_manual_entry = pyqtSignal(int)
    go_to_auto_entry = pyqtSignal(int)
    go_to_dc_auto = pyqtSignal(int)

    def __init__(self, mac_address):
        super().__init__()
        self.mac_address = mac_address
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
        self.selected_production_label.setMinimumWidth(100)
        self.selected_production_label.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred)
        header_layout.addWidget(self.selected_production_label, stretch=1)

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
        self.headers = ["prod_id", "Date", "Customer", "Product Code", "Product Color", "Lot No", "Qty Produced", "WIP"]
        self.rows = get_all_production_data()

        self.table_records = QTableView()
        self.table_model = TableModel(self.rows, self.headers)
        self.table_records.setModel(self.table_model)
        self.table_records.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        # Force the "Details" column (index 3) to stretch and fill empty space
        self.table_records.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table_records.setColumnWidth(1, 80)
        self.table_records.setColumnWidth(3, 110)
        self.table_records.setColumnWidth(4, 110)
        self.table_records.setColumnWidth(5, 130)
        self.table_records.setMouseTracking(True)
        self.table_records.viewport().setMouseTracking(True)
        # 2. Install the event filter on the VIEWPORT (the actual area where rows are)
        self.table_records.viewport().installEventFilter(self)
        self.table_records.verticalHeader().setVisible(False)  # hide row numbers
        self.table_records.setColumnHidden(0, True)
        self.table_records.setColumnHidden(7, True)
        self.table_records.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_records.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table_records.setAlternatingRowColors(True)
        self.table_records.setSortingEnabled(True)
        self.table_records.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table_records.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_records.sortByColumn(0, Qt.SortOrder.DescendingOrder)
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
        self.details_row = [["0", "--", "0.00", "0.00", "0.00"]]
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
        self.btn_cancelled.clicked.connect(self.btn_cancel_clicked)
        controls_layout.addWidget(self.btn_cancelled)

        controls_layout.addStretch()

        self.btn_sync = QPushButton("Sync", objectName="SuccessButton")
        self.btn_sync.setIcon(fa.icon('fa5s.sync-alt', color='white'))
        self.btn_sync.clicked.connect(self.run_production_sync)
        controls_layout.addWidget(self.btn_sync)

        self.btn_refresh = QPushButton("Refresh", objectName="InfoButton")
        self.btn_refresh.setIcon(fa.icon('fa5s.redo', color='white'))
        self.btn_refresh.clicked.connect(self.refresh_records)
        controls_layout.addWidget(self.btn_refresh)

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
        wip_no = self.table_model._data[row][7]

        try:
            prod_id = self.table_model._data[row][0]  # Get from model data directly
            customer = self.table_model._data[row][2]
            lot_no = self.table_model._data[row][5]

            # --- Update Label with WIP No if it exists ---
            wip_display = f" | WIP: {wip_no}" if wip_no and str(wip_no).strip() not in ("", "None", "0") else ""
            self.selected_production_label.setText(f"LOT NO: {lot_no} - {customer}{wip_display}")

            self.load_production_details(prod_id)

        except IndexError:
            print("Error: Could not read row data")

    def load_production_details(self, prod_id):
        try:
            if not prod_id:
                self.details_table_model.clear_data()
                return

            details = get_single_production_details(prod_id)
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
        # view_manual_dc = menu.addAction(fa.icon('msc.tools'), " Manual - DC")
        view_auto_dc = menu.addAction(fa.icon('mdi.monitor-eye'), " Auto - DC")

        action = menu.exec(self.table_records.viewport().mapToGlobal(position))

        if action == view_auto_mb:
            self.view_auto(prod_id)
        elif action == view_manual_mb:
            self.view_manual(prod_id)
        elif action == view_auto_dc:
            self.view_auto_dc(prod_id)
        # elif action == view_manual_dc:
        #     self.view_manual_dc(prod_id)


    def view_manual(self, prod_id):
        self.go_to_manual_entry.emit(prod_id)
    def view_auto(self, prod_id):
        self.go_to_auto_entry.emit(prod_id)

    # def view_manual_dc(self, prod_id):
    #     print("DC manual row ID:", prod_id)

    def view_auto_dc(self, prod_id):
        self.go_to_dc_auto.emit(prod_id)

    def refresh_records(self):
        try:
            self.table_model.set_data(self.rows)

            # Reset the selection in the UI
            self.table_records.clearSelection()
            self.table_records.sortByColumn(0, Qt.SortOrder.DescendingOrder)
            self.table_records.scrollToTop()
            self.selected_production_label.setText("INDEX REF. - FORMULATION NO.: No Selection")

            # Reset the details table to its default empty state
            self.details_table_model.set_data(self.details_row)

            # del setup_auto_completers._cached_expanded_lots

            # Clear search bar if text was entered
            self.search_input.clear()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to refresh data: {e}")

    def btn_cancel_clicked(self):
        if self.btn_cancelled.text() == "Cancelled":
            self.cancelled_records()
        else:
            self.production_records()

    def cancelled_records(self):
        try:
            cancelled_rows = get_cancelled_production_data()

            self.table_model.set_data(cancelled_rows)

            # Reset the selection in the UI
            self.table_records.clearSelection()
            self.table_records.sortByColumn(0, Qt.SortOrder.DescendingOrder)
            self.table_records.scrollToTop()
            self.table_records.setStyleSheet("""
                QTableView {
                    background-color: #fceaea;   /* Light red background */
                    alternate-background-color: #f9d5d5;
                    gridline-color: #e0b1b1;
                    color: #721c24;              /* Dark red text */
                    selection-background-color: #b83232;
                    selection-color: white;
                }
                QHeaderView::section {
                    background-color: #b83232;
                    color: white;
                    border: 1px solid #9e2a2a;
                    padding: 4px;
                }
            """)
            self.selected_production_label.setText("INDEX REF. - FORMULATION NO.: No Selection")

            # Reset the details table to its default empty state
            self.details_table_model.set_data(self.details_row)

            # Clear search bar if text was entered
            self.search_input.clear()

            #     change name of button
            self.btn_cancelled.setText("Show Records")
            self.btn_cancelled.setObjectName("SuccessButton")
            self.btn_cancelled.setIcon(fa.icon('ri.file-paper-2-fill', color='white'))
            self.btn_cancelled.style().unpolish(self.btn_cancelled)
            self.btn_cancelled.style().polish(self.btn_cancelled)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to refresh data: {e}")

    def production_records(self):
        try:

            self.table_model.set_data(self.rows)

            # Reset the selection in the UI
            self.table_records.clearSelection()
            self.table_records.sortByColumn(0, Qt.SortOrder.DescendingOrder)
            self.table_records.scrollToTop()
            self.table_records.setStyleSheet("")
            self.selected_production_label.setText("INDEX REF. - FORMULATION NO.: No Selection")

            # Reset the details table to its default empty state
            self.details_table_model.set_data(self.details_row)

            # Clear search bar if text was entered
            self.search_input.clear()

            #     change name of button
            self.btn_cancelled.setText("Cancelled")
            self.btn_cancelled.setObjectName("DangerButton")
            self.btn_cancelled.setIcon(fa.icon('mdi.cancel', color='white'))
            self.btn_cancelled.style().unpolish(self.btn_cancelled)
            self.btn_cancelled.style().polish(self.btn_cancelled)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to refresh data: {e}")

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
                self.rows = get_all_production_data()
                loading_dialog.accept()

            if success:

                QMessageBox.information(self, "Sync Complete", message)
            else:
                QMessageBox.critical(self, "Sync Error", message)

        except Exception as e:
            print(f"Error in on_sync_finished: {e}")