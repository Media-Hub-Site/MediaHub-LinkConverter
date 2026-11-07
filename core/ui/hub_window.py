import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QGridLayout, QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtGui import QPixmap, QIcon, QColor, QDrag
from PyQt6.QtCore import QMimeData
from PyQt6.QtCore import Qt, QSize
from core.theme_manager import ThemeManager
from core.updater import CheckUpdateThread, UpdateDialog


def get_asset_path(filename):
    import sys
    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    return os.path.join(base_dir, "assets", "hub", filename)


# ─────────────────────────────────────────────────────────────────────
#  AppCard
# ─────────────────────────────────────────────────────────────────────
class AppCard(QFrame):
    def __init__(self, card_id, title, subtitle, icon_file, btn_text,
                 btn_type="install", is_disabled=False, parent=None):
        super().__init__(parent)
        self.card_id = card_id
        self.setAcceptDrops(True)
        self.btn_type = btn_type
        self._is_disabled = is_disabled

        if is_disabled:
            self.setObjectName("appCardDisabled")
        else:
            self.setObjectName("appCard")
            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(15)
            shadow.setXOffset(0)
            shadow.setYOffset(4)
            shadow.setColor(QColor(0, 0, 0, 80))
            self.setGraphicsEffect(shadow)

        self.setFixedHeight(180)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Icon
        self._icon_label = QLabel()
        pixmap = QPixmap(get_asset_path(icon_file))
        if not pixmap.isNull():
            self._icon_label.setPixmap(
                pixmap.scaled(100, 100,
                              Qt.AspectRatioMode.KeepAspectRatio,
                              Qt.TransformationMode.SmoothTransformation)
            )
        self._icon_label.setFixedSize(100, 100)
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self._icon_label)

        content_layout = QVBoxLayout()
        content_layout.setSpacing(5)

        self._title_label = QLabel(title)
        self._title_label.setWordWrap(True)

        self._subtitle_label = QLabel(subtitle)
        self._subtitle_label.setWordWrap(True)

        content_layout.addWidget(self._title_label)
        content_layout.addWidget(self._subtitle_label)
        content_layout.addStretch()

        action_layout = QHBoxLayout()
        self.action_btn = QPushButton(btn_text)
        self.action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if btn_type == "install":
            self.action_btn.setIcon(
                self.style().standardIcon(self.style().StandardPixmap.SP_ArrowDown))
        elif btn_type == "open":
            self.action_btn.setIcon(
                self.style().standardIcon(self.style().StandardPixmap.SP_DialogApplyButton))
        else:
            self.action_btn.setEnabled(False)

        action_layout.addWidget(self.action_btn)
        action_layout.addStretch()

        if btn_type != "disabled":
            self._portable_label = QLabel("🔗 PORTABLE")
            action_layout.addWidget(self._portable_label)
        else:
            self._portable_label = None

        content_layout.addLayout(action_layout)
        main_layout.addLayout(content_layout)


    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.pos()

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        if not hasattr(self, 'drag_start_position'):
            return
        if (event.pos() - self.drag_start_position).manhattanLength() < 10:
            return
            
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(self.card_id)
        drag.setMimeData(mime_data)
        
        pixmap = self.grab()
        drag.setPixmap(pixmap.scaled(300, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        drag.setHotSpot(event.pos())
        
        drag.exec(Qt.DropAction.MoveAction)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText() and event.source() != self:
            event.acceptProposedAction()

    def dropEvent(self, event):
        source_id = event.mimeData().text()
        target_id = self.card_id
        if hasattr(self.window(), "swap_cards"):
            self.window().swap_cards(source_id, target_id)
        event.acceptProposedAction()

    def apply_styles(self, styles: dict):
        if self._is_disabled:
            self.setStyleSheet(styles["card_disabled"])
        else:
            self.setStyleSheet(styles["card_normal"])
        self._title_label.setStyleSheet(styles["card_title"])
        self._subtitle_label.setStyleSheet(styles["card_subtitle"])
        if self._portable_label:
            self._portable_label.setStyleSheet(styles["portable"])
        if self.btn_type == "install":
            self.action_btn.setStyleSheet(styles["btn_install"])
        elif self.btn_type == "open":
            self.action_btn.setStyleSheet(styles["btn_open"])
        else:
            self.action_btn.setStyleSheet(styles["btn_disabled"])


# ─────────────────────────────────────────────────────────────────────
#  HubWindow
# ─────────────────────────────────────────────────────────────────────
class HubWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Media Hub")
        self.resize(900, 800)
        self._tm = ThemeManager.instance()
        self.init_ui()
        self._apply_theme()
        
        # Start update check in background
        self.update_thread = CheckUpdateThread(self)
        self.update_thread.update_available.connect(self.show_update_dialog)
        self.update_thread.start()

    def show_update_dialog(self, version, description, download_url, size_mb):
        dialog = UpdateDialog(version, description, download_url, size_mb, self)
        dialog.exec()


    def swap_cards(self, id1, id2):
        import json
        idx1 = next(i for i, c in enumerate(self._all_cards) if c.card_id == id1)
        idx2 = next(i for i, c in enumerate(self._all_cards) if c.card_id == id2)
        
        self._all_cards[idx1], self._all_cards[idx2] = self._all_cards[idx2], self._all_cards[idx1]
        
        for card in self._all_cards:
            self.grid_layout.removeWidget(card)
            
        cols = 2
        for i, card in enumerate(self._all_cards):
            r = i // cols
            c = i % cols
            self.grid_layout.addWidget(card, r, c)
            
        self.save_layout()
        
    def save_layout(self):
        import json, os
        order = [c.card_id for c in self._all_cards]
        appdata = os.environ.get('ProgramData', '')
        if appdata:
            path = os.path.join(appdata, "MediaHub", "settings.json")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w') as f:
                json.dump({"hub_order": order}, f)

    def init_ui(self):
        import json, os
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(40, 30, 40, 40)
        main_layout.setSpacing(20)

        header_layout = QHBoxLayout()
        self.title_label = QLabel("MEDIA HUB")
        self.title_label.setObjectName("hubTitle")
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()

        self.toggle_btn = QPushButton()
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.setFixedHeight(38)
        self.toggle_btn.clicked.connect(self._toggle_dark_mode)
        header_layout.addWidget(self.toggle_btn)

        main_layout.addLayout(header_layout)

        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(20)

        self.media_card = AppCard(card_id="media", title="MULTIMEDIA CONVERTER", subtitle="Video, Audio, and Batch Processing", icon_file="media.png", btn_text=" ABRIR", btn_type="open")
        self.media_card.action_btn.clicked.connect(self.launch_media_converter)
        
        self.docs_card = AppCard(card_id="docs", title="DOCUMENT CONVERTER", subtitle="PDF, Word, Excel, and OCR", icon_file="docs.png", btn_text=" ABRIR", btn_type="open")
        self.docs_card.action_btn.clicked.connect(self.launch_document_converter)
        
        self.quality_card = AppCard(card_id="quality", title="QUALITY ENHANCER", subtitle="AI Image Super Resolution", icon_file="quality.webp", btn_text=" ABRIR", btn_type="open")
        self.quality_card.action_btn.clicked.connect(self.launch_quality_enhancer)
        
        self.bg_card = AppCard(card_id="bg", title="BACKGROUND ERASER", subtitle="AI-Powered Background Removal", icon_file="backgrounderaser.webp", btn_text=" ABRIR", btn_type="open")
        self.bg_card.action_btn.clicked.connect(self.launch_bg_remover)
        
        self.link_card = AppCard(card_id="link", title="LINK CONVERTER", subtitle="YouTube, TikTok, Instagram & more", icon_file="link_converter.webp", btn_text=" ABRIR", btn_type="open")
        self.link_card.action_btn.clicked.connect(self.launch_link_converter)
        
        self.subtitle_card = AppCard(card_id="subtitle", title="SUBTITLE GENERATOR", subtitle="Whisper AI auto-transcription", icon_file="subtitle.png", btn_text=" ABRIR", btn_type="open")
        self.subtitle_card.action_btn.clicked.connect(self.launch_subtitle_generator)
        
        self.watermark_card = AppCard(card_id="watermark", title="BULK WATERMARK", subtitle="Apply logo to images and videos", icon_file="bulkwatermark.webp", btn_text=" ABRIR", btn_type="open")
        self.watermark_card.action_btn.clicked.connect(self.launch_watermark_tool)

        self._card_dict = {
            "media": self.media_card, "docs": self.docs_card, "quality": self.quality_card,
            "bg": self.bg_card, "link": self.link_card, "subtitle": self.subtitle_card, "watermark": self.watermark_card
        }
        
        order = ["media", "docs", "quality", "bg", "link", "subtitle", "watermark"]
        try:
            appdata = os.environ.get('ProgramData', '')
            path = os.path.join(appdata, "MediaHub", "settings.json")
            with open(path, 'r') as f:
                saved = json.load(f).get("hub_order", [])
                if len(saved) == len(order) and all(k in self._card_dict for k in saved):
                    order = saved
        except:
            pass
            
        self._all_cards = [self._card_dict[k] for k in order]
        
        cols = 2
        for i, card in enumerate(self._all_cards):
            r = i // cols
            c = i % cols
            self.grid_layout.addWidget(card, r, c)
            
        main_layout.addLayout(self.grid_layout)
    # ── Theme ─────────────────────────────────────────────────────────────────
    def _toggle_dark_mode(self):
        self._tm.toggle()
        self._apply_theme()

    def _apply_theme(self):
        styles = self._tm.hub_styles()
        self.setStyleSheet(styles["window"])
        self.title_label.setStyleSheet(styles["title"])
        self.toggle_btn.setStyleSheet(styles["toggle_btn"])
        self.toggle_btn.setText("☀️  Modo Claro" if self._tm.is_dark else "🌙  Modo Oscuro")
        for card in self._all_cards:
            card.apply_styles(styles)

    # ── Launchers ─────────────────────────────────────────────────────────────
    def launch_media_converter(self):
        from apps.media_converter.ui.index import LauncherWindow
        self.media_window = LauncherWindow()
        self.media_window.show()
        self.close()

    def launch_document_converter(self):
        from apps.document_converter.ui.index import DocumentLauncherWindow
        self.doc_window = DocumentLauncherWindow()
        self.doc_window.show()
        self.close()

    def launch_quality_enhancer(self):
        from apps.media_converter.ui.quality_enhancer import QualityEnhancerUI
        self.quality_window = QualityEnhancerUI()
        self.quality_window.show()
        self.close()

    def launch_link_converter(self):
        from apps.link_converter.link_converter_window import LinkConverterWindow
        self.link_window = LinkConverterWindow()
        self.link_window.show()
        self.close()

    def launch_bg_remover(self):
        from apps.media_converter.ui.bg_remover import BackgroundRemoverUI
        self.bg_window = BackgroundRemoverUI()
        self.bg_window.show()
        self.close()

    def launch_subtitle_generator(self):
        from apps.media_converter.ui.subtitle_generator import SubtitleGeneratorUI
        self.sub_window = SubtitleGeneratorUI()
        self.sub_window.show()
        self.close()

    def launch_watermark_tool(self):
        from apps.media_converter.ui.watermark_tool import WatermarkToolUI
        self.wm_window = WatermarkToolUI()
        self.wm_window.show()
        self.close()
