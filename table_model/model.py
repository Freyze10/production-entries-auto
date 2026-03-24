from PyQt6.QtCore import Qt, QAbstractTableModel

class TableModel(QAbstractTableModel):
    def __init__(self, data, headers):
        super().__init__()
        self._all_data = data or []
        self._data = data
        self._headers = headers

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self._headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            return str(self._data[index.row()][index.column()])
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self._headers[section]
            else:
                return str(section+1)
        return None

    # ── Critical for sorting ──
    def sort(self, column, order):
        self.layoutAboutToBeChanged.emit()
        self._data.sort(
            key=lambda row: row[column],
            reverse=(order == Qt.SortOrder.DescendingOrder)
        )
        self.layoutChanged.emit()

    def set_data(self, data):
        """Update the entire data and refresh the view"""
        self.beginResetModel()
        self._all_data = data
        self._data = data[:]
        self.endResetModel()

    def filter_data(self, search_text):
        """Filter rows based on search text (searches all columns + hidden prod_id)"""
        if not search_text or not search_text.strip():
            self._data = self._all_data[:]  # show all
        else:
            search_text = search_text.lower().strip()
            self._data = []
            for row in self._all_data:
                # Convert entire row to string and search
                row_str = " ".join(str(item).lower() for item in row)
                if search_text in row_str:
                    self._data.append(row)

        self.beginResetModel()
        self.endResetModel()

    def clear_data(self):
        """Clear all data"""
        self.beginResetModel()
        self._data = [["0", "--", "0.00", "0.00", "0.00"],
            ["0", "--", "0.00", "0.00", "0.00"],
            ["0", "--", "0.00", "0.00", "0.00"],
            ["0", "--", "0.00", "0.00", "0.00"]]
        self.endResetModel()