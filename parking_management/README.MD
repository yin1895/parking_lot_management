# 停车场管理系统

本仓库为一个简单的停车场管理系统，包含车牌识别、GUI 管理界面、会员与计费功能。

快速开始：

1. 创建并激活虚拟环境（Windows PowerShell）：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. 运行程序：

```powershell
python main.py
```

3. 运行测试：

```powershell
pytest -q tests
```

说明：
- 配置文件位于 `data/config.json`，可通过环境变量 `PARKING_DATA_DIR` 覆盖数据目录位置。
- 日志保存在 `data/logs/parking_app.log`。