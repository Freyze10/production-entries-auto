import win32print
from datetime import datetime
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor, QTextBlockFormat, QTextCursor
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QComboBox,
                             QTextEdit, QPushButton, QLabel, QMessageBox,
                             QWidget, QScrollArea, QFrame)
import qtawesome as fa

import win32print
from datetime import datetime
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor, QTextBlockFormat
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QComboBox,
                             QTextEdit, QPushButton, QLabel, QMessageBox,
                             QWidget, QScrollArea)
import qtawesome as fa


class ProductionPrintPreview(QDialog):
    printed = pyqtSignal(str)

    def __init__(self, production_data: dict, materials_data: list, parent=None):
        super().__init__(parent)
        self.data = production_data or {}
        self.mats = materials_data or []
        self.default_font_size = 10

        self.setWindowTitle("Industrial Sharp Preview - Epson LX-310")
        self.resize(1100, 950)
        self.setStyleSheet("background:#525659;")

        self.setup_ui()
        self.refresh_preview()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # --- Toolbar ---
        toolbar = QWidget()
        toolbar.setFixedHeight(60)
        toolbar.setStyleSheet("background:#f8f9fa; border-bottom: 1px solid #ddd; padding: 5px;")
        tb_layout = QHBoxLayout(toolbar)

        self.printer_combo = QComboBox()
        self.load_printers()
        tb_layout.addWidget(QLabel("<b>PRINTER:</b>"))
        tb_layout.addWidget(self.printer_combo, 1)

        tb_layout.addStretch()
        btn_print = QPushButton(" START PRINTING ")
        btn_print.setIcon(fa.icon('fa5s.print', color='white'))
        btn_print.setStyleSheet(
            "background:#28a745; color:white; padding:10px 20px; font-weight:bold; border-radius:4px;")
        btn_print.clicked.connect(self.print_report)
        tb_layout.addWidget(btn_print)
        main_layout.addWidget(toolbar)

        # --- Scroll Area ---
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
        self.preview_area.setMinimumHeight(1100)

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

    def build_report_map(self, mode="screen"):
        # 1. Define characters and Hardware Codes
        if mode == "screen":
            H, V, TL, TR, BL, BR = "─", "│", "┌", "┐", "└", "┘"
            B_ON, B_OFF = "<b>", "</b>"
            S_ON = '<span style="font-size: 18px; font-weight: bold;">'
            S_OFF = '</span>'
        else:
            H, V, TL, TR, BL, BR = "\xc4", "\xb3", "\xda", "\xbf", "\xc0", "\xd9"
            ESC = '\x1b'
            B_ON, B_OFF = ESC + 'E', ESC + 'F'
            S_ON = ESC + 'W' + '\x01' + ESC + 'E'
            S_OFF = ESC + 'F' + ESC + 'W' + '\x00'

        WIDTH, BOX_W = 80, 34
        LEFT_W = WIDTH - BOX_W
        lines = []

        # --- BOX HELPERS ---
        def box_ln(label, val):
            return f"{V} {label[:17]:<17} : {str(val)[:10]:<10} {V}"

        def box_spacer():
            return f"{V}{' ' * (BOX_W - 2)}{V}"

        # --- 1. HEADER (LINES 0 to 8) ---
        lines.append(f"{'':<{34}}{TL}{H * (BOX_W - 2)}{TR}")
        lines.append(f"{'MASTERBATCH PHILIPPINES, INC.':<{LEFT_W}}{box_ln('PRODUCTION ID', self.data.get('prod_id', ''))}")
        lines.append(f"{'PRODUCTION ENTRY':<{LEFT_W}}{box_spacer()}")
        f_no = f"FORM NO. {self.data.get('form_no', 'FM00012A1')}"
        lines.append(f"{f_no:<{LEFT_W}}{box_ln('PRODUCTION DATE', self.data.get('production_date', ''))}")
        lines.append(f"{' ':<{LEFT_W}}{box_spacer()}")
        lines.append(f"{' ':<{LEFT_W}}{box_ln('ORDER FORM NO.', self.data.get('order_form_no', ''))}")
        lines.append(f"{' ':<{LEFT_W}}{box_spacer()}")
        lines.append(f"{' ':<{LEFT_W}}{box_ln('FORMULATION NO.', self.data.get('formulation_id', ''))}")
        lines.append(f"{' ':<{LEFT_W}}{BL}{H * (BOX_W - 2)}{BR}")

        # --- 2. PRODUCT DETAILS ---
        lines.append("")  # Line 9: Gap after header

        c1, c2 = 16, 22

        def det_row(k1, v1, k2, v2):
            return f"{k1:<{c1}} {B_ON}{str(v1)[:20]:<{c2}}{B_OFF} {k2:<{c1}} {B_ON}{str(v2)[:20]:<{c2}}{B_OFF}"

        lines.append(det_row('PRODUCT CODE  :', self.data.get('product_code', ''), 'MIXING TIME   :',
                             self.data.get('mixing_time', '')))
        lines.append(det_row('PRODUCT COLOR :', self.data.get('product_color', ''), 'MACHINE NO    :',
                             self.data.get('machine_no', '')))
        lines.append(det_row('DOSAGE        :', self.data.get('dosage', ''), 'QTY REQUIRED  :',
                             self.data.get('qty_required', '')))
        cust = str(self.data.get('customer', ''))
        lines.append(det_row('CUSTOMER      :', cust[:20], 'QTY PER BATCH :', self.data.get('qty_per_batch', '')))
        if len(cust) > 20:
            lines.append(f"{' ':<17}{B_ON}{cust[20:60]:<60}{B_OFF}")
        lines.append(det_row('LOT NO.       :', self.data.get('lot_number', ''), 'QTY TO PRODUCE:',
                             self.data.get('qty_produced', '')))

        # Center Summary
        summary = self.batch_text()
        if mode == "screen":
            # We wrap this in a special div to center it visually in HTML
            lines.append(f'<div align="center">{S_ON}{summary}{S_OFF}</div>')
        else:
            # For the printer, we center it in 40 characters because they are double-width
            lines.append(S_ON + summary.center(40) + S_OFF)

        # --- 3. MATERIALS TABLE ---
        lines.append(H * WIDTH)
        lines.append(f"{'MATERIAL CODE':<25} {'LARGE SCALE (Kg.)':>18} {'SMALL SCALE (grm.)':>19} {'WEIGHT (Kg.)':>18}")
        lines.append(H * WIDTH)

        for m in self.mats:
            m_c = str(m.get('material_code', ''))[:24]

            # 1. Format the numbers to their EXACT column widths FIRST
            # This ensures the spaces are calculated correctly
            l_v_padded = f"{float(m.get('large_scale', 0)):18.6f}"
            s_v_padded = f"{float(m.get('small_scale', 0)):19.6f}"
            w_v_padded = f"{float(m.get('total_weight', 0)):18.6f}"

            # 2. Now wrap the padded strings in Bold.
            # The columns will stay perfectly aligned because the tags have 0 visual width.
            lines.append(
                f"{m_c:<25} "
                f"{B_ON}{l_v_padded}{B_OFF} "
                f"{B_ON}{s_v_padded}{B_OFF} "
                f"{B_ON}{w_v_padded}{B_OFF}"
            )

        lines.append(H * WIDTH)

        # --- 4. TOTAL NOTE ---
        prod_total = f"{float(self.data.get('qty_produced', 0)):.6f}"
        lines.append(f"NOTE: {summary[:42]:<44} TOTAL: {B_ON}{prod_total:>18}{B_OFF}")

        # INSERTING NEW LINES AFTER TOTAL
        lines.append("")  # Blank Line 1
        lines.append("")  # Blank Line 2
        lines.append("")  # Blank Line 3

        # --- 5. FOOTER / SIGNATURES ---
        u = "▔" * 24

        def sig_ln(lab_l, val_l, lab_r, val_r):
            return f"{lab_l:<14}{str(val_l)[:22]:<27}{lab_r:<16}{str(val_r)[:22]:<20}"

        lines.append(sig_ln("PREPARED BY :", self.data.get('prepared_by', ''), "APPROVED BY    :",
                            self.data.get('approved_by', '')))
        lines.append(f"{' ':<14}{' ':<28}{' ':<16}{u}")
        lines.append(sig_ln("PRINTED ON  :", datetime.now().strftime('%m/%d/%y %I:%M %p'), "MAT'L RELEASED :", ""))
        lines.append(f"{' ':<14}{' ':<28}{' ':<16}{u}")
        lines.append(f"{"MBPI-SYSTEM-2022":<14} {'':<23} {"PROCESSED BY   : ":<16}")
        lines.append(f"{' ':<14}{' ':<28}{' ':<16}{u}")

        return "\n".join(lines)

    def refresh_preview(self):
        # 1. Get the map with <b> tags
        raw_content = self.build_report_map(mode="screen")

        # 2. Convert newlines to <br> and wrap in a white-space preserving div
        # 'white-space: pre' is the secret to keeping your 80-character alignment in HTML
        html_content = f"""
        <div style="white-space: pre; font-family: 'Courier New';">
            {raw_content.replace('\n', '<br>')}
        </div>
        """
        self.preview_area.setHtml(html_content)

        # 3. Re-apply the Line Height (setHtml resets formatting, so we do this last)
        doc = self.preview_area.document()
        total_blocks = doc.blockCount()
        header_end = 9
        footer_start = total_blocks - 6

        for i in range(total_blocks):
            block = doc.findBlockByNumber(i)
            fmt = block.blockFormat()

            if i <= header_end:
                line_h = 100.0
            elif i >= footer_start:
                line_h = 70.0
            else:
                line_h = 130.0

            fmt.setLineHeight(line_h, QTextBlockFormat.LineHeightTypes.ProportionalHeight.value)
            cursor = QTextCursor(block)
            cursor.setBlockFormat(fmt)

    def print_report(self):
        printer_name = self.printer_combo.currentText()
        try:
            raw_text = self.build_report_map(mode="printer")
            ESC = '\x1b'

            # Split text into lines to apply hardware spacing at specific points
            lines = raw_text.split('\n')

            # --- HARDWARE SPACING SETTINGS (n/216 inch) ---
            # 24 = Tight (100%), 36 = Standard, 54 = Wide (150%), 40 = Neater (110%)

            # 1. Header Section
            init = ESC + '@' + ESC + 't\x01' + ESC + 'x\x01' + (ESC + '3' + '\x18')
            header = "\n".join(lines[:10])

            # 2. Body Section (Switch to 150%)
            body_init = ESC + '3' + '\x36'
            # Footer is the last 6 lines
            body = "\n".join(lines[10:-6])

            # 3. Footer Section (Switch to 110% / 40 dots)
            footer_init = ESC + '3' + '\x28'  # \x28 is 40 in decimal
            footer = "\n".join(lines[-6:])

            final_payload = init + header + body_init + body + footer_init + footer + '\x0c'

            hPrinter = win32print.OpenPrinter(printer_name)
            try:
                hJob = win32print.StartDocPrinter(hPrinter, 1, ("Production Report", None, "RAW"))
                win32print.StartPagePrinter(hPrinter)
                win32print.WritePrinter(hPrinter, final_payload.encode('latin-1'))
                win32print.EndPagePrinter(hPrinter)
                win32print.EndDocPrinter(hPrinter)
                QMessageBox.information(self, "Success", "Printed Successfully.")
            finally:
                win32print.ClosePrinter(hPrinter)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def batch_text(self):
        req, per = float(self.data.get('qty_required', 0)), float(self.data.get('qty_per_batch', 1))
        n = int(req / per) if per > 0 else 1
        return f"{n} batch{'es' if n != 1 else ''} by {per:.3f} KG."



if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    img_data = {"prod_id": "100502", "production_date": "03/02/26", "qty_required": 37.4, "qty_per_batch": 37.4}
    img_mats = [{"material_code": "W35", "large_scale": 1.65, "small_scale": 0, "total_weight": 1.65}]
    dialog = ProductionPrintPreview(img_data, img_mats)
    dialog.show()
    sys.exit(app.exec())