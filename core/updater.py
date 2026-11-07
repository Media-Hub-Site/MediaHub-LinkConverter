import os
import sys
import re
import requests
import subprocess
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextBrowser, QProgressBar, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QFont

from core.config import APP_VERSION, GITHUB_REPO

API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


def extract_version_from_release(data: dict) -> str:
    """
    Extrae el número de versión del release de GitHub.
    Primero intenta leerlo desde el nombre de los assets (ej: 'MediaHub_v1.4_Setup.exe'),
    luego desde el tag_name como respaldo.
    Devuelve la versión sin 'v' (ej: '1.4').
    """
    # Buscar en los assets: MediaHub_v{VERSION}_Setup.exe
    for asset in data.get("assets", []):
        asset_name = asset.get("name", "")
        match = re.search(r'MediaHub_v([\d.]+)', asset_name, re.IGNORECASE)
        if match:
            return match.group(1)

    # Respaldo: usar el tag_name del release
    tag = data.get("tag_name", "")
    match = re.search(r'v?([\d.]+)', tag)
    if match:
        return match.group(1)

    return ""

class DownloadThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, download_url, save_path):
        super().__init__()
        self.download_url = download_url
        self.save_path = save_path
        self._is_cancelled = False

    def run(self):
        try:
            response = requests.get(self.download_url, stream=True, timeout=10)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            block_size = 8192
            downloaded_size = 0

            with open(self.save_path, 'wb') as file:
                for data in response.iter_content(block_size):
                    if self._is_cancelled:
                        return
                    file.write(data)
                    downloaded_size += len(data)
                    if total_size > 0:
                        percentage = int((downloaded_size / total_size) * 100)
                        self.progress.emit(percentage)
            
            self.finished.emit(self.save_path)
        except Exception as e:
            self.error.emit(str(e))

    def cancel(self):
        self._is_cancelled = True


