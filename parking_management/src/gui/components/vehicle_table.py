from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem
from PySide6.QtGui import QFont
from PySide6.QtCore import Signal


class VehicleTable(QWidget):
    # signal emitted when a plate is selected (double-click)
    plate_selected = Signal(str)

    def __init__(self, parking_lot, parent=None):
        super().__init__(parent)
        self.parking_lot = parking_lot

        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(['车牌号', '入场时间'])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        # 双击选择行以向外发出车牌号
        self.table.itemDoubleClicked.connect(self._on_item_double_clicked)

    def refresh(self):
        current_vehicles = self.parking_lot.get_current_vehicles()
        self.table.setRowCount(len(current_vehicles))
        for i, (_, vehicle) in enumerate(current_vehicles.iterrows()):
            self.table.setItem(i, 0, QTableWidgetItem(vehicle['License Plate']))
            self.table.setItem(i, 1, QTableWidgetItem(str(vehicle['Entry Time'])))

    def _on_item_double_clicked(self, item):
        try:
            row = item.row()
            plate_item = self.table.item(row, 0)
            if plate_item:
                plate = plate_item.text()
                # 发射信号
                try:
                    self.plate_selected.emit(plate)
                except Exception:
                    # 兼容性：如果外部不是信号/槽机制，直接回调留待上层连接
                    pass
        except Exception:
            pass
