# Fisher钓鱼模块 v1.0

## 概述
Fisher是AutoFish项目的核心钓鱼模块，采用清晰的模块化架构和UI逻辑分离设计，实现智能化钓鱼自动化。

## 功能特性

### 🎯 核心功能
- **智能状态识别**: 基于YOLO模型识别7种钓鱼状态
- **OCR文字识别**: 智能识别"向左拉"、"向右拉"提示
- **多线程协调**: 主控制线程、鼠标点击线程、OCR识别线程
- **状态机逻辑**: 完整的钓鱼流程自动化控制

### 🔧 技术特点
- **模块化架构**: 清晰的功能模块划分
- **配置管理**: 灵活的YAML配置系统
- **线程安全**: 完善的多线程协调机制
- **UI分离**: 界面逻辑与业务逻辑完全分离

## 状态映射表

| 状态编号 | 状态名称 | 检测方式 | 说明 |
|---------|---------|---------|------|
| 0 | 等待上钩状态 | YOLO | 初始等待状态 |
| 1 | 鱼上钩末提线状态 | YOLO | 触发快速点击 |
| 2 | 提线中_耐力未到二分之一 | YOLO | 继续快速点击 |
| 3 | 提线中_耐力已到二分之一 | YOLO | 暂停点击等待 |
| 4 | 向右拉_txt | OCR | 按D键 |
| 5 | 向左拉_txt | OCR | 按A键 |
| 6 | 钓鱼成功状态_txt | YOLO | 按F键确认 |

## 模块架构

### 核心模块
```
modules/fisher/
├── config.py              # 配置管理
├── model_detector.py      # YOLO模型检测
├── ocr_detector.py        # OCR文字识别
├── input_controller.py    # 输入控制
├── fishing_controller.py  # 钓鱼控制器
├── ui.py                 # UI界面
├── main.py              # 程序入口
├── config.yaml          # 配置文件
└── README.md           # 说明文档
```

### 模块职责

#### 1. 配置管理 (config.py)
- 统一的配置管理系统
- 支持YAML配置文件
- 热键、时间、路径等配置项
- 配置验证和保存功能

#### 2. 模型检测器 (model_detector.py)
- YOLO模型加载和推理
- 屏幕截图和状态检测
- GPU/CPU自动选择
- 置信度阈值管理

#### 3. OCR检测器 (ocr_detector.py)
- Tesseract OCR初始化
- 文字识别和预处理
- 方向文字检测
- 置信度过滤

#### 4. 输入控制器 (input_controller.py)
- 多线程鼠标点击
- 键盘按键模拟
- 随机时间间隔
- 线程安全控制

#### 5. 钓鱼控制器 (fishing_controller.py) 
- 状态机核心逻辑
- 多线程协调管理
- 超时处理机制
- 状态转换控制

#### 6. UI界面 (ui.py)
- 主控制界面
- 状态显示窗口
- 设置对话框
- 实时状态更新

## 钓鱼流程

### 流程图
```
开始 → 检测状态0/1 → 快速点击 → 状态2/3切换 → OCR方向检测 → 状态6处理 → 抛竿 → 循环
```

### 详细流程
1. **初始检测**: 识别状态0或1，3分钟超时
2. **点击阶段**: 状态1触发快速点击线程
3. **提线阶段**: 状态2/3切换，控制点击暂停/恢复
4. **方向控制**: OCR识别4/5状态，按对应方向键
5. **成功处理**: 状态6等待1.5秒按F键
6. **抛竿循环**: 长按2秒鼠标左键，进入下一轮

## 多线程架构

### 线程设计
- **主控制线程**: 状态机逻辑，状态转换控制
- **鼠标点击线程**: 独立的快速点击控制
- **OCR识别线程**: 方向文字检测和按键响应

### 线程通信
- 使用`threading.Event`控制线程状态
- 线程安全的状态更新机制  
- 统一的资源清理和异常处理

## 配置说明

### 模型配置
```yaml
model:
  model_path: "runs/fishing_model_latest.pt"
  confidence_threshold: 0.5
  device: "auto"
  detection_interval: 0.1
```

### OCR配置
```yaml
ocr:
  tesseract_path: "D:\\Python\\tool\\Tesseract-OCR"
  language: "chi_sim+eng"
  confidence_threshold: 60
  detection_interval: 0.2
```

### 时间配置
```yaml
timing:
  initial_timeout: 180
  click_delay_min: 0.054
  click_delay_max: 0.127
  state3_pause_time: 1.0
  success_wait_time: 1.5
  cast_hold_time: 2.0
  key_press_time: 1.0
```

## 使用方法

### 启动程序
```bash
# 直接启动Fisher模块
python modules/fisher/main.py

# 或通过主程序启动
python main.py
```

### 界面操作
1. **开始钓鱼**: 点击"开始钓鱼"按钮或使用热键
2. **停止钓鱼**: 点击"停止钓鱼"按钮或使用热键
3. **查看设置**: 点击"设置"按钮配置参数
4. **状态监控**: 左上角状态窗口实时显示

### 热键操作
- `Ctrl+Alt+S`: 开始钓鱼
- `Ctrl+Alt+X`: 停止钓鱼  
- `Ctrl+Alt+Q`: 紧急停止

## 系统要求

### 必要依赖
- Python 3.7+
- PyTorch + Ultralytics (YOLO)  
- OpenCV + PIL (图像处理)
- Tesseract OCR (文字识别)
- PyAutoGUI (输入模拟)
- tkinter (界面框架)

### 系统配置
- 模型文件: `runs/fishing_model_latest.pt`
- OCR路径: `D:\Python\tool\Tesseract-OCR`
- 支持GPU加速 (可选)

## 开发说明

### 代码规范
- 遵循PEP 8编码规范
- 完整的中文注释说明
- 类型提示和文档字符串
- 异常处理和资源清理

### 扩展开发
- 模块化设计便于功能扩展
- 清晰的接口定义和文档
- 配置驱动的参数管理
- 完善的错误处理机制

## 故障排除

### 常见问题
1. **模型加载失败**: 检查模型文件路径和权限
2. **OCR初始化失败**: 检查Tesseract安装和路径
3. **点击无响应**: 检查管理员权限和游戏窗口
4. **状态检测异常**: 调整置信度阈值和检测间隔

### 调试方法
- 查看控制台输出日志
- 使用设置界面测试组件
- 检查配置文件参数
- 验证系统依赖完整性

## 版本历史

### v1.0 (2024-12-28)
- 🎯 完整的钓鱼状态机实现
- 🔧 模块化架构重构
- 🖥️ 用户友好的GUI界面
- ⚙️ 灵活的配置管理系统
- 🧵 稳定的多线程协调机制

## 许可证
本项目遵循MIT许可证，详见LICENSE文件。

## 贡献
欢迎提交Issue和Pull Request来改进项目。

---
*AutoFish Team - 让钓鱼更智能* 