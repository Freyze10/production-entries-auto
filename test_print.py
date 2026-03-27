import win32print
from datetime import datetime
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QComboBox,
                             QTextEdit, QPushButton, QLabel, QMessageBox, QWidget)
import qtawesome as fa


class ProductionPrintPreview(QDialog):
    printed = pyqtSignal(str)

    def __init__(self, production_data: dict, materials_data: list, parent=None):
        super().__init__(parent)
        self.data = production_data or {}
        self.mats = materials_data or []

        self.setWindowTitle("Sharp Text Preview - Epson LX-310")
        self.resize(1000, 900)
        self.setStyleSheet("background:#f0f0f0;")

        self.setup_ui()
        self.refresh_preview()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Toolbar
        toolbar = QWidget()
        toolbar.setStyleSheet("background:#f8f9fa; border-bottom: 1px solid #ddd; padding: 10px;")
        tb_layout = QHBoxLayout(toolbar)

        tb_layout.addWidget(QLabel("<b>PRINTER:</b>"))
        self.printer_combo = QComboBox()
        self.load_printers()
        tb_layout.addWidget(self.printer_combo, 1)

        btn_print = QPushButton(" START PRINTING ")
        btn_print.setIcon(fa.icon('fa5s.print', color='white'))
        btn_print.setStyleSheet(
            "background:#28a745; color:white; padding:10px 20px; font-weight:bold; border:none; border-radius:4px;")
        btn_print.clicked.connect(self.print_report)
        tb_layout.addWidget(btn_print)
        layout.addWidget(toolbar)

        # The Preview Area (Virtual Paper)
        self.preview_area = QTextEdit()
        self.preview_area.setReadOnly(True)
        self.preview_area.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)

        # Fixed-width font is essential for 80-char alignment
        font = QFont("Courier New", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.preview_area.setFont(font)

        self.preview_area.setStyleSheet("""
            background-color: white; 
            color: #333; 
            border: 2px solid #999; 
            padding: 30px;
        """)
        layout.addWidget(self.preview_area)

    def load_printers(self):
        try:
            printers = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
            for p in printers:
                self.printer_combo.addItem(p[2])
            self.printer_combo.setCurrentText(win32print.GetDefaultPrinter())
        except:
            pass

    def build_report_map(self, mode="screen"):
        # Mode-based character selection
        if mode == "screen":
            H, V, TL, TR, BL, BR = "─", "│", "┌", "┐", "└", "┘"
            BOLD_ON, BOLD_OFF = "", ""
        else:
            # PC437 Hardware Codes for the LX-310
            H, V, TL, TR, BL, BR = "\xc4", "\xb3", "\xda", "\xbf", "\xc0", "\xd9"
            ESC = '\x1b'
            BOLD_ON, BOLD_OFF = ESC + 'E', ESC + 'F'

        width = 80  # Total characters for Letter Size
        box_w = 30  # Width of the right-hand ID box
        left_w = width - box_w  # Space for the company name on the left (50 chars)

        lines = []

        # --- COMBINED HEADER & ID BOX SECTION ---
        # Line 1: Company Name + Box Top
        l1_text = f"{BOLD_ON}MASTERBATCH PHILIPPINES, INC.{BOLD_OFF}"
        l1_padding = left_w - len("MASTERBATCH PHILIPPINES, INC.")
        lines.append(f"{l1_text}{' ' * l1_padding}{TL}{H * (box_w - 2)}{TR}")

        # Line 2: Subtitle + Box Content 1
        l2_text = "PRODUCTION ENTRY"
        l2_padding = left_w - len(l2_text)
        content1 = f" PRODUCTION ID   : {self.data.get('prod_id', ''):<8} "
        lines.append(f"{l2_text}{' ' * l2_padding}{V}{content1}{V}")

        # Line 3: Form No + Box Content 2
        l3_text = f"FORM NO. {self.data.get('form_no', 'FM00012A1')}"
        l3_padding = left_w - len(l3_text)
        content2 = f" PRODUCTION DATE : {self.data.get('production_date', ''):<8} "
        lines.append(f"{l3_text}{' ' * l3_padding}{V}{content2}{V}")

        # Line 4: Empty + Box Content 3
        content3 = f" ORDER FORM NO.  : {self.data.get('order_form_no', ''):<8} "
        lines.append(f"{' ' * left_w}{V}{content3}{V}")

        # Line 5: Empty + Box Content 4
        content4 = f" FORMULATION NO. : {self.data.get('formulation_id', ''):<8} "
        lines.append(f"{' ' * left_w}{V}{content4}{V}")

        # Line 6: Empty + Box Bottom
        lines.append(f"{' ' * left_w}{BL}{H * (box_w - 2)}{BR}")
        lines.append("")

        # --- 2-COLUMN DETAILS SECTION ---
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

        # Summary
        summary = self.batch_text()
        lines.append("\n" + BOLD_ON + summary.center(width).upper() + BOLD_OFF + "\n")

        # --- EXPANDED TABLE SECTION (Full 80 Chars) ---
        lines.append(H * width)
        # Column Layout: 25 | 18 | 19 | 18 = 80 total
        lines.append(f"{'MATERIAL CODE':<25} {'LARGE SCALE (Kg.)':>18} {'SMALL SCALE (grm.)':>19} {'WEIGHT (Kg.)':>18}")
        lines.append(H * width)

        for m in self.mats:
            code = str(m.get('material_code', ''))[:24]
            l_val = f"{float(m.get('large_scale', 0)):.7f}"
            s_val = f"{float(m.get('small_scale', 0)):.7f}"
            w_val = f"{float(m.get('total_weight', 0)):.7f}"
            lines.append(f"{code:<25} {l_val:>18} {s_val:>19} {w_val:>18}")

        lines.append(H * width)
        total = f"{float(self.data.get('qty_produced', 0)):.6f}"
        lines.append(f"NOTE: {summary:<44} TOTAL: {BOLD_ON}{total:>18}{BOLD_OFF}\n\n")

        # Footers
        u = "_" * 25
        lines.append(f"{'PREPARED BY: ' + self.data.get('prepared_by', ''):<42} APPROVED BY       : {u}")
        lines.append(
            f"{'PRINTED ON : ' + datetime.now().strftime('%m/%d/%y %I:%M:%S %p'):<42} MAT'L RELEASED BY  : {u}")
        lines.append(f"{'MBPI-SYSTEM-2017':<42} PROCESSED BY      : {u}")

        return "\n".join(lines)

    def refresh_preview(self):
        self.preview_area.setPlainText(self.build_report_map(mode="screen"))

    def print_report(self):
        printer_name = self.printer_combo.currentText()
        try:
            raw_text = self.build_report_map(mode="printer")
            ESC = '\x1b'
            # Reset + PC437 + NLQ Mode
            init_printer = ESC + '@' + ESC + 't\x01' + ESC + 'x\x01'
            full_payload = init_printer + raw_text + '\x0c'  # Add Page Eject

            hPrinter = win32print.OpenPrinter(printer_name)
            try:
                hJob = win32print.StartDocPrinter(hPrinter, 1, ("Production Report", None, "RAW"))
                win32print.StartPagePrinter(hPrinter)
                # latin-1 allows the high-ASCII box characters to pass through correctly
                win32print.WritePrinter(hPrinter, full_payload.encode('latin-1'))
                win32print.EndPagePrinter(hPrinter)
                win32print.EndDocPrinter(hPrinter)
                QMessageBox.information(self, "Success", "Printed Successfully!")
                self.accept()
            finally:
                win32print.ClosePrinter(hPrinter)
        except Exception as e:
            QMessageBox.critical(self, "Printing Error", str(e))

    def batch_text(self):
        req = float(self.data.get('qty_required', 0))
        per = float(self.data.get('qty_per_batch', 0))
        n = 1 if per == 0 else int(req / per)
        return f"{n} batch{'es' if n > 1 else ''} by {per:.3f} KG."


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    img_data = {
        "prod_id": "100502", "production_date": "03/02/26", "order_form_no": "42441", "formulation_id": "16534",
        "product_code": "BA4756E", "product_color": "BLUE", "dosage": 100.0, "customer": "EVERGOOD PLASTIC",
        "lot_number": "8755AN", "mixing_time": "3 MINS.", "machine_no": "2", "qty_required": 37.4,
        "qty_per_batch": 37.4,
        "qty_produced": 37.4, "prepared_by": "R. MAGSALIN"
    }
    img_mats = [
        {"material_code": "W35", "large_scale": 1.65, "small_scale": 0, "total_weight": 1.65},
        {"material_code": "FG-6551AN", "large_scale": 12.4, "small_scale": 0, "total_weight": 12.4}
    ]

    dialog = ProductionPrintPreview(img_data, img_mats)
    dialog.show()
    sys.exit(app.exec())