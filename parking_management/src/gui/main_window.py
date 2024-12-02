from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QPushButton, QLabel, QLineEdit, QTableWidget,
                              QTableWidgetItem, QMessageBox, QGroupBox, QDialog,
                              QSpacerItem, QSizePolicy, QFrame, QFormLayout)
from PySide6.QtCore import Qt, QTimer, QSize, QTime
from PySide6.QtGui import QImage, QPixmap, QFont, QIcon
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.core.parking_lot import ParkingLot
from src.utils.config import Config
from src.utils.plate_recognizer import PlateRecognizer
import cv2
from collections import Counter
from .admin_panel import AdminPanel
from .login_dialog import LoginDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.parking_lot = ParkingLot()
        try:
            # 从配置中获取模型路径
            model_paths = self.config.get_model_paths()
            detect_model_path = model_paths['detect_model']
            rec_model_path = model_paths['rec_model']
            self.plate_recognizer = PlateRecognizer(detect_model_path, rec_model_path)
            self.camera_active = False  # 添加摄像头状态标志
        except Exception as e:
            QMessageBox.warning(self, "初始化警告", f"车牌识别模块初始化失败: {str(e)}\n将禁用车牌识别功能")
            self.plate_recognizer = None
            
        self.setup_ui()
        
        # 设置定时器更新显示
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_display)
        self.timer.start(self.config.get('gui', 'refresh_rate'))

        # 添加用于显示摄像头画面的定时器
        self.camera_timer = QTimer()
        self.camera_timer.timeout.connect(self.update_camera)
        
        self.recognized_plates = []  # 存储识别到的车牌号
        self.recognition_timer = QTimer()  # 用于计时5秒
        self.recognition_timer.timeout.connect(self.finalize_recognition)
        self.start_time = None

    def setup_ui(self):
        """设置UI界面"""
        # 设置窗口基本属性
        self.setWindowTitle("智能停车场管理系统")
        self.setMinimumSize(1200, 800)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 左侧面板（状态和操作区）
        left_panel = self.create_left_panel()
        main_layout.addWidget(left_panel, 1)
        
        # 右侧面板（摄像头和车辆列表）
        right_panel = self.create_right_panel()
        main_layout.addWidget(right_panel, 2)

    def create_left_panel(self):
        """创建左侧面板"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel)
        layout = QVBoxLayout(panel)
        layout.setSpacing(20)
        
        # 状态显示区域
        status_group = QGroupBox("停车场状态")
        status_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 6px;
                margin-top: 6px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        status_layout = QVBoxLayout()
        
        # 使用大字体显示状态
        font = QFont()
        font.setPointSize(16)
        
        self.total_spaces_label = QLabel(f"总车位：{self.parking_lot.total_spaces}")
        self.available_spaces_label = QLabel(f"可用车位：{self.parking_lot.available_spaces}")
        self.total_spaces_label.setFont(font)
        self.available_spaces_label.setFont(font)
        
        status_layout.addWidget(self.total_spaces_label)
        status_layout.addWidget(self.available_spaces_label)
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # 车牌输入区域
        input_group = QGroupBox("车牌输入")
        input_layout = QVBoxLayout()
        
        self.plate_input = QLineEdit()
        self.plate_input.setPlaceholderText("请输入车牌号或使用摄像头识别")
        self.plate_input.setMinimumHeight(40)
        self.plate_input.setFont(QFont("Arial", 12))
        input_layout.addWidget(self.plate_input)
        
        # 操作按钮区域
        button_layout = QHBoxLayout()
        self.entry_button = QPushButton("车辆入场")
        self.exit_button = QPushButton("车辆出场")
        
        # 在这里连接按钮信号
        self.entry_button.clicked.connect(self.handle_entry)
        self.exit_button.clicked.connect(self.handle_exit)
        
        self.entry_button.setMinimumHeight(40)
        self.exit_button.setMinimumHeight(40)
        
        # 设置按钮样式
        button_style = """
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """
        self.entry_button.setStyleSheet(button_style)
        self.exit_button.setStyleSheet(button_style.replace("#2196F3", "#4CAF50")
                                                  .replace("#1976D2", "#388E3C")
                                                  .replace("#0D47A1", "#1B5E20"))
        
        button_layout.addWidget(self.entry_button)
        button_layout.addWidget(self.exit_button)
        input_layout.addLayout(button_layout)
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # 管理员入口
        self.admin_button = QPushButton("管理员入口")
        # 连接管理员按钮信号
        self.admin_button.clicked.connect(self.show_admin_login)
        
        self.admin_button.setStyleSheet(button_style.replace("#2196F3", "#9E9E9E"))
        self.admin_button.setMinimumHeight(40)
        layout.addWidget(self.admin_button)
        
        # 添加弹性空间
        layout.addStretch()
        
        return panel

    def create_right_panel(self):
        """创建右侧面板"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel)
        layout = QVBoxLayout(panel)
        layout.setSpacing(20)
        
        # 摄像头区域
        camera_group = QGroupBox("车牌识别")
        camera_layout = QVBoxLayout()
        
        self.camera_label = QLabel()
        self.camera_label.setMinimumSize(640, 480)
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setStyleSheet("""
            QLabel {
                border: 2px solid #cccccc;
                border-radius: 4px;
                background-color: #f5f5f5;
            }
        """)
        camera_layout.addWidget(self.camera_label)
        
        if self.plate_recognizer:
            self.camera_button = QPushButton("开启摄像头")
            self.camera_button.clicked.connect(self.toggle_camera)
            self.camera_button.setMinimumHeight(40)
            self.camera_button.setStyleSheet("""
                QPushButton {
                    background-color: #FF5722;
                    color: white;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #F4511E;
                }
                QPushButton:pressed {
                    background-color: #D84315;
                }
            """)
            camera_layout.addWidget(self.camera_button)
        
        camera_group.setLayout(camera_layout)
        layout.addWidget(camera_group)
        
        # 在场车辆列表
        vehicles_group = QGroupBox("在场车辆")
        vehicles_layout = QVBoxLayout()
        
        self.vehicles_table = QTableWidget()
        self.vehicles_table.setColumnCount(2)
        self.vehicles_table.setHorizontalHeaderLabels(["车牌号", "入场时间"])
        self.vehicles_table.horizontalHeader().setStretchLastSection(True)
        self.vehicles_table.setStyleSheet("""
            QTableWidget {
                border: none;
                gridline-color: #e0e0e0;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 6px;
                border: none;
                border-bottom: 2px solid #e0e0e0;
                font-weight: bold;
            }
        """)
        
        vehicles_layout.addWidget(self.vehicles_table)
        vehicles_group.setLayout(vehicles_layout)
        layout.addWidget(vehicles_group)
        
        return panel

    def update_camera(self):
        """更新摄像头画面"""
        if self.plate_recognizer and self.camera_active:
            ret, frame = self.plate_recognizer.camera.read()
            if ret:
                # 转换图像格式用于显示
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
                scaled_pixmap = QPixmap.fromImage(qt_image).scaled(
                    self.camera_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.camera_label.setPixmap(scaled_pixmap)
                
                # 尝试识别车牌
                outputs = self.plate_recognizer.detect_plate(frame)
                if outputs is not None and len(outputs) > 0:
                    for output in outputs:
                        rect = output[:4].astype(int)
                        plate_image = frame[rect[1]:rect[3], rect[0]:rect[2]]
                        plate_no, _ = self.plate_recognizer.recognize_text(plate_image)
                        self.recognized_plates.append(plate_no)

    def toggle_camera(self):
        """切换摄像头状态"""
        if not self.plate_recognizer:
            return
            
        if not self.camera_active:
            # 初始化摄像头
            self.plate_recognizer.camera = cv2.VideoCapture(0)
            if not self.plate_recognizer.camera.isOpened():
                QMessageBox.warning(self, "错误", "无法打开摄像头")
                return
            
            # 开启摄像头
            self.camera_active = True
            self.camera_button.setText("关闭摄像头")
            self.camera_timer.start(30)  # 约30FPS
            self.recognition_timer.start(5000)  # 5秒计时器
            self.start_time = QTime.currentTime()
        else:
            self.stop_camera()

    def stop_camera(self):
        """停止摄像头"""
        self.camera_active = False
        self.camera_timer.stop()
        self.recognition_timer.stop()
        self.plate_recognizer.stop_camera()
        self.camera_button.setText("开启摄像头")
        self.camera_label.clear()
        self.recognized_plates.clear()

    def finalize_recognition(self):
        """在5秒后处理识别结果"""
        if self.recognized_plates:
            # 选择出现次数最多的车牌号
            most_common_plate = Counter(self.recognized_plates).most_common(1)[0][0]
            self.plate_input.setText(most_common_plate)
        
        # 停止摄像头
        self.stop_camera()

    def handle_file_recognition(self):
        """处理图片文件识别"""
        if not self.plate_recognizer:
            return
            
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择图片",
            "",
            "图片文件 (*.png *.jpg *.jpeg)"
        )
        
        if file_path:
            success, result = self.plate_recognizer.process_image(file_path)
            if success:
                self.plate_input.setText(result)
                QMessageBox.information(self, "识别成功", f"识别到车牌号：{result}")
            else:
                QMessageBox.warning(self, "识别失败", result)

    def update_display(self):
        """更新显示信息"""
        # 更新状态标签
        status = self.parking_lot.get_parking_status()
        self.total_spaces_label.setText(f"总车位：{status['total_spaces']}")
        self.available_spaces_label.setText(f"可用车位：{status['available_spaces']}")

        # 更新在场车辆表格
        current_vehicles = self.parking_lot.get_current_vehicles()
        self.vehicles_table.setRowCount(len(current_vehicles))
        for i, (_, vehicle) in enumerate(current_vehicles.iterrows()):
            self.vehicles_table.setItem(i, 0, QTableWidgetItem(vehicle['License Plate']))
            self.vehicles_table.setItem(i, 1, QTableWidgetItem(str(vehicle['Entry Time'])))

    def handle_entry(self):
        """处理车辆入场"""
        plate = self.plate_input.text().strip()
        if not plate:
            QMessageBox.warning(self, "警告", "请输入车牌号")
            return
        
        success, message = self.parking_lot.process_entry(plate)
        if success:
            QMessageBox.information(self, "成功", message)
            self.plate_input.clear()
        else:
            QMessageBox.warning(self, "失败", message)
        self.update_display()

    def handle_exit(self):
        """处理车辆出场"""
        plate = self.plate_input.text().strip()
        if not plate:
            QMessageBox.warning(self, "警告", "请输入车牌号")
            return
        
        success, message = self.parking_lot.process_exit(plate)
        if success:
            QMessageBox.information(self, "成功", message)
            self.plate_input.clear()
        else:
            QMessageBox.warning(self, "失败", message)
        self.update_display()

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

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("管理员登录")
        self.setFixedSize(300, 150)

        layout = QVBoxLayout()
        form_layout = QFormLayout()

        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)

        form_layout.addRow("用户名:", self.username_input)
        form_layout.addRow("密码:", self.password_input)

        self.login_button = QPushButton("登录")
        self.login_button.clicked.connect(self.verify_credentials)

        layout.addLayout(form_layout)
        layout.addWidget(self.login_button)
        self.setLayout(layout)

    def verify_credentials(self):
        username = self.username_input.text()
        password = self.password_input.text()
        # 假设管理员账号为admin，密码为1234
        if username == "admin" and password == "1234":
            self.accept()
        else:
            QMessageBox.warning(self, "登录失败", "用户名或密码错误") 