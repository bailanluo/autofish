# Fisher钓鱼模块项目框架文档 v1.0

## 项目概述
Fisher是AutoFish项目的全新钓鱼模块，采用清晰的模块化架构和UI逻辑分离设计，实现智能化钓鱼自动化。本文档描述了完整的项目架构和各组件功能。

## 目录结构
```
modules/fisher/
├── __init__.py              # 模块初始化
├── config.py               # 配置管理器
├── model_detector.py       # YOLO模型检测器
├── ocr_detector.py         # OCR文字识别器
├── input_controller.py     # 输入控制器
├── fishing_controller.py   # 钓鱼控制器(核心)
├── ui.py                  # UI界面模块
├── main.py                # 程序入口
├── config.yaml            # 配置文件
├── test_fisher.py         # 测试脚本
└── README.md             # 说明文档
```

## 核心架构

### 1. 配置管理器 (config.py)
**职责**: 统一的配置管理系统
**功能**:
- YAML配置文件加载和保存
- 配置项验证和默认值管理
- 动态配置更新和热键设置
- 路径验证和状态映射

**核心类**:
- `FisherConfig`: 主配置管理类
- `ModelConfig`: 模型相关配置
- `OCRConfig`: OCR相关配置
- `TimingConfig`: 时间相关配置
- `HotkeyConfig`: 热键相关配置
- `UIConfig`: 界面相关配置

**全局实例**: `fisher_config`

### 2. 模型检测器 (model_detector.py)
**职责**: YOLO模型加载和钓鱼状态检测
**功能**:
- YOLO模型初始化和设备选择
- 屏幕截图和图像预处理
- 状态0-3、6的识别和置信度管理
- 多状态检测和特定状态过滤

**核心类**:
- `ModelDetector`: 主检测器类

**全局实例**: `model_detector`

### 3. OCR检测器 (ocr_detector.py)
**职责**: Tesseract OCR初始化和文字识别
**功能**:
- OCR引擎初始化和测试
- 图像预处理和文字提取
- 方向文字检测(状态4、5)
- 置信度过滤和结果验证

**核心类**:
- `OCRDetector`: 主OCR检测器类

**全局实例**: `ocr_detector`

### 4. 输入控制器 (input_controller.py)
**职责**: 鼠标键盘操作和多线程控制
**功能**:
- 多线程鼠标快速点击
- 键盘按键模拟(A/D/F键)
- 随机时间间隔和线程安全
- 鼠标长按和紧急停止

**核心类**:
- `InputController`: 主输入控制器类

**全局实例**: `input_controller`

### 5. 钓鱼控制器 (fishing_controller.py) ⭐ 核心
**职责**: 钓鱼状态机和多线程协调
**功能**:
- 完整的钓鱼状态机逻辑
- 三线程协调管理(主控制/点击/OCR)
- 超时处理和异常恢复
- 状态转换和回调通知

**核心类**:
- `FishingController`: 主控制器类
- `FishingState`: 状态枚举
- `FishingStatus`: 状态信息类

**全局实例**: `fishing_controller`

### 6. UI界面模块 (ui.py)
**职责**: 图形用户界面和用户交互
**功能**:
- 主控制界面(开始/停止/设置)
- 透明状态显示窗口
- 设置对话框和参数配置
- 实时状态更新和日志显示

**核心类**:
- `FisherUI`: 主界面类
- `StatusWindow`: 状态显示窗口
- `SettingsDialog`: 设置对话框

**全局实例**: `fisher_ui`

## 状态机流程

### 钓鱼状态定义
```python
class FishingState(Enum):
    STOPPED = "停止状态"
    WAITING_INITIAL = "等待初始状态"
    WAITING_HOOK = "等待上钩状态"
    FISH_HOOKED = "鱼上钩状态"
    PULLING_NORMAL = "提线中_耐力未到二分之一"
    PULLING_HALFWAY = "提线中_耐力已到二分之一"
    SUCCESS = "钓鱼成功状态"
    CASTING = "抛竿状态"
    ERROR = "错误状态"
```

### 状态转换流程
```
STOPPED → WAITING_INITIAL → WAITING_HOOK → FISH_HOOKED 
    ↓
PULLING_NORMAL ⇄ PULLING_HALFWAY → SUCCESS → CASTING → WAITING_INITIAL
    ↓
  ERROR (异常处理)
```

## 多线程架构

### 线程设计
1. **主控制线程**: 
   - 状态机逻辑控制
   - 模型检测和状态转换
   - 超时处理和异常恢复

2. **鼠标点击线程**:
   - 状态1激活，快速点击
   - 状态3暂停，状态2恢复
   - 状态6停止，线程安全控制

