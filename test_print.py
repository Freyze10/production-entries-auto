import win32print
from datetime import datetime
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QComboBox,
                             QTextEdit, QPushButton, QLabel, QMessageBox,
                             QWidget, QScrollArea, QFrame)
import qtawesome as fa


class ProductionPrintPreview(QDialog):
    printed = pyqtSignal(str)

    def __init__(self, production_data: dict, materials_data: list, parent=None):
        super().__init__(parent)
        self.data = production_data or {}
        self.mats = materials_data or []
        self.default_font_size = 10

        self.setWindowTitle("Sharp Text Preview - Epson LX-310")

        # --- REQUIREMENT 1: Dialog size slightly bigger than Letter (8.5x11) ---
        # Letter is ~816px wide. We set dialog to ~1000px to give breathing room.
        self.resize(1050, 950)
        self.setStyleSheet("background:#525659;")  # Dark grey background like PDF viewers

        self.setup_ui()
        self.refresh_preview()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- TOOLBAR ---
        toolbar = QWidget()
        toolbar.setFixedHeight(60)
        toolbar.setStyleSheet("background:#f8f9fa; border-bottom: 1px solid #ddd; padding: 5px;")
        tb_layout = QHBoxLayout(toolbar)

        tb_layout.addWidget(QLabel("<b>PRINTER:</b>"))
        self.printer_combo = QComboBox()
        self.load_printers()
        tb_layout.addWidget(self.printer_combo, 1)

        tb_layout.addSpacing(20)
        tb_layout.addWidget(QLabel("<b>ZOOM:</b>"))

        btn_zoom_in = QPushButton();
        btn_zoom_in.setIcon(fa.icon('fa5s.search-plus'))
        btn_zoom_in.clicked.connect(lambda: self.preview_area.zoomIn(1))
        tb_layout.addWidget(btn_zoom_in)

        btn_zoom_out = QPushButton();
        btn_zoom_out.setIcon(fa.icon('fa5s.search-minus'))
        btn_zoom_out.clicked.connect(lambda: self.preview_area.zoomOut(1))
        tb_layout.addWidget(btn_zoom_out)

        btn_zoom_reset = QPushButton("100%");
        btn_zoom_reset.clicked.connect(self.reset_zoom)
        tb_layout.addWidget(btn_zoom_reset)

        tb_layout.addStretch()

        btn_print = QPushButton(" START PRINTING ")
        btn_print.setIcon(fa.icon('fa5s.print', color='white'))
        btn_print.setStyleSheet(
            "background:#28a745; color:white; padding:10px 20px; font-weight:bold; border-radius:4px;")
        btn_print.clicked.connect(self.print_report)
        tb_layout.addWidget(btn_print)

        main_layout.addWidget(toolbar)

        # --- REQUIREMENT 2: Center the Preview in the Dialog ---
        # We use a ScrollArea with a centered widget inside
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)  # This centers the "Paper"
        scroll.setStyleSheet("background:#525659; border:none;")

        # This container holds the "Paper" and expands to fill the scroll area
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Inner centering
        container_layout.setContentsMargins(40, 40, 40, 40)

        # The "Virtual Paper" (QTextEdit)
        self.preview_area = QTextEdit()
        self.preview_area.setReadOnly(True)
        self.preview_area.setUndoRedoEnabled(False)
        self.preview_area.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)

        font = QFont("Courier New", 10)
        font.setFixedPitch(True)  # Crucial for alignment
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.preview_area.setFont(font)

        # Fix the width to simulate 8.5 inches (approx 816 pixels) if 850
        self.preview_area.setFixedWidth(750)
        # Letter height is 11 inches (approx 1056 pixels)
        self.preview_area.setMinimumHeight(1100)

        # Initialize Monospaced Font
        self.preview_font = QFont("Courier New", self.default_font_size)
        self.preview_font.setStyleHint(QFont.StyleHint.Monospace)
        self.preview_area.setFont(self.preview_font)

        # Paper Styling (White sheet with shadow effect)
        self.preview_area.setStyleSheet("""
            background-color: white; 
            color: black; 
            border: 1px solid #777;
            padding: 50px;
        """)

        container_layout.addWidget(self.preview_area)
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def reset_zoom(self):
        font = self.preview_area.font()
        font.setPointSize(self.default_font_size)
        self.preview_area.setFont(font)

    def load_printers(self):
        try:
            printers = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
            for p in printers: self.printer_combo.addItem(p[2])
            self.printer_combo.setCurrentText(win32print.GetDefaultPrinter())
        except:
            pass

    def build_report_map(self, mode="screen"):
        # 1. Define characters
        if mode == "screen":
            H, V, TL, TR, BL, BR = "─", "│", "┌", "┐", "└", "┘"
            B_ON, B_OFF = "", ""  # NO ESCAPE CODES FOR UI
        else:
            H, V, TL, TR, BL, BR = "\xc4", "\xb3", "\xda", "\xbf", "\xc0", "\xd9"
            B_ON, B_OFF = '\x1bE', '\x1bF'  # Printer Hardware Bold

        width = 80
        box_w = 30
        left_w = width - box_w  # 50
        lines = []

        # Helper: Creates a fixed-width row for the ID Box (exactly 30 chars)
        def make_box_part(label, val):
            # Label(15) + ":" (2) + Val (7) + Borders/Spaces (6) = 30
            l_str = label[:15]
            v_str = str(val)[:7]
            content = f" {l_str:<15}: {v_str:<7} "
            return f"{V}{content}{V}"

        # --- HEADER BLOCK (Strict 80 char alignment) ---
        # Line 1
        t1 = "MASTERBATCH PHILIPPINES, INC."
        lines.append(f"{B_ON}{t1:<{left_w}}{B_OFF}{TL}{H * (box_w - 2)}{TR}")

        # Line 2
        t2 = "PRODUCTION ENTRY"
        lines.append(f"{t2:<{left_w}}{make_box_part('PRODUCTION ID', self.data.get('prod_id', ''))}")

        # Line 3
        t3 = f"FORM NO. {self.data.get('form_no', 'FM00012A1')}"
        lines.append(f"{t3:<{left_w}}{make_box_part('PRODUCTION DATE', self.data.get('production_date', ''))}")

        # Line 4
        lines.append(f"{' ':<{left_w}}{make_box_part('ORDER FORM NO.', self.data.get('order_form_no', ''))}")

        # Line 5
        lines.append(f"{' ':<{left_w}}{make_box_part('FORMULATION NO.', self.data.get('formulation_id', ''))}")

        # Line 6
        lines.append(f"{' ':<{left_w}}{BL}{H * (box_w - 2)}{BR}")
        lines.append("")

        # --- 2-COLUMN DETAILS (Using f-string formatting for fixed columns) ---
        # Col width mapping: Label(15) + Space(1) + Data(20) + Label(15) + Space(1) + Data(28) = 80
        def det_row(k1, v1, k2, v2):
            # We wrap the data in Bold AFTER padding to keep the grid perfect
            v1_pad = f"{str(v1)[:20]:<20}"
            v2_pad = f"{str(v2)[:25]:<25}"
            return f"{k1:<15} {B_ON}{v1_pad}{B_OFF} {k2:<15} {B_ON}{v2_pad}{B_OFF}"

        lines.append(det_row('PRODUCT CODE  :', self.data.get('product_code', ''), 'MIXING TIME   :',
                             self.data.get('mixing_time', '')))
        lines.append(det_row('PRODUCT COLOR :', self.data.get('product_color', ''), 'MACHINE NO    :',
                             self.data.get('machine_no', '')))
        lines.append(det_row('DOSAGE        :', self.data.get('dosage', ''), 'QTY REQUIRED  :',
                             self.data.get('qty_required', '')))

        # Handle long Customer Name
        cust = self.data.get('customer', '')
        lines.append(det_row('CUSTOMER      :', cust, 'QTY PER BATCH :', self.data.get('qty_per_batch', '')))
        if len(cust) > 20:
            lines.append(f"{'':<16}{B_ON}{cust[20:50]:<50}{B_OFF}")

        lines.append(det_row('LOT NO.       :', self.data.get('lot_number', ''), 'QTY TO PRODUCE:',
                             self.data.get('qty_produced', '')))

        # Batch Text Center
        summary = self.batch_text()
        lines.append("\n" + B_ON + summary.center(width).upper() + B_OFF + "\n")

        # --- TABLE ---
        lines.append(H * width)
        # Cols: 25, 18, 19, 18
        lines.append(f"{'MATERIAL CODE':<25} {'LARGE SCALE (Kg.)':>18} {'SMALL SCALE (grm.)':>19} {'WEIGHT (Kg.)':>18}")
        lines.append(H * width)

        for m in self.mats:
            m_code = str(m.get('material_code', ''))[:24]
            l_val = str(m.get('large_scale', '0.0000000'))
            s_val = str(m.get('small_scale', '0.0000000'))
            w_val = str(m.get('total_weight', '0.0000000'))
            lines.append(f"{m_code:<25} {l_val:>18} {s_val:>19} {w_val:>18}")

        lines.append(H * width)
        t_val = str(self.data.get('qty_produced', '0.000000'))
        lines.append(f"NOTE: {summary:<44} TOTAL: {B_ON}{t_val:>18}{B_OFF}\n\n")

        # Footer
        u = "_" * 20
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
            init_printer = ESC + '@' + ESC + 't\x01' + ESC + 'x\x01'
            full_payload = init_printer + raw_text + '\x0c'
            hPrinter = win32print.OpenPrinter(printer_name)
            try:
                hJob = win32print.StartDocPrinter(hPrinter, 1, ("Production Report", None, "RAW"))
                win32print.StartPagePrinter(hPrinter)
                win32print.WritePrinter(hPrinter, full_payload.encode('latin-1'))
                win32print.EndPagePrinter(hPrinter)
                win32print.EndDocPrinter(hPrinter)
                QMessageBox.information(self, "Success", "Printed Successfully!")
                # self.accept()
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
    img_data = {"prod_id": "100502", "production_date": "03/02/26", "qty_required": 37.4, "qty_per_batch": 37.4}
    img_mats = [{"material_code": "W35", "large_scale": 1.65, "small_scale": 0, "total_weight": 1.65}]
    dialog = ProductionPrintPreview(img_data, img_mats)
    dialog.show()
    sys.exit(app.exec())