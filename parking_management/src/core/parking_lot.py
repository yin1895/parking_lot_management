import os
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import re
from src.utils.config import Config
from src.utils.logger import get_logger
import math

class ParkingLot:
    def __init__(self):
        self.config = Config()
        self.total_spaces = self.config.get('parking_lot', 'total_spaces')
        self.hourly_rate = self.config.get('parking_lot', 'hourly_rate')
        self.member_hourly_rate = self.config.get('parking_lot', 'member_hourly_rate')
        self.logger = get_logger('ParkingLot')
        self.logger.info('ParkingLot 初始化')
        
        # 初始化可用车位数量
        self.available_spaces = self.total_spaces
        
        # 初始化闸门状态
        self.gate_status = "closed"
        
        # 使用配置中的 data dir
        data_dir = self.config.get_data_dir()
        os.makedirs(data_dir, exist_ok=True)

        # 数据文件路径
        self.data_file = self.config.records_file

        # 会员数据文件路径
        self.members_file = self.config.members_file
        self.load_members()

        # 初始化或加载数据
        if os.path.exists(self.data_file):
            self.records = pd.read_csv(self.data_file)
            self.logger.debug(f'加载记录文件: {self.data_file}, 共 {len(self.records)} 条')
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

    def load_members(self):
        """加载会员数据"""
        try:
            if os.path.exists(self.members_file): 
                try:
                    members_df = pd.read_csv(self.members_file)
                except pd.errors.EmptyDataError:
                    # 成员文件存在但为空，视为没有会员，不记录为异常
                    self.members = []
                    return
                self.logger.debug(f'从 {self.members_file} 加载会员数据, rows={len(members_df)}')
                if 'member_since' in members_df.columns:
                    members_df['member_since'] = pd.to_datetime(members_df['member_since'], errors='coerce')
                else:
                    members_df['member_since'] = pd.NaT
                # ensure 'plate' column exists
                if 'plate' not in members_df.columns and len(members_df.columns) > 0:
                    members_df = members_df.rename(columns={members_df.columns[0]: 'plate'})
                self.members = members_df.to_dict('records')
            else:
                self.members = []
                self._save_members()
        except Exception:
            # 记录异常但不终止
            try:
                self.logger.exception('加载会员数据失败')
            except Exception:
                pass
            self.members = []

    def _save_members(self):
        """保存会员数据"""
        members_df = pd.DataFrame(self.members)
        os.makedirs(os.path.dirname(self.members_file), exist_ok=True)
        try:
            members_df.to_csv(self.members_file, index=False)
            self.logger.debug(f'已保存会员数据到 {self.members_file}, rows={len(members_df)}')
        except Exception:
            try:
                self.logger.exception('保存会员数据失败')
            except Exception:
                pass

    def save_members(self):
        """保存会员数据"""
        try:
            members_df = pd.DataFrame(self.members) 
            members_df.to_csv(self.members_file, index=False)
            self.logger.debug(f'保存会员数据 (save_members) 到 {self.members_file}')
        except Exception:
            try:
                self.logger.exception('保存会员数据失败')
            except Exception:
                pass

    def get_members(self):
        """获取所有会员"""
        return self.members

    def add_member(self, plate):
        """添加会员
        Args:
            plate: 车牌号
        Returns:
            bool: 是否添加成功
        """
        # 判断是否已存在激活会员
        for m in self.members:
            if m.get('plate') == plate and m.get('status') == 'active':
                return False
        member_record = {
            'plate': plate,
            'member_since': datetime.now(),
            'status': 'active'
        }
        self.members.append(member_record)
        self._save_members()
        return True

    def delete_member(self, plate):
        """删除会员"""
        for m in list(self.members):
            if m.get('plate') == plate:
                self.members.remove(m)
                self._save_members()
                return True
        return False

    def is_member(self, plate):
        """检查是否是会员"""
        return self.get_member_record(plate) is not None

    def update_prices(self, normal_price, member_price):
        """更新价格设置"""
        self.hourly_rate = normal_price
        self.member_hourly_rate = member_price
        self.config.set('parking_lot', 'hourly_rate', normal_price)
        self.config.set('parking_lot', 'member_hourly_rate', member_price)
        self.config._save_config()

    def calculate_fee(self, entry_time, exit_time, plate):
        """计算停车费用，考虑会员状态变化
        Args:
            entry_time: 入场时间
            exit_time: 出场时间
            plate: 车牌号
        Returns:
            float: 停车费用
        """
        # 获取会员记录
        member_record = self.get_member_record(plate)
        
        if not member_record:
            # 如果从未是会员，按普通费率计算
            duration = (exit_time - entry_time).total_seconds() / 3600
            hours = math.ceil(duration)
            return round(hours * self.hourly_rate, 2)
        
        member_since = member_record['member_since']
        
        if member_since <= entry_time:
            # 如果入场时已经是会员，全程按会员费率计算
            duration = (exit_time - entry_time).total_seconds() / 3600
            hours = math.ceil(duration)
            return round(hours * self.member_hourly_rate, 2)
        
        if member_since >= exit_time:
            # 如果离场时还不是会员，全程按普通费率计算
            duration = (exit_time - entry_time).total_seconds() / 3600
            hours = math.ceil(duration)
            return round(hours * self.hourly_rate, 2)
        
        # 分段计费：会员前和会员后
        normal_duration = (member_since - entry_time).total_seconds() / 3600
        member_duration = (exit_time - member_since).total_seconds() / 3600
        
        normal_hours = math.ceil(normal_duration)
        member_hours = math.ceil(member_duration)
        
        total_fee = (normal_hours * self.hourly_rate) + (member_hours * self.member_hourly_rate)
        return round(total_fee, 2)

    def _save_records(self):
        """保存记录到CSV文件"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            self.records.to_csv(self.data_file, index=False)
            self.logger.debug(f'已保存记录到 {self.data_file}, 总条数 {len(self.records)}')
            # 保存价格到配置文件
            self.config.set('parking_lot', 'hourly_rate', self.hourly_rate)
        except Exception:
            self.logger.exception('保存记录失败')

    def validate_license_plate(self, plate):
        """验证车牌号格式"""
        pattern = r'^[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领][A-Z][A-Z0-9]{5}$'
        return bool(re.match(pattern, plate))

    def check_duplicate_entry(self, plate):
        current_vehicles = self.records[self.records['Exit Time'].isna()]
        return plate in current_vehicles['License Plate'].values

    def get_parking_status(self):
        """获取停车场状态"""
        return {
            'total_spaces': self.total_spaces,
            'available_spaces': self.available_spaces,
            'gate_status': self.gate_status
        }

    def get_current_vehicles(self):
        """获取当前在场车辆"""
        return self.records[self.records['Exit Time'].isna()]

    def process_entry(self, plate):
        """处理车辆入场"""
        if not self.validate_license_plate(plate):
            return False, "无效的车牌号"
            
        # 检查车位是否已满
        if self.available_spaces <= 0:
            return False, "停车场已满"
            
        # 检查车辆是否已在场内
        if len(self.records[
            (self.records['License Plate'] == plate) & 
            (self.records['Exit Time'].isna())
        ]) > 0:
            return False, "该车辆已在停车场内"
            
        # 记录入场
        entry_time = datetime.now()
        new_record = pd.DataFrame({
            'License Plate': [plate],
            'Entry Time': [entry_time],
            'Exit Time': [pd.NA],
            'Fee': [0.0]
        })
        
        # 确保数据类型一致
        if len(self.records) > 0:
            new_record = new_record.astype(self.records.dtypes)
        
        # 如果当前 records 为空，直接赋值以避免 pd.concat 在空或全 NA 条目上的未来行为变化警告
        if self.records is None or len(self.records) == 0:
            # reset_index to ensure a clean 0..n index
            self.records = new_record.reset_index(drop=True)
        else:
            self.records = pd.concat([self.records, new_record], ignore_index=True)
        self.available_spaces -= 1
        self._save_records()
        self.logger.info(f'process_entry: plate={plate}, entry_time={entry_time}, available_spaces={self.available_spaces}')

        return True, f"车辆 {plate} 已成功入场"

    def process_exit(self, plate):
        """处理车辆出场"""
        # 查找未出场的记录
        current_record = self.records[
            (self.records['License Plate'] == plate) & 
            (self.records['Exit Time'].isna())
        ]
        
        if len(current_record) == 0:
            return False, "未找到该车辆的入场记录"
            
        # 记录出场时间和计费
        exit_time = datetime.now()
        entry_time = current_record.iloc[0]['Entry Time']
        fee = self.calculate_fee(entry_time, exit_time, plate)
        
        # 更新记录
        self.records.loc[current_record.index, 'Exit Time'] = exit_time
        self.records.loc[current_record.index, 'Fee'] = fee
        self.available_spaces += 1
        self._save_records()
        self.logger.info(f'process_exit: plate={plate}, entry_time={entry_time}, exit_time={exit_time}, fee={fee}, available_spaces={self.available_spaces}')

        return True, f"车辆 {plate} 已出场，费用：{fee}元"

    def get_records_by_date(self, date):
        """获取指定日期的记录，用于报表生成"""
        date_records = self.records[
            pd.to_datetime(self.records['Entry Time']).dt.date == date
        ]
        return date_records 

    def get_member_record(self, plate):
        """获取会员记录
        Args:
            plate: 车牌号
        Returns:
            dict: 会员记录，如果不是会员则返回None
        """
        for member in self.members:
            if member['plate'] == plate and member['status'] == 'active':
                return member
        return None

    def get_records_by_date_range(self, start_date, end_date, plate=None):
        """获取指定日期范围内的记录
        Args:
            start_date: 开始日期
            end_date: 结束日期
            plate: 车牌号（可选）
        Returns:
            list: 符合条件的记录列表
        """
        # 转换日期为datetime
        start_datetime = pd.Timestamp(start_date)
        end_datetime = pd.Timestamp(end_date) + timedelta(days=1)  # 包含结束日期
        
        # 筛选日期范围内的记录
        mask = (pd.to_datetime(self.records['Entry Time']) >= start_datetime) & \
               (pd.to_datetime(self.records['Entry Time']) < end_datetime)
        
        if plate:
            # 如果指定了车牌号，添加车牌过滤条件
            mask = mask & (self.records['License Plate'] == plate)
        
        filtered_records = self.records[mask].copy()
        return filtered_records.to_dict('records')

    def get_member_status(self, plate):
        """获取会员状态
        Args:
            plate: 车牌号
        Returns:
            str: 会员状态
        """
        member = self.get_member_record(plate)
        if member:
            return member['status']
        return None

    def update_member_status(self, plate, status):
        """更新会员状态
        Args:
            plate: 车牌号
            status: 新状态
        Returns:
            bool: 是否更新成功
        """
        for member in self.members:
            if member['plate'] == plate:
                member['status'] = status
                self._save_members()
                return True
        return False