# 智能停车场管理系统

一个基于Python的智能停车场管理系统，集成了车牌识别功能，支持实时摄像头识别、会员管理和停车记录管理。

## 功能特点

- 🚗 实时车牌识别
  - 支持摄像头实时识别
  - 5秒连续识别，自动选择最优结果
  - 支持车牌颜色识别

- 📊 停车场管理
  - 车位状态实时监控
  - 智能分段计费系统
    - 支持普通用户和会员差别计费
    - 支持会员状态变更自动分段计费
  - 车辆进出记录管理

- 👥 会员管理
  - 会员添加与删除
  - 会员状态管理
  - 会员优惠价格设置

- 📈 数据管理
  - 历史记录查询
    - 支持日期范围筛选
    - 支持车牌号筛选
  - 停车时长统计
  - 费用明细查看

- 💻 用户界面
  - 直观的图形界面
  - 实时显示停车场状态
  - 支持手动输入和自动识别
  - 管理员控制面板

## 系统要求

- Python 3.8+
- OpenCV
- PySide6
- ONNX Runtime (推荐 `onnxruntime-gpu` 用于启用 CUDA 加速，若无 GPU 则可回退到 CPU 版本)
- Pandas
- 其他依赖见 requirements.txt

## 安装步骤

1. 克隆仓库
## 安装步骤

1. 克隆仓库
```bash     
git clone https://github.com/yin1895/parking-management.git
cd parking-management
```

2. 创建虚拟环境（推荐使用anaconda）
```bash
conda create -n parking python=3.8
conda activate parking
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 运行程序
```bash
python main.py
```

## 使用说明

### 基本操作
1. 启动系统
```bash
python main.py
```

2. 车牌识别
- 点击"开启摄像头"按钮启动识别
- 系统将在5秒内进行连续识别
- 自动选择最佳识别结果

3. 车辆管理
- 车辆入场：输入车牌号或使用识别结果，点击"车辆入场"
- 车辆出场：输入车牌号或使用识别结果，点击"车辆出场"
- 系统自动记录时间并计算费用

### 管理员功能
1. 登录管理界面
- 点击"管理员入口"
- 默认账号：admin
- 默认密码：1234

2. 会员管理
- 添加/删除会员
- 查看会员列表
- 设置会员价格

3. 历史记录查询
- 按日期范围查询
- 按车牌号筛选
- 查看详细停车记录

## 项目结构

# 智能停车场管理系统

这是一个基于 Python 的智能停车场管理示例项目，包含摄像头车牌检测与识别、车辆进出记录、会员与计费管理以及图形化管理界面。

本仓库是我的计算机视觉学习副产物，侧重于工程化（配置、日志、UI 可用性）与可维护性。项目的车牌识别核心（模型与解码逻辑）为关键逻辑，且耦合度很低。PS：如果你有毕设、生产需求可以cv拿走，但是请尽量保持不变，可仅在外围加入可配置项与异步调用以提升稳定性。

## 快速开始

环境要求
- **Python 3.8+**（项目已针对 3.10/3.13 做兼容性处理）  
  **注意：经测试反馈，在 Python 3.8 环境下偶见识别模块导入失败问题，迁移至高版本可解决此问题。**
- OpenCV
- PySide6
- ONNX Runtime（建议安装 `onnxruntime-gpu` 以启用 CUDA 加速；如无 GPU 环境可使用 `onnxruntime` CPU 版本）
- pandas

1. 克隆仓库并进入目录

```powershell
git clone https://github.com/yin1895/parking-management.git
cd parking-management
```

2. 创建并激活虚拟环境（示例 Windows + venv）

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. 安装依赖

```powershell
pip install -r parking_management/requirements.txt
# 若要启用 GPU 加速（Windows + CUDA），推荐先安装对应的 wheel，例如：
# pip install onnxruntime-gpu
```

4. 运行测试（可选）

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

5. 启动程序

```powershell
python parking_management\main.py
```

## 主要功能

- 实时车牌检测与识别（基于 ONNX 模型）
- 支持摄像头实时识别与手动上传图片识别（异步、QThread）
- 多摄像头选择（自动探测常见索引）
- 车辆入/出管理与分段计费，支持会员差异化计费
- 管理员面板与会员管理

## 配置

项目默认配置位于 `parking_management/data/config.json`，可通过该文件或环境变量覆盖以下项（示例）：

- 模型文件路径
- GUI 刷新率
- 停车场容量与计费规则

不要在未备份的情况下修改识别模型文件（weights），除非你清楚改动影响；识别算法核心已被视为不可随意更改的敏感部分。

## 清理与常见问题

- 如果你遇到奇怪的问题(例如识别模块忽然无法导入)或想要减小仓库体积，可以删除 Python 编译缓存：

```powershell
Get-ChildItem -Path . -Recurse -Include '__pycache__','*.pyc' | Where-Object { $_.FullName -notmatch '\.venv\\' } | ForEach-Object { Remove-Item -LiteralPath $_.FullName -Recurse -Force }
```

- 摄像头无法打开：检查权限、驱动、设备索引（ControlPanel 自动探测 0..4）、某些设备有物理开关
- 识别不准确：改善光线、调整摄像头角度或图片清晰度

## 开发与变更记录（近期）

- 重构：将 GUI 组件化（StatusPanel、CameraPanel、ControlPanel、VehicleTable），简化主窗口职责
- 增强：添加多摄像头选择、手动图片上传与拖放、异步识别 `RecognizeWorker(QThread)`
- 改进：集中化配置、日志（旋转日志）与对 ParkingLot 的健壮性改进
- 保留原则：车牌识别的核心逻辑未被修改，仅添加了可配置参数与外围预处理选项

## 贡献

欢迎提交 issue 或 pull request。提交前请确保：

- 运行并通过现有测试
- 说明你遇到的和解决的问题
- 遵守 `.gitignore` 里的规则，不提交编译缓存

## 许可证

MIT License — 详情见 LICENSE 文件

## 联系

Feel Free To Contact Me：3023001549@tju.edu.cn
