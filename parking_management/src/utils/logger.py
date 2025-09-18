import logging
import os
from logging.handlers import RotatingFileHandler
from .config import Config


def get_logger(name=__name__, *, max_bytes=5 * 1024 * 1024, backup_count=5):
    """返回一个配置好的 logger，日志会写入 data/logs/parking_app.log 并按大小轮转。

    参数:
        name: logger 名称
        max_bytes: 单个日志文件最大字节数，默认 5MB
        backup_count: 保留的轮转文件数量
    """
    cfg = Config()
    data_dir = cfg.get_data_dir()
    # 从配置读取轮转参数（允许通过 config.json 或环境变量调整）
    try:
        logging_cfg = cfg.get_logging_config()
        max_bytes = int(logging_cfg.get('max_bytes', max_bytes))
        backup_count = int(logging_cfg.get('backup_count', backup_count))
    except Exception:
        # 忽略配置读取错误，使用默认参数
        pass
    log_dir = os.path.join(data_dir, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, 'parking_app.log')

    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)

        # 按大小轮转的文件处理器
        fh = RotatingFileHandler(log_path, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8')
        fh.setLevel(logging.DEBUG)

        # 控制台处理器
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        logger.addHandler(fh)
        logger.addHandler(ch)
    return logger
