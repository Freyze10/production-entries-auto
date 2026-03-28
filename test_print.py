import win32print
import win32ui
import io
import os
from PIL import Image, ImageWin
from datetime import datetime
from PyQt6.QtCore import Qt, QRect, QPoint, QSize
from PyQt6.QtGui import QPainter, QFont, QPen, QColor, QPixmap, QImage
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QComboBox,
                             QPushButton, QLabel, QMessageBox, QWidget,
                             QScrollArea)
import qtawesome as fa


class ModernProductionPreview(QDialog):
    def __init__(self, data, mats, parent=None):
        super().__init__(parent)
        self.data = data
        self.mats = mats
        self.zoom_factor = 1.0

        self.setWindowTitle("Industrial Graphical Preview - Epson LX-310")
        self.resize(1150, 950)
        self.setStyleSheet("background:#525659;")

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # --- Toolbar ---
        toolbar = QWidget()
        toolbar.setFixedHeight(60)
        toolbar.setStyleSheet("background:#f8f9fa; border-bottom: 1px solid #ddd; padding: 5px;")
        tb_layout = QHBoxLayout(toolbar)

        self.printer_combo = QComboBox()
        self.load_printers()
        tb_layout.addWidget(QLabel("<b>PRINTER:</b>"))
        tb_layout.addWidget(self.printer_combo, 1)

        tb_layout.addSpacing(20)
        tb_layout.addWidget(QLabel("<b>ZOOM:</b>"))
        btn_in = QPushButton("+");
        btn_in.clicked.connect(lambda: self.adjust_zoom(0.1))
        btn_out = QPushButton("-");
        btn_out.clicked.connect(lambda: self.adjust_zoom(-0.1))
        tb_layout.addWidget(btn_out);
        tb_layout.addWidget(btn_in)

        tb_layout.addStretch()

        btn_print = QPushButton(" PRINT TO LX-310 ")
        btn_print.setIcon(fa.icon('fa5s.print', color='white'))
        btn_print.setStyleSheet(
            "background:#28a745; color:white; padding:10px 20px; font-weight:bold; border-radius:4px;")
        btn_print.clicked.connect(self.print_via_bitmapping)
        tb_layout.addWidget(btn_print)
        layout.addWidget(toolbar)

        # --- Centered Scroll Area ---
        self.scroll = QScrollArea()
        self.scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll.setStyleSheet("background:#525659; border:none;")

        self.paper = QLabel()
        self.render_paper()

        self.scroll.setWidget(self.paper)
        layout.addWidget(self.scroll)

    def load_printers(self):
        try:
            printers = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
            for p in printers: self.printer_combo.addItem(p[2])
            self.printer_combo.setCurrentText(win32print.GetDefaultPrinter())
        except:
            pass

    def adjust_zoom(self, delta):
        self.zoom_factor = max(0.4, min(2.0, self.zoom_factor + delta))
        self.render_paper()

    def render_paper(self, high_res=False):
        """Draws the exact report layout."""
        dpi = 300 if high_res else 96
        # Calculation for Letter size (8.5 x 11)
        scaling = (dpi / 96.0) * (1.0 if high_res else self.zoom_factor)
        w = int(8.5 * dpi * (1.0 if high_res else self.zoom_factor))
        h = int(11.0 * dpi * (1.0 if high_res else self.zoom_factor))

        pixmap = QPixmap(w, h)
        pixmap.fill(Qt.GlobalColor.white)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        pen = QPen(Qt.GlobalColor.black, 1.5 * scaling)
        painter.setPen(pen)

        # --- 1. HEADER SECTION (Left - Compact) ---
        f_norm = QFont("Courier New", int(10 * scaling))
        f_bold = QFont("Courier New", int(10 * scaling), QFont.Weight.Bold)

        painter.setFont(f_bold)
        painter.drawText(int(40 * scaling), int(60 * scaling), "MASTERBATCH PHILIPPINES, INC.")
        painter.setFont(f_norm)
        painter.drawText(int(40 * scaling), int(80 * scaling), "PRODUCTION ENTRY")
        painter.drawText(int(40 * scaling), int(100 * scaling), f"FORM NO. {self.data.get('form_no', 'FM00012A1')}")

        # --- 2. ID BOX SECTION (Right - Spaced Out) ---
        box_x, box_y, box_w, box_h = int(500 * scaling), int(40 * scaling), int(310 * scaling), int(140 * scaling)
        painter.drawRect(box_x, box_y, box_w, box_h)

        bx = box_x + int(10 * scaling)
        by = box_y + int(25 * scaling)
        gap = int(28 * scaling)  # Vertical spacing inside box

        painter.drawText(bx, by, f"PRODUCTION ID   : {self.data.get('prod_id', '')}")
        painter.drawText(bx, by + gap, f"PRODUCTION DATE : {self.data.get('production_date', '')}")
        painter.drawText(bx, by + gap * 2, f"ORDER FORM NO.  : {self.data.get('order_form_no', '')}")
        painter.drawText(bx, by + gap * 3, f"FORMULATION NO. : {self.data.get('formulation_id', '')}")

        # --- 3. PRODUCT DETAILS (2 Columns) ---
        y = int(230 * scaling)
        col1, col2 = int(40 * scaling), int(460 * scaling)

        def draw_row(label1, val1, label2, val2, current_y):
            painter.setFont(f_norm)
            painter.drawText(col1, current_y, label1)
            painter.drawText(col2, current_y, label2)
            painter.setFont(f_bold)
            painter.drawText(col1 + int(140 * scaling), current_y, str(val1))
            painter.drawText(col2 + int(140 * scaling), current_y, str(val2))

        draw_row("PRODUCT CODE  :", self.data.get('product_code', ''), "MIXING TIME   :",
                 self.data.get('mixing_time', ''), y)
        y += int(25 * scaling)
        draw_row("PRODUCT COLOR :", self.data.get('product_color', ''), "MACHINE NO    :",
                 self.data.get('machine_no', ''), y)
        y += int(25 * scaling)
        draw_row("DOSAGE        :", f"{float(self.data.get('dosage', 0)):.6f}", "QTY REQUIRED  :",
                 f"{float(self.data.get('qty_required', 0)):.6f}", y)
        y += int(25 * scaling)
        draw_row("CUSTOMER      :", self.data.get('customer', '')[:25], "QTY PER BATCH :",
                 f"{float(self.data.get('qty_per_batch', 0)):.6f}", y)
        y += int(25 * scaling)
        draw_row("LOT NO.       :", self.data.get('lot_number', ''), "QTY TO PRODUCE:",
                 f"{float(self.data.get('qty_produced', 0)):.6f}", y)

        # --- 4. BATCH SUMMARY (Centered) ---
        y += int(50 * scaling)
        painter.setFont(f_bold)
        batch_txt = f"{self.data.get('batch_text', '1 batch by 0.000 KG.')}".upper()
        painter.drawText(QRect(0, y, w, int(30 * scaling)), Qt.AlignmentFlag.AlignCenter, batch_txt)

        # --- 5. MATERIALS TABLE ---
        y += int(40 * scaling)
        painter.setPen(QPen(Qt.GlobalColor.black, 2 * scaling))
        painter.drawLine(int(40 * scaling), y, int(810 * scaling), y)  # Header Top
        y += int(20 * scaling)
        painter.setFont(f_norm)
        painter.drawText(int(45 * scaling), y, "MATERIAL CODE")
        painter.drawText(int(300 * scaling), y, "LARGE SCALE (Kg.)")
        painter.drawText(int(510 * scaling), y, "SMALL SCALE (grm.)")
        painter.drawText(int(690 * scaling), y, "WEIGHT (Kg.)")
        y += int(10 * scaling)
        painter.drawLine(int(40 * scaling), y, int(810 * scaling), y)  # Header Bottom

        y += int(25 * scaling)
        painter.setFont(f_bold)
        for m in self.mats:
            painter.drawText(int(45 * scaling), y, str(m['material_code']))
            painter.drawText(int(300 * scaling), y, f"{float(m['large_scale']):15.7f}")
            painter.drawText(int(510 * scaling), y, f"{float(m['small_scale']):15.7f}")
            painter.drawText(int(690 * scaling), y, f"{float(m['total_weight']):15.7f}")
            y += int(25 * scaling)

        painter.drawLine(int(40 * scaling), y, int(810 * scaling), y)  # Table Bottom

        # --- 6. FOOTER / SIGNATURES ---
        y += int(70 * scaling)
        painter.setFont(f_norm)
        # Left Side
        painter.drawText(int(40 * scaling), y, f"PREPARED BY: {self.data.get('prepared_by', '')}")
        painter.drawText(int(40 * scaling), y + int(25 * scaling),
                         f"PRINTED ON : {datetime.now().strftime('%m/%d/%y %I:%M %p')}")
        painter.drawText(int(40 * scaling), y + int(50 * scaling), "MBPI-SYSTEM-2017")

        # Right Side Signatures
        sig_x = int(480 * scaling)
        line_x = sig_x + int(140 * scaling)
        line_w = int(180 * scaling)

        def draw_sig(label, name, current_y):
            painter.drawText(sig_x, current_y, label)
            # Draw the name ON TOP of the line
            painter.setFont(f_bold)
            painter.drawText(line_x + 5, current_y, str(name))
            painter.setFont(f_norm)
            # Draw the underline
            painter.drawLine(line_x, current_y + 4, line_x + line_w, current_y + 4)

        draw_sig("APPROVED BY    :", self.data.get('approved_by', ''), y)
        draw_sig("MAT'L RELEASED :", "", y + int(35 * scaling))
        draw_sig("PROCESSED BY   :", "", y + int(70 * scaling))

        painter.end()
        self.paper.setPixmap(pixmap)
        return pixmap

    def print_via_bitmapping(self):
        """Converts to 1-bit Monochrome for maximum LX-310 sharpness."""
        printer_name = self.printer_combo.currentText()
        try:
            # 1. Render at 300 DPI (High Res)
            pixmap = self.render_paper(high_res=True)

            # 2. Convert to Black & White (No Grays = No Blur)
            qimg = pixmap.toImage().convertToFormat(QImage.Format.Format_Mono)

            # 3. Buffer to PIL
            byte_io = io.BytesIO()
            qimg.save(byte_io, "BMP")
            bmp = Image.open(byte_io)

            # 4. Spool to Hardware
            hdc = win32ui.CreateDC()
            hdc.CreatePrinterDC(printer_name)
            hdc.StartDoc("Production Entry")
            hdc.StartPage()

            dib = ImageWin.Dib(bmp)
            # Map to printer resolution
            pw = hdc.GetDeviceCaps(110)
            ph = hdc.GetDeviceCaps(111)
            dib.draw(hdc.GetHandleOutput(), (0, 0, pw, ph))

            hdc.EndPage()
            hdc.EndDoc()
            hdc.DeleteDC()
            QMessageBox.information(self, "Success", "Report printed sharply.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Print Error", str(e))


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # SAMPLE DATA
    sample_data = {
        "prod_id": "100502", "production_date": "03/02/26", "order_form_no": "42441",
        "formulation_id": "16534", "product_code": "BA4756E", "product_color": "BLUE",
        "dosage": 100.0, "customer": "EVERGOOD PLASTIC INDUSTRY INC.", "lot_number": "8755AN",
        "mixing_time": "3 MINS.", "machine_no": "2", "qty_required": 37.4,
        "qty_per_batch": 37.4, "qty_produced": 37.4, "prepared_by": "R. MAGSALIN",
        "approved_by": "M. VERDE", "batch_text": "1 batch by 37.400 KG."
    }
    sample_mats = [{"material_code": "W35", "large_scale": 1.65, "small_scale": 0, "total_weight": 1.65}]

    win = ModernProductionPreview(sample_data, sample_mats)
    win.show()
    sys.exit(app.exec())