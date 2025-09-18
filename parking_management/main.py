import sys
import os
from PySide6.QtWidgets import QApplication
from src.gui.main_window import MainWindow
from src.utils.config import Config
from src.utils.logger import get_logger

def init_project():
    """初始化项目必要的目录结构"""
    # 确保数据目录存在
    cfg = Config()
    os.makedirs(cfg.get_data_dir(), exist_ok=True)
    # create logs directory
    os.makedirs(os.path.join(cfg.get_data_dir(), 'logs'), exist_ok=True)

def main():
    """程序主入口"""
    try:
        # 初始化项目结构
        init_project()
        # 加载配置
        config = Config()
        # 初始化日志
        logger = get_logger('parking_app')
        logger.info('Starting application')

        # 创建QApplication实例
        app = QApplication(sys.argv)

        # 创建并显示主窗口
        window = MainWindow()
        window.show()

        # 运行应用程序
        sys.exit(app.exec())

    except Exception as e:
        # 在发生异常时写日志
        try:
            logger = get_logger('parking_app')
            logger.exception('程序启动错误')
        except Exception:
            print(f"程序启动错误: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()