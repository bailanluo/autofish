# AutoFish v2.4 重构版 - 使用说明

## 🎯 重构版特色

- **精简架构** - 从15个文件精简为5个核心模块
- **代码减少60%** - 去除过度设计，专注核心功能
- **稳定可靠** - 完善的错误处理和资源管理
- **易于维护** - 清晰的模块职责分离

## 🚀 快速开始

### 1. 测试环境
```bash
# 运行测试脚本验证所有模块
python modules/auto_fisher/test_refactored.py
```

### 2. 启动程序
```bash
# 方式一：直接运行Python脚本
python modules/auto_fisher/new_main.py

# 方式二：使用启动脚本（Windows）
启动重构版钓鱼.bat
```

## ⚙️ 配置要求

### 必需文件
- **模型文件**: `runs/fishing_model_latest.pt`
- **OCR程序**: `D:\Python\tool\Tesseract-OCR`

### 配置文件
程序首次运行会自动创建：`config/fishing_config.yaml`

## 🎮 使用界面

### 主界面功能
- **开始钓鱼** - 启动自动钓鱼程序
- **停止钓鱼** - 停止钓鱼程序
- **设置** - 配置快捷键和界面选项

### 状态显示窗口
- 位置：屏幕左上角
- 显示：当前钓鱼状态
- 样式：蓝色字体，透明背景

### 设置选项
- 快捷键配置（开始/停止/暂停）
- 界面显示选项
- 状态窗口开关

## 🔄 钓鱼流程

```
1. 等待进入钓鱼状态 (检测状态0或1)
2. 等待上钩 (状态0)
3. 鱼上钩 (状态1) → 开始快速点击
4. 提线中 (状态2) → 继续点击 + OCR检测
5. 耐力不足 (状态3) → 暂停点击 + OCR检测
6. 方向控制 (状态4/5) → 按住方向键 (A/F)
7. 钓鱼成功 (状态6) → 确认 → 抛竿 → 重新开始
```

## 📊 状态映射

| 状态ID | 状态名称 | 检测方式 | 操作 |
|--------|----------|----------|------|
| 0 | 等待上钩状态 | YOLO | 等待 |
| 1 | 鱼上钩末提线状态 | YOLO | 快速点击 |
| 2 | 提线中_耐力未到二分之一 | YOLO | 继续点击+OCR |
| 3 | 提线中_耐力已到二分之一 | YOLO | 暂停点击+OCR |
| 4 | 向右拉_txt | OCR | 按住F键 |
| 5 | 向左拉_txt | OCR | 按住A键 |
| 6 | 钓鱼成功状态_txt | YOLO/OCR | 确认+抛竿 |

## ⚡ 快捷键

默认快捷键配置：
- **F1** - 开始钓鱼
- **F2** - 停止钓鱼  
- **F3** - 暂停钓鱼

可在设置中自定义修改。

## 🔧 高级配置

编辑 `config/fishing_config.yaml` 进行高级配置：

```yaml
# 钓鱼流程配置
fishing:
  max_wait_time: 180          # 最大等待时间（秒）
  click_interval_min: 0.054   # 点击间隔最小值
  click_interval_max: 0.127   # 点击间隔最大值
  success_wait_time: 1.5      # 成功状态等待时间
  cast_hold_time: 2.0         # 抛竿按住时间

# 模型配置
model:
  confidence_threshold: 0.5   # 置信度阈值
  detection_interval: 0.1     # 检测间隔

# OCR配置
ocr:
  confidence_threshold: 60    # OCR置信度阈值
  detection_interval: 0.2     # OCR检测间隔
```

## 🐛 问题排查

### 常见问题

1. **程序无法启动**
   - 检查是否以管理员身份运行
   - 确认Python环境正确
   - 运行测试脚本检查模块状态

2. **模型检测失败**
   - 确认模型文件路径：`runs/fishing_model_latest.pt`
   - 检查模型文件是否存在且完整

3. **OCR识别失败**
   - 确认OCR路径：`D:\Python\tool\Tesseract-OCR`
   - 检查Tesseract是否正确安装

4. **状态检测不准确**
   - 调整置信度阈值
   - 检查游戏界面是否清晰
   - 确认游戏窗口位置

### 日志文件
查看详细日志：`logs/auto_fisher_new.log`

### 测试验证
```bash
# 验证所有模块状态
python modules/auto_fisher/test_refactored.py
```

## 📁 文件结构

```
modules/auto_fisher/
├── config.py              # 配置管理模块
├── state_detector.py      # 状态检测器
├── input_controller.py    # 输入控制器
├── fishing_controller.py  # 钓鱼控制器
├── ui.py                  # UI界面
├── new_main.py            # 新版主入口
├── test_refactored.py     # 测试脚本
├── README_重构版.md       # 本说明文件
└── 重构完成说明.md        # 重构报告
```

## 🎉 重构优势总结

### 相比旧版本
- ✅ **代码量减少60%** - 更易维护
- ✅ **模块数量减少** - 架构更清晰
- ✅ **错误处理完善** - 运行更稳定
- ✅ **资源管理优化** - 内存使用更高效
- ✅ **配置统一管理** - 设置更方便

### 功能保持完整
- ✅ 所有钓鱼状态检测
- ✅ 多线程操作协调
- ✅ OCR文字识别
- ✅ 用户界面交互
- ✅ 快捷键支持

**立即开始使用重构版本，体验更稳定的钓鱼助手！** 🎣 