# 智能停车场管理系统

一个开源的 Python 智能停车场管理项目，集成摄像头车牌检测与识别、车辆进出记录、会员管理与分段计费。项目重点在工程化与易用性：配置集中、日志完善、异步识别保证 UI 响应。车牌识别核心模型与解码逻辑位于 `parking_management/src/utils/plate_recognizer.py`，为不可随意修改的核心模块。

---

## 功能特点

- 🚗 **实时车牌识别**
  - 支持摄像头实时识别
  - 5秒连续识别，自动选择最优结果
  - 支持车牌颜色识别
- 📊 **停车场管理**
  - 车位状态实时监控
  - 智能分段计费系统
  - 支持普通用户和会员差别计费
  - 会员状态变更自动分段计费
  - 车辆进出记录管理
- 👥 **会员管理**
  - 会员添加与删除
  - 会员状态管理
  - 会员优惠价格设置
- 📈 **数据管理**
  - 历史记录查询
  - 支持日期范围筛选
  - 支持车牌号筛选
  - 停车时长统计
  - 费用明细查看
- 💻 **用户界面**
  - 直观的图形界面
  - 实时显示停车场状态
  - 支持手动输入和自动识别
  - 管理员控制面板

---

## 目录（快速导航）

- [特性](#功能特点)
- [环境要求](#环境要求)
- [快速开始（Windows）](#快速开始windows)
- [快速开始（Linux/macOS）](#快速开始linuxmacos)
- [GPU 加速说明](#gpu-加速说明)
- [运行与使用](#运行与使用)
- [配置](#配置)
- [故障排查](#故障排查)
- [开发者指南](#开发者指南)
- [贡献与许可证](#贡献与许可证)

---

## 环境要求

- Python 3.8+
- OpenCV
- PySide6
- pandas
- ONNX Runtime（建议：`onnxruntime-gpu`，无 GPU 时回退到 `onnxruntime`）

依赖已列在 `parking_management/requirements.txt`。

---

## 快速开始（Windows）

### 安装步骤

1. 克隆仓库并进入目录：

   ```powershell
   git clone https://github.com/yin1895/parking-management.git
   cd parking-management
   ```

2. 创建并激活虚拟环境（venv 示例）：

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   或使用 Anaconda：

   ```bash
   conda create -n parking python=3.8
   conda activate parking
   ```

3. 安装依赖：

   ```powershell
   pip install -r parking_management/requirements.txt
   # 若需 GPU 支持（Windows + CUDA），建议先安装 onnxruntime-gpu：
   # pip install --no-cache-dir onnxruntime-gpu
   ```

4. 运行程序：

   ```powershell
   python main.py
   ```

5. 运行测试（可选）：

   ```powershell
   .\.venv\Scripts\python.exe -m pytest -q
   ```

---

## 快速开始（Linux / macOS）

1. 克隆并进入：

   ```bash
   git clone https://github.com/yin1895/parking-management.git
   cd parking-management
   ```

2. 创建并激活虚拟环境：

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. 安装依赖：

   ```bash
   pip install -r parking_management/requirements.txt
   # 若需 GPU 支持（Linux + CUDA），请根据你的 CUDA 与 cuDNN 版本安装兼容的 onnxruntime-gpu wheel
   ```

4. 运行：

   ```bash
   python parking_management/main.py
   ```

---

## 使用说明

### 基本操作

1. 启动系统：

   ```powershell
   python main.py
   ```

2. 车牌识别

   - 点击"开启摄像头"按钮启动识别
   - 系统将在5秒内进行连续识别，自动选择最佳识别结果

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

---

## 项目结构

```
parking_management/
├── data/           # 数据和配置文件
├── weights/        # 模型文件
├── src/            # 源代码
│   ├── core/       # 核心业务逻辑
│   ├── gui/        # 图形界面
│   └── utils/      # 工具类
├── main.py         # 程序入口
└── requirements.txt # 项目依赖
```

---

## GPU 加速说明

- 推荐在支持 CUDA 的机器上安装 `onnxruntime-gpu` 以获得更快的推理速度。
- 代码默认尝试按优先级使用 provider（如 `['CUDAExecutionProvider','CPUExecutionProvider']`）。若加载 GPU provider 失败，会自动回退到 CPU 并在日志中记录。
- 项目在能检测到 `CUDAExecutionProvider` 时会尝试使用 ONNX Runtime 的 IOBinding（若运行时支持）以减少 host<->device 的复制；若不可用则回退为普通 `session.run()`。

常用排查命令（在虚拟环境中运行）：

```powershell
python -c "import onnxruntime as ort; print(getattr(ort,'__file__',None), getattr(ort,'__version__',None), hasattr(ort,'SessionOptions'), ort.get_available_providers())"
```

如果输出异常或没有 `SessionOptions`，尝试卸载并重装：

```powershell
pip uninstall -y onnxruntime onnxruntime-gpu
pip install --no-cache-dir onnxruntime-gpu
```

---

## 配置说明

系统配置文件位于 `parking_management/data/config.json`，可修改以下参数：

- 停车场容量
- 计费标准（普通/会员）
- 界面刷新率
- 其他系统参数

可用环境变量覆盖部分配置，例如：`PLATE_USE_CUDA=1` 强制尝试 CUDA。

---

## 常见问题

1. **摄像头无法打开**
   - 检查摄像头连接
   - 确认摄像头未被其他程序占用
   - 检查摄像头驱动是否正确安装
   - 检查摄像头物理开关是否打开

2. **车牌识别不准确**
   - 确保光线充足
   - 调整摄像头角度
   - 确保车牌在画面中清晰可见

3. **管理员登录问题**
   - 确认使用默认账号密码
   - 检查输入是否正确（注意大小写）

4. **识别模块导入失败**
   - 确认已激活虚拟环境并安装 `onnxruntime` 或 `onnxruntime-gpu`
   - 如遇模块不完整（如 `SessionOptions` 丢失），请尝试重新安装

5. **摄像头无法打开**
   - 检查设备权限与驱动；尝试系统相机应用确认设备正常
   - 控件会探测索引 0..4，部分设备在更高索引上才可用

6. **识别准确率问题**
   - 检查光照、摄像头分辨率、车牌角度与清晰度

清理 Python 缓存（删除 __pycache__ 与 .pyc，保留 .venv）：

```powershell
Get-ChildItem -Path . -Recurse -Include '__pycache__','*.pyc' | Where-Object { $_.FullName -notmatch '\.venv\\' } | ForEach-Object { Remove-Item -LiteralPath $_.FullName -Recurse -Force }
```

---

## 开发计划

- [x] 添加会员管理功能
- [x] 实现分段计费系统
- [x] 添加历史记录查询
- [ ] 添加数据统计和报表功能
- [ ] 优化车牌识别准确率
- [ ] 添加更多用户权限管理
- [ ] 支持多摄像头接入

---

## 开发者指南

- 主要代码位置：
  - 核心逻辑：`parking_management/src/core/parking_lot.py`
  - GUI：`parking_management/src/gui/`（组件化为多个 panel）
  - 识别：`parking_management/src/utils/plate_recognizer.py`
- 测试：`parking_management/tests/`（使用 pytest）
- 日志：由 `src/utils/logger.py` 管理，默认写入 `parking_management/data/logs/`

近期改动：

- GUI 组件化（StatusPanel / CameraPanel / ControlPanel / VehicleTable）
- 添加多摄像头支持与手动图片上传识别
- 添加 IOBinding 的尝试支持（GPU 情况下）并自动回退
- 健壮性改进：处理空 CSV、避免 numpy 真值困扰、线程生命周期管理

---

## 贡献

欢迎提交 Issue / Pull Request 来帮助改进项目。请在 PR 中包含：

- 变更说明
- 测试步骤或已通过的测试

---

## 许可证

MIT License — 详情见 LICENSE 文件。

---

## 联系方式

如有问题或建议，请通过以下方式联系：

- Email: 3023001549@tju.edu.cn

