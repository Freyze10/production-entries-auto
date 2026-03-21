from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QVBoxLayout, QFrame, QDialog, QLabel


class LoadingDialog(QDialog):
    def __init__(self, title_text="Processing...", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Please Wait")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setModal(True)
        self.setMinimumSize(400, 200)
        self.frame = QFrame(self)
        self.frame.setObjectName("HeaderCard")
        self.frame.setStyleSheet("""
            QFrame#HeaderCard { 
                background-color: #f8f9fa; 
                border-radius: 10px; 
                border: 1px solid #d0d0d0; 
            }
        """)
        main_layout = QVBoxLayout(self);
        main_layout.addWidget(self.frame)
        layout = QVBoxLayout(self.frame);
        layout.setContentsMargins(30, 30, 30, 30);
        layout.setSpacing(20)
        self.title_label = QLabel(title_text);
        self.title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold));
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("color: #0078d4; font-family: 'Segoe UI';")
        self.animation_label = QLabel("Loading...");
        self.animation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.animation_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.animation_label.setStyleSheet("color: #0078d4; font-family: 'Segoe UI';")
        self.progress_label = QLabel("Initializing...");
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter);
        self.progress_label.setWordWrap(True)
        self.progress_label.setFont(QFont("Segoe UI", 11))
        self.progress_label.setStyleSheet("color: #555; font-family: 'Segoe UI'; background-color: transparent; min-height:34px;")
        layout.addWidget(self.title_label);
        layout.addWidget(self.animation_label);
        layout.addWidget(self.progress_label)

    def update_progress(self, text):
        self.progress_label.setText(text)

    def closeEvent(self, event):
        event.accept()