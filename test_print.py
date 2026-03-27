import io
import os
import win32print
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

from PyQt6.QtCore import Qt, pyqtSignal, QBuffer, QIODevice, QSize
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtPdf import QPdfDocument
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

        self.pdf_buffer = io.BytesIO()
        self.generate_pdf()
        self.pdf_bytes = self.pdf_buffer.getvalue()

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
        btn_print = QPushButton(" PRINT TO EPSON LX-310 ")
        btn_print.setIcon(fa.icon('fa5s.print', color='white'))
        btn_print.setStyleSheet(
            "background:#28a745; color:white; padding:8px 15px; font-weight:bold; border-radius:4px;")
        btn_print.clicked.connect(self.print_report)
        tb_layout.addWidget(btn_print)
        layout.addWidget(toolbar)

        self.pdf_view = QPdfView(self)
        self.pdf_view.setDocument(self.pdf_doc)
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.Custom)
        self.pdf_view.setZoomFactor(1.0)
        layout.addWidget(self.pdf_view)

    def generate_raw_text(self):
        """Generates Sharp RAW Text for Epson LX-310."""
        ESC = '\x1b'
        RESET = ESC + '@'
        BOLD_ON = ESC + 'E'
        BOLD_OFF = ESC + 'F'
        QUALITY_ROMAN = ESC + 'x1' + ESC + 'k0'  # Near Letter Quality + Roman Font

        width = 80
        lines = []
        lines.append(RESET + QUALITY_ROMAN)
        lines.append(BOLD_ON + "MASTERBATCH PHILIPPINES, INC." + BOLD_OFF)
        lines.append("PRODUCTION ENTRY")

        form_no = f"FORM NO. {self.data.get('form_no', 'FM00012A1'):<28}"
        lines.append(f"{form_no}+----------------------------+")
        lines.append(f"{'':<37}| PRODUCTION ID   : {self.data.get('prod_id', ''):<8} |")
        lines.append(f"{'':<37}| PRODUCTION DATE : {self.data.get('production_date', ''):<8} |")
        lines.append(f"{'':<37}| ORDER FORM NO.  : {self.data.get('order_form_no', ''):<8} |")
        lines.append(f"{'':<37}| FORMULATION NO. : {self.data.get('formulation_id', ''):<8} |")
        lines.append(f"{'':<37}+----------------------------+")
        lines.append("")

        # 2 Column Details
        c1, c2 = 16, 22

        def row(k1, v1, k2, v2):
            return f"{k1:<{c1}} {BOLD_ON}{v1:<{c2}}{BOLD_OFF} {k2:<{c1}} {BOLD_ON}{v2}{BOLD_OFF}"

        lines.append(row('PRODUCT CODE  :', self.data.get('product_code', ''), 'MIXING TIME   :',
                         self.data.get('mixing_time', '')))
        lines.append(row('PRODUCT COLOR :', self.data.get('product_color', ''), 'MACHINE NO    :',
                         self.data.get('machine_no', '')))
        lines.append(row('DOSAGE        :', f"{float(self.data.get('dosage', 0)):.6f}", 'QTY REQUIRED  :',
                         f"{float(self.data.get('qty_required', 0)):.6f}"))
        lines.append(row('CUSTOMER      :', self.data.get('customer', '')[:20], 'QTY PER BATCH :',
                         f"{float(self.data.get('qty_per_batch', 0)):.6f}"))
        lines.append(row('LOT NO.       :', self.data.get('lot_number', ''), 'QTY TO PRODUCE:',
                         f"{float(self.data.get('qty_produced', 0)):.6f}"))
        lines.append("")
        lines.append(BOLD_ON + self.batch_text().center(width).upper() + BOLD_OFF + "\n")

        lines.append("-" * width)
        lines.append(f"{'MATERIAL CODE':<20} {'LARGE SCALE (Kg.)':>18} {'SMALL SCALE (grm.)':>19} {'WEIGHT (Kg.)':>18}")
        lines.append("-" * width)
        for m in self.mats:
            lines.append(
                f"{str(m['material_code']):<20} {float(m['large_scale']):18.7f} {float(m['small_scale']):19.7f} {float(m['total_weight']):18.7f}")
        lines.append("-" * width)
        lines.append(
            f"NOTE: {self.batch_text():<40} TOTAL: {BOLD_ON}{float(self.data.get('qty_produced', 0)):>18.6f}{BOLD_OFF}\n\n")

        lines.append(f"{'PREPARED BY: ' + self.data.get('prepared_by', ''):<40} APPROVED BY    : ____________________")
        lines.append(
            f"{'PRINTED ON : ' + datetime.now().strftime('%m/%d/%y %I:%M:%S %p'):<40} MAT'L RELEASED BY: ____________________")
        lines.append(f"{'MBPI-SYSTEM-2017':<40} PROCESSED BY    : ____________________")
        lines.append('\x0c')
        return "\n".join(lines)

    def generate_pdf(self):
        """Creates a high-fidelity PDF preview mimicking the dot-matrix layout."""
        doc = SimpleDocTemplate(self.pdf_buffer, pagesize=letter, leftMargin=30, rightMargin=30, topMargin=30,
                                bottomMargin=30)
        styles = getSampleStyleSheet()
        # Define Courier styles for that 'Printer' look
        styles.add(ParagraphStyle(name='C', fontName='Courier', fontSize=10, leading=12))
        styles.add(ParagraphStyle(name='CB', fontName='Courier-Bold', fontSize=10, leading=12))
        styles.add(ParagraphStyle(name='CB_Center', parent=styles['CB'], alignment=TA_CENTER, fontSize=12))
        styles.add(ParagraphStyle(name='C_Right', parent=styles['C'], alignment=TA_RIGHT))

        story = []

        # --- 1. HEADER SECTION (Left Title vs Right ID Box) ---
        title_part = [
            [Paragraph("MASTERBATCH PHILIPPINES, INC.", styles['CB'])],
            [Paragraph("PRODUCTION ENTRY", styles['C'])],
            [Paragraph("FORM NO. FM00012A1", styles['C'])]
        ]
        title_table = Table(title_part, colWidths=[4 * inch])
        title_table.setStyle(TableStyle([('LEFTPADDING', (0, 0), (-1, -1), 0), ('TOPPADDING', (0, 0), (-1, -1), 1)]))

        id_part = [
            [Paragraph("PRODUCTION ID   :", styles['C']), Paragraph(self.data.get('prod_id', ''), styles['CB'])],
            [Paragraph("PRODUCTION DATE :", styles['C']),
             Paragraph(self.data.get('production_date', ''), styles['CB'])],
            [Paragraph("ORDER FORM NO.  :", styles['C']), Paragraph(self.data.get('order_form_no', ''), styles['CB'])],
            [Paragraph("FORMULATION NO. :", styles['C']), Paragraph(self.data.get('formulation_id', ''), styles['CB'])]
        ]
        id_table = Table(id_part, colWidths=[1.6 * inch, 1.2 * inch])
        id_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 0), (-1, -1), 'Courier'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ]))

        header_outer = Table([[title_table, id_table]], colWidths=[4.2 * inch, 3 * inch])
        header_outer.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 0)]))
        story.append(header_outer)
        story.append(Spacer(1, 15))

        # --- 2. DETAILS SECTION (2-Column Layout) ---
        details_data = [
            [Paragraph("PRODUCT CODE  :", styles['C']), Paragraph(self.data.get('product_code', ''), styles['CB']),
             Paragraph("MIXING TIME   :", styles['C']), Paragraph(self.data.get('mixing_time', ''), styles['CB'])],
            [Paragraph("PRODUCT COLOR :", styles['C']), Paragraph(self.data.get('product_color', ''), styles['CB']),
             Paragraph("MACHINE NO    :", styles['C']), Paragraph(self.data.get('machine_no', ''), styles['CB'])],
            [Paragraph("DOSAGE        :", styles['C']),
             Paragraph(f"{float(self.data.get('dosage', 0)):.6f}", styles['CB']),
             Paragraph("QTY REQUIRED  :", styles['C']),
             Paragraph(f"{float(self.data.get('qty_required', 0)):.6f}", styles['CB'])],
            [Paragraph("CUSTOMER      :", styles['C']), Paragraph(self.data.get('customer', ''), styles['CB']),
             Paragraph("QTY PER BATCH :", styles['C']),
             Paragraph(f"{float(self.data.get('qty_per_batch', 0)):.6f}", styles['CB'])],
            [Paragraph("LOT NO.       :", styles['C']), Paragraph(self.data.get('lot_number', ''), styles['CB']),
             Paragraph("QTY TO PRODUCE:", styles['C']),
             Paragraph(f"{float(self.data.get('qty_produced', 0)):.6f}", styles['CB'])]
        ]
        det_table = Table(details_data, colWidths=[1.4 * inch, 2.2 * inch, 1.4 * inch, 2.2 * inch])
        det_table.setStyle(TableStyle([('LEFTPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 2)]))
        story.append(det_table)
        story.append(Spacer(1, 15))

        # --- 3. BATCH SUMMARY ---
        story.append(Paragraph(self.batch_text().upper(), styles['CB_Center']))
        story.append(Spacer(1, 10))

        # --- 4. MATERIALS TABLE ---
        mat_header = ["MATERIAL CODE", "LARGE SCALE (Kg.)", "SMALL SCALE (grm.)", "WEIGHT (Kg.)"]
        mat_rows = [mat_header]
        for m in self.mats:
            mat_rows.append([
                m['material_code'],
                f"{float(m['large_scale']):.7f}",
                f"{float(m['small_scale']):.7f}",
                f"{float(m['total_weight']):.7f}"
            ])

        m_table = Table(mat_rows, colWidths=[2.2 * inch, 1.8 * inch, 1.8 * inch, 1.6 * inch])
        m_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Courier'),
            ('LINEABOVE', (0, 0), (-1, 0), 1, colors.black),
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
            ('LINEBELOW', (0, -1), (-1, -1), 1, colors.black),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(m_table)

        # Total Row
        total_tbl = Table([[Paragraph(f"NOTE: {self.batch_text()}", styles['C']), "TOTAL:",
                            Paragraph(f"{float(self.data.get('qty_produced', 0)):.6f}", styles['CB'])]],
                          colWidths=[4.8 * inch, 1 * inch, 1.6 * inch])
        total_tbl.setStyle(TableStyle([('ALIGN', (1, 0), (1, 0), 'RIGHT'), ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
                                       ('LEFTPADDING', (0, 0), (-1, -1), 0)]))
        story.append(total_tbl)
        story.append(Spacer(1, 40))

        # --- 5. FOOTER / SIGNATURES ---
        sig_data = [
            [f"PREPARED BY: {self.data.get('prepared_by', '')}", "APPROVED BY       : ____________________"],
            [f"PRINTED ON : {datetime.now().strftime('%m/%d/%y %I:%M:%S %p')}",
             "MAT'L RELEASED BY : ____________________"],
            ["MBPI-SYSTEM-2017", "PROCESSED BY      : ____________________"]
        ]
        sig_table = Table(sig_data, colWidths=[3.8 * inch, 3.6 * inch])
        sig_table.setStyle(
            TableStyle([('FONTNAME', (0, 0), (-1, -1), 'Courier'), ('LEFTPADDING', (0, 0), (-1, -1), 0)]))
        story.append(sig_table)

        doc.build(story)

    def print_report(self):
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dialog = QPrintDialog(printer, self)
        if dialog.exec():
            try:
                printer_name = printer.printerName()
                raw_text = self.generate_raw_text()
                hPrinter = win32print.OpenPrinter(printer_name)
                try:
                    hJob = win32print.StartDocPrinter(hPrinter, 1, ("Production Report", None, "RAW"))
                    win32print.StartPagePrinter(hPrinter)
                    win32print.WritePrinter(hPrinter, raw_text.encode('ascii', 'ignore'))
                    win32print.EndPagePrinter(hPrinter)
                    win32print.EndDocPrinter(hPrinter)
                finally:
                    win32print.ClosePrinter(hPrinter)
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def on_zoom_changed(self, text):
        val = int(text.replace("%", "")) / 100.0
        self.pdf_view.setZoomFactor(val)

    def batch_text(self):
        req = float(self.data.get('qty_required', 0))
        per = float(self.data.get('qty_per_batch', 0))
        n = 1 if per == 0 else int(req / per)
        label = "batch" if n == 1 else "batches"
        return f"{n} {label} by {per:.3f} KG."


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    # SAMPLE DATA REPLICATING YOUR IMAGE
    img_data = {
        "prod_id": "100502", "production_date": "03/02/26", "order_form_no": "42441", "formulation_id": "16534",
        "product_code": "BA4756E", "product_color": "BLUE", "dosage": 100.0,
        "customer": "EVERGOOD PLASTIC INDUSTRY INC.",
        "lot_number": "8755AN", "mixing_time": "3 MINS.", "machine_no": "2", "qty_required": 37.4,
        "qty_per_batch": 37.4,
        "qty_produced": 37.4, "prepared_by": "R. MAGSALIN"
    }
    img_mats = [
        {"material_code": "W35", "large_scale": 1.65, "small_scale": 0, "total_weight": 1.65},
        {"material_code": "B106", "large_scale": 2.25, "small_scale": 0, "total_weight": 0.60},
        {"material_code": "B112", "large_scale": 2.62, "small_scale": 5.0, "total_weight": 0.375},
        {"material_code": "V42", "large_scale": 2.68, "small_scale": 0, "total_weight": 0.06},
        {"material_code": "V49", "large_scale": 2.74, "small_scale": 0, "total_weight": 0.06},
        {"material_code": "L37", "large_scale": 3.49, "small_scale": 0, "total_weight": 0.75},
        {"material_code": "L28", "large_scale": 4.24, "small_scale": 0, "total_weight": 0.75},
        {"material_code": "K907", "large_scale": 16.24, "small_scale": 5.0, "total_weight": 12.005},
        {"material_code": "LL6", "large_scale": 8.75, "small_scale": 0, "total_weight": 8.75},
        {"material_code": "FG-6551AN", "large_scale": 12.4, "small_scale": 0, "total_weight": 12.4},
    ]

    dialog = ProductionPrintPreview(img_data, img_mats)
    dialog.show()
    sys.exit(app.exec())