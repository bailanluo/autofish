"""
优化后的模型训练模块主入口
使用配置管理器和优化后的组件
"""

import os
import sys
import logging
import tkinter as tk
from pathlib import Path

# 添加项目根目录到Python路径
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.append(str(ROOT_DIR))

from modules.logger import setup_logger, LogContext
from modules.config_manager import ConfigManager

# 获取logger
logger = logging.getLogger(__name__)

def check_dependencies():
    """检查依赖项"""
    missing_deps = []
    
    # 检查必要的Python包
    required_packages = [
        ('tkinter', 'GUI界面'),
        ('PIL', '图像处理'),
        ('numpy', '数值计算'),
        ('yaml', '配置文件解析')
    ]
    
    for package, description in required_packages:
        try:
            __import__(package)
            logger.debug(f"✓ {package} ({description}) - 可用")
        except ImportError:
            missing_deps.append(f"{package} ({description})")
            logger.warning(f"✗ {package} ({description}) - 不可用")
    
    # 检查可选的深度学习包
    optional_packages = [
        ('ultralytics', 'YOLO模型训练'),
        ('torch', 'PyTorch深度学习框架'),
        ('cv2', 'OpenCV图像处理')
    ]
    
    for package, description in optional_packages:
        try:
            __import__(package)
            logger.info(f"✓ {package} ({description}) - 可用")
        except ImportError:
            logger.warning(f"✗ {package} ({description}) - 不可用，部分功能受限")
    
    return missing_deps

def main():
    """主函数"""
    try:
        # 设置日志
        with LogContext(logger, "模型训练模块"):
            logger.info("启动完整训练流程模块")
            
            # 检查依赖
            missing_deps = check_dependencies()
            if missing_deps:
                logger.error(f"缺少必要依赖: {', '.join(missing_deps)}")
                print(f"错误: 缺少必要依赖项")
                print("请安装以下包:")
                for dep in missing_deps:
                    print(f"  - {dep}")
                return False
            
            # 检查是否有命令行参数
            if len(sys.argv) > 1:
                if sys.argv[1] == "--pipeline":
                    # 使用命令行模式运行训练流程
                    return run_pipeline_mode()
                elif sys.argv[1] == "--help":
                    print_help()
                    return True
            
            # 导入GUI组件
            from modules.model_trainer.training_ui import TrainingUI
            from modules.model_trainer.training_pipeline import TrainingPipeline
            
            # 创建训练流程实例
            pipeline = TrainingPipeline()
            
            # 创建GUI
            root = tk.Tk()
            app = TrainingUI(root, pipeline)  # 只传入训练流程
            
            logger.info("完整训练流程界面已启动")
            app.run()
            
            return True
            
    except Exception as e:
        logger.error(f"启动模型训练模块失败: {str(e)}")
        print(f"启动失败: {str(e)}")
        return False

def run_pipeline_mode():
    """运行命令行训练流程模式"""
    try:
        from modules.model_trainer.training_pipeline import TrainingPipeline
        
        logger.info("启动命令行训练流程模式")
        
        # 创建训练流程
        pipeline = TrainingPipeline()
        
        # 设置回调函数
        def progress_callback(stage: str, data: dict):
            progress = data.get('progress', 0)
            print(f"[{stage}] 进度: {progress:.1f}%")
        
        def completion_callback(success: bool, message: str, data: dict):
            if success:
                print("=" * 50)
                print("训练完成!")
                print(f"消息: {message}")
                if 'latest_training_dir' in data:
                    print(f"训练结果: {data['latest_training_dir']}")
                if 'trained_models' in data:
                    print(f"训练模型: {len(data['trained_models'])} 个")
                print("=" * 50)
            else:
                print(f"训练失败: {message}")
        
        pipeline.set_progress_callback(progress_callback)
        pipeline.set_completion_callback(completion_callback)
        
        # 默认训练配置
        config = {
            'model_type': 'yolov8n',
            'epochs': 100,
            'batch_size': 16,
            'lr0': 0.01,
            'imgsz': 640,
            'patience': 50,
            'train_ratio': 0.8,
            'val_ratio': 0.2,
            'force_recreate_data': False
        }
        
        print("开始完整训练流程...")
        print(f"配置: {config}")
        
        # 启动训练
        success = pipeline.run_complete_training(config)
        if success:
            print("训练已启动，请等待完成...")
            # 等待训练完成
            import time
            while pipeline.is_running:
                time.sleep(5)
            return True
        else:
            print("训练启动失败")
            return False
            
    except Exception as e:
        logger.error(f"命令行训练模式失败: {str(e)}")
        print(f"命令行训练失败: {str(e)}")
        return False

def print_help():
    """打印帮助信息"""
    print("AutoFish 模型训练模块")
    print("=" * 40)
    print("用法:")
    print("  python -m modules.model_trainer.main           # 启动GUI界面")
    print("  python -m modules.model_trainer.main --pipeline # 命令行训练模式")
    print("  python -m modules.model_trainer.main --help     # 显示帮助")
    print()
    print("训练流程:")
    print("  1. 从 data/raw/images/ 获取标注数据")
    print("  2. 自动分割为训练集和验证集")
    print("  3. 下载/使用预训练模型 (model/)")
    print("  4. 执行完整训练流程")
    print("  5. 保存训练结果到 runs/")
    print()
    print("支持的模型类型:")
    print("  - yolo11n, yolo11s, yolo11m, yolo11l, yolo11x")
    print("  - yolov8n, yolov8s, yolov8m, yolov8l, yolov8x")

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1) 