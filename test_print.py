import win32print
from datetime import datetime
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QComboBox,
                             QTextEdit, QPushButton, QLabel, QMessageBox)
import qtawesome as fa


class ProductionPrintPreview(QDialog):
    printed = pyqtSignal(str)

    def __init__(self, production_data: dict, materials_data: list, parent=None):
        super().__init__(parent)
        self.data = production_data or {}
        self.mats = materials_data or []

        self.setWindowTitle("Sharp Text Preview - Epson LX-310")
        self.resize(900, 850)
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

        # Fixed-width font is essential for alignment
        font = QFont("Courier New", 11)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.preview_area.setFont(font)

        # Styling the preview to look like a dot-matrix sheet
        self.preview_area.setStyleSheet("""
            background-color: white; 
            color: #333; 
            border: 2px solid #999; 
            padding: 40px;
            font-weight: bold;
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
        """
        The 'Source of Truth' for the report.
        mode='screen' returns Unicode for the UI.
        mode='printer' returns HEX bytes for the LX-310.
        """
        # Define characters based on mode
        if mode == "screen":
            H, V, TL, TR, BL, BR = "─", "│", "┌", "┐", "└", "┘"
            BOLD_ON, BOLD_OFF = "", ""  # HTML/RichText handles bold differently if needed
        else:
            # PC437 Hardware Codes for solid lines
            H, V, TL, TR, BL, BR = "\xc4", "\xb3", "\xda", "\xbf", "\xc0", "\xd9"
            ESC = '\x1b'
            BOLD_ON, BOLD_OFF = ESC + 'E', ESC + 'F'

        width = 80
        lines = []

        # Header
        lines.append(f"{BOLD_ON}MASTERBATCH PHILIPPINES, INC.{BOLD_OFF}")
        lines.append("PRODUCTION ENTRY")

        # Top Box
        box_w = 28
        top_border = TL + (H * box_w) + TR
        bot_border = BL + (H * box_w) + BR

        f_no = f"FORM NO. {self.data.get('form_no', 'FM00012A1'):<28}"
        lines.append(f"{f_no}{top_border}")

        def box_row(label, val):
            content = f" {label:<16} : {val:<8} "
            return f"{'':<37}{V}{content}{V}"

        lines.append(box_row("PRODUCTION ID", self.data.get('prod_id', '')))
        lines.append(box_row("PRODUCTION DATE", self.data.get('production_date', '')))
        lines.append(box_row("ORDER FORM NO.", self.data.get('order_form_no', '')))
        lines.append(box_row("FORMULATION NO.", self.data.get('formulation_id', '')))
        lines.append(f"{'':<37}{bot_border}")
        lines.append("")

        # 2-Column Info
        c1, c2 = 16, 22

        def l(k1, v1, k2, v2):
            return f"{k1:<{c1}} {BOLD_ON}{v1:<{c2}}{BOLD_OFF} {k2:<{c1}} {BOLD_ON}{v2}{BOLD_OFF}"

        lines.append(l('PRODUCT CODE  :', self.data.get('product_code', ''), 'MIXING TIME   :',
                       self.data.get('mixing_time', '')))
        lines.append(l('PRODUCT COLOR :', self.data.get('product_color', ''), 'MACHINE NO    :',
                       self.data.get('machine_no', '')))
        lines.append(l('DOSAGE        :', f"{float(self.data.get('dosage', 0)):.6f}", 'QTY REQUIRED  :',
                       f"{float(self.data.get('qty_required', 0)):.6f}"))
        lines.append(l('CUSTOMER      :', self.data.get('customer', '')[:20], 'QTY PER BATCH :',
                       f"{float(self.data.get('qty_per_batch', 0)):.6f}"))
        lines.append(l('LOT NO.       :', self.data.get('lot_number', ''), 'QTY TO PRODUCE:',
                       f"{float(self.data.get('qty_produced', 0)):.6f}"))

        # Center Summary
        summary = self.batch_text()
        lines.append("\n" + BOLD_ON + summary.center(width).upper() + BOLD_OFF + "\n")

        # Table Section
        lines.append(H * width)
        lines.append(f"{'MATERIAL CODE':<20} {'LARGE SCALE (Kg.)':>18} {'SMALL SCALE (grm.)':>19} {'WEIGHT (Kg.)':>18}")
        lines.append(H * width)

        for m in self.mats:
            code = str(m.get('material_code', ''))[:20]
            l_val = f"{float(m.get('large_scale', 0)):.7f}"
            s_val = f"{float(m.get('small_scale', 0)):.7f}"
            w_val = f"{float(m.get('total_weight', 0)):.7f}"
            lines.append(f"{code:<20} {l_val:>18} {s_val:>19} {w_val:>18}")

        lines.append(H * width)
        total = f"{float(self.data.get('qty_produced', 0)):.6f}"
        lines.append(f"NOTE: {summary:<40} TOTAL: {BOLD_ON}{total:>18}{BOLD_OFF}\n\n")

        # Footers
        u = "_" * 20
        lines.append(f"{'PREPARED BY: ' + self.data.get('prepared_by', ''):<40} APPROVED BY    : {u}")
        lines.append(f"{'PRINTED ON : ' + datetime.now().strftime('%m/%d/%y %I:%M:%S %p'):<40} MAT'L RELEASED BY: {u}")
        lines.append(f"{'MBPI-SYSTEM-2017':<40} PROCESSED BY    : {u}")

        return "\n".join(lines)

    def refresh_preview(self):
        screen_text = self.build_report_map(mode="screen")
        self.preview_area.setPlainText(screen_text)

    def print_report(self):
        printer_name = self.printer_combo.currentText()
        try:
            # 1. Generate the RAW Bytes with hardware codes
            raw_text = self.build_report_map(mode="printer")

            # 2. Add ESC/P Initialization codes
            ESC = '\x1b'
            # Reset + Select PC437 + Set NLQ (High Quality) mode
            init_printer = ESC + '@' + ESC + 't\x01' + ESC + 'x\x01'
            eject_page = '\x0c'

            full_payload = init_printer + raw_text + eject_page

            # 3. Spool to printer
            hPrinter = win32print.OpenPrinter(printer_name)
            try:
                hJob = win32print.StartDocPrinter(hPrinter, 1, ("Production Report", None, "RAW"))
                win32print.StartPagePrinter(hPrinter)
                # We use latin-1 because it maps 1:1 with the HEX codes \xda, \xc4, etc.
                win32print.WritePrinter(hPrinter, full_payload.encode('latin-1'))
                win32print.EndPagePrinter(hPrinter)
                win32print.EndDocPrinter(hPrinter)
                QMessageBox.information(self, "Success", "Report printed perfectly!")
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


# --- TEST ---
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication, QWidget

    app = QApplication(sys.argv)

    img_data = {
        "prod_id": "100502", "production_date": "03/02/26", "order_form_no": "42441", "formulation_id": "16534",
        "product_code": "BA4756E", "product_color": "BLUE", "dosage": 100.0, "customer": "EVERGOOD PLASTIC",
        "lot_number": "8755AN", "mixing_time": "3 MINS.", "machine_no": "2", "qty_required": 37.4,
        "qty_per_batch": 37.4,
        "qty_produced": 37.4, "prepared_by": "R. MAGSALIN"
    }
    img_mats = [{"material_code": "W35", "large_scale": 1.65, "small_scale": 0, "total_weight": 1.65},
                {"material_code": "B106", "large_scale": 2.25, "small_scale": 0, "total_weight": 0.60}]

    dialog = ProductionPrintPreview(img_data, img_mats)
    dialog.show()
    sys.exit(app.exec())