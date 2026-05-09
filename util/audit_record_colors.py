from PyQt6.QtWidgets import QStyledItemDelegate, QStyle
from PyQt6.QtGui import QColor, QBrush
from PyQt6.QtCore import Qt
from css.styles import AppStyles


class RowColorDelegate(QStyledItemDelegate):
    def __init__(self, mode="audit", parent=None):
        super().__init__(parent)
        self.mode = mode  # "audit" or "production"

    def paint(self, painter, option, index):
        # 1. Determine the background color
        row = index.row()
        model = index.model()
        bg_hex = "#FFFFFF"  # Default white

        if self.mode == "audit":
            # Column 2 is "Action Type"
            action_index = index.sibling(row, 2)
            action_type = str(action_index.data(Qt.ItemDataRole.DisplayRole) or "").strip().upper()
            bg_hex = AppStyles.ACTION_COLORS.get(action_type, "#FFFFFF")

        elif self.mode == "production":
            # Column 8 is "is_printed" (hidden metadata)
            printed_index = index.sibling(row, 8)
            is_printed = printed_index.data()  # Returns True or False

            if is_printed is False:
                bg_hex = "#FEF3C7"  # Light Amber/Yellow for unprinted

        color = QColor(bg_hex)

        # 2. Handle Selection and Hover (Darken the background color)
        if option.state & QStyle.StateFlag.State_Selected:
            color = color.darker(115)
        elif option.state & QStyle.StateFlag.State_MouseOver:
            color = color.darker(105)

        # 3. Fill the background
        painter.save()
        painter.fillRect(option.rect, color)
        painter.restore()

        # 4. Fix Text Color and Selection Style
        # This prevents the text from turning white when selected
        new_option = option
        new_option.palette.setColor(option.palette.ColorRole.Highlight, color)
        new_option.palette.setColor(option.palette.ColorRole.HighlightedText, QColor("#0F172A"))

        # 5. Paint the actual content (text/icons)
        super().paint(painter, new_option, index)