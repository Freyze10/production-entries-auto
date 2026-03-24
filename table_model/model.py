from PyQt6.QtCore import Qt, QAbstractTableModel

class TableModel(QAbstractTableModel):
    def __init__(self, data, headers):
        super().__init__()
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
        self._data = data
        self.endResetModel()

    def clear_data(self):
        """Clear all data"""
        self.beginResetModel()
        self._data = [["0", "--", "0.00", "0.00", "0.00"],
            ["0", "--", "0.00", "0.00", "0.00"],
            ["0", "--", "0.00", "0.00", "0.00"],
            ["0", "--", "0.00", "0.00", "0.00"]]
        self.endResetModel()