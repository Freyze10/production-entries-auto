from PyQt6.QtWidgets import QMessageBox


def show_printed_locked_message(self):
    """Helper to show the popup after data is visible."""
    QMessageBox.information(
        self,
        "Record Locked",
        "This production record has already been printed.\n\n"
        "To maintain data integrity, editing and saving are disabled for this ID."
    )
