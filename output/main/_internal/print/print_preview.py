import os
import shutil
import sys
import tempfile

import qtawesome as fa
import win32print
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtPdf import QPdfDocument
from PyQt6.QtPdfWidgets import QPdfView
from PyQt6.QtWidgets import (QComboBox, QHBoxLayout, QLabel, QMessageBox,
                             QPushButton, QVBoxLayout, QWidget)

from db.update import print_production
from db.write import log_audit_trail
from print.production_form import export_pdf, fill_template, print_docx

BASE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_PATH = os.path.join(BASE_DIR, "prod_form_template.docx")


class _Worker(QThread):
    """Runs a slow Word call off the UI thread."""
    ok = pyqtSignal()
    failed = pyqtSignal(str)

    def __init__(self, fn, *args):
        super().__init__()
        self.fn, self.args = fn, args

    def run(self):
        try:
            self.fn(*self.args)
            self.ok.emit()
        except Exception as e:
            self.failed.emit(str(e))


class ProductionPrintPreview(QWidget):
    printed = pyqtSignal(str)

    def __init__(self, production_data: dict, materials_data: list, wip_no=False, parent=None, audit=None,
                 role="Editor"):
        super().__init__(parent)
        self.data = production_data or {}
        self.mats = materials_data or []
        self.wip_no = wip_no
        self.audit = audit
        self.can_print = str(role).upper() != "VIEWER"
        self._worker = None

        self.tmp_dir = tempfile.mkdtemp(prefix="mbpi_print_")
        self.docx_path = os.path.join(self.tmp_dir, "production.docx")
        self.pdf_path = os.path.join(self.tmp_dir, "production.pdf")

        self.setWindowFlags(Qt.WindowType.Window |
                            Qt.WindowType.WindowMinimizeButtonHint |
                            Qt.WindowType.WindowMaximizeButtonHint |
                            Qt.WindowType.WindowCloseButtonHint)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowTitle("Print Preview")
        self.resize(900, 950)
        self.setStyleSheet("background:#525659;")

        self.setup_ui()
        self.build_preview()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        toolbar = QWidget()
        toolbar.setFixedHeight(60)
        toolbar.setStyleSheet("background:#f8f9fa; border-bottom: 1px solid #ddd; padding: 5px;")
        tb_layout = QHBoxLayout(toolbar)

        self.printer_combo = QComboBox()
        self.load_printers()
        tb_layout.addWidget(QLabel("<b>PRINTER:</b>"))
        tb_layout.addWidget(self.printer_combo, 1)

        self.status = QLabel("")
        tb_layout.addWidget(self.status)

        self.btn_print = QPushButton(" START PRINTING ")
        self.btn_print.setIcon(fa.icon('fa5s.print', color='white'))
        self.btn_print.setStyleSheet(
            "background:#28a745; color:white; padding:10px 20px; font-weight:bold; border-radius:4px;")
        self.btn_print.clicked.connect(self.print_report)
        tb_layout.addWidget(self.btn_print)
        main_layout.addWidget(toolbar)

        self.pdf_doc = QPdfDocument(self)
        self.pdf_view = QPdfView(self)
        self.pdf_view.setDocument(self.pdf_doc)
        self.pdf_view.setPageMode(QPdfView.PageMode.MultiPage)
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
        main_layout.addWidget(self.pdf_view, 1)

    def load_printers(self):
        try:
            printers = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
            for p in printers:
                self.printer_combo.addItem(p[2])
            self.printer_combo.setCurrentText(win32print.GetDefaultPrinter())
        except Exception:
            pass

    # ------------------------------------------------------------ helpers
    def _set_busy(self, busy, text=""):
        self.status.setText(text)
        self.btn_print.setEnabled(self.can_print and not busy)
        if not self.can_print:
            self.btn_print.setObjectName("disabled_btn")

    def _run(self, fn, *args, done):
        self._worker = _Worker(fn, *args)
        self._worker.ok.connect(done)
        self._worker.failed.connect(self._on_error)
        self._worker.start()

    def _on_error(self, msg):
        self.btn_print.setText(" START PRINTING ")
        self._set_busy(False)
        QMessageBox.critical(self, "Error", msg)

    # ------------------------------------------------------------ preview
    def build_preview(self):
        self._set_busy(True, "Preparing preview...")
        try:
            fill_template(TEMPLATE_PATH, self.docx_path, self.data, self.mats, self.wip_no)
        except Exception as e:
            self._on_error(f"Could not fill the template:\n{e}")
            return
        self._run(export_pdf, self.docx_path, self.pdf_path, done=self._show_pdf)

    def _show_pdf(self):
        self.pdf_doc.load(self.pdf_path)
        self._set_busy(False)

    # ------------------------------------------------------------ printing
    def print_report(self):
        self.btn_print.setText(" SENDING... ")
        self._set_busy(True, "Sending to printer...")
        self._run(print_docx, self.docx_path, self.printer_combo.currentText(), done=self._printed)

    def _printed(self):
        try:
            QMessageBox.information(self, "Success", "Printed Successfully.")
            log_audit_trail(self.audit['mac'], self.audit['action'], self.audit['details'])
            print_production(self.data.get('prod_id'))
            self.close()
        except Exception as e:
            self._on_error(str(e))

    def closeEvent(self, event):
        if self._worker is not None and self._worker.isRunning():
            self._worker.wait()
        self.pdf_doc.close()  # release the file so the temp folder can be deleted
        shutil.rmtree(self.tmp_dir, ignore_errors=True)
        super().closeEvent(event)