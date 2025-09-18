from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGroupBox
from PySide6.QtGui import QFont


class StatusPanel(QWidget):
    def __init__(self, parking_lot, parent=None, font_size=16):
        super().__init__(parent)
        self.parking_lot = parking_lot
        self.group = QGroupBox("停车场状态")
        layout = QVBoxLayout(self.group)

        font = QFont()
        font.setPointSize(font_size)

        self.total_spaces_label = QLabel("")
        self.available_spaces_label = QLabel("")
        # 新增：显示识别后端和摄像头信息
        self.provider_label = QLabel("")
        self.camera_info_label = QLabel("")
        self.total_spaces_label.setFont(font)
        self.available_spaces_label.setFont(font)
        self.provider_label.setFont(font)
        self.camera_info_label.setFont(font)

        layout.addWidget(self.total_spaces_label)
        layout.addWidget(self.available_spaces_label)
        layout.addWidget(self.provider_label)
        layout.addWidget(self.camera_info_label)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.group)

        self.update()

    def update(self):
        status = self.parking_lot.get_parking_status()
        self.total_spaces_label.setText(f"总车位：{status['total_spaces']}")
        self.available_spaces_label.setText(f"可用车位：{status['available_spaces']}")
        # provider 与摄像头信息由外部调用者通过 set 方法更新

    def set_provider(self, provider_name: str):
        try:
            self.provider_label.setText(f"识别后端：{provider_name}")
        except Exception:
            pass

    def set_camera_info(self, info: str):
        try:
            self.camera_info_label.setText(f"摄像头：{info}")
        except Exception:
            pass
