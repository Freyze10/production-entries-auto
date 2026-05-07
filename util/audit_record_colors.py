from PyQt6.QtWidgets import QStyledItemDelegate, QStyle
from PyQt6.QtGui import QColor, QBrush
from PyQt6.QtCore import Qt
from css.styles import AppStyles


class RowColorDelegate(QStyledItemDelegate):

    def __init__(self, action_col=2, parent=None):
        super().__init__(parent)
        self.action_col = action_col  # column index where action type lives

    def paint(self, painter, option, index):
        # 1. Get the action value from the action column of this row
        action_index = index.sibling(index.row(), self.action_col)
        action_type = str(action_index.data(Qt.ItemDataRole.DisplayRole) or "").strip().upper()

        # 2. Look up color from ACTION_COLORS, fallback to white
        color_hex = AppStyles.ACTION_COLORS.get(action_type, "#FFFFFF")
        color = QColor(color_hex)

        # 3. Darken slightly on selection or hover
        if option.state & QStyle.StateFlag.State_Selected:
            color = color.darker(120)
        elif option.state & QStyle.StateFlag.State_MouseOver:
            color = color.darker(105)

        # 4. Paint the background
        painter.fillRect(option.rect, color)

        # 5. Fix text color so it stays dark (not inverted by selection highlight)
        option.palette.setColor(option.palette.ColorRole.Highlight, color)
        option.palette.setColor(option.palette.ColorRole.HighlightedText, QColor("#0F172A"))

        # 6. Paint the text/icon normally
        super().paint(painter, option, index)