from PyQt6.QtCore import Qt, QAbstractTableModel


class TableModel(QAbstractTableModel):
    def __init__(self, data, headers):
        super().__init__()
        self._data = data  # list of dicts, each dict must have a unique 'id'
        self._headers = headers

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self._headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        row_data = self._data[index.row()]
        column_key = self._headers[index.column()]

        if role == Qt.ItemDataRole.DisplayRole:
            return str(row_data.get(column_key, ""))
        elif role == Qt.ItemDataRole.UserRole:
            # Return the unique ID for the row
            return row_data.get("id")
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self._headers[section].capitalize()
            else:
                return str(section + 1)
        return None

    def sort(self, column, order):
        """Sort table by column index."""
        key = self._headers[column]
        self.layoutAboutToBeChanged.emit()
        try:
            # Attempt numeric sort first
            self._data.sort(
                key=lambda x: float(x.get(key, 0)),
                reverse=(order == Qt.SortOrder.DescendingOrder)
            )
        except ValueError:
            # Fallback to string sort
            self._data.sort(
                key=lambda x: str(x.get(key, "")),
                reverse=(order == Qt.SortOrder.DescendingOrder)
            )
        self.layoutChanged.emit()