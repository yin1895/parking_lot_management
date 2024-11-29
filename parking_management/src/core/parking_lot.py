import pandas as pd
from datetime import datetime
import numpy as np
import re
import os
from ..utils.config import Config

class ParkingLot:
    def __init__(self):
        self.config = Config()
        self.total_spaces = self.config.total_spaces
        self.available_spaces = self.total_spaces
        self.gate_status = "closed"
        self.data_file = self.config.records_file
        
        # 初始化或加载数据
        if os.path.exists(self.data_file):
            self.records = pd.read_csv(self.data_file)
            # 确保时间列的格式正确
            for col in ['Entry Time', 'Exit Time']:
                if col in self.records.columns:
                    self.records[col] = pd.to_datetime(self.records[col])
            # 更新可用车位
            current_parked = len(self.records[self.records['Exit Time'].isna()])
            self.available_spaces = self.total_spaces - current_parked
        else:
            self.records = pd.DataFrame(columns=[
                'License Plate', 'Entry Time', 'Exit Time', 'Fee'
            ])
            self._save_records()

    def _save_records(self):
        """保存记录到CSV文件"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        self.records.to_csv(self.data_file, index=False)

    def validate_license_plate(self, license_plate):
        pattern = r'^[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领][A-Z][A-Z0-9]{5}$'
        return bool(re.match(pattern, license_plate))

    def check_duplicate_entry(self, license_plate):
        current_vehicles = self.records[self.records['Exit Time'].isna()]
        return license_plate in current_vehicles['License Plate'].values

    def get_parking_status(self):
        """获取停车场状态信息，用于GUI显示"""
        return {
            'total_spaces': self.total_spaces,
            'available_spaces': self.available_spaces,
            'occupied_spaces': self.total_spaces - self.available_spaces,
            'gate_status': self.gate_status
        }

    def get_current_vehicles(self):
        """获取当前在场车辆信息，用于GUI显示"""
        return self.records[self.records['Exit Time'].isna()]

    def process_entry(self, license_plate):
        """处理车辆入场"""
        if not self.validate_license_plate(license_plate):
            return False, "无效的车牌号格式"

        if self.check_duplicate_entry(license_plate):
            return False, "该车辆已在停车场内"

        if self.available_spaces <= 0:
            return False, "停车场已满"

        entry_time = datetime.now()
        new_record = pd.DataFrame([{
            'License Plate': license_plate,
            'Entry Time': entry_time,
            'Exit Time': None,
            'Fee': None
        }])
        self.records = pd.concat([self.records, new_record], ignore_index=True)
        self.available_spaces -= 1
        self._save_records()
        return True, f"车辆 {license_plate} 已入场"

    def process_exit(self, license_plate):
        """处理车辆出场"""
        if not self.validate_license_plate(license_plate):
            return False, "无效的车牌号格式"

        vehicle_record = self.records[
            (self.records['License Plate'] == license_plate) & 
            (self.records['Exit Time'].isna())
        ]

        if vehicle_record.empty:
            return False, "未找到该车辆的入场记录"

        exit_time = datetime.now()
        record_index = vehicle_record.index[0]
        entry_time = self.records.at[record_index, 'Entry Time']
        
        # 计算停车时长和费用
        duration = (exit_time - pd.to_datetime(entry_time)).total_seconds() / 3600
        fee = self.calculate_fee(duration)

        # 更新记录
        self.records.at[record_index, 'Exit Time'] = exit_time
        self.records.at[record_index, 'Fee'] = fee
        self.available_spaces += 1
        self._save_records()

        return True, f"车辆 {license_plate} 已出场，费用：{fee:.2f}元"

    def calculate_fee(self, duration):
        """计算停车费用"""
        hourly_rate = self.config.hourly_rate
        return np.ceil(duration) * hourly_rate

    def get_records_by_date(self, date):
        """获取指定日期的记录，用于报表生成"""
        date_records = self.records[
            pd.to_datetime(self.records['Entry Time']).dt.date == date
        ]
        return date_records 