import win32print
import win32ui
import io
import os
import tempfile
from PIL import Image, ImageWin
from datetime import datetime
from PyQt6.QtCore import Qt, QRect, QPoint, QSize
from PyQt6.QtGui import QPainter, QFont, QPen, QColor, QPixmap, QImage
from PyQt6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout,
                             QComboBox, QPushButton, QLabel, QMessageBox,
                             QWidget, QScrollArea)
import qtawesome as fa


class FlexibleIndustrialPreview(QDialog):
    def __init__(self, data, mats, parent=None):
        super().__init__(parent)
        self.data = data
        self.mats = mats
        self.zoom_factor = 1.0

        self.setWindowTitle("Industrial Design Preview - Epson LX-310")
        self.resize(1100, 950)
        self.setStyleSheet("background:#525659;")  # PDF-style background

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # --- Toolbar ---
        toolbar = QWidget()
        toolbar.setFixedHeight(60)
        toolbar.setStyleSheet("background:#f8f9fa; border-bottom: 1px solid #ddd;")
        tb_layout = QHBoxLayout(toolbar)

        self.printer_combo = QComboBox()
        self.load_printers()
        tb_layout.addWidget(QLabel("<b>PRINTER:</b>"))
        tb_layout.addWidget(self.printer_combo, 1)

        # Zoom
        btn_in = QPushButton("+");
        btn_in.clicked.connect(lambda: self.adjust_zoom(0.1))
        btn_out = QPushButton("-");
        btn_out.clicked.connect(lambda: self.adjust_zoom(-0.1))
        tb_layout.addWidget(QLabel("<b>ZOOM:</b>"))
        tb_layout.addWidget(btn_out);
        tb_layout.addWidget(btn_in)

        tb_layout.addStretch()

        btn_print = QPushButton(" PRINT SHARP ")
        btn_print.setIcon(fa.icon('fa5s.print', color='white'))
        btn_print.setStyleSheet(
            "background:#28a745; color:white; padding:10px 20px; font-weight:bold; border-radius:4px;")
        btn_print.clicked.connect(self.print_high_quality)
        tb_layout.addWidget(btn_print)
        layout.addWidget(toolbar)

        # --- Centered Paper View ---
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
        self.zoom_factor = max(0.5, min(2.0, self.zoom_factor + delta))
        self.render_paper()

    def draw_report(self, painter, scale):
        """
        THE CANVAS: This is where you customize EVERYTHING.
        Use coordinates (x, y) to place elements.
        """
        # Set Pen for lines
        painter.setPen(QPen(Qt.GlobalColor.black, 1.5 * scale))

        # 1. Fonts
        f_header = QFont("Courier New", int(10 * scale), QFont.Weight.Bold)
        f_label = QFont("Courier New", int(10 * scale))
        f_data = QFont("Courier New", int(10 * scale), QFont.Weight.Bold)

        # 2. Company Info (Left)
        painter.setFont(f_header)
        painter.drawText(int(50 * scale), int(60 * scale), "MASTERBATCH PHILIPPINES, INC.")
        painter.setFont(f_label)
        painter.drawText(int(50 * scale), int(80 * scale), "PRODUCTION ENTRY")
        painter.drawText(int(50 * scale), int(100 * scale), f"FORM NO. {self.data.get('form_no', 'FM00012A1')}")

        # 3. ID Box (Right) - Customizable position and spacing
        box_x, box_y, box_w, box_h = int(500 * scale), int(40 * scale), int(300 * scale), int(140 * scale)
        painter.drawRect(box_x, box_y, box_w, box_h)

        bx = box_x + int(15 * scale)
        by = box_y + int(30 * scale)
        row_h = int(28 * scale)  # Vertical Spacing inside box

        painter.drawText(bx, by, f"PRODUCTION ID   : {self.data.get('prod_id', '')}")
        painter.drawText(bx, by + row_h, f"PRODUCTION DATE : {self.data.get('production_date', '')}")
        painter.drawText(bx, by + row_h * 2, f"ORDER FORM NO.  : {self.data.get('order_form_no', '')}")
        painter.drawText(bx, by + row_h * 3, f"FORMULATION NO. : {self.data.get('formulation_id', '')}")

        # 4. Details Section (2 Columns)
        y = int(240 * scale)
        c1, c2 = int(50 * scale), int(480 * scale)

        def draw_field(x, curr_y, label, value):
            painter.setFont(f_label)
            painter.drawText(x, curr_y, label)
            painter.setFont(f_data)
            painter.drawText(x + int(140 * scale), curr_y, str(value))

        draw_field(c1, y, "PRODUCT CODE  :", self.data.get('product_code', ''))
        draw_field(c2, y, "MIXING TIME   :", self.data.get('mixing_time', ''))
        y += int(28 * scale)
        draw_field(c1, y, "PRODUCT COLOR :", self.data.get('product_color', ''))
        draw_field(c2, y, "MACHINE NO    :", self.data.get('machine_no', ''))
        y += int(28 * scale)
        draw_field(c1, y, "DOSAGE        :", f"{float(self.data.get('dosage', 0)):.6f}")
        draw_field(c2, y, "QTY REQUIRED  :", f"{float(self.data.get('qty_required', 0)):.6f}")
        # ... and so on ...

        # 5. Table (Drawn with lines)
        y += int(80 * scale)
        painter.drawLine(int(50 * scale), y, int(800 * scale), y)  # Top Line
        y += int(20 * scale)
        painter.setFont(f_label)
        painter.drawText(int(50 * scale), y, "MATERIAL CODE")
        painter.drawText(int(280 * scale), y, "LARGE SCALE (Kg.)")
        painter.drawText(int(500 * scale), y, "SMALL SCALE (grm.)")
        painter.drawText(int(680 * scale), y, "WEIGHT (Kg.)")
        y += int(10 * scale)
        painter.drawLine(int(50 * scale), y, int(800 * scale), y)  # Header line

        painter.setFont(f_data)
        for m in self.mats:
            y += int(25 * scale)
            painter.drawText(int(50 * scale), y, str(m['material_code']))
            painter.drawText(int(280 * scale), y, f"{float(m['large_scale']):.7f}")
            painter.drawText(int(680 * scale), y, f"{float(m['total_weight']):.7f}")

        y += int(15 * scale)
        painter.drawLine(int(50 * scale), y, int(800 * scale), y)  # Bottom line

        # 6. Signatures (Names ON lines)
        y += int(80 * scale)
        painter.setFont(f_label)
        painter.drawText(int(500 * scale), y, "APPROVED BY    :")
        painter.setFont(f_data)
        painter.drawText(int(640 * scale), y, str(self.data.get('approved_by', '')))
        painter.drawLine(int(635 * scale), y + 5, int(800 * scale), y + 5)  # The Underline

    def render_paper(self, high_res=False):
        dpi = 300 if high_res else 96
        # Scaling relative to screen resolution
        current_scale = (dpi / 96.0) * (1.0 if high_res else self.zoom_factor)

        # Letter dimensions in pixels
        w = int(8.5 * dpi * (1.0 if high_res else self.zoom_factor))
        h = int(11.0 * dpi * (1.0 if high_res else self.zoom_factor))

        pixmap = QPixmap(w, h)
        pixmap.fill(Qt.GlobalColor.white)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)  # SHARP EDGES
        self.draw_report(painter, current_scale)
        painter.end()

        self.paper.setPixmap(pixmap)
        return pixmap

    def print_high_quality(self):
        """
        The Secret Logic: Converts the GUI drawing into a
        binary pin-map for the dot-matrix head.
        """
        printer_name = self.printer_combo.currentText()
        temp_path = os.path.join(tempfile.gettempdir(), "sharp_print.bmp")

        try:
            # 1. Render at high resolution (No zoom, 300 DPI)
            pixmap = self.render_paper(high_res=True)

            # 2. CONVERT TO 1-BIT MONOCHROME (This removes all blur)
            qimage = pixmap.toImage().convertToFormat(QImage.Format.Format_Mono)
            qimage.save(temp_path, "BMP")

            # 3. Open with PIL and convert to RGB (Windows Driver requirement)
            # Starting with Mono ensures pixels are either PURE Black or PURE White.
            bmp = Image.open(temp_path).convert("RGB")

            # 4. Spool to Hardware
            hdc = win32ui.CreateDC()
            hdc.CreatePrinterDC(printer_name)

            # Get Hardware Printer Resolutions
            phys_w = hdc.GetDeviceCaps(110)  # HORZRES
            phys_h = hdc.GetDeviceCaps(111)  # VERTRES

            hdc.StartDoc("Sharp Production Print")
            hdc.StartPage()

            # Draw the monochrome map directly to the printer pins
            dib = ImageWin.Dib(bmp)
            dib.draw(hdc.GetHandleOutput(), (0, 0, phys_w, phys_h))

            hdc.EndPage()
            hdc.EndDoc()
            hdc.DeleteDC()

            if os.path.exists(temp_path): os.remove(temp_path)
            QMessageBox.information(self, "Success", "Printed with Pixel-Perfect Sharpness.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


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

    win = FlexibleIndustrialPreview(sample_data, sample_mats)
    win.show()
    sys.exit(app.exec())