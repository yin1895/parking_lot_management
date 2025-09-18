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
# 智能停车场管理系统

一个基于 Python 的智能停车场管理系统，集成了车牌检测与识别、车辆进出和会员管理。该项目以工程化、可维护性为目标，车牌识别核心（模型与解码逻辑）为关键部分，已尽量与外围逻辑解耦。

## 功能概览

- 实时车牌检测与识别（支持摄像头与手动图片上传）
- 多摄像头选择与切换
- 异步识别（QThread worker），避免阻塞 UI
- 车辆进/出记录、分段计费与会员规则支持
- 管理员面板与历史记录查询

## 要求

- Python 3.8+
- OpenCV
- PySide6
- pandas
- ONNX Runtime（建议安装 `onnxruntime-gpu` 以启用 CUDA 加速；无 GPU 时回退到 CPU 版本）
- 其余依赖请参见 `parking_management/requirements.txt`

> 注意：本项目中车牌识别模型和权重文件放在 `parking_management/src/weights/`，不要在未备份情况下随意替换模型文件。

## 快速安装（Windows 示例）

1. 克隆仓库并进入目录：

```powershell
git clone https://github.com/yin1895/parking-management.git
cd parking-management
```

2. 创建并激活虚拟环境（建议使用 venv 或 conda）：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. 安装依赖：

```powershell
pip install -r parking_management/requirements.txt
# 若想启用 GPU（CUDA），可先安装 onnxruntime-gpu：
# pip install --no-cache-dir onnxruntime-gpu
```

4. 运行测试（可选）：

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

5. 启动应用：

```powershell
python parking_management\main.py
```

## GPU 加速与 ONNX Runtime（简要说明）

- 推荐安装 `onnxruntime-gpu`（在支持的 Windows + CUDA 环境中可显著加快推理）。
- 代码已实现“GPU 优先、失败回退到 CPU”的策略：程序会尝试使用 CUDAExecutionProvider 加载模型，若失败会自动回退到 CPUExecutionProvider，并在日志中记录所用 provider。
- 对于大尺寸或高吞吐场景，代码尝试使用 ONNX Runtime 的 IOBinding（若可用）以减少 host<->device 复制，若环境不支持则回退为普通的 `session.run()`。

常见排查命令（在虚拟环境中运行）：

```powershell
python -c "import onnxruntime as ort; print(getattr(ort,'__file__',None), getattr(ort,'__version__',None), hasattr(ort,'SessionOptions'))"
```

如果输出显示 `SessionOptions` 不可用或模块路径异常，通常为安装不完整或环境被覆盖（请尝试卸载并重装 `onnxruntime-gpu`）。

## 使用说明（简要）

- 启动后在主界面选择摄像头并点击“开启摄像头”开始实时识别。
- 系统会在识别时间窗口（可配置）内连续识别并在结束时选择最常见/置信最高的结果填入输入框。
- 也可通过“上传图片”手动识别单张图片，识别在后台线程执行，不会阻塞 UI。

## 配置

主要配置位于 `parking_management/data/config.json`（也可通过环境变量覆盖常用项）。常见可配置项：

- 模型路径（detect/rec）
- GUI 刷新率
- 计费规则与停车容量

请在修改前备份原配置文件。

## 故障排查

- 识别模块无法导入：
  - 检查虚拟环境是否激活并且已安装 `onnxruntime` 或 `onnxruntime-gpu`。
  - 尝试卸载并重装：

```powershell
pip uninstall -y onnxruntime onnxruntime-gpu
pip install --no-cache-dir onnxruntime-gpu
```

- 摄像头无法打开：检查设备索引、摄像头权限与驱动，尝试使用系统相机应用确认设备可用。
- 识别精度低：改善光照、提高分辨率或调整摄像头角度。
- 清理缓存（删除 Python 字节码）：

```powershell
Get-ChildItem -Path . -Recurse -Include '__pycache__','*.pyc' | Where-Object { $_.FullName -notmatch '\.venv\\' } | ForEach-Object { Remove-Item -LiteralPath $_.FullName -Recurse -Force }
```

## 开发说明（近期改动）

- GUI 组件化（StatusPanel、CameraPanel、ControlPanel、VehicleTable）
- 增加多摄像头与手动上传图片功能
- 添加异步识别 worker（QThread）以提升 UI 响应性
- 增强 ParkingLot 与日志处理的鲁棒性

车牌识别核心算法在 `parking_management/src/utils/plate_recognizer.py`，为项目敏感核心，外围优化已做但核心识别逻辑尽量保持不变。

## 贡献

- 欢迎提交 issue 和 pull request。提交前请确保：
  - 运行并通过现有测试
  - 在 PR 描述中说明修改点与原因

## 许可证

MIT License — 详情见 LICENSE。

## 联系

若需帮助请发邮件：3023001549@tju.edu.cn
