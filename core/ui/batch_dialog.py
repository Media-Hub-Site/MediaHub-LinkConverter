import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QLabel,
    QListWidgetItem, QAbstractItemView, QCheckBox
)
from PyQt6.QtCore import Qt
from core.ui.hub_theme import HUB_WINDOW_STYLE

class BatchDialog(QDialog):
    def __init__(self, batch_files, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Administrar Archivos en Lote")
        self.resize(500, 420)
        self.setStyleSheet(HUB_WINDOW_STYLE)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        
        self.original_files = list(batch_files)
        self.current_files = list(batch_files)
        
        self._updating_checkbox = False
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        # Label de conteo (dinámico)
        self.count_label = QLabel()
        self.count_label.setStyleSheet("color: white; font-weight: bold; font-size: 12pt;")
        self._update_count_label()
        layout.addWidget(self.count_label)
        
        # Checkbox "Seleccionar todos"
        self.select_all_check = QCheckBox("Seleccionar todos")
        self.select_all_check.setStyleSheet("""
            QCheckBox {
                color: #ccc;
                font-size: 10pt;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 2px solid #666;
                background-color: #2b2b36;
            }
            QCheckBox::indicator:checked {
                background-color: #5d5dff;
                border-color: #5d5dff;
            }
            QCheckBox::indicator:hover {
                border-color: #5d5dff;
            }
        """)
        self.select_all_check.stateChanged.connect(self.on_select_all_changed)
        layout.addWidget(self.select_all_check)
        
        # List Widget
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #2b2b36;
                color: white;
                border: 1px solid #444;
                border-radius: 8px;
                padding: 5px;
                font-size: 11pt;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #3a3a46;
            }
            QListWidget::item:selected {
                background-color: #5d5dff;
                border-radius: 4px;
            }
        """)
        self.list_widget.itemSelectionChanged.connect(self.on_selection_changed)
        self.update_list()
        layout.addWidget(self.list_widget)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.remove_btn = QPushButton("Quitar Seleccionados")
        self.remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff4d4d;
                color: white;
                border-radius: 6px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #ff6666; }
            QPushButton:pressed { background-color: #cc0000; }
        """)
        self.remove_btn.clicked.connect(self.remove_selected)
        btn_layout.addWidget(self.remove_btn)
        
        btn_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #444;
                color: white;
                border-radius: 6px;
                padding: 10px;
            }
            QPushButton:hover { background-color: #555; }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        self.accept_btn = QPushButton("Guardar Cambios")
        self.accept_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.accept_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 6px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        self.accept_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.accept_btn)
        
        layout.addLayout(btn_layout)

    def _update_count_label(self):
        n = len(self.current_files)
        self.count_label.setText(f"Archivos listos para procesar ({n}):")

    def update_list(self):
        self.list_widget.clear()
        for f in self.current_files:
            item = QListWidgetItem(os.path.basename(f))
            item.setData(Qt.ItemDataRole.UserRole, f)
            self.list_widget.addItem(item)
        self._update_count_label()

    def on_select_all_changed(self, state):
        if self._updating_checkbox:
            return
        if state == Qt.CheckState.Checked.value:
            self.list_widget.selectAll()
        else:
            self.list_widget.clearSelection()

    def on_selection_changed(self):
        """Sincroniza el estado del checkbox con la selección actual."""
        self._updating_checkbox = True
        total = self.list_widget.count()
        selected = len(self.list_widget.selectedItems())
        if selected == 0:
            self.select_all_check.setCheckState(Qt.CheckState.Unchecked)
        elif selected == total:
            self.select_all_check.setCheckState(Qt.CheckState.Checked)
        else:
            self.select_all_check.setCheckState(Qt.CheckState.PartiallyChecked)
        self._updating_checkbox = False

    def remove_selected(self):
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            return
            
        for item in selected_items:
            file_path = item.data(Qt.ItemDataRole.UserRole)
            if file_path in self.current_files:
                self.current_files.remove(file_path)
                
        self.update_list()
        # Resetear checkbox después de quitar
        self._updating_checkbox = True
        self.select_all_check.setCheckState(Qt.CheckState.Unchecked)
        self._updating_checkbox = False
        
    def get_files(self):
        return self.current_files
