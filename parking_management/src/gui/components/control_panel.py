from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QGroupBox, QComboBox
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, Signal
import cv2
from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QPixmap
import os


class ControlPanel(QWidget):
    # 信号: 请求开始摄像头(index), 请求上传文件(path)
    request_camera_start = Signal(int)
    request_upload = Signal(str)
    def __init__(self, parent_window, logger=None, parent=None):
        super().__init__(parent)
        self.parent_window = parent_window
        self.logger = logger

        panel = QGroupBox('操作')
        layout = QVBoxLayout(panel)

        self.plate_input = QLineEdit()
        self.plate_input.setPlaceholderText('请输入车牌号或使用摄像头识别')
        self.plate_input.setMinimumHeight(40)
        self.plate_input.setFont(QFont('Arial', 12))
        # accessibility
        self.plate_input.setAccessibleName('plate_input')
        layout.addWidget(self.plate_input)

        # 摄像头选择与上传图片
        camera_layout = QHBoxLayout()
        self.camera_selector = QComboBox()
        # 自动探测常见摄像头索引（0..4），仅添加可打开的设备
        found = False
        for i in range(0, 5):
            try:
                cap = cv2.VideoCapture(i)
                if cap is not None and cap.isOpened():
                    self.camera_selector.addItem(f"摄像头 {i}", i)
                    found = True
                    try:
                        cap.release()
                    except Exception:
                        pass
                else:
                    try:
                        cap.release()
                    except Exception:
                        pass
            except Exception:
                pass
        if not found:
            # 退回到默认 0..3
            for i in range(0, 4):
                self.camera_selector.addItem(f"摄像头 {i}", i)
        self.upload_button = QPushButton('上传图片识别')
        camera_layout.addWidget(self.camera_selector)
        camera_layout.addWidget(self.upload_button)
        layout.addLayout(camera_layout)

        # 拖放预览
        self.preview_label = QLabel()
        self.preview_label.setFixedSize(200, 120)
        self.preview_label.setStyleSheet('border: 1px solid #ddd; background-color: #fff;')
        layout.addWidget(self.preview_label)

        # 启用拖放
        self.setAcceptDrops(True)

        button_layout = QHBoxLayout()
        self.entry_button = QPushButton('车辆入场')
        self.exit_button = QPushButton('车辆出场')
        button_layout.addWidget(self.entry_button)
        button_layout.addWidget(self.exit_button)
        layout.addLayout(button_layout)

        self.admin_button = QPushButton('管理员入口')
        # 快捷键：Ctrl+E 入场，Ctrl+X 出场
        self.entry_button.setShortcut('Ctrl+E')
        self.exit_button.setShortcut('Ctrl+X')
        self.admin_button.setShortcut('Ctrl+A')
        layout.addWidget(self.admin_button)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(panel)

        # connect signals externally from MainWindow
        # 内部信号连接
        self.upload_button.clicked.connect(self._on_upload_clicked)
        self.camera_selector.currentIndexChanged.connect(self._on_camera_changed)

    def _on_camera_changed(self, idx):
        try:
            cam_index = self.camera_selector.itemData(idx)
            if cam_index is None:
                cam_index = idx
            self.request_camera_start.emit(int(cam_index))
        except Exception:
            pass

    def _on_upload_clicked(self):
        # 通过 request_upload 发射空字符串，MainWindow 将打开 QFileDialog 完成实际选择
        self.request_upload.emit("")

    def set_selected_camera(self, index: int):
        """Set the camera selector to the item with given index (if present)."""
        try:
            # find item with matching data
            for i in range(self.camera_selector.count()):
                try:
                    data = self.camera_selector.itemData(i)
                    if data == index:
                        # avoid emitting currentIndexChanged when setting programmatically
                        try:
                            self.camera_selector.blockSignals(True)
                            self.camera_selector.setCurrentIndex(i)
                        finally:
                            try:
                                self.camera_selector.blockSignals(False)
                            except Exception:
                                pass
                        return
                except Exception:
                    pass
            # fallback: if index within range, set by index
            if 0 <= index < self.camera_selector.count():
                try:
                    self.camera_selector.blockSignals(True)
                    self.camera_selector.setCurrentIndex(index)
                finally:
                    try:
                        self.camera_selector.blockSignals(False)
                    except Exception:
                        pass
        except Exception:
            pass

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].toLocalFile():
                path = urls[0].toLocalFile()
                if os.path.splitext(path)[1].lower() in ('.png', '.jpg', '.jpeg', '.bmp'):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event):
        try:
            urls = event.mimeData().urls()
            if not urls:
                return
            path = urls[0].toLocalFile()
            if not path:
                return
            if os.path.splitext(path)[1].lower() not in ('.png', '.jpg', '.jpeg', '.bmp'):
                return
            # 更新预览
            try:
                pix = QPixmap(path).scaled(self.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.preview_label.setPixmap(pix)
            except Exception:
                pass
            # 发射上传信号并把路径传给 MainWindow
            self.request_upload.emit(path)
        except Exception:
            pass
