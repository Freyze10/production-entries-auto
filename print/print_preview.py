import win32print
import qtawesome as fa
import math
from datetime import datetime
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QTextBlockFormat, QTextCursor
from PyQt6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout,
                             QComboBox, QTextEdit, QPushButton, QLabel,
                             QMessageBox, QWidget, QScrollArea)


class ProductionPrintPreview(QDialog):
    printed = pyqtSignal(str)

    def __init__(self, production_data: dict, materials_data: list, wip_no=False, parent=None):
        super().__init__(parent)
        self.data = production_data or {}
        self.mats = materials_data or []
        self.wip_no = wip_no
        self.default_font_size = 10

        self.setWindowTitle("Industrial Sharp Preview - Epson LX-310")
        self.resize(1100, 950)
        self.setStyleSheet("background:#525659;")

        self.setup_ui()
        self.refresh_preview()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        toolbar = QWidget()
        toolbar.setFixedHeight(60)
        toolbar.setStyleSheet("background:#f8f9fa; border-bottom: 1px solid #ddd; padding: 5px;")
        tb_layout = QHBoxLayout(toolbar)

        self.printer_combo = QComboBox()
        self.load_printers()
        tb_layout.addWidget(QLabel("<b>PRINTER:</b>"))
        tb_layout.addWidget(self.printer_combo, 1)

        tb_layout.addStretch()
        self.btn_print = QPushButton(" START PRINTING ")
        self.btn_print.setIcon(fa.icon('fa5s.print', color='white'))
        self.btn_print.setStyleSheet(
            "background:#28a745; color:white; padding:10px 20px; font-weight:bold; border-radius:4px;")
        self.btn_print.clicked.connect(self.print_report)
        tb_layout.addWidget(self.btn_print)
        main_layout.addWidget(toolbar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll.setStyleSheet("background:#525659; border:none;")

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.setContentsMargins(40, 40, 40, 40)

        self.preview_area = QTextEdit()
        self.preview_area.setReadOnly(True)
        self.preview_area.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.preview_area.setFixedWidth(800)
        self.preview_area.setMinimumHeight(1000)
        self.preview_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.preview_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        font = QFont("Courier New", self.default_font_size)
        font.setFixedPitch(True)
        self.preview_area.setFont(font)
        self.preview_area.setStyleSheet("background-color: white; color: black; border: 1px solid #777; padding: 50px;")

        container_layout.addWidget(self.preview_area)
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def load_printers(self):
        try:
            printers = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
            for p in printers: self.printer_combo.addItem(p[2])
            self.printer_combo.setCurrentText(win32print.GetDefaultPrinter())
        except:
            pass

    def get_line_params(self, index, text, total_count):
        """
        CENTRAL SPACING LOGIC
        Returns (UI_Proportional_Height, Printer_ESC_Dots)
        """
        text = text.upper()
        header_limit = 16 if self.wip_no else 13
        material_row = True if self.wip_no else False
        sig_start = total_count - 6

        if material_row:
            if 23 <= index <= 25:
                return 90.0, 28
        else:
            if 20 <= index <= 22:
                return 90.0, 28
        if index <= header_limit:
            return 50.0, 15
        elif "BATCH BY" in text:
            return 160.0, 48
        elif index >= sig_start:
            return 80.0, 22  # Footer is now consistently tighter
        else:
            return 135.0, 40

    def build_report_map(self, mode="screen"):
        if mode == "screen":
            H, V, TL, TR, BL, BR = "─", "│", "┌", "┐", "└", "┘"
            B_ON, B_OFF = "<b>", "</b>"
            S_ON, S_OFF = '<span style="font-size: 18px; font-weight: bold;">', '</span>'
        else:
            # Using standard ASCII for high-speed dot matrix stability
            H, V, TL, TR, BL, BR = "-", "|", "+", "+", "+", "+"
            ESC = '\x1b'
            B_ON, B_OFF = ESC + 'E', ESC + 'F'
            S_ON, S_OFF = ESC + 'W' + '\x01' + ESC + 'E', ESC + 'F' + ESC + 'W' + '\x00'

        WIDTH, BOX_W = 80, 34
        LEFT_W = WIDTH - BOX_W
        lines = []

        def box_ln(label, val):
            return f"{V} {label[:15]:<15} : {str(val)[:12]:<12} {V}"

        # --- 1. HEADER ---
        f_no = f"FORM NO. {self.data.get('form_no', 'FM00012A1')}"
        lines.append(f"{'':<{LEFT_W}}{TL}{H * (BOX_W - 2)}{TR}")
        lines.append(f"{' ':<{LEFT_W}}{V}{' ' * (BOX_W - 2)}{V}")
        lines.append(f"{'':<{LEFT_W}}{box_ln('PRODUCTION ID', self.data.get('prod_id', ''))}")
        lines.append(f"{'':<{LEFT_W}}{V}{' ' * (BOX_W - 2)}{V}")
        lines.append(f"{'MASTERBATCH PHILIPPINES, INC.':<{LEFT_W}}{V}{' ' * (BOX_W - 2)}{V}")
        lines.append(f"{' ':<{LEFT_W}}{box_ln('PRODUCTION DATE', self.data.get('production_date', ''))}")
        lines.append(f"{' ':<{LEFT_W}}{V}{' ' * (BOX_W - 2)}{V}")
        lines.append(f"{'PRODUCTION ENTRY':<{LEFT_W}}{V}{' ' * (BOX_W - 2)}{V}")
        lines.append(f"{' ':<{LEFT_W}}{box_ln('ORDER FORM NO.', self.data.get('order_form_no', ''))}")
        lines.append(f"{f_no:<{LEFT_W}}{V}{' ' * (BOX_W - 2)}{V}")
        lines.append(f"{' ':<{LEFT_W}}{V}{' ' * (BOX_W - 2)}{V}")
        lines.append(f"{' ':<{LEFT_W}}{box_ln('FORMULATION NO.', self.data.get('formulation_id', ''))}")
        lines.append(f"{' ':<{LEFT_W}}{V}{' ' * (BOX_W - 2)}{V}")

        if self.wip_no:
            lines.append(f"{' ':<{LEFT_W}}{V}{' ' * (BOX_W - 2)}{V}")
            lines.append(f"{' ':<{LEFT_W}}{box_ln('WIP', self.data.get('wip_no', ''))}")
            lines.append(f"{' ':<{LEFT_W}}{V}{' ' * (BOX_W - 2)}{V}")

        lines.append(f"{' ':<{LEFT_W}}{BL}{H * (BOX_W - 2)}{BR}")
        lines.append(" ")

        # --- 2. DETAILS ---
        c1, c2 = 14, 34

        def det_row(k1, v1, k2, v2):
            return f"{k1:<{c1}} {B_ON}{str(v1)[:34]:<{c2}}{B_OFF} {k2:<{c1}} {B_ON}{str(v2)[:20]:<{c1}}{B_OFF}"

        lines.append(det_row('PRODUCT CODE :', self.data.get('product_code', ''), 'MIXING TIME   :',
                             self.data.get('mixing_time', '')))
        lines.append(det_row('PRODUCT COLOR:', self.data.get('product_color', ''), 'MACHINE NO    :',
                             self.data.get('machine_no', '')))
        lines.append(det_row('DOSAGE       :', self.data.get('dosage', ''), 'QTY REQUIRED  :',
                             self.data.get('qty_required', '')))
        cust = str(self.data.get('customer', ''))
        lines.append(det_row('CUSTOMER     :', cust[:34], 'QTY PER BATCH :', self.data.get('qty_per_batch', '')))
        if len(cust) > 34:
            lines.append(f"{' ':<15}{B_ON}{cust[34:68]:<65}{B_OFF}")
        lines.append(det_row('LOT NO.      :', self.data.get('lot_number', ''), 'QTY TO PRODUCE:',
                             self.data.get('qty_produced', '')))

        summary = self.batch_text()
        if mode == "screen":
            lines.append(f'<div align="center">{S_ON}{summary.upper()}{S_OFF}</div>')
        else:
            lines.append(S_ON + summary.upper().center(40) + S_OFF)

        # --- 3. MATERIALS TABLE ---
        lines.append(H * WIDTH)
        lines.append(f"{'MATERIAL CODE':<25} {'LARGE SCALE (Kg.)':>18} {'SMALL SCALE (grm.)':>17} {'WEIGHT (Kg.)':>15}")
        lines.append(H * WIDTH)
        for m in self.mats:
            m_c = str(m.get('material_code', ''))
            if not m_c.strip():
                lines.append(" " * WIDTH)  # Empty row for physical split
                continue

            l_v = f"{float(m.get('large_scale', 0)):18.6f}"
            s_v = f"{float(m.get('small_scale', 0)):17.6f}"
            w_v = f"{float(m.get('total_weight', 0)):15.6f}"
            lines.append(f"{B_ON}{m_c[:24]:<25} {l_v} {s_v} {w_v}{B_OFF}")
        lines.append(H * WIDTH)

        # --- 4. TOTAL ---
        prod_total = f"{float(self.data.get('qty_produced', 0)):.6f}"
        lines.append(f"NOTE: {summary[:42]:<44} TOTAL: {B_ON}{prod_total:>18}{B_OFF}")
        lines.append(" ")
        lines.append(" ")

        # --- 5. FOOTER ---
        u = H * 24  # Simplified underline for printer

        def sig_ln(lab_l, val_l, lab_r, val_r):
            return f"{lab_l:<14}{str(val_l)[:22]:<26}{lab_r:<16}{str(val_r)[:24]:^24}"

        lines.append(sig_ln("PREPARED BY :", self.data.get('prepared_by', ''), "APPROVED BY    :",
                            self.data.get('approved_by', '')))
        lines.append(f"{' ':<14}{' ':<26}{' ':<16}{u}")
        lines.append(sig_ln("PRINTED ON  :", datetime.now().strftime('%m/%d/%y %I:%M %p'), "MAT'L RELEASED :", ""))
        lines.append(f"{' ':<14}{' ':<26}{' ':<16}{u}")
        lines.append(f"{'MBPI-SYSTEM-2022':<14}{' ':<24}{'PROCESSED BY   :':<16}{' ':^24}")
        lines.append(f"{' ':<14}{' ':<26}{' ':<16}{u}")

        return lines

    def refresh_preview(self):
        lines = self.build_report_map(mode="screen")
        html_parts = []
        for line in lines:
            if "span style" in line or 'align="center"' in line:
                html_parts.append(line)
            else:
                clean_line = line.replace(" ", "&nbsp;")
                html_parts.append(f'<div style="white-space: nowrap;">{clean_line}</div>')

        self.preview_area.setHtml(
            f"""<div style="font-family: 'Courier New'; color: black;">{"".join(html_parts)}</div>""")

        doc = self.preview_area.document()
        total_blocks = doc.blockCount()
        for i in range(total_blocks):
            block = doc.findBlockByNumber(i)
            ui_height, _ = self.get_line_params(i, block.text(), total_blocks)

            fmt = block.blockFormat()
            fmt.setLineHeight(ui_height, QTextBlockFormat.LineHeightTypes.ProportionalHeight.value)
            cursor = QTextCursor(block)
            cursor.setBlockFormat(fmt)

        self.preview_area.setFixedHeight(max(1100, int(doc.size().height()) + 120))

    def print_report(self):
        self.btn_print.setText(" SENDING... ")
        self.btn_print.setEnabled(False)
        QApplication.processEvents()

        printer_name = self.printer_combo.currentText()
        try:
            lines = self.build_report_map(mode="printer")
            ESC = '\x1b'
            INIT = ESC + '@' + ESC + 't\x01' + ESC + 'x\x01'

            payload = INIT
            total_count = len(lines)

            for i, line in enumerate(lines):
                # Get the hardware dots for this line index
                _, dots = self.get_line_params(i, line, total_count)

                # ESC '3' + chr(n) sets line spacing to n/180 inch
                spacing_cmd = ESC + '3' + chr(dots)
                payload += spacing_cmd + line + "\n"

            # Reset to standard 1/6" spacing and Form Feed
            payload += ESC + '2' + '\x0c'

            hPrinter = win32print.OpenPrinter(printer_name)
            try:
                hJob = win32print.StartDocPrinter(hPrinter, 1, ("Production Entry", None, "RAW"))
                win32print.StartPagePrinter(hPrinter)
                win32print.WritePrinter(hPrinter, payload.encode('latin-1'))
                win32print.EndPagePrinter(hPrinter)
                win32print.EndDocPrinter(hPrinter)
                QMessageBox.information(self, "Success", "Printed Successfully.")
                self.accept()
            finally:
                win32print.ClosePrinter(hPrinter)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Print error: {str(e)}")
        finally:
            self.btn_print.setText(" START PRINTING ")
            self.btn_print.setEnabled(True)

    def batch_text(self):
        try:
            req = float(self.data.get('qty_required', 0))
            per = float(self.data.get('qty_per_batch', 1))
            n = int(req / per) if per > 0 else 1
            return f"{n} batch{'es' if n != 1 else ''} by {per:.3f} KG."
        except:
            return "1 batch by 0.000 KG."


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    # Test Data
    test_data = {"prod_id": "100502", "production_date": "03/02/26", "qty_required": 37.4,
                 "qty_per_batch": 37.4, "product_code": "SAMPLE-PROD", "qty_produced": 37.4, "approved_by": "M. VERDE"}
    test_mats = [{"material_code": "W35", "large_scale": 1.65, "small_scale": 0, "total_weight": 1.65},
                 {"material_code": "SPLIT-ITEM", "large_scale": 25.0, "small_scale": 0, "total_weight": 25.0},
                 {"material_code": "", "large_scale": 0, "small_scale": 0, "total_weight": 0},
                 {"material_code": "SPLIT-ITEM", "large_scale": 10.0, "small_scale": 0, "total_weight": 10.0}]

    ProductionPrintPreview(test_data, test_mats, wip_no=True).exec()