class UpdateDialog(QDialog):
    def __init__(self, version, description, download_url, size_mb, parent=None):
        super().__init__(parent)
        self.version = version
        self.download_url = download_url
        self.size_mb = size_mb
        self.download_thread = None

        self.setWindowTitle("Actualización Disponible")
        self.setFixedSize(500, 400)
        
        self.init_ui(description)

    def init_ui(self, description):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Title
        title_label = QLabel(f"¡Actualización {self.version} disponible!")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        title_label.setFont(font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Description
        self.desc_browser = QTextBrowser()
        self.desc_browser.setMarkdown(description)
        self.desc_browser.setOpenExternalLinks(True)
        layout.addWidget(self.desc_browser)

        # Size info
        size_label = QLabel(f"Peso de la actualización: {self.size_mb:.2f} MB")
        font_small = QFont()
        font_small.setPointSize(10)
        size_label.setFont(font_small)
        size_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(size_label)

        # Progress bar (hidden initially)
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Buttons
        self.btn_layout = QHBoxLayout()
        
        self.btn_update = QPushButton("Actualizar ahora")
        self.btn_update.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_update.clicked.connect(self.start_update)
        
        self.btn_skip = QPushButton("Quedarme con mi versión")
        self.btn_skip.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_skip.clicked.connect(self.reject)

        self.btn_layout.addWidget(self.btn_update)
        self.btn_layout.addWidget(self.btn_skip)
        
        layout.addLayout(self.btn_layout)

    def start_update(self):
        self.btn_update.setEnabled(False)
        self.btn_skip.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.desc_browser.setEnabled(False)

        # Create temp file path
        filename = f"MediaHub_Update_{self.version}.exe"
        temp_dir = os.environ.get("TEMP", os.path.expanduser("~"))
        save_path = os.path.join(temp_dir, filename)

        self.download_thread = DownloadThread(self.download_url, save_path)
        self.download_thread.progress.connect(self.progress_bar.setValue)
        self.download_thread.finished.connect(self.on_download_finished)
        self.download_thread.error.connect(self.on_download_error)
        self.download_thread.start()

    def on_download_finished(self, save_path):
        self.progress_bar.setValue(100)
        QMessageBox.information(self, "Descarga Completa", "La actualización se ha descargado. La aplicación se cerrará para instalar la nueva versión.")
        
        # Execute the installer and exit
        try:
            os.startfile(save_path)
            QApplication.quit()
            sys.exit(0)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo ejecutar el instalador: {e}\n\nPuedes ejecutarlo manualmente desde:\n{save_path}")
            self.accept()

    def on_download_error(self, error_msg):
        QMessageBox.critical(self, "Error de Descarga", f"Ocurrió un error al descargar la actualización:\n{error_msg}")
        self.btn_update.setEnabled(True)
        self.btn_skip.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.desc_browser.setEnabled(True)

    def closeEvent(self, event):
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.cancel()
            self.download_thread.wait()
        super().closeEvent(event)


class CheckUpdateThread(QThread):
    update_available = pyqtSignal(str, str, str, float)

    def run(self):
        try:
            response = requests.get(API_URL, timeout=5)
            response.raise_for_status()
            data = response.json()

            lat_v = extract_version_from_release(data)
            if not lat_v:
                return

            curr_v = APP_VERSION.lstrip('v')

            curr_parts = [int(x) for x in curr_v.split('.') if x.isdigit()]
            lat_parts = [int(x) for x in lat_v.split('.') if x.isdigit()]

            if not curr_parts or not lat_parts:
                is_newer = (curr_v != lat_v)
            else:
                is_newer = False
                is_older = False
                for c, l in zip(curr_parts, lat_parts):
                    if l > c:
                        is_newer = True
                        break
                    elif l < c:
                        is_older = True
                        break

                if len(lat_parts) > len(curr_parts) and not is_newer and not is_older:
                    is_newer = True

            if is_newer:
                description = data.get("body", "No hay descripción disponible.")
                assets = data.get("assets", [])
                download_url = None
                size_mb = 0

                for asset in assets:
                    if asset.get("name", "").endswith(".exe"):
                        download_url = asset.get("browser_download_url")
                        size_mb = asset.get("size", 0) / (1024 * 1024)
                        break

                if download_url:
                    self.update_available.emit(lat_v, description, download_url, size_mb)

        except Exception as e:
            print(f"Update check failed: {e}")

def check_for_updates(parent=None):
    """
    Checks GitHub for newer releases.
    Extrae la versión desde el nombre del asset (ej: 'MediaHub_v1.4_Setup.exe')
    para comparar correctamente con APP_VERSION.
    """
    try:
        response = requests.get(API_URL, timeout=5)
        response.raise_for_status()
        data = response.json()

        lat_v = extract_version_from_release(data)
        if not lat_v:
            return

        curr_v = APP_VERSION.lstrip('v')

        curr_parts = [int(x) for x in curr_v.split('.') if x.isdigit()]
        lat_parts = [int(x) for x in lat_v.split('.') if x.isdigit()]

        if not curr_parts or not lat_parts:
            is_newer = (curr_v != lat_v)
        else:
            is_newer = False
            is_older = False
            for c, l in zip(curr_parts, lat_parts):
                if l > c:
                    is_newer = True
                    break
                elif l < c:
                    is_older = True
                    break

            if len(lat_parts) > len(curr_parts) and not is_newer and not is_older:
                is_newer = True

        if is_newer:
            description = data.get("body", "No hay descripción disponible.")
            assets = data.get("assets", [])
            download_url = None
            size_mb = 0

            for asset in assets:
                if asset.get("name", "").endswith(".exe"):
                    download_url = asset.get("browser_download_url")
                    size_mb = asset.get("size", 0) / (1024 * 1024)
                    break

            if download_url:
                dialog = UpdateDialog(lat_v, description, download_url, size_mb, parent)
                dialog.exec()

    except Exception as e:
        print(f"Update check failed: {e}")