3. **OCR识别线程**:
   - 状态2/3激活
   - 方向文字检测(4/5)
   - 对应按键响应(A/D)

### 线程通信
- `threading.Event`: 线程状态控制
- `threading.Lock`: 状态更新同步
- 回调函数: UI状态更新
- 统一异常处理和资源清理

## 配置系统

### 配置文件结构 (config.yaml)
```yaml
model:              # 模型配置
  model_path: "runs/fishing_model_latest.pt"
  confidence_threshold: 0.5
  device: "auto"
  detection_interval: 0.1

ocr:                # OCR配置
  tesseract_path: "D:\\Python\\tool\\Tesseract-OCR"
  language: "chi_sim+eng"
  confidence_threshold: 60
  detection_interval: 0.2

timing:             # 时间配置
  initial_timeout: 180
  click_delay_min: 0.054
  click_delay_max: 0.127
  state3_pause_time: 1.0
  success_wait_time: 1.5
  cast_hold_time: 2.0
  key_press_time: 1.0

hotkey:             # 热键配置
  start_fishing: "ctrl+alt+s"
  stop_fishing: "ctrl+alt+x"
  emergency_stop: "ctrl+alt+q"

ui:                 # 界面配置
  show_status_window: true
  status_window_position: [10, 10]
  status_window_color: "blue"
  main_window_size: [400, 300]
```

## 公共组件

### 日志系统
- 使用项目全局日志系统: `modules/logger.py`
- 统一的日志格式和颜色方案
- 实时日志显示和文件保存

### 工具类库
- 图像处理: `utils/image_utils.py`
- 文件操作: `utils/file_utils.py`
- 热键管理: `utils/hotkey_utils.py`

### 数据目录
- 模型文件: `runs/fishing_model_latest.pt`
- 配置文件: `config/fishing_config.yaml`

## API接口

### 主要对外接口
```python
# 配置管理
fisher_config.get_model_path()
fisher_config.validate_paths()
fisher_config.save_config()

# 模型检测
model_detector.detect_states(image=None)
model_detector.detect_specific_state(target_state)
model_detector.capture_screen(region=None)

# OCR识别
ocr_detector.detect_direction_text(image=None)
ocr_detector.extract_text(image)

# 输入控制
input_controller.start_clicking()
input_controller.stop_clicking()
input_controller.press_key(key, duration=None)

# 钓鱼控制
fishing_controller.start_fishing()
fishing_controller.stop_fishing()
fishing_controller.set_status_callback(callback)

# UI界面
fisher_ui.create_window()
fisher_ui.run()
```

## 错误处理

### 异常类型
- 模型加载异常
- OCR初始化异常
- 输入设备异常
- 线程同步异常
- 配置文件异常

### 处理机制
- 完善的异常捕获和日志记录
- 自动重试和降级处理
- 资源清理和状态恢复
- 用户友好的错误提示

## 扩展点

### 功能扩展
- 新状态检测: 在`model_detector.py`中添加
- 新按键操作: 在`input_controller.py`中添加
- 新配置项: 在`config.py`中添加
- 新UI组件: 在`ui.py`中添加

### 算法优化
- 检测间隔动态调整
- 置信度自适应阈值
- 多模型集成检测
- 性能监控和优化

## 测试和调试

### 测试脚本
- `test_fisher.py`: 完整的模块测试
- 各模块独立测试功能
- 依赖项检查和验证

### 调试方法
- 控制台日志输出
- UI实时状态显示
- 配置参数动态调整
- 性能指标监控

## 部署和使用

### 环境要求
- Python 3.7+
- PyTorch + Ultralytics
- OpenCV + PIL
- Tesseract OCR
- PyAutoGUI + keyboard

### 启动方式
```bash
# 测试模块
python modules/fisher/test_fisher.py

# 启动Fisher
python modules/fisher/main.py

# 通过主程序
python main.py
```

### 配置建议
- 根据硬件调整检测间隔
- 根据游戏调整置信度阈值
- 根据习惯设置热键
- 根据屏幕调整状态窗口位置

## 版本历史

### v1.0.1 (2024-12-28)
- **错误修复版本**
- 修复mss库线程安全问题 - 屏幕截取延迟初始化
- 修复方法命名冲突 - stop_clicking Event对象重命名
- 新增热键管理器模块 - 独立热键处理
- 改进资源清理逻辑
- 增强错误处理和调试信息

### v1.0 (2024-12-28)
- 初始版本发布
- 完整的7模块架构
- 基础钓鱼功能实现
- 多线程状态机

---
*AutoFish Team - Fisher钓鱼模块架构文档*
*创建时间: 2024-12-28*
*版本: v1.0.1* 