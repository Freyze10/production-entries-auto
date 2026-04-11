# util/field_format.py
import math
import re

from PyQt6.QtWidgets import QMessageBox, QLineEdit, QTableWidgetItem
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent

def format_to_float(self, event, number, ):
    """Format the input to a float with 6 decimal places when focus is lost."""
    text = number.text().strip()
    try:
        if text:
            value = float(text)
            number.setText(f"{value:.6f}")
    except ValueError:
        QMessageBox.warning(self, "Invalid Input", "Please enter a valid number.")
        number.setFocus()
        number.selectAll()
        return
    QLineEdit.focusOutEvent(number, event)


def production_mixing_time(event, line_edit):
    text = line_edit.text().strip()

    # Remove any existing MIN/MINS/MIN./MINS. (case-insensitive)
    text = re.sub(r'\s*MIN\.?S?\s*$', '', text, flags=re.IGNORECASE).strip()

    # Match valid number (integer or float)
    match = re.match(r'^(\d*\.?\d+)', text)
    if match:
        number_str = match.group(1)
        try:
            value = float(number_str)
            # Determine singular/plural
            unit = "MIN." if value == 1.0 else "MINS."
            line_edit.setText(f"{number_str} {unit}")
        except ValueError:
            line_edit.setText("5 MINS.")  # fallback
    else:
        # Optional: revert to default if invalid
        line_edit.setText("5 MINS.")


def update_batch_notes(required, per_batch, notes_field):
    """
    Reusable function to calculate and display batch information.

    Parameters:
        required:    Quantity required (can be float, int, or str)
        per_batch:   Quantity per batch (can be float, int, or str)
        notes_field: The QLineEdit / QLabel / widget where the text will be shown
    """
    try:
        # Convert inputs to float safely
        req = float(required) if required is not None else 0.0
        per = float(per_batch) if per_batch is not None else 0.0

        if per <= 0:
            raise ValueError("Per batch quantity must be greater than zero")

        # Use math.ceil to round UP (important for batching)
        n = math.ceil(req / per)

        text = f"{n} batch{'es' if n != 1 else ''} by {per:.3f} KG."
        notes_field.setText(text)

    except Exception:
        notes_field.setText("1 batch by 0.000 KG.")

class SmartDateEdit(QLineEdit):
    """
    A QLineEdit that auto-formats numeric input into MM/DD/YYYY.

    - Only accepts numeric keys (0–9)
    - Slashes are inserted automatically after MM and DD
    - Backspace removes the last digit (and trailing slash if needed)
    - Displays a placeholder: MM/DD/YYYY
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("MM/DD/YYYY")
        self.setMaxLength(10)
        self._digits = ""  # stores only the raw digits the user has typed

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _format(self, digits: str) -> str:
        """Convert a raw digit string (up to 8 chars) into MM/DD/YYYY format."""
        d = digits[:8]
        result = ""
        if len(d) >= 1:
            result += d[:2]  # MM
        if len(d) >= 3:
            result += "/" + d[2:4]  # /DD
        if len(d) >= 5:
            result += "/" + d[4:8]  # /YYYY
        elif len(d) == 3 or len(d) == 4:
            result += "/"  # trailing slash after DD digits start
        return result

    def _apply(self):
        """Re-render the formatted string into the widget without triggering recursion."""
        self.blockSignals(True)
        self.setText(self._format(self._digits))
        # Move cursor to end
        self.setCursorPosition(len(self.text()))
        self.blockSignals(False)

    # ── Event override ────────────────────────────────────────────────────────

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()

        # Allow: Backspace
        if key == Qt.Key.Key_Backspace:
            if self._digits:
                self._digits = self._digits[:-1]
                self._apply()
            return

        # Allow: Delete (clear all)
        if key == Qt.Key.Key_Delete:
            self._digits = ""
            self._apply()
            return

        # Allow: Tab, Return, navigation keys — pass through normally
        if key in (Qt.Key.Key_Tab, Qt.Key.Key_Backtab, Qt.Key.Key_Return,
                   Qt.Key.Key_Enter, Qt.Key.Key_Left, Qt.Key.Key_Right,
                   Qt.Key.Key_Home, Qt.Key.Key_End):
            super().keyPressEvent(event)
            return

        # Allow: Ctrl+A, Ctrl+C, Ctrl+V, Ctrl+X
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier and key in (
                Qt.Key.Key_A, Qt.Key.Key_C, Qt.Key.Key_V, Qt.Key.Key_X
        ):
            super().keyPressEvent(event)
            return

        # Only accept digit keys 0–9
        if Qt.Key.Key_0 <= key <= Qt.Key.Key_9:
            if len(self._digits) < 8:  # MM DD YYYY = 8 digits max
                self._digits += event.text()
                self._apply()
            return

        # Block everything else (letters, symbols, space, etc.)

    # ── Public helpers ────────────────────────────────────────────────────────

    def date_text(self) -> str:
        """Return the formatted date string, e.g. '02/23/2026'."""
        return self.text()

    def is_complete(self) -> bool:
        """Return True only when all 8 digits have been entered (MM/DD/YYYY)."""
        return len(self._digits) == 8

    def clear_date(self):
        """Reset the field."""
        self._digits = ""
        self._apply()

    def set_date_text(self, date_str: str):
        """
        Pre-fill the field from a string.
        Accepts 'MM/DD/YYYY', 'MMDDYYYY', or any string — strips non-digits.
        """
        digits = "".join(ch for ch in date_str if ch.isdigit())
        self._digits = digits[:8]
        self._apply()


class NumericTableWidgetItem(QTableWidgetItem):
    def __init__(self, value, display_text=None, is_float=False):
        self.value = value
        self.is_float = is_float
        if display_text is None:
            if is_float:
                display_text = f"{value:.6f}" if value is not None else ""
            else:
                display_text = str(value) if value is not None else ""
        super().__init__(display_text)

    def __lt__(self, other):
        if isinstance(other, NumericTableWidgetItem):
            if self.is_float:
                return float(self.value) < float(other.value)
            else:
                return int(self.value) < int(other.value)
        return super().__lt__(other)