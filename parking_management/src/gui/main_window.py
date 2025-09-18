from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QMessageBox, QDialog, QFormLayout, QLineEdit, QPushButton)
from PySide6.QtCore import Qt, QTimer, QSize, QTime
from PySide6.QtGui import QImage, QPixmap, QFont, QIcon
import sys
import pyttsx3
import os
import threading
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.core.parking_lot import ParkingLot
from src.utils.config import Config
from src.utils.plate_recognizer import PlateRecognizer
from src.utils.logger import get_logger
import cv2
from collections import Counter
from .admin_panel import AdminPanel
from .login_dialog import LoginDialog
from .components.status_panel import StatusPanel
from .components.camera_panel import CameraPanel
from .components.vehicle_table import VehicleTable
from .components.control_panel import ControlPanel
from PySide6.QtWidgets import QFileDialog
from PySide6.QtCore import QTimer
from .workers import RecognizeWorker

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.logger = get_logger('MainWindow')
        self.logger.info('MainWindow 初始化')
        # track background workers for cleanup on exit
        self._workers = []
        self.parking_lot = ParkingLot()
        # ensure camera_active exists even if PlateRecognizer init fails
        self.camera_active = False
        try:
            # 从配置中获取模型路径
            model_paths = self.config.get_model_paths()
            detect_model_path = model_paths['detect_model']
            rec_model_path = model_paths['rec_model']
            self.plate_recognizer = PlateRecognizer(detect_model_path, rec_model_path)
            self.camera_active = False  # 添加摄像头状态标志
        except Exception as e:
            try:
                self.logger.exception('车牌识别模块初始化失败')
            except Exception:
                pass
            QMessageBox.warning(self, "初始化警告", f"车牌识别模块初始化失败: {str(e)}\n将禁用车牌识别功能")
            self.plate_recognizer = None
            
        self.setup_ui()
        
        # 设置定时器更新显示
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_display)
        try:
            self.timer.start(int(self.config.get('gui', 'refresh_rate') or 1000))
        except Exception:
            self.timer.start(1000)

        # 添加用于显示摄像头画面的定时器
        self.camera_timer = QTimer()
        self.camera_timer.timeout.connect(self.update_camera)
        
        self.recognized_plates = []  # 存储识别到的车牌号
        self.recognition_timer = QTimer()  # 用于计时5秒
        self.recognition_timer.timeout.connect(self.finalize_recognition)
        self.start_time = None
        self.logger.debug('UI 组件初始化完成，定时器已配置')

        # 在定时器初始化完成后尝试恢复并启动上次使用的摄像头（容错）
        try:
            last_idx = self.config.get('data', 'last_camera_index')
            if last_idx is not None:
                try:
                    # 恢复选择（UI 反映）
                    self.control_panel.set_selected_camera(int(last_idx))
                except Exception:
                    pass
                # 仅当 camera_timer 已初始化时才尝试自动启动摄像头
                try:
                    if getattr(self, 'camera_timer', None) is not None:
                        try:
                            self._on_request_camera_start(int(last_idx))
                        except Exception:
                            pass
                except Exception:
                    pass
        except Exception:
            pass


    def setup_ui(self):
        """设置UI界面"""
        # 设置窗口基本属性
        # 设置窗口基本属性
        try:
            title = self.config.get('gui', 'window_title') or "智能停车场管理系统"
            width = int(self.config.get('gui', 'window_size').get('width', 1200))
            height = int(self.config.get('gui', 'window_size').get('height', 800))
        except Exception:
            title = "智能停车场管理系统"
            width, height = 1200, 800
        self.setWindowTitle(title)
        self.setMinimumSize(width, height)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 创建布局
        main_layout = QHBoxLayout(central_widget)

        # 左侧：状态 + 控件
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        self.status_panel = StatusPanel(self.parking_lot)
        self.control_panel = ControlPanel(self, logger=self.logger)
        left_layout.addWidget(self.status_panel)
        left_layout.addWidget(self.control_panel)
        left_layout.addStretch()
        main_layout.addWidget(left_container, 1)

        # 右侧：摄像头 + 车辆表
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        self.camera_panel = CameraPanel(self.plate_recognizer, logger=self.logger)
        self.vehicle_table = VehicleTable(self.parking_lot)
        right_layout.addWidget(self.camera_panel)
        right_layout.addWidget(self.vehicle_table)
        main_layout.addWidget(right_container, 2)

        # Wire up signals
        if self.camera_panel.camera_button:
            self.camera_panel.camera_button.clicked.connect(self.toggle_camera)
        self.control_panel.entry_button.clicked.connect(self.handle_entry)
        self.control_panel.exit_button.clicked.connect(self.handle_exit)
        self.control_panel.admin_button.clicked.connect(self.show_admin_login)
        # synchronize plate input
        self.plate_input = self.control_panel.plate_input
        # 当车辆表格双击行时，将车牌号填入输入框
        try:
            self.vehicle_table.plate_selected.connect(lambda p: self.plate_input.setText(p))
        except Exception:
            # 兼容性：如果 vehicle_table 未定义 signal，忽略
            try:
                pass
            except Exception:
                pass

        # 连接摄像头选择与上传信号
        try:
            self.control_panel.request_camera_start.connect(self._on_request_camera_start)
            self.control_panel.request_upload.connect(self._on_request_upload)
        except Exception:
            pass

        # 恢复上次使用的摄像头索引（如果配置中存在），仅恢复选择，不在此处启动摄像头
        try:
            last_idx = self.config.get('data', 'last_camera_index')
            if last_idx is not None:
                try:
                    self.control_panel.set_selected_camera(int(last_idx))
                except Exception:
                    pass
        except Exception:
            pass

        # 将识别后端信息展示到状态面板（如果可用）
        try:
            if getattr(self, 'plate_recognizer', None) is not None:
                prov = getattr(self.plate_recognizer, 'detect_provider', None) or getattr(self.plate_recognizer, 'rec_provider', None)
                if prov:
                    try:
                        self.status_panel.set_provider(prov)
                    except Exception:
                        pass
        except Exception:
            pass

    # old panel creation methods removed; replaced with modular components

    def update_camera(self):
        """更新摄像头画面"""
        if not (self.plate_recognizer and self.camera_active):
            return

        try:
            ret, frame = self.plate_recognizer.camera.read()
            if not ret or frame is None:
                return

            # 使用 CameraPanel 提供的方法显示画面
            try:
                self.camera_panel.set_pixmap(frame)
            except Exception:
                # 退回到直接设置 label（容错）
                try:
                    rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    h, w, ch = rgb_image.shape
                    bytes_per_line = ch * w
                    qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
                    scaled_pixmap = QPixmap.fromImage(qt_image).scaled(
                        self.camera_panel.camera_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.camera_panel.camera_label.setPixmap(scaled_pixmap)
                except Exception:
                    pass

            # 识别车牌（异常捕获）
            outputs = None
            try:
                outputs = self.plate_recognizer.detect_plate(frame)
            except Exception:
                try:
                    self.logger.exception('detect_plate 调用失败')
                except Exception:
                    pass

            # safe check for numpy arrays or lists
            has_outputs = False
            try:
                if outputs is not None:
                    if hasattr(outputs, 'size'):
                        has_outputs = outputs.size > 0
                    else:
                        has_outputs = len(outputs) > 0
            except Exception:
                has_outputs = False

            if has_outputs:
                for output in outputs:
                    try:
                        rect = output[:4].astype(int)
                        plate_image = frame[rect[1]:rect[3], rect[0]:rect[2]]
                        plate_no, _ = self.plate_recognizer.recognize_text(plate_image)
                        if plate_no:
                            self.recognized_plates.append(plate_no)
                            self.logger.debug(f'detect_plate 识别到车牌: {plate_no}')
                    except Exception:
                        try:
                            self.logger.exception('识别单个车牌失败')
                        except Exception:
                            pass
        except Exception:
            try:
                self.logger.exception('update_camera 出现异常')
            except Exception:
                pass

    def toggle_camera(self):
        """切换摄像头状态"""
        if not self.plate_recognizer:
            return
        try:
            if not self.camera_active:
                # 初始化摄像头
                # 使用当前控制面板选择的摄像头索引，回退到 0
                try:
                    idx_data = self.control_panel.camera_selector.currentData()
                    start_idx = int(idx_data) if idx_data is not None else 0
                except Exception:
                    start_idx = 0
                ok = self.camera_panel.start_camera(start_idx)
                if not ok:
                    QMessageBox.warning(self, "错误", "无法打开摄像头")
                    self.logger.warning('无法打开摄像头')
                    return

                # 开启摄像头
                self.camera_active = True
                self.logger.info('摄像头已开启')
                # 保存当前摄像头索引到配置（如果可用）
                try:
                    idx = getattr(self.camera_panel, 'current_index', None)
                    if idx is not None:
                        try:
                            self.config.set('data', 'last_camera_index', int(idx))
                        except Exception:
                            pass
                except Exception:
                    pass
                if getattr(self.camera_panel, 'camera_button', None):
                    try:
                        self.camera_panel.camera_button.setText("关闭摄像头")
                    except Exception:
                        pass
                self.camera_timer.start(30)  # 约30FPS
                self.recognition_timer.start(5000)  # 5秒计时器
                self.start_time = QTime.currentTime()
            else:
                self.stop_camera()
        except Exception:
            try:
                self.logger.exception('toggle_camera 出错')
            except Exception:
                pass

    def stop_camera(self):
        """停止摄像头"""
        try:
            self.camera_active = False
            self.camera_timer.stop()
            self.recognition_timer.stop()
            if self.plate_recognizer:
                try:
                    self.plate_recognizer.stop_camera()
                except Exception:
                    pass
            if getattr(self.camera_panel, 'camera_button', None):
                try:
                    self.camera_panel.camera_button.setText("开启摄像头")
                except Exception:
                    pass
            # 不再清空 label，CameraPanel.stop_camera 会保留最后一帧以保持画面可见
            try:
                self.camera_panel.stop_camera()
            except Exception:
                pass
            try:
                self.status_panel.set_camera_info("已停止")
            except Exception:
                pass
            self.recognized_plates.clear()
            self.logger.info('摄像头已关闭并清理状态')
        except Exception:
            try:
                self.logger.exception('stop_camera 出错')
            except Exception:
                pass

    def finalize_recognition(self):
        """在5秒后处理识别结果"""
        if self.recognized_plates:
            # 选择出现次数最多的车牌号
            most_common_plate = Counter(self.recognized_plates).most_common(1)[0][0]
            self.plate_input.setText(most_common_plate)
        try:
            if self.recognized_plates:
                # 选择出现次数最多的车牌号
                most_common_plate = Counter(self.recognized_plates).most_common(1)[0][0]
                self.plate_input.setText(most_common_plate)
        except Exception:
            try:
                self.logger.exception('finalize_recognition 处理识别结果失败')
            except Exception:
                pass
        finally:
            # 停止摄像头
            self.stop_camera()
            self.logger.debug('finalize_recognition 已处理并停止摄像头')

    def _on_request_camera_start(self, index: int):
        # 切换摄像头到指定索引
        try:
            # 如果摄像头已开启，先停止
            if self.camera_active:
                self.stop_camera()
            ok = self.camera_panel.start_camera(index)
            if ok:
                self.camera_active = True
                self.camera_timer.start(30)
                self.recognition_timer.start(5000)
                self.logger.info(f'摄像头 {index} 已开启')
                try:
                    self.status_panel.set_camera_info(f"索引 {index}")
                except Exception:
                    pass
                # 更新按钮文本
                if getattr(self.camera_panel, 'camera_button', None):
                    try:
                        self.camera_panel.camera_button.setText('关闭摄像头')
                    except Exception:
                        pass
                # 保存上次使用的摄像头索引到配置（防御性保存）
                try:
                    self.config.set('data', 'last_camera_index', int(index))
                except Exception:
                    pass
            else:
                QMessageBox.warning(self, '错误', f'无法打开摄像头 {index}')
            # 保存上次使用的摄像头索引到配置
            try:
                self.config.set('data', 'last_camera_index', int(index))
            except Exception:
                pass
        except Exception:
            try:
                self.logger.exception('_on_request_camera_start 出错')
            except Exception:
                pass

    def _on_request_upload(self, _):
        # 打开文件选择并对图像进行识别
        try:
            path, _ = QFileDialog.getOpenFileName(self, '选择图片', os.getcwd(), 'Images (*.png *.jpg *.jpeg *.bmp)')
            if not path:
                return
            # 使用 QThread worker 在后台执行识别
            try:
                worker = RecognizeWorker(self.plate_recognizer, path)
                # 追踪 worker，便于在退出时清理
                try:
                    self._workers.append(worker)
                except Exception:
                    pass

                # 绑定 finished 回调，确保调用主线程的处理函数并移除 worker
                def _on_finished(res, w=worker):
                    try:
                        self._on_worker_finished(res)
                    finally:
                        try:
                            if w in self._workers:
                                self._workers.remove(w)
                        except Exception:
                            pass

                worker.finished.connect(_on_finished)
                worker.start()
            except Exception:
                try:
                    self.logger.exception('启动 RecognizeWorker 失败')
                except Exception:
                    pass
        except Exception:
            try:
                self.logger.exception('_on_request_upload 出错')
            except Exception:
                pass

    def _on_worker_finished(self, res: dict):
        try:
            if not res.get('ok'):
                QMessageBox.information(self, '提示', res.get('msg', '识别失败'))
            else:
                self.plate_input.setText(res.get('plate', '') or '')
                QMessageBox.information(self, '识别结果', f"车牌: {res.get('plate')}\n颜色: {res.get('color')}")
        except Exception:
            try:
                self.logger.exception('_on_worker_finished 出错')
            except Exception:
                pass


    def update_display(self):
        """更新显示信息，使用组件的刷新接口"""
        try:
            # 更新状态面板
            try:
                self.status_panel.update()
            except Exception:
                pass

            # 更新在场车辆表格
            try:
                self.vehicle_table.refresh()
            except Exception:
                pass
        except Exception:
            try:
                self.logger.exception('update_display 出错')
            except Exception:
                pass

    def handle_entry(self):
        """处理车辆入场"""
        plate = self.plate_input.text().strip()
        if not plate:
            QMessageBox.warning(self, "警告", "请输入车牌号")
            return
        try:
            plate = self.plate_input.text().strip()
            if not plate:
                QMessageBox.warning(self, "警告", "请输入车牌号")
                return

            success, message = self.parking_lot.process_entry(plate)
            if success:
                QMessageBox.information(self, "成功", message)
                self.logger.info(f'入场成功: {plate} - {message}')
                self.plate_input.clear()
                # 异步播报
                self.speak(f"{plate} 欢迎入场")
            else:
                QMessageBox.warning(self, "失败", message)
                self.logger.warning(f'入场失败: {plate} - {message}')
            self.update_display()
        except Exception:
            try:
                self.logger.exception('handle_entry 异常')
            except Exception:
                pass

    def handle_exit(self):
        """处理车辆出场"""
        plate = self.plate_input.text().strip()
        if not plate:
            QMessageBox.warning(self, "警告", "请输入车牌号")
            return
        try:
            plate = self.plate_input.text().strip()
            if not plate:
                QMessageBox.warning(self, "警告", "请输入车牌号")
                return

            success, message = self.parking_lot.process_exit(plate)
            if success:
                QMessageBox.information(self, "成功", message)
                self.logger.info(f'出场成功: {plate} - {message}')
                self.plate_input.clear()
                self.speak(f"{plate} 一路顺风")  # 播报出场信息
            else:
                QMessageBox.warning(self, "失败", message)
                self.logger.warning(f'出场失败: {plate} - {message}')
            self.update_display()
        except Exception:
            try:
                self.logger.exception('handle_exit 异常')
            except Exception:
                pass

    def show_message(self, message, success=True):
        """显示消息框"""
        QMessageBox.information(self, "提示", message) if success else \
        QMessageBox.warning(self, "警告", message) 

    def show_admin_login(self):
        """显示管理员登录对话框"""
        login_dialog = LoginDialog(self)
        if login_dialog.exec() == QDialog.Accepted:
            self.show_admin_panel()

    def show_admin_panel(self):
        """显示管理界面"""
        admin_panel = AdminPanel(self)
        admin_panel.exec()

    def speak(self, text):
        """播报文本信息"""
        # 非阻塞播报，放到后台线程
        def _speak(t):
            try:
                engine = pyttsx3.init()
                engine.say(t)
                engine.runAndWait()
            except Exception:
                try:
                    self.logger.exception('speak 播报失败')
                except Exception:
                    pass

        try:
            thr = threading.Thread(target=_speak, args=(text,), daemon=True)
            thr.start()
        except Exception:
            try:
                self.logger.exception('speak 启动线程失败')
            except Exception:
                pass

    def closeEvent(self, event):
        """退出时保存当前使用的摄像头索引到配置"""
        try:
            idx = None
            try:
                if getattr(self.camera_panel, 'current_index', None) is not None:
                    idx = int(self.camera_panel.current_index)
            except Exception:
                idx = None
            if idx is not None:
                try:
                    self.config.set('data', 'last_camera_index', idx)
                except Exception:
                    pass
        except Exception:
            pass
        # 尝试优雅停止并等待后台 workers
        try:
            for w in list(getattr(self, '_workers', [])):
                try:
                    # 如果 worker 提供了停止接口，可以调用；否则请求退出并等待
                    if hasattr(w, 'requestInterruption'):
                        try:
                            w.requestInterruption()
                        except Exception:
                            pass
                    try:
                        w.quit()
                    except Exception:
                        pass
                    try:
                        w.wait(2000)
                    except Exception:
                        pass
                except Exception:
                    pass
        except Exception:
            try:
                self.logger.exception('关闭时清理 worker 失败')
            except Exception:
                pass
        super().closeEvent(event)

# LoginDialog implementation moved to src/gui/login_dialog.py