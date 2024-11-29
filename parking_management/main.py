import sys
import os
from PySide6.QtWidgets import QApplication
from src.gui.main_window import MainWindow
from src.utils.config import Config

def init_project():
    """初始化项目必要的目录结构"""
    # 确保数据目录存在
    os.makedirs('data', exist_ok=True)

def main():
    """程序主入口"""
    try:
        # 初始化项目结构
        init_project()
        
        # 加载配置
        config = Config()
        
        # 创建QApplication实例
        app = QApplication(sys.argv)
        
        # 创建并显示主窗口
        window = MainWindow()
        window.show()
        
        # 运行应用程序
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"程序启动错误: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()