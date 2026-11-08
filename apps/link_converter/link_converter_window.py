import os
import sys
import subprocess
import urllib.request
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QLineEdit, QFileDialog, QProgressBar, QMessageBox, QFrame, QScrollArea,
    QComboBox, QGridLayout
)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QIcon, QPixmap, QImage

from apps.link_converter.ui_theme import get_app_colors, apply_window_theme
from apps.link_converter.platform_detector import detect_platform
from apps.link_converter.downloader import MetadataWorker, DownloadWorker


class DownloadCard(QFrame):
    """Tarjeta individual interactiva para cada video, audio o imagen en la cola."""

    def __init__(self, item_data: dict, output_dir: str, parent_manager):
        super().__init__()
        self.item_data = item_data
        self.output_dir = output_dir
        self.parent_manager = parent_manager
        self._colors = parent_manager._colors
        self.worker = None
        self.saved_path = None
        self.is_downloading = False
        self.is_finished = False

        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(f"""
            QFrame#downloadCard {{
                background-color: {self._colors['card']};
                border: 1px solid {self._colors['border']};
                border-radius: 14px;
            }}
        """)
        self.setObjectName("downloadCard")
        self.setFixedHeight(125)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(14)

        # 1. Miniatura / Icono de plataforma
        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(110, 75)
        self.thumb_label.setStyleSheet(f"background-color: {self._colors['bg']}; border-radius: 8px;")
        self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._load_thumbnail(self.item_data.get("thumbnail_url"))
        layout.addWidget(self.thumb_label)

        # 2. Información del contenido
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        self.title_label = QLabel(self.item_data.get("title", "Cargando enlace..."))
        self.title_label.setStyleSheet(f"color: {self._colors['text_main']}; font-weight: 700; font-size: 11pt;")
        self.title_label.setWordWrap(False)
        info_layout.addWidget(self.title_label)

        uploader = self.item_data.get("uploader", "")
        duration = self.item_data.get("duration", "")
        meta_text = f"👤 {uploader}   •   ⏱️ {duration}" if duration else f"👤 {uploader}"
        self.meta_label = QLabel(meta_text)
        self.meta_label.setStyleSheet(f"color: {self._colors['text_muted']}; font-size: 8.5pt;")
        info_layout.addWidget(self.meta_label)

        # Barra de progreso individual
        self.prog_bar = QProgressBar()
        self.prog_bar.setFixedHeight(8)
        self.prog_bar.setTextVisible(False)
        self.prog_bar.setValue(0)
        self.prog_bar.setVisible(False)
        self.prog_bar.setStyleSheet(f"""
            QProgressBar {{
                background: {self._colors['bg']};
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background: {self._colors['accent']};
                border-radius: 4px;
            }}
        """)
        info_layout.addWidget(self.prog_bar)

        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet(f"color: {self._colors['text_muted']}; font-size: 8.5pt; font-weight: 600;")
        self.status_lbl.setVisible(False)
        info_layout.addWidget(self.status_lbl)

        layout.addLayout(info_layout, stretch=1)

        # 3. Controles por tarjeta (Formato, Calidad y Acción)
        controls_layout = QVBoxLayout()
        controls_layout.setSpacing(6)
        controls_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        top_controls = QHBoxLayout()
        top_controls.setSpacing(6)

        # Combo Tipo / Formato
        self.type_combo = QComboBox()
        self.type_combo.setStyleSheet(self._combo_style())
        if self.item_data.get("default_type") == "image":
            self.type_combo.addItems(["JPG", "PNG", "WEBP"])
        else:
            self.type_combo.addItems(["🎬 MP4", "🎬 MKV", "🎵 MP3", "🎵 M4A", "🎵 WAV"])
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        top_controls.addWidget(self.type_combo)

        # Combo Calidad (para video)
        self.qual_combo = QComboBox()
        self.qual_combo.setStyleSheet(self._combo_style())
        self.qual_combo.addItems(["Máxima", "1080p", "720p", "480p"])
        top_controls.addWidget(self.qual_combo)

        # Botón Quitar Tarjeta
        self.btn_del = QPushButton("✕")
        self.btn_del.setFixedSize(28, 28)
        self.btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_del.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {self._colors['text_muted']};
                border: 1px solid {self._colors['border']};
                border-radius: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: rgba(235, 87, 87, 0.2);
                color: #FF5A5A;
                border-color: #FF5A5A;
            }}
        """)
        self.btn_del.clicked.connect(self.remove_card)
        top_controls.addWidget(self.btn_del)

        controls_layout.addLayout(top_controls)

        # Botón Acción de Descarga / Abrir
        self.btn_action = QPushButton("⬇️ Descargar")
        self.btn_action.setFixedHeight(34)
        self.btn_action.setFixedWidth(140)
        self.btn_action.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_action.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._colors['accent']};
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                font-weight: 700;
                font-size: 9.5pt;
            }}
            QPushButton:hover {{
                background-color: {self._colors['accent_hover']};
            }}
            QPushButton:disabled {{
                background-color: {self._colors['border']};
                color: {self._colors['text_muted']};
            }}
        """)
        self.btn_action.clicked.connect(self.start_download)
        controls_layout.addWidget(self.btn_action, alignment=Qt.AlignmentFlag.AlignRight)

        layout.addLayout(controls_layout)

    def _combo_style(self):
        return f"""
            QComboBox {{
                background-color: {self._colors['bg']};
                color: {self._colors['text_main']};
                border: 1px solid {self._colors['border']};
                border-radius: 7px;
                padding: 4px 8px;
                font-size: 8.5pt;
                font-weight: 600;
            }}
        """

    def _on_type_changed(self, idx):
        text = self.type_combo.currentText()
        is_video = "🎬" in text
        self.qual_combo.setVisible(is_video)

    def _load_thumbnail(self, thumb_url):
        if not thumb_url:
            self.thumb_label.setText("🎬")
            return

        # Descarga ligera de miniatura en hilo si es HTTP
        def fetch():
            try:
                req = urllib.request.Request(
                    thumb_url,
                    headers={"User-Agent": "Mozilla/5.0"}
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    raw = resp.read()
                    img = QImage()
                    if img.loadFromData(raw):
                        pix = QPixmap.fromImage(img).scaled(
                            110, 75,
                            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                            Qt.TransformationMode.SmoothTransformation
                        )
                        QTimer.singleShot(0, lambda: self.thumb_label.setPixmap(pix))
            except Exception:
                pass

        import threading
        threading.Thread(target=fetch, daemon=True).start()

    def start_download(self):
        if self.is_finished:
            # Si ya terminó, abre el archivo o la carpeta
            if self.saved_path and os.path.exists(self.saved_path):
                os.startfile(self.saved_path)
            else:
                os.startfile(self.output_dir)
            return

        if self.is_downloading:
            if self.worker:
                self.worker.cancel()
            return

        self.is_downloading = True
        self.prog_bar.setVisible(True)
        self.status_lbl.setVisible(True)
        self.status_lbl.setText("Iniciando descarga...")
        self.btn_action.setText("✕ Cancelar")
        self.btn_action.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(235, 87, 87, 0.2);
                color: #FF5A5A;
                border: 1px solid #FF5A5A;
                border-radius: 8px;
                font-weight: 700;
            }}
        """)
        self.type_combo.setEnabled(False)
        self.qual_combo.setEnabled(False)

        # Formato y calidad
        type_str = self.type_combo.currentText()
        if "🎵" in type_str:
            media_type = "audio"
            fmt = type_str.replace("🎵", "").strip().lower()
        elif "🎬" in type_str:
            media_type = "video"
            fmt = type_str.replace("🎬", "").strip().lower()
        else:
            media_type = "image"
            fmt = type_str.strip().lower()

        q_str = self.qual_combo.currentText()
        qual = "best" if q_str == "Máxima" else q_str.replace("p", "")

        self.worker = DownloadWorker(
            self.item_data["url"], media_type, fmt, qual, self.output_dir
        )
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_progress(self, pct, status_text):
        self.prog_bar.setValue(pct)
        self.status_lbl.setText(status_text)

    def _on_finished(self, title, saved_path):
        self.is_downloading = False
        self.is_finished = True
        self.saved_path = saved_path
        self.prog_bar.setVisible(False)
        self.status_lbl.setText("✅ Completado")
        self.status_lbl.setStyleSheet("color: #4EBE82; font-weight: 700; font-size: 8.5pt;")

        self.btn_action.setText("▶️ Abrir Archivo")
        self.btn_action.setStyleSheet(f"""
            QPushButton {{
                background-color: #2E7D32;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: #388E3C;
            }}
        """)
        self.parent_manager._on_card_completed()

    def _on_error(self, err_msg):
        self.is_downloading = False
        self.prog_bar.setVisible(False)
        self.status_lbl.setText(f"❌ {err_msg}")
        self.status_lbl.setStyleSheet("color: #FF5A5A; font-weight: 600; font-size: 8.5pt;")
        self.btn_action.setText("🔄 Reintentar")
        self.btn_action.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._colors['accent']};
                color: #FFFFFF;
                border-radius: 8px;
                font-weight: 700;
            }}
        """)
        self.type_combo.setEnabled(True)
        self.qual_combo.setEnabled(True)
        self.parent_manager._on_card_completed()

    def remove_card(self):
        if self.worker and self.is_downloading:
            self.worker.cancel()
        self.parent_manager.remove_card(self)


class LinkConverterWindow(QWidget):
    """Muro de Tarjetas Dinámicas con soporte multi-enlace, playlists y descargas concurrentes."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Link Converter — Media Hub")
        self.resize(1020, 720)
        self.setMinimumSize(920, 620)
        apply_window_theme(self)
        self._colors = get_app_colors()

        self.cards = []
        self.max_concurrent = 3
        self.download_queue = []

        # Carpeta de salida por defecto (Downloads del usuario)
        downloads = os.path.join(os.environ.get("USERPROFILE", os.path.expanduser("~")), "Downloads")
        self.output_dir = downloads if os.path.isdir(downloads) else os.path.expanduser("~")

        self.init_ui()

        # Revisión automática del portapapeles al iniciar
        QTimer.singleShot(400, self.check_clipboard_on_startup)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 20, 28, 20)
        main_layout.setSpacing(14)

        # ── 1. Header con Salir ──────────────────────────────────────────────
        header_row = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("LINK CONVERTER")
        title.setStyleSheet(f"font-size: 19pt; font-weight: 800; color: {self._colors['text_main']}; letter-spacing: 0.5px;")
        desc = QLabel("Descarga videos, audios o playlists completas de YouTube, TikTok, Instagram y más.")
        desc.setStyleSheet(f"color: {self._colors['text_muted']}; font-size: 10pt;")
        title_box.addWidget(title)
        title_box.addWidget(desc)
        header_row.addLayout(title_box)
        header_row.addStretch()

        exit_btn = QPushButton("🚪 Salir")
        exit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        exit_btn.setFixedHeight(34)
        exit_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {self._colors['text_muted']};
                padding: 4px 14px;
                border-radius: 8px;
                font-weight: 600;
                border: 1px solid {self._colors['border']};
            }}
            QPushButton:hover {{
                background-color: rgba(235, 87, 87, 0.15);
                color: #FF5A5A;
                border-color: rgba(235, 87, 87, 0.4);
            }}
        """)
        exit_btn.clicked.connect(self.close)
        header_row.addWidget(exit_btn)
        main_layout.addLayout(header_row)

        # ── 2. Barra de Entrada y Acciones Rápidas ───────────────────────────
        input_card = QFrame()
        input_card.setStyleSheet(f"background-color: {self._colors['card']}; border-radius: 14px; padding: 12px;")
        input_layout = QVBoxLayout(input_card)
        input_layout.setSpacing(10)

        entry_row = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("🔗 Pega aquí uno o varios enlaces (YouTube, TikTok, Instagram, Playlists...)")
        self.url_input.setFixedHeight(44)
        self.url_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self._colors['bg']};
                color: {self._colors['text_main']};
                border: 1.5px solid {self._colors['border']};
                border-radius: 10px;
                padding: 0 14px;
                font-size: 11pt;
            }}
            QLineEdit:focus {{
                border-color: {self._colors['accent']};
            }}
        """)
        self.url_input.returnPressed.connect(self.add_urls_from_input)
        entry_row.addWidget(self.url_input)

        self.btn_add = QPushButton("➕ Añadir Enlace")
        self.btn_add.setFixedHeight(44)
        self.btn_add.setFixedWidth(140)
        self.btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._colors['accent']};
                color: #FFFFFF;
                border: none;
                border-radius: 10px;
                font-size: 10.5pt;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: {self._colors['accent_hover']};
            }}
        """)
        self.btn_add.clicked.connect(self.add_urls_from_input)
        entry_row.addWidget(self.btn_add)
        input_layout.addLayout(entry_row)

        # Acciones secundarias (Pegar de Portapapeles y Carpeta)
        sub_row = QHBoxLayout()
        self.btn_clipboard = QPushButton("📋 Pegar del Portapapeles")
        self.btn_clipboard.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clipboard.setStyleSheet(self._sub_btn_style())
        self.btn_clipboard.clicked.connect(self.paste_from_clipboard)
        sub_row.addWidget(self.btn_clipboard)

        self.btn_folder = QPushButton(f"📁 Guardar en: {os.path.basename(self.output_dir)}")
        self.btn_folder.setToolTip(self.output_dir)
        self.btn_folder.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_folder.setStyleSheet(self._sub_btn_style())
        self.btn_folder.clicked.connect(self.change_output_folder)
        sub_row.addWidget(self.btn_folder)

        sub_row.addStretch()

        # Botón Descargar Todo
        self.btn_download_all = QPushButton("🚀 Descargar Todo (0)")
        self.btn_download_all.setEnabled(False)
        self.btn_download_all.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_download_all.setStyleSheet(f"""
            QPushButton {{
                background-color: #2E7D32;
                color: white;
                border-radius: 8px;
                padding: 6px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #388E3C; }}
            QPushButton:disabled {{ background-color: {self._colors['border']}; color: {self._colors['text_muted']}; }}
        """)
        self.btn_download_all.clicked.connect(self.start_download_all)
        sub_row.addWidget(self.btn_download_all)

        # Botón Limpiar
        self.btn_clear_done = QPushButton("🧹 Limpiar Completados")
        self.btn_clear_done.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear_done.setStyleSheet(self._sub_btn_style())
        self.btn_clear_done.clicked.connect(self.clear_completed)
        sub_row.addWidget(self.btn_clear_done)

        input_layout.addLayout(sub_row)
        main_layout.addWidget(input_card)

        # ── 3. Muro de Tarjetas Dinámicas (Scroll Area) ──────────────────────
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(f"""
            QScrollArea {{
                border: 1px solid {self._colors['border']};
                border-radius: 14px;
                background-color: {self._colors['bg']};
            }}
        """)

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(14, 14, 14, 14)
        self.cards_layout.setSpacing(10)
        self.cards_layout.addStretch()

        # Mensaje de Muro Vacío
        self.empty_label = QLabel("🎯 Pega o añade un enlace arriba para comenzar a descargar.")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet(f"color: {self._colors['text_muted']}; font-size: 11pt; font-weight: 600; padding: 50px;")
        self.cards_layout.insertWidget(0, self.empty_label)

        self.scroll.setWidget(self.cards_container)
        main_layout.addWidget(self.scroll)

    def _sub_btn_style(self):
        return f"""
            QPushButton {{
                background-color: {self._colors['bg']};
                color: {self._colors['text_main']};
                border: 1px solid {self._colors['border']};
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 9pt;
                font-weight: 600;
            }}
            QPushButton:hover {{
                border-color: {self._colors['accent']};
            }}
        """

    def check_clipboard_on_startup(self):
        """Verifica si en el portapapeles hay una URL compatible al abrir la aplicación."""
        cb = QApplication.clipboard()
        text = cb.text().strip()
        if text.startswith("http://") or text.startswith("https://"):
            self.url_input.setText(text)

    def paste_from_clipboard(self):
        cb = QApplication.clipboard()
        text = cb.text().strip()
        if text:
            self.url_input.setText(text)
            self.add_urls_from_input()

    def change_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta de Descargas", self.output_dir)
        if folder:
            self.output_dir = folder
            self.btn_folder.setText(f"📁 Guardar en: {os.path.basename(folder)}")
            self.btn_folder.setToolTip(folder)
            for c in self.cards:
                c.output_dir = folder

    def add_urls_from_input(self):
        raw = self.url_input.text().strip()
        if not raw:
            return

        # Separar si pegaron múltiples links por saltos de línea o espacios
        urls = [u.strip() for u in raw.replace(",", " ").split() if u.strip().startswith("http")]
        if not urls:
            QMessageBox.warning(self, "Enlace Inválido", "Por favor ingresa una URL válida (ej. https://...)")
            return

        self.url_input.clear()
        self.empty_label.setVisible(False)

        for u in urls:
            self._fetch_and_create_card(u)

    def _fetch_and_create_card(self, url: str):
        # Crear worker de metadatos para resolver título, miniatura o playlist
        meta_worker = MetadataWorker(url, parent=self)

        def on_info_ready(items):
            if len(items) > 1:
                # Es una Playlist
                reply = QMessageBox.question(
                    self,
                    "Playlist Detectada",
                    f"Se detectó una lista de reproducción con {len(items)} videos.\n"
                    f"¿Deseas agregar todos los videos a la cola de descargas?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                if reply == QMessageBox.StandardButton.Yes:
                    for it in items:
                        self._add_card(it)
                else:
                    self._add_card(items[0])
            else:
                self._add_card(items[0])

        def on_info_error(err):
            # Fallback tarjeta con la URL directa
            fallback_item = {
                "url": url,
                "title": url,
                "uploader": "Enlace Multimedia",
                "duration": "",
                "thumbnail_url": "",
                "is_playlist": False,
                "default_type": "video",
            }
            self._add_card(fallback_item)

        meta_worker.finished_info.connect(on_info_ready)
        meta_worker.error.connect(on_info_error)
        meta_worker.start()

    def _add_card(self, item_data):
        card = DownloadCard(item_data, self.output_dir, self)
        self.cards.append(card)
        self.cards_layout.insertWidget(len(self.cards) - 1, card)
        self._update_all_button()

    def remove_card(self, card):
        if card in self.cards:
            self.cards.remove(card)
            self.cards_layout.removeWidget(card)
            card.deleteLater()
            self._update_all_button()

        if not self.cards:
            self.empty_label.setVisible(True)

    def clear_completed(self):
        completed = [c for c in self.cards if c.is_finished]
        for c in completed:
            self.remove_card(c)

    def _update_all_button(self):
        pending = [c for c in self.cards if not c.is_finished and not c.is_downloading]
        self.btn_download_all.setText(f"🚀 Descargar Todo ({len(pending)})")
        self.btn_download_all.setEnabled(len(pending) > 0)

    def start_download_all(self):
        """Descargas concurrentes / paralelas (máximo 3 en paralelo)."""
        pending = [c for c in self.cards if not c.is_finished and not c.is_downloading]
        self.download_queue = pending
        self._pump_queue()

    def _pump_queue(self):
        active_count = sum(1 for c in self.cards if c.is_downloading)
        while active_count < self.max_concurrent and self.download_queue:
            next_card = self.download_queue.pop(0)
            next_card.start_download()
            active_count += 1
        self._update_all_button()

    def _on_card_completed(self):
        self._update_all_button()
        self._pump_queue()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LinkConverterWindow()
    window.show()
    sys.exit(app.exec())
