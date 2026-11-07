import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QWidget, QGridLayout, QApplication
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from core.theme_manager import ThemeManager

class ResultViewerDialog(QDialog):
    def __init__(self, output_dir, parent=None):
        super().__init__(parent)
        self.output_dir = output_dir
        self.setWindowTitle("Resultados del Proceso")
        self.setMinimumSize(700, 500)
        self._tm = ThemeManager.instance()
        self.init_ui()
        self._apply_theme()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)

        title = QLabel("Proceso Completado")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18pt; font-weight: bold;")
        self.layout.addWidget(title)

        subtitle = QLabel(f"Archivos guardados en: {self.output_dir}")
        subtitle.setWordWrap(True)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(subtitle)

        # Scroll Area for thumbnails
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.grid = QGridLayout(self.scroll_content)
        self.grid.setSpacing(15)

        self.load_thumbnails()

        self.scroll.setWidget(self.scroll_content)
        self.layout.addWidget(self.scroll)

        # Footer buttons
        footer = QHBoxLayout()
        footer.addStretch()

        open_folder_btn = QPushButton("  Abrir Carpeta  ")
        open_folder_btn.setMinimumHeight(40)
        open_folder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        open_folder_btn.clicked.connect(self.open_folder)
        footer.addWidget(open_folder_btn)

        close_btn = QPushButton("  Cerrar  ")
        close_btn.setMinimumHeight(40)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        footer.addWidget(close_btn)

        self.layout.addLayout(footer)

    def load_thumbnails(self):
        if not os.path.exists(self.output_dir):
            return

        files = [f for f in os.listdir(self.output_dir) if os.path.isfile(os.path.join(self.output_dir, f))]
        files.sort(key=lambda x: os.path.getmtime(os.path.join(self.output_dir, x)), reverse=True)

        cols = 4
        for i, file in enumerate(files[:50]): # Limitar a 50 para evitar lag
            file_path = os.path.join(self.output_dir, file)
            ext = os.path.splitext(file)[1].lower()

            item_widget = QWidget()
            item_layout = QVBoxLayout(item_widget)
            item_layout.setContentsMargins(5, 5, 5, 5)

            thumb_label = QLabel()
            thumb_label.setFixedSize(120, 120)
            thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            thumb_label.setStyleSheet("background-color: #2a2a2a; border-radius: 8px;")

            # Generate Thumbnail
            if ext in ['.jpg', '.jpeg', '.png', '.webp', '.bmp']:
                pixmap = QPixmap(file_path)
                if not pixmap.isNull():
                    thumb_label.setPixmap(pixmap.scaled(110, 110, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            else:
                thumb_label.setText("🎥" if ext in ['.mp4', '.mkv', '.avi', '.mov', '.webm'] else ("🎵" if ext in ['.mp3', '.wav', '.m4a'] else "📄"))
                thumb_label.setStyleSheet("background-color: #2a2a2a; border-radius: 8px; font-size: 30pt;")

            name_label = QLabel(file)
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name_label.setWordWrap(True)
            name_label.setStyleSheet("font-size: 9pt;")
            
            item_layout.addWidget(thumb_label, alignment=Qt.AlignmentFlag.AlignCenter)
            item_layout.addWidget(name_label)

            row = i // cols
            col = i % cols
            self.grid.addWidget(item_widget, row, col)

    def open_folder(self):
        import subprocess
        try:
            os.startfile(self.output_dir)
        except AttributeError:
            subprocess.Popen(["xdg-open", self.output_dir])

    def _apply_theme(self):
        styles = self._tm.hub_styles()
        self.setStyleSheet(styles["window"])
        
        # Style buttons with the primary and secondary colors
        btn_style = f"""
            QPushButton {{
                background-color: #3b82f6;
                color: white;
                border-radius: 6px;
                font-weight: bold;
                padding: 0 20px;
            }}
            QPushButton:hover {{
                background-color: #2563eb;
            }}
        """
        secondary_btn_style = f"""
            QPushButton {{
                background-color: #4b5563;
                color: white;
                border-radius: 6px;
                font-weight: bold;
                padding: 0 20px;
            }}
            QPushButton:hover {{
                background-color: #374151;
            }}
        """
        for btn in self.findChildren(QPushButton):
            if "Cerrar" in btn.text():
                btn.setStyleSheet(secondary_btn_style)
            else:
                btn.setStyleSheet(btn_style)
