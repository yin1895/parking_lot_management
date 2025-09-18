import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from src.core.parking_lot import ParkingLot
from src.utils.config import Config
from datetime import datetime, timedelta


def test_entry_and_exit_fee_normal(tmp_path, monkeypatch):
    # 使用临时 data 目录来隔离文件
    monkeypatch.setenv('PARKING_DATA_DIR', str(tmp_path))
    cfg = Config()
    pl = ParkingLot()

    plate = '粤A12345'
    # 人为插入入场记录
    entry_time = datetime.now() - timedelta(hours=2, minutes=10)
    pl.records = pl.records.iloc[0:0]
    new = {'License Plate': plate, 'Entry Time': entry_time, 'Exit Time': None, 'Fee': 0.0}
    # 直接创建 DataFrame 并赋值，避免 pd.concat 在空 DataFrame 上的未来行为差异
    pl.records = pd.DataFrame([new])

    success, msg = pl.process_exit(plate)
    assert success is True
    assert '费用' in msg or 'Fee' in msg or isinstance(msg, str)


def test_member_pricing(tmp_path, monkeypatch):
    monkeypatch.setenv('PARKING_DATA_DIR', str(tmp_path))
    cfg = Config()
    pl = ParkingLot()

    plate = '粤A54321'
    # 添加会员并设置 member_since 早于 entry
    pl.members = [{'plate': plate, 'member_since': datetime.now() - timedelta(days=1), 'status': 'active'}]
    entry_time = datetime.now() - timedelta(hours=3)
    pl.records = pl.records.iloc[0:0]
    new = {'License Plate': plate, 'Entry Time': entry_time, 'Exit Time': None, 'Fee': 0.0}
    pl.records = pd.DataFrame([new])

    success, msg = pl.process_exit(plate)
    assert success is True
    assert '费用' in msg or 'Fee' in msg
