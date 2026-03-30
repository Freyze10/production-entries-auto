import win32print
import qtawesome as fa
from datetime import datetime
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QTextBlockFormat, QTextCursor
from PyQt6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout,
                             QComboBox, QTextEdit, QPushButton, QLabel,
                             QMessageBox, QWidget, QScrollArea)


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

        toolbar = QWidget()
        toolbar.setFixedHeight(60)
        toolbar.setStyleSheet("background:#f8f9fa; border-bottom:1px solid #ddd; padding:5px;")
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
        self.preview_area.setStyleSheet(
            "background-color:white; color:black; border:1px solid #777; padding:50px;")

        container_layout.addWidget(self.preview_area)
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def load_printers(self):
        try:
            printers = win32print.EnumPrinters(
                win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
            for p in printers:
                self.printer_combo.addItem(p[2])
            self.printer_combo.setCurrentText(win32print.GetDefaultPrinter())
        except:
            pass

    def build_report_map(self, mode="screen"):
        if mode == "screen":
            # Unicode box chars — render correctly in Qt preview
            H, V, TL, TR, BL, BR = "─", "│", "┌", "┐", "└", "┘"
            B_ON,  B_OFF  = "<b>", "</b>"
            S_ON,  S_OFF  = '<span style="font-size:18px; font-weight:bold;">', '</span>'
            U_CHAR = "▔"
        else:
            # ── Hardware bytes for Epson LX-310 ──────────────────────────────
            # These \xNN escapes are Latin-1 codepoints. When the payload is
            # encoded with latin-1 (see print_report), each character maps to
            # its own byte value unchanged:
            #   "\xc4" → U+00C4 → latin-1 encode → 0xC4 → LX-310 draws ─
            #   "\xdf" → U+00DF → latin-1 encode → 0xDF → LX-310 draws ▀
            # This is exactly how the original working version operated.
            H, V, TL, TR, BL, BR = "\xc4", "\xb3", "\xda", "\xbf", "\xc0", "\xd9"
            U_CHAR = "\xdf"          # upper-half block = overline on dot-matrix

            ESC    = '\x1b'
            B_ON,  B_OFF  = ESC + 'E', ESC + 'F'
            S_ON,  S_OFF  = (ESC + 'W\x01' + ESC + 'E',
                             ESC  + 'F'     + ESC + 'W\x00')

        WIDTH, BOX_W = 80, 34
        LEFT_W = WIDTH - BOX_W
        lines  = []

        def box_ln(label, val):
            return f"{V} {label[:17]:<17} : {str(val)[:10]:<10} {V}"

        # --- 1. HEADER ---
        lines.append(f"{'':<{LEFT_W}}{TL}{H * (BOX_W - 2)}{TR}")
        lines.append(
            f"{'MASTERBATCH PHILIPPINES, INC.':<{LEFT_W}}"
            f"{box_ln('PRODUCTION ID', self.data.get('prod_id', ''))}")
        lines.append(f"{'PRODUCTION ENTRY':<{LEFT_W}}{V}{' ' * (BOX_W - 2)}{V}")
        f_no = f"FORM NO. {self.data.get('form_no', 'FM00012A1')}"
        lines.append(
            f"{f_no:<{LEFT_W}}"
            f"{box_ln('PRODUCTION DATE', self.data.get('production_date', ''))}")
        lines.append(f"{' ':<{LEFT_W}}{V}{' ' * (BOX_W - 2)}{V}")
        lines.append(f"{' ':<{LEFT_W}}{box_ln('ORDER FORM NO.',  self.data.get('order_form_no',  ''))}")
        lines.append(f"{' ':<{LEFT_W}}{V}{' ' * (BOX_W - 2)}{V}")
        lines.append(f"{' ':<{LEFT_W}}{box_ln('FORMULATION NO.', self.data.get('formulation_id', ''))}")
        lines.append(f"{' ':<{LEFT_W}}{BL}{H * (BOX_W - 2)}{BR}")
        lines.append("")

        # --- 2. DETAILS ---
        c1, c2 = 14, 34

        def det_row(k1, v1, k2, v2):
            return (f"{k1:<{c1}} {B_ON}{str(v1)[:34]:<{c2}}{B_OFF} "
                    f"{k2:<{c1}} {B_ON}{str(v2)[:20]:<{c1}}{B_OFF}")

        lines.append(det_row('PRODUCT CODE :', self.data.get('product_code',  ''),
                             'MIXING TIME   :', self.data.get('mixing_time',   '')))
        lines.append(det_row('PRODUCT COLOR:', self.data.get('product_color', ''),
                             'MACHINE NO    :', self.data.get('machine_no',    '')))
        lines.append(det_row('DOSAGE       :', self.data.get('dosage',        ''),
                             'QTY REQUIRED  :', self.data.get('qty_required',  '')))
        cust = str(self.data.get('customer', ''))
        lines.append(det_row('CUSTOMER     :', cust[:34],
                             'QTY PER BATCH :', self.data.get('qty_per_batch', '')))
        if len(cust) > 34:
            lines.append(f"{' ':<15}{B_ON}{cust[34:68]:<65}{B_OFF}")
        lines.append(det_row('LOT NO.      :', self.data.get('lot_number',    ''),
                             'QTY TO PRODUCE:', self.data.get('qty_produced',  '')))

        summary = self.batch_text()
        if mode == "screen":
            lines.append(f'<div align="center">{S_ON}{summary.upper()}{S_OFF}</div>')
        else:
            lines.append(S_ON + summary.upper().center(40) + S_OFF)

        # --- 3. MATERIALS TABLE ---
        lines.append(H * WIDTH)
        lines.append(
            f"{'MATERIAL CODE':<25} {'LARGE SCALE (Kg.)':>18} "
            f"{'SMALL SCALE (grm.)':>17} {'WEIGHT (Kg.)':>15}")
        lines.append(H * WIDTH)
        for m in self.mats:
            m_c = str(m.get('material_code', ''))
            if not m_c.strip():
                lines.append(" " * WIDTH)
                continue
            l_v = f"{float(m.get('large_scale',  0)):18.7f}"
            s_v = f"{float(m.get('small_scale',  0)):17.7f}"
            w_v = f"{float(m.get('total_weight', 0)):15.7f}"
            lines.append(
                f"{m_c[:24]:<25} {B_ON}{l_v}{B_OFF} {B_ON}{s_v}{B_OFF} {B_ON}{w_v}{B_OFF}")
        lines.append(H * WIDTH)

        # --- 4. TOTAL & GAPS ---
        prod_total = f"{float(self.data.get('qty_produced', 0)):.6f}"
        lines.append(f"NOTE: {summary[:42]:<44} TOTAL: {B_ON}{prod_total:>18}{B_OFF}")
        lines.append(" "); lines.append(" "); lines.append(" ")

        # --- 5. FOOTER ---
        u = U_CHAR * 22

        def sig_ln(lab_l, val_l, lab_r, val_r):
            return (f"{lab_l:<14}{str(val_l)[:22]:<26}"
                    f"{lab_r:<16}{str(val_r)[:24]:^24}")

        lines.append(sig_ln("PREPARED BY :", self.data.get('prepared_by', ''),
                            "APPROVED BY    :", self.data.get('approved_by', '')))
        lines.append(f"{' ':<14}{' ':<26}{' ':<16}{u}")
        lines.append(sig_ln("PRINTED ON  :", datetime.now().strftime('%m/%d/%y %I:%M %p'),
                            "MAT'L RELEASED :", ""))
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
                html_parts.append(
                    f'<div style="white-space:nowrap;">{line.replace(" ", "&nbsp;")}</div>')
        self.preview_area.setHtml(
            f'<div style="font-family:\'Courier New\'; color:black;">{"".join(html_parts)}</div>')

        doc          = self.preview_area.document()
        total_blocks = doc.blockCount()
        for i in range(total_blocks):
            block = doc.findBlockByNumber(i)
            fmt   = block.blockFormat()
            text  = block.text().upper()
            if i <= 9:                       line_h = 100.0
            elif i >= (total_blocks - 6):    line_h = 95.0
            elif "BATCH BY" in text:         line_h = 160.0
            else:                            line_h = 135.0
            fmt.setLineHeight(line_h, QTextBlockFormat.LineHeightTypes.ProportionalHeight.value)
            cursor = QTextCursor(block)
            cursor.setBlockFormat(fmt)

        content_height = doc.size().height()
        self.preview_area.setFixedHeight(max(1100, int(content_height) + 120))

    def print_report(self):
        self.btn_print.setText(" SENDING... ")
        self.btn_print.setEnabled(False)
        QApplication.processEvents()

        printer_name = self.printer_combo.currentText()
        try:
            lines    = self.build_report_map(mode="printer")
            raw_text = "\n".join(lines)

            ESC  = '\x1b'
            # ESC @      → reset printer to defaults
            # ESC t 0x01 → select IBM CP437 / Extended Graphics character table
            # ESC x 0x01 → NLQ mode
            init = ESC + '@' + ESC + 't\x01' + ESC + 'x\x01'

            parts  = raw_text.split('\n')
            header = "\n".join(parts[:10])
            body   = "\n".join(parts[10:-6])
            footer = "\n".join(parts[-6:])

            payload = (
                init
                + ESC + '3\x18' + header + "\n"
                + ESC + '3\x30' + body   + "\n"
                + ESC + '3\x16' + footer + '\x0c'
            )

            # ── Encode with latin-1 ───────────────────────────────────────────
            # latin-1 maps each character to its own codepoint byte unchanged,
            # so "\xc4" (U+00C4) → byte 0xC4, "\xdf" (U+00DF) → byte 0xDF, etc.
            # The Epson LX-310 hardware interprets those bytes as box-drawing
            # characters in its built-in IBM Extended Graphics charset.
            # This is what made the original version work correctly.
            encoded = payload.encode('latin-1', errors='replace')

            hPrinter = win32print.OpenPrinter(printer_name)
            try:
                hJob = win32print.StartDocPrinter(hPrinter, 1,
                                                  ("Production Report", None, "RAW"))
                win32print.StartPagePrinter(hPrinter)
                win32print.WritePrinter(hPrinter, encoded)
                win32print.EndPagePrinter(hPrinter)
                win32print.EndDocPrinter(hPrinter)
                QMessageBox.information(self, "Success", "Printed successfully.")
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
            req = float(self.data.get('qty_required', 0))
            per = float(self.data.get('qty_per_batch', 1))
            n   = int(req / per) if per > 0 else 1
            return f"{n} batch{'es' if n != 1 else ''} by {per:.3f} KG."
        except:
            return "1 batch by 0.000 KG."


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    img_data = {
        "prod_id": "100502", "production_date": "03/02/26",
        "qty_required": 37.4, "qty_per_batch": 37.4,
        "approved_by": "M. VERDE"
    }
    img_mats = [{"material_code": "W35", "large_scale": 1.65, "small_scale": 0, "total_weight": 1.65}]
    ProductionPrintPreview(img_data, img_mats).exec()