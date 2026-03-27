import io
import os
import tempfile
import win32api
import win32print
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from PyQt6.QtCore import Qt, pyqtSignal, QBuffer, QIODevice, QSize, QPointF
from PyQt6.QtGui import QPainter, QPageSize, QAction
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtPdf import QPdfDocument, QPdfDocumentRenderOptions
from PyQt6.QtPdfWidgets import QPdfView
from PyQt6.QtWidgets import *
import qtawesome as fa


class ProductionPrintPreview(QDialog):
    printed = pyqtSignal(str)

    def __init__(self, production_data: dict, materials_data: list, parent=None):
        super().__init__(parent)
        self.data = production_data or {}
        self.mats = materials_data or []

        self.setWindowTitle("Print Preview - Production Entry")
        self.resize(1100, 950)
        self.setStyleSheet("background:white;")

        # Generate the PDF in memory for the preview
        self.pdf_buffer = io.BytesIO()
        self.generate_pdf(self.pdf_buffer)
        self.pdf_bytes = self.pdf_buffer.getvalue()

        # Load into the UI Viewer
        self.qbuffer = QBuffer(self)
        self.qbuffer.setData(self.pdf_bytes)
        self.qbuffer.open(QIODevice.OpenModeFlag.ReadOnly)
        self.pdf_doc = QPdfDocument(self)
        self.pdf_doc.load(self.qbuffer)

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        toolbar = QWidget()
        toolbar.setStyleSheet("background:#f8f9fa; border-bottom: 1px solid #ddd; padding: 5px;")
        tb_layout = QHBoxLayout(toolbar)

        tb_layout.addWidget(QLabel("<b>Preview Zoom:</b>"))
        self.zoom_combo = QComboBox()
        self.zoom_combo.addItems(["75%", "100%", "125%", "150%"])
        self.zoom_combo.setCurrentText("100%")
        self.zoom_combo.currentTextChanged.connect(self.on_zoom_changed)
        tb_layout.addWidget(self.zoom_combo)

        tb_layout.addStretch()
        btn_print = QPushButton(" PRINT TO SYSTEM ")
        btn_print.setIcon(fa.icon('fa5s.print', color='white'))
        btn_print.setStyleSheet(
            "background:#28a745; color:white; padding:8px 15px; font-weight:bold; border-radius:4px;")
        btn_print.clicked.connect(self.print_report)
        tb_layout.addWidget(btn_print)
        layout.addWidget(toolbar)

        self.pdf_view = QPdfView(self)
        self.pdf_view.setDocument(self.pdf_doc)
        layout.addWidget(self.pdf_view)

    def generate_pdf(self, target):
        """Creates the PDF. target can be a file path or a BytesIO buffer."""
        # Use thicker lines (1.2) so the LX-310 pins hit more solidly
        doc = SimpleDocTemplate(target, pagesize=letter, leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30)
        styles = getSampleStyleSheet()

        # Use Courier because it aligns perfectly with dot-matrix pins
        styles.add(ParagraphStyle(name='C', fontName='Courier', fontSize=10, leading=12))
        styles.add(ParagraphStyle(name='CB', fontName='Courier-Bold', fontSize=10, leading=12))
        styles.add(ParagraphStyle(name='CB_Center', parent=styles['CB'], alignment=TA_CENTER, fontSize=12))

        story = []

        # 1. Header and ID Box
        title_part = [[Paragraph("MASTERBATCH PHILIPPINES, INC.", styles['CB'])],
                      [Paragraph("PRODUCTION ENTRY", styles['C'])], [Paragraph("FORM NO. FM00012A1", styles['C'])]]
        id_part = [
            [Paragraph("PRODUCTION ID   :", styles['C']), Paragraph(self.data.get('prod_id', ''), styles['CB'])],
            [Paragraph("PRODUCTION DATE :", styles['C']),
             Paragraph(self.data.get('production_date', ''), styles['CB'])],
            [Paragraph("ORDER FORM NO.  :", styles['C']), Paragraph(self.data.get('order_form_no', ''), styles['CB'])],
            [Paragraph("FORMULATION NO. :", styles['C']), Paragraph(self.data.get('formulation_id', ''), styles['CB'])]
        ]

        header_table = Table([[Table(title_part), Table(id_part, colWidths=[1.6 * inch, 1.2 * inch])]],
                             colWidths=[4.2 * inch, 3 * inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOX', (1, 0), (1, 0), 1.2, colors.black),  # Thicker box for dot-matrix clarity
        ]))
        story.append(header_table)
        story.append(Spacer(1, 15))

        # 2. Details
        details_data = [
            [Paragraph("PRODUCT CODE  :", styles['C']), Paragraph(self.data.get('product_code', ''), styles['CB']),
             Paragraph("MIXING TIME   :", styles['C']), Paragraph(self.data.get('mixing_time', ''), styles['CB'])],
            [Paragraph("PRODUCT COLOR:", styles['C']), Paragraph(self.data.get('product_color', ''), styles['CB']),
             Paragraph("MACHINE NO:", styles['C']), Paragraph(self.data.get('machine_no', ''), styles['CB'])],
            [Paragraph("DOSAGE        :", styles['C']),
             Paragraph(f"{float(self.data.get('dosage', 0)):.6f}", styles['CB']),
             Paragraph("QTY REQUIRED:", styles['C']),
             Paragraph(f"{float(self.data.get('qty_required', 0)):.6f}", styles['CB'])],
            [Paragraph("CUSTOMER :", styles['C']), Paragraph(self.data.get('customer', ''), styles['CB']),
             Paragraph("QTY PER BATCH:", styles['C']),
             Paragraph(f"{float(self.data.get('qty_per_batch', 0)):.6f}", styles['CB'])],
            [Paragraph("LOT NO.:", styles['C']), Paragraph(self.data.get('lot_number', ''), styles['CB']),
             Paragraph("QTY TO PRODUCE:", styles['C']),
             Paragraph(f"{float(self.data.get('qty_produced', 0)):.6f}", styles['CB'])]
        ]
        story.append(Table(details_data, colWidths=[1.4 * inch, 2.2 * inch, 1.5 * inch, 2.3 * inch]))
        story.append(Spacer(1, 15))

        # 3. Batch Title
        story.append(Paragraph(self.batch_text().upper(), styles['CB_Center']))
        story.append(Spacer(1, 10))

        # 4. Table
        mat_rows = [["MATERIAL CODE", "LARGE SCALE (Kg.)", "SMALL SCALE (grm.)", "WEIGHT (Kg.)"]]
        for m in self.mats:
            mat_rows.append([m['material_code'], f"{float(m['large_scale']):.7f}", f"{float(m['small_scale']):.7f}",
                             f"{float(m['total_weight']):.7f}"])

        m_table = Table(mat_rows, colWidths=[2.2 * inch, 1.8 * inch, 1.8 * inch, 1.6 * inch])
        m_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Courier'),
            ('LINEABOVE', (0, 0), (-1, 0), 1.2, colors.black),
            ('LINEBELOW', (0, 0), (-1, 0), 1.2, colors.black),
            ('LINEBELOW', (0, -1), (-1, -1), 1.2, colors.black),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ]))
        story.append(m_table)
        story.append(Spacer(1, 40))

        # 5. Signatures
        sig_data = [
            [f"PREPARED BY: {self.data.get('prepared_by', '')}", "APPROVED BY       : ____________________"],
            [f"PRINTED ON : {datetime.now().strftime('%m/%d/%y %I:%M:%S %p')}",
             "MAT'L RELEASED BY : ____________________"],
            ["MBPI-SYSTEM-2017", "PROCESSED BY      : ____________________"]
        ]
        story.append(Table(sig_data, colWidths=[3.8 * inch, 3.6 * inch]))

        doc.build(story)

    def print_report(self):
        """Prints the report directly from memory to avoid file access errors."""
        # 1. Select Printer
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dialog = QPrintDialog(printer, self)
        if dialog.exec() != QPrintDialog.DialogCode.Accepted:
            return

        try:
            # 2. Use the document already loaded in the preview
            # It is already in memory, so no temporary file is needed.
            doc = self.pdf_doc

            if doc.status() != QPdfDocument.Status.Ready:
                QMessageBox.warning(self, "Error", "PDF document is not ready.")
                return

            painter = QPainter(printer)

            # --- THE SHARPNESS SETTINGS ---
            # Disable smoothing to prevent blurry text on dot-matrix pins
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)

            # High-density rendering options
            options = QPdfDocumentRenderOptions()

            for i in range(doc.pageCount()):
                if i > 0:
                    printer.newPage()

                # Render the PDF page to a high-resolution image
                # (Multiplying by 3 ensures the dot-matrix pins have enough 'data' to print clearly)
                page_size = doc.pagePointSize(i).toSize()
                image = doc.render(i, page_size * 3, options)

                # Draw the sharp image to the printer page
                rect = printer.pageRect(QPrinter.Unit.DevicePixel)
                painter.drawImage(rect, image)

            painter.end()

            # No temporary files to delete = No WinError 32!
            QMessageBox.information(self, "Success", "Sent to printer!")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to print: {e}")

    def on_zoom_changed(self, text):
        val = int(text.replace("%", "")) / 100.0
        self.pdf_view.setZoomFactor(val)

    def batch_text(self):
        req, per = float(self.data.get('qty_required', 0)), float(self.data.get('qty_per_batch', 0))
        n = 1 if per == 0 else int(req / per)
        return f"{n} batch{'es' if n > 1 else ''} by {per:.3f} KG."


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    img_data = {"prod_id": "100502", "production_date": "03/02/26", "product_code": "BA4756E",
                "customer": "EVERGOOD PLASTIC", "qty_required": 37.4, "qty_per_batch": 37.4,
                "prepared_by": "R. MAGSALIN"}
    img_mats = [{"material_code": "W35", "large_scale": 1.65, "small_scale": 0, "total_weight": 1.65}]
    dialog = ProductionPrintPreview(img_data, img_mats)
    dialog.show()
    sys.exit(app.exec())