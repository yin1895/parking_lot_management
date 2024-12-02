from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                              QLineEdit, QPushButton, QFormLayout, QTableWidget,
                              QTableWidgetItem, QMessageBox, QHeaderView, QGroupBox,
                              QDateEdit, QTabWidget, QWidget)
from PySide6.QtCore import Qt, QDate
import pandas as pd
from datetime import datetime, timedelta

class AdminPanel(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("管理界面")
        self.setMinimumSize(800, 600)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 创建各个标签页
        self.price_tab = self.create_price_tab()
        self.member_tab = self.create_member_tab()
        self.history_tab = self.create_history_tab()
        
        # 添加标签页
        self.tab_widget.addTab(self.price_tab, "价格设置")
        self.tab_widget.addTab(self.member_tab, "会员管理")
        self.tab_widget.addTab(self.history_tab, "历史记录")
        
        # 设置主布局
        layout = QVBoxLayout()
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)
        
        # 加载数据
        self.load_member_data()
        self.load_history_data()

    def create_price_tab(self):
        """创建价格设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 价格设置组
        price_group = QGroupBox("价格设置")
        price_layout = QFormLayout()
        
        self.price_input = QLineEdit()
        self.member_price_input = QLineEdit()
        
        # 设置当前价格
        self.price_input.setText(str(self.parent.parking_lot.hourly_rate))
        self.member_price_input.setText(str(self.parent.parking_lot.member_hourly_rate))
        
        price_layout.addRow("普通价格（元/小时）:", self.price_input)
        price_layout.addRow("会员价格（元/小时）:", self.member_price_input)
        
        save_button = QPushButton("保存设置")
        save_button.clicked.connect(self.save_price_changes)
        
        price_group.setLayout(price_layout)
        layout.addWidget(price_group)
        layout.addWidget(save_button)
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget

    def create_member_tab(self):
        """创建会员管理标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 添加会员组
        add_group = QGroupBox("添加会员")
        add_layout = QHBoxLayout()
        
        self.member_plate_input = QLineEdit()
        self.member_plate_input.setPlaceholderText("请输入车牌号")
        add_button = QPushButton("添加")
        add_button.clicked.connect(self.add_member)
        
        add_layout.addWidget(self.member_plate_input)
        add_layout.addWidget(add_button)
        add_group.setLayout(add_layout)
        
        # 会员列表组
        list_group = QGroupBox("会员列表")
        list_layout = QVBoxLayout()
        
        self.member_table = QTableWidget()
        self.member_table.setColumnCount(4)
        self.member_table.setHorizontalHeaderLabels(["车牌号", "加入时间", "状态", "操作"])
        self.member_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        list_layout.addWidget(self.member_table)
        list_group.setLayout(list_layout)
        
        layout.addWidget(add_group)
        layout.addWidget(list_group)
        
        widget.setLayout(layout)
        return widget

    def create_history_tab(self):
        """创建历史记录标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 搜索组
        search_group = QGroupBox("搜索条件")
        search_layout = QHBoxLayout()
        
        self.start_date = QDateEdit()
        self.end_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-7))
        self.end_date.setDate(QDate.currentDate())
        
        self.plate_search = QLineEdit()
        self.plate_search.setPlaceholderText("车牌号（可选）")
        
        search_button = QPushButton("搜索")
        search_button.clicked.connect(self.search_history)
        
        search_layout.addWidget(QLabel("开始日期:"))
        search_layout.addWidget(self.start_date)
        search_layout.addWidget(QLabel("结束日期:"))
        search_layout.addWidget(self.end_date)
        search_layout.addWidget(self.plate_search)
        search_layout.addWidget(search_button)
        
        search_group.setLayout(search_layout)
        
        # 历史记录表格
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels(["车牌号", "入场时间", "出场时间", "停车时长", "费用"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(search_group)
        layout.addWidget(self.history_table)
        
        widget.setLayout(layout)
        return widget

    def load_member_data(self):
        """加载会员数据"""
        members = self.parent.parking_lot.get_members()
        self.member_table.setRowCount(len(members))
        
        for i, member in enumerate(members):
            plate_item = QTableWidgetItem(member['plate'])
            time_item = QTableWidgetItem(str(member['member_since']))
            status_item = QTableWidgetItem(member['status'])
            
            delete_button = QPushButton("删除")
            delete_button.clicked.connect(lambda checked, p=member['plate']: self.delete_member(p))
            
            self.member_table.setItem(i, 0, plate_item)
            self.member_table.setItem(i, 1, time_item)
            self.member_table.setItem(i, 2, status_item)
            self.member_table.setCellWidget(i, 3, delete_button)

    def load_history_data(self):
        """加载历史数据"""
        self.search_history()

    def search_history(self):
        """搜索历史记录"""
        start_date = self.start_date.date().toPython()
        end_date = self.end_date.date().toPython()
        plate = self.plate_search.text().strip()
        
        # 获取记录
        records = self.parent.parking_lot.get_records_by_date_range(start_date, end_date, plate)
        
        # 显示记录
        self.history_table.setRowCount(len(records))
        for i, record in enumerate(records):
            plate_item = QTableWidgetItem(record['License Plate'])
            entry_item = QTableWidgetItem(str(record['Entry Time']))
            exit_item = QTableWidgetItem(str(record['Exit Time']) if pd.notna(record['Exit Time']) else "未出场")
            
            # 计算停车时长
            if pd.notna(record['Exit Time']):
                duration = (record['Exit Time'] - record['Entry Time']).total_seconds() / 3600
                duration_str = f"{duration:.1f}小时"
            else:
                duration_str = "未出场"
            
            duration_item = QTableWidgetItem(duration_str)
            fee_item = QTableWidgetItem(f"¥{record['Fee']:.2f}" if pd.notna(record['Fee']) else "-")
            
            self.history_table.setItem(i, 0, plate_item)
            self.history_table.setItem(i, 1, entry_item)
            self.history_table.setItem(i, 2, exit_item)
            self.history_table.setItem(i, 3, duration_item)
            self.history_table.setItem(i, 4, fee_item)

    def save_price_changes(self):
        """保存价格设置"""
        try:
            new_price = float(self.price_input.text())
            new_member_price = float(self.member_price_input.text())
            
            if new_price <= 0 or new_member_price <= 0:
                raise ValueError("价格必须大于0")
                
            self.parent.parking_lot.update_prices(new_price, new_member_price)
            QMessageBox.information(self, "成功", "价格设置已更新")
            
        except ValueError as e:
            QMessageBox.warning(self, "错误", str(e))

    def add_member(self):
        """添加会员"""
        plate = self.member_plate_input.text().strip()
        if not plate:
            QMessageBox.warning(self, "错误", "请输入车牌号")
            return
            
        if self.parent.parking_lot.add_member(plate):
            QMessageBox.information(self, "成功", f"已将 {plate} 添加为会员")
            self.member_plate_input.clear()
            self.load_member_data()
        else:
            QMessageBox.warning(self, "错误", "添加会员失败")

    def delete_member(self, plate):
        """删除会员"""
        if QMessageBox.question(self, "确认", f"确定要删除会员 {plate} 吗？") == QMessageBox.Yes:
            if self.parent.parking_lot.delete_member(plate):
                QMessageBox.information(self, "成功", f"已删除会员 {plate}")
                self.load_member_data()
            else:
                QMessageBox.warning(self, "错误", "删除会员失败") 