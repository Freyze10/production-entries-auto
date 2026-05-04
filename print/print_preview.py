import win32print
import qtawesome as fa
from datetime import datetime
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QTextBlockFormat, QTextCursor
from PyQt6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout,
                             QComboBox, QTextEdit, QPushButton, QLabel,
                             QMessageBox, QWidget, QScrollArea)

from db.update import print_production
from db.write import log_audit_trail


class ProductionPrintPreview(QDialog):
    printed = pyqtSignal(str)

    def __init__(self, production_data: dict, materials_data: list, wip_no=False, parent=None, audit=None,
                 role="Editor"):
        super().__init__(parent)
        self.data = production_data or {}
        self.mats = materials_data or []
        self.wip_no = wip_no
        self.audit = audit
        self.user_role = role
        # INCREASED FONT SIZE BY 1
        self.default_font_size = 11

        self.setWindowTitle("Print Preview")
        self.resize(1100, 950)
        self.setStyleSheet("background:#525659;")

        self.setup_ui()
        self.refresh_preview()

        if str(self.user_role).upper() == "VIEWER":
            self.btn_print.setEnabled(False)
            self.btn_print.setObjectName("disabled_btn")

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
        self.preview_area.setFixedWidth(850)  # Widened slightly for font 11
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

    def build_report_map(self, mode="screen"):
        if mode == "screen":
            H, V, TL, TR, BL, BR = "─", "│", "┌", "┐", "└", "┘"
            B_ON, B_OFF = "<b>", "</b>"
            S_ON, S_OFF = '<span style="font-size: 18px; font-weight: bold;">', '</span>'
        else:
            H, V, TL, TR, BL, BR = "\xc4", "\xb3", "\xda", "\xbf", "\xc0", "\xd9"
            ESC = '\x1b'
            B_ON, B_OFF = ESC + 'E', ESC + 'F'
            # Select 10 CPI (Pica) for slightly larger characters
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
        lines.append(f"{'PRODUCTION ENTRY':<{LEFT_W}}{V}{' ' * (BOX_W - 2)}{V}")
        lines.append(f"{' ':<{LEFT_W}}{V}{' ' * (BOX_W - 2)}{V}")
        lines.append(f"{f_no:<{LEFT_W}}{box_ln('ORDER FORM NO.', self.data.get('order_form_no', ''))}")
        lines.append(f"{' ':<{LEFT_W}}{V}{' ' * (BOX_W - 2)}{V}")
        lines.append(f"{' ':<{LEFT_W}}{V}{' ' * (BOX_W - 2)}{V}")
        lines.append(f"{' ':<{LEFT_W}}{box_ln('FORMULATION NO.', self.data.get('formulation_id', ''))}")
        lines.append(f"{' ':<{LEFT_W}}{V}{' ' * (BOX_W - 2)}{V}")

        if self.wip_no is True:
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
        if len(cust) > 34:
            display_cust = cust[:31] + "..."
        else:
            display_cust = cust
        lines.append(det_row('CUSTOMER     :', display_cust, 'QTY PER BATCH :', self.data.get('qty_per_batch', '')))
        lines.append(det_row('LOT NO.      :', self.data.get('lot_number', ''), 'QTY TO PRODUCE:',
                             self.data.get('qty_produced', '')))
        lines.append(" ")
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
                lines.append(" " * WIDTH)
                continue
            l_v = f"{float(m.get('large_scale', 0)):18.6f}"
            s_v = f"{float(m.get('small_scale', 0)):17.6f}"
            w_v = f"{float(m.get('total_weight', 0)):15.6f}"
            lines.append(f"{B_ON}{m_c[:24]:<25} {l_v} {s_v} {w_v}{B_OFF}")
        lines.append(H * WIDTH)

        # --- 4. TOTAL & GAPS ---
        prod_total = f"{float(self.data.get('qty_produced', 0)):.6f}"
        lines.append(f"NOTE: {summary[:42]:<44} TOTAL: {B_ON}{prod_total:>18}{B_OFF}")
        lines.append(" ");
        lines.append(" ");
        lines.append(" ")

        # --- 5. FOOTER / SIGNATURES ---
        u = H * 24

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
            fmt = block.blockFormat()
            text = block.text().upper()

            if self.wip_no is True:
                if i <= 15:
                    line_h = 50.0
                elif 23 <= i <= 26:
                    line_h = 90
                elif i >= (total_blocks - 6):
                    line_h = 80.0
                elif "BATCH BY" in text:
                    line_h = 160.0
                else:
                    line_h = 145.0
            else:
                if i <= 13:
                    line_h = 50.0
                elif 20 <= i <= 23:
                    line_h = 90
                elif i >= (total_blocks - 6):
                    line_h = 80.0
                elif "BATCH BY" in text:
                    line_h = 160.0
                else:
                    line_h = 145.0

            fmt.setLineHeight(line_h, QTextBlockFormat.LineHeightTypes.ProportionalHeight.value)
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

            # --- HARDWARE INITIALIZATION ---
            init = (ESC + '@' +  # Reset
                    ESC + 'x\x00' +  # Draft Mode (Fast)
                    ESC + 'P' +  # 10 CPI (Largest characters)
                    ESC + 'U\x00')  # Bidirectional

            # --- INCREASED SPACING DOTS (1/180 inch units) ---
            DOTS_HEADER = chr(20)  # Was 15
            DOTS_BODY = chr(54)  # Was 44
            DOTS_SUMM = chr(64)  # Was 48
            DOTS_FOOTER = chr(30)  # Was 24

            header_end = 16 if self.wip_no is True else 14
            footer_start = len(lines) - 6

            payload = init
            for i, line in enumerate(lines):
                # Set dynamic spacing based on current line zone
                if i == 0:
                    payload += ESC + '3' + DOTS_HEADER
                elif i == header_end:
                    payload += ESC + '3' + DOTS_BODY
                elif "BATCH BY" in line.upper():
                    payload += ESC + '3' + DOTS_SUMM
                elif i == header_end + 6:  # Return to body after summary
                    payload += ESC + '3' + DOTS_BODY
                elif i == header_end + 8:  # for the material row header
                    payload += ESC + '3' + chr(44)
                elif i == footer_start:
                    payload += ESC + '3' + DOTS_FOOTER

                payload += line + "\n"

            payload += '\x0c'  # Form Feed

            hPrinter = win32print.OpenPrinter(printer_name)
            try:
                hJob = win32print.StartDocPrinter(hPrinter, 1, ("Production Entry", None, "RAW"))
                win32print.StartPagePrinter(hPrinter)
                win32print.WritePrinter(hPrinter, payload.encode('latin-1'))
                win32print.EndPagePrinter(hPrinter)
                win32print.EndDocPrinter(hPrinter)

                QMessageBox.information(self, "Success", "Printed Successfully.")
                log_audit_trail(self.audit['mac'], self.audit['action'], self.audit['details'])
                print_production(self.data.get('prod_id'))
                self.accept()
            finally:
                win32print.ClosePrinter(hPrinter)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        finally:
            self.btn_print.setText(" START PRINTING ")
            self.btn_print.setEnabled(True)

    def batch_text(self):
        try:
            req, per = float(self.data.get('qty_required', 0)), float(self.data.get('qty_per_batch', 1))
            n = int(req / per) if per > 0 else 1
            return f"{n} batch{'es' if n != 1 else ''} by {per:.3f} KG."
        except:
            return "1 batch by 0.000 KG."