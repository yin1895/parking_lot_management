from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QPushButton, QLabel, QLineEdit, QTableWidget,
                              QTableWidgetItem, QMessageBox, QGroupBox, QFileDialog)
from PySide6.QtCore import Qt, QTimer, QTime
from PySide6.QtGui import QImage, QPixmap
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.core.parking_lot import ParkingLot
from src.utils.config import Config
from src.utils.plate_recognizer import PlateRecognizer
import cv2
from collections import Counter

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
        gui_config = self.config.get_gui_config()
        self.setWindowTitle(gui_config['window_title'])
        self.setMinimumSize(
            gui_config['window_size']['width'],
            gui_config['window_size']['height']
        )

        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 状态显示区域
        status_group = QGroupBox("停车场状态")
        status_layout = QHBoxLayout()
        self.total_spaces_label = QLabel(f"总车位：{self.parking_lot.total_spaces}")
        self.available_spaces_label = QLabel(f"可用车位：{self.parking_lot.available_spaces}")
        status_layout.addWidget(self.total_spaces_label)
        status_layout.addWidget(self.available_spaces_label)
        status_group.setLayout(status_layout)
        main_layout.addWidget(status_group)

        # 车牌识别区域
        recognition_group = QGroupBox("车牌识别")
        recognition_layout = QVBoxLayout()  # 改为垂直布局
        
        # 添加摄像头画面显示标签
        self.camera_label = QLabel()
        self.camera_label.setMinimumSize(640, 480)  # 设置最小尺寸
        recognition_layout.addWidget(self.camera_label)
        
        # 添加控制按钮
        button_layout = QHBoxLayout()
        if self.plate_recognizer:
            self.camera_button = QPushButton("开启摄像头")
            self.camera_button.clicked.connect(self.toggle_camera)
            button_layout.addWidget(self.camera_button)
        else:
            button_layout.addWidget(QLabel("车牌识别功能未启用"))
        
        recognition_layout.addLayout(button_layout)
        recognition_group.setLayout(recognition_layout)
        main_layout.addWidget(recognition_group)

        # 操作区域
        operation_group = QGroupBox("车辆进出")
        operation_layout = QHBoxLayout()
        
        # 车牌输入
        self.plate_input = QLineEdit()
        self.plate_input.setPlaceholderText("请输入车牌号")
        operation_layout.addWidget(self.plate_input)

        # 进出按钮
        self.entry_button = QPushButton("车辆入场")
        self.exit_button = QPushButton("车辆出场")
        self.entry_button.clicked.connect(self.handle_entry)
        self.exit_button.clicked.connect(self.handle_exit)
        operation_layout.addWidget(self.entry_button)
        operation_layout.addWidget(self.exit_button)
        
        operation_group.setLayout(operation_layout)
        main_layout.addWidget(operation_group)

        # 在场车辆列表
        vehicles_group = QGroupBox("在场车辆")
        vehicles_layout = QVBoxLayout()
        self.vehicles_table = QTableWidget()
        self.vehicles_table.setColumnCount(2)
        self.vehicles_table.setHorizontalHeaderLabels(["车牌号", "入场时间"])
        self.vehicles_table.horizontalHeader().setStretchLastSection(True)
        vehicles_layout.addWidget(self.vehicles_table)
        vehicles_group.setLayout(vehicles_layout)
        main_layout.addWidget(vehicles_group)

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
        success, message = self.parking_lot.process_entry(plate)
        self.show_message(message, success)
        if success:
            self.plate_input.clear()
        self.update_display()

    def handle_exit(self):
        """处理车辆出场"""
        plate = self.plate_input.text().strip()
        success, message = self.parking_lot.process_exit(plate)
        self.show_message(message, success)
        if success:
            self.plate_input.clear()
        self.update_display()

    def show_message(self, message, success=True):
        """显示消息框"""
        QMessageBox.information(self, "提示", message) if success else \
        QMessageBox.warning(self, "警告", message) 