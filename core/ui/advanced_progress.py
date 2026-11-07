from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QPushButton, QMessageBox
from PyQt6.QtCore import Qt

class AdvancedProgressDialog(QDialog):
    def __init__(self, title, total, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(400, 160)
        
        # Ocultar el botón de cerrar para forzar el uso del botón Cancelar
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        
        self.setStyleSheet("""
            QDialog { background-color: #1e1e2e; color: #ffffff; }
            QLabel { color: #ffffff; font-size: 11pt; font-weight: bold; }
            QProgressBar {
                border: 2px solid #3a3a52;
                border-radius: 5px;
                text-align: center;
                background-color: #2b2b3b;
                color: white;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #6c63ff;
                width: 10px;
            }
            QPushButton {
                background-color: #2b2b3b;
                color: #ffffff;
                border-radius: 6px;
                padding: 8px 16px;
                border: 2px solid #3a3a52;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #35354a; color: white; }
            QPushButton#cancelBtn { background-color: #ff4b4b; border-color: #ff4b4b; color: white; }
            QPushButton#cancelBtn:hover { background-color: #ff6b6b; }
            QPushButton#pauseBtn { background-color: #f39c12; border-color: #f39c12; color: white; }
            QPushButton#pauseBtn:hover { background-color: #f1c40f; }
            QPushButton:disabled { background-color: #555555; border-color: #555555; color: #aaaaaa; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(15)
        
        self.label = QLabel("Preparando...")
        self.label.setWordWrap(True)
        layout.addWidget(self.label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # Botones
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.pause_btn = QPushButton("Pausar")
        self.pause_btn.setObjectName("pauseBtn")
        self.pause_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.pause_btn.clicked.connect(self.toggle_pause)
        btn_layout.addWidget(self.pause_btn)
        
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.clicked.connect(self.request_cancel)
        btn_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(btn_layout)
        
        self.is_paused = False
        self.is_cancelled = False
        self._base_text = "Procesando..."

    def setLabelText(self, text):
        self._base_text = text
        if self.is_paused:
            self.label.setText(text + " (PAUSADO)")
        else:
            self.label.setText(text)
        
    def setValue(self, value):
        self.progress_bar.setValue(value)

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_btn.setText("Reanudar")
            self.pause_btn.setStyleSheet("background-color: #27ae60; border-color: #27ae60; color: white;")
            self.label.setText(self._base_text + " (PAUSADO)")
        else:
            self.pause_btn.setText("Pausar")
            self.pause_btn.setStyleSheet("background-color: #f39c12; border-color: #f39c12; color: white;")
            self.label.setText(self._base_text)

    def request_cancel(self):
        reply = QMessageBox.question(
            self,
            "Confirmar Cancelación",
            "¿Estás seguro de que deseas cancelar?\nSe terminará el archivo actual y se abortará el resto.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.is_cancelled = True
            self.label.setText("Cancelando... Por favor espera.")
            self.pause_btn.setEnabled(False)
            self.cancel_btn.setEnabled(False)
