import json
import os


class Config:
    _instance = None
    _default_config = {
        "parking_lot": {
            "total_spaces": 100,
            "hourly_rate": 5,
            "member_hourly_rate": 3,
        },
        "gui": {
            "window_title": "停车场管理系统",
            "window_size": {
                "width": 800,
                "height": 600
            },
            "refresh_rate": 1000  # 界面刷新率（毫秒）
        },
        "logging": {
            # 默认轮转参数：5MB, 保留5份
            "max_bytes": 5242880,
            "backup_count": 5
        },
        "data": {
            "records_file": "parking_records.csv",
            "members_file": "members.csv",
            "data_dir": "data"
        }
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        """加载配置文件，如果不存在则创建默认配置"""
        # 支持通过环境变量覆盖数据目录
        data_dir = os.environ.get('PARKING_DATA_DIR') or self._default_config['data']['data_dir']
        self.data_dir = data_dir
        # ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        self.config_path = os.path.join(self.data_dir, 'config.json')

        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
            except (json.JSONDecodeError, OSError):
                self._config = self._default_config.copy()
                self._save_config()
        else:
            self._config = self._default_config.copy()
            self._save_config()

        # ensure data keys exist
        data_section = self._config.setdefault('data', {})
        data_section.setdefault('data_dir', self.data_dir)
        data_section.setdefault('records_file', self._default_config['data']['records_file'])
        data_section.setdefault('members_file', self._default_config['data']['members_file'])

    def _save_config(self):
        """保存配置到文件"""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, indent=4, ensure_ascii=False)

    def get(self, section, key=None):
        """获取配置项"""
        if key is None:
            return self._config.get(section, {})
        return self._config.get(section, {}).get(key)

    def set(self, section, key, value):
        """设置配置项并保存"""
        if section not in self._config:
            self._config[section] = {}
        self._config[section][key] = value
        self._save_config()

    def get_data_dir(self):
        return self.data_dir

    @property
    def members_file(self):
        return os.path.join(self.data_dir, self.get('data', 'members_file'))

    @property
    def records_file(self):
        return os.path.join(self.data_dir, self.get('data', 'records_file'))

    def get_parking_config(self):
        """获取停车场配置"""
        return self.get('parking_lot')

    def get_logging_config(self):
        """获取日志配置，返回 dict，含 max_bytes, backup_count"""
        logging_cfg = self.get('logging') or {}
        return {
            'max_bytes': int(logging_cfg.get('max_bytes', self._default_config['logging']['max_bytes'])),
            'backup_count': int(logging_cfg.get('backup_count', self._default_config['logging']['backup_count']))
        }

    def get_gui_config(self):
        """获取GUI配置"""
        return self.get('gui')

    def get_data_config(self):
        """获取数据存储配置"""
        return self.get('data')

    @property
    def total_spaces(self):
        return self.get('parking_lot', 'total_spaces')

    @property
    def hourly_rate(self):
        return self.get('parking_lot', 'hourly_rate')

    @property
    def member_hourly_rate(self):
        return self.get('parking_lot', 'member_hourly_rate')

    def get_model_paths(self):
        """
        获取ONNX模型路径
        """
        # 支持在配置中指定 models: {"detect_model": "...", "rec_model": "..."}
        models = self.get('models')
        if not models:
            # 尝试读取默认 weights 目录（相对 src 层级）
            base = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'weights')
            return {
                'detect_model': os.path.join(base, 'plate_detect.onnx'),
                'rec_model': os.path.join(base, 'plate_rec_color.onnx')
            }
        return models


if __name__ == "__main__":
    config = Config()
    print("停车场总车位:", config.total_spaces)
    print("每小时费率:", config.hourly_rate)