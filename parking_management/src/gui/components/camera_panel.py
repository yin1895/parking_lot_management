from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QGroupBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QImage
import cv2


class CameraPanel(QWidget):
    def __init__(self, plate_recognizer, logger=None, parent=None):
        super().__init__(parent)
        self.plate_recognizer = plate_recognizer
        self.logger = logger
        self.current_index = None

        self.group = QGroupBox('车牌识别')
        layout = QVBoxLayout(self.group)

        self.camera_label = QLabel()
        self.camera_label.setMinimumSize(640, 480)
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setStyleSheet('border: 2px solid #cccccc; border-radius: 4px; background-color: #f5f5f5;')
        layout.addWidget(self.camera_label)

        self.camera_button = None
        if self.plate_recognizer:
            self.camera_button = QPushButton('开启摄像头')
            layout.addWidget(self.camera_button)
        else:
            disabled = QLabel('车牌识别未初始化，摄像头功能禁用')
            disabled.setStyleSheet('color: #a00;')
            layout.addWidget(disabled)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.group)
        # keep last frame for smoother UX
        self._last_frame = None

    def set_pixmap(self, frame):
        # frame is expected to be a BGR numpy array
        try:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        except Exception:
            return
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        image = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pix = QPixmap.fromImage(image).scaled(self.camera_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.camera_label.setPixmap(pix)
        # store last frame (BGR)
        try:
            self._last_frame = frame.copy()
        except Exception:
            self._last_frame = None

    def start_camera(self, index=0):
        """Start camera capture for given index. Returns True on success."""
        try:
            # Try to open the requested camera first. Only if successful,
            # swap it in for the plate_recognizer.camera. This prevents a
            # brief period where no camera is opened while switching.
            cap = cv2.VideoCapture(int(index))
            if not cap or not cap.isOpened():
                try:
                    cap.release()
                except Exception:
                    pass
                return False

            # At this point the new camera is available; swap safely
            if self.plate_recognizer:
                try:
                    old = getattr(self.plate_recognizer, 'camera', None)
                    self.plate_recognizer.camera = cap
                    self.current_index = int(index)
                    # release old after successful swap
                    if old is not None:
                        try:
                            old.release()
                        except Exception:
                            pass
                    return True
                except Exception:
                    try:
                        cap.release()
                    except Exception:
                        pass
                    return False
            else:
                try:
                    cap.release()
                except Exception:
                    pass
                return False
        except Exception:
            return False

    def stop_camera(self):
        try:
            if self.plate_recognizer and getattr(self.plate_recognizer, 'camera', None) is not None:
                try:
                    # release physical camera but retain last frame for display
                    try:
                        self.plate_recognizer.camera.release()
                    except Exception:
                        pass
                except Exception:
                    pass
                self.plate_recognizer.camera = None
            self.current_index = None
            # do not clear the label here; keep last_frame visible until explicitly cleared
            # if _last_frame exists, ensure it's still shown
            try:
                if self._last_frame is not None:
                    self.set_pixmap(self._last_frame)
            except Exception:
                pass
        except Exception:
            pass
