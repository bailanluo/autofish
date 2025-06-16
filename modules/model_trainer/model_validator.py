"""
模型验证器
负责训练好的YOLO模型的验证和性能评估
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import cv2
import numpy as np
from PIL import Image

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from modules.logger import setup_logger, LogContext

try:
    from ultralytics import YOLO
    ULTRALYTICS_AVAILABLE = True
except ImportError:
    ULTRALYTICS_AVAILABLE = False

class ModelValidator:
    """模型验证器 - 负责模型性能评估和测试"""
    
    def __init__(self, data_dir: str = "data"):
        """
        初始化模型验证器
        
        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = Path(data_dir)
        self.logger = setup_logger('ModelValidator')
        
        # 检查依赖
        if not ULTRALYTICS_AVAILABLE:
            self.logger.error("Ultralytics YOLO库未安装，请执行: pip install ultralytics")
            raise ImportError("需要安装ultralytics库")
        
        # 动态加载类别映射（与训练脚本保持一致）
        self.class_names, self.chinese_names = self._load_class_mapping()
        
        self.logger.info(f"已加载 {len(self.class_names)} 个类别")
    
    def _load_class_mapping(self) -> Tuple[Dict[int, str], Dict[int, str]]:
        """
        动态加载类别映射（与训练时保持一致）
        
        Returns:
            Tuple[Dict[int, str], Dict[int, str]]: 英文名称映射和中文名称映射
        """
        try:
            # 直接使用用户提供的正确映射（训练配置文件可能不准确）
            self.logger.info("使用用户提供的实际训练时类别映射")
            return self._get_default_mapping()
            
        except Exception as e:
            self.logger.error(f"加载类别映射失败: {str(e)}")
            # 如果出错，仍然返回正确的映射
            return self._get_default_mapping()
    
    def _load_from_train_config(self, config_file: Path) -> Tuple[Dict[int, str], Dict[int, str]]:
        """从训练配置文件加载类别映射"""
        import yaml
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 从配置文件中提取类别映射
        class_names = config.get('names', {})
        chinese_names = {}
        
        # 从class_details中获取中文名称
        if 'class_details' in config and 'chinese_names' in config['class_details']:
            chinese_names = config['class_details']['chinese_names']
        else:
            # 如果没有中文名称，使用英文名称
            chinese_names = class_names.copy()
        
        # 确保类型正确
        class_names = {int(k): str(v) for k, v in class_names.items()}
        chinese_names = {int(k): str(v) for k, v in chinese_names.items()}
        
        self.logger.info(f"从训练配置文件加载类别映射: {len(class_names)} 个类别")
        return class_names, chinese_names
    
    def _load_from_mapping_file(self, mapping_file: Path) -> Tuple[Dict[int, str], Dict[int, str]]:
        """从映射文件加载类别"""
        class_names = {}
        chinese_names = {}
        
        with open(mapping_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # 解析格式: "0: 钓鱼成功状态_txt -> fishing_success_txt"
                    if ':' in line and '->' in line:
                        parts = line.split(':')
                        class_id = int(parts[0].strip())
                        
                        name_parts = parts[1].split('->')
                        chinese_name = name_parts[0].strip()
                        english_name = name_parts[1].strip()
                        
                        class_names[class_id] = english_name
                        chinese_names[class_id] = chinese_name
        
        return class_names, chinese_names
    
    def _generate_from_data_dir(self) -> Tuple[Dict[int, str], Dict[int, str]]:
        """从数据目录动态生成类别映射"""
        raw_images_dir = self.data_dir / "raw" / "images"
        
        if not raw_images_dir.exists():
            self.logger.warning(f"原始数据目录不存在: {raw_images_dir}")
            return self._get_default_mapping()
        
        # 获取所有类别目录
        class_dirs = [d for d in raw_images_dir.iterdir() if d.is_dir()]
        class_dirs.sort()  # 确保顺序一致
        
        class_names = {}
        chinese_names = {}
        
        for idx, class_dir in enumerate(class_dirs):
            chinese_name = class_dir.name
            # 简单的中文转英文规则
            english_name = self._chinese_to_english(chinese_name)
            
            class_names[idx] = english_name
            chinese_names[idx] = chinese_name
        
        return class_names, chinese_names
    
    def _chinese_to_english(self, chinese_name: str) -> str:
        """简单的中文转英文映射"""
        mapping = {
            '钓鱼成功状态_txt': 'fishing_success_txt',
            '向右拉_txt': 'pull_right_txt',
            '向左拉_txt': 'pull_left_txt',
            '提线中_耐力已到二分之一状态': 'pulling_stamina_half',
            '提线中_耐力未到二分之一状态': 'pulling_stamina_low',
            '鱼上钩末提线状态': 'hooked_no_pull',
            '等待上钩状态': 'waiting_hook',
            '进入钓鱼状态': 'in_fishing',
            '未进入钓鱼状态': 'not_fishing',
            '有鱼饵': 'has_bait',
            '选饵状态': 'select_bait'
        }
        return mapping.get(chinese_name, chinese_name.lower().replace(' ', '_'))
    
    def _get_default_mapping(self) -> Tuple[Dict[int, str], Dict[int, str]]:
        """获取默认的类别映射（使用用户提供的正确映射）"""
        # 使用用户提供的实际训练时映射
        chinese_names = {
            0: '等待上钩状态',
            1: '鱼上钩末提线状态',
            2: '提线中_耐力未到二分之一状态',
            3: '提线中_耐力已到二分之一状态',
            4: '向右拉_txt',
            5: '向左拉_txt',
            6: '钓鱼成功状态_txt'
        }
        
        class_names = {
            0: 'waiting_hook',
            1: 'fishing_success_txt',
            2: 'pulling_stamina_low',
            3: 'pulling_stamina_half',
            4: 'pull_right_txt',
            5: 'pull_left_txt',
            6: 'hooked_no_pull'
        }
        
        return class_names, chinese_names
    
    def validate_model(self, model_path: str) -> Dict[str, float]:
        """
        验证模型性能
        
        Args:
            model_path: 模型文件路径
            
        Returns:
            Dict[str, float]: 验证结果指标
        """
        try:
            with LogContext(self.logger, f"验证模型 {model_path}"):
                # 检查模型文件
                if not Path(model_path).exists():
                    self.logger.error(f"模型文件不存在: {model_path}")
                    return {}
                
                # 检查验证数据
                val_config = self.data_dir / "train_config.yaml"
                if not val_config.exists():
                    self.logger.error(f"验证配置文件不存在: {val_config}")
                    return {}
                
                # 加载模型
                model = YOLO(model_path)
                
                # 执行验证
                self.logger.info("开始模型验证...")
                results = model.val(data=str(val_config), verbose=False)
                
                # 提取指标
                metrics = self._extract_metrics(results)
                
                self.logger.info(f"模型验证完成，mAP@0.5: {metrics.get('map50', 0.0):.4f}")
                return metrics
                
        except Exception as e:
            self.logger.error(f"模型验证失败: {str(e)}")
            return {}
    
    def _extract_metrics(self, results) -> Dict[str, float]:
        """
        从验证结果中提取指标
        
        Args:
            results: YOLO验证结果
            
        Returns:
            Dict[str, float]: 指标字典
        """
        metrics = {}
        
        try:
            # 主要指标
            if hasattr(results, 'box'):
                box_metrics = results.box
                metrics['map50'] = float(getattr(box_metrics, 'map50', 0.0))
                metrics['map75'] = float(getattr(box_metrics, 'map75', 0.0))
                metrics['map50_95'] = float(getattr(box_metrics, 'map', 0.0))
                metrics['precision'] = float(getattr(box_metrics, 'mp', 0.0))
                metrics['recall'] = float(getattr(box_metrics, 'mr', 0.0))
            else:
                # 兼容不同版本的结果格式
                metrics['map50'] = float(getattr(results, 'map50', 0.0))
                metrics['map75'] = float(getattr(results, 'map75', 0.0))
                metrics['map50_95'] = float(getattr(results, 'map', 0.0))
                metrics['precision'] = float(getattr(results, 'mp', 0.0))
                metrics['recall'] = float(getattr(results, 'mr', 0.0))
            
            # 计算F1分数
            precision = metrics.get('precision', 0.0)
            recall = metrics.get('recall', 0.0)
            if precision + recall > 0:
                metrics['f1_score'] = 2 * (precision * recall) / (precision + recall)
            else:
                metrics['f1_score'] = 0.0
                
        except Exception as e:
            self.logger.warning(f"提取指标时出错: {str(e)}")
        
        return metrics
    
    def test_single_image(self, model_path: str, image_path: str, 
                         confidence_threshold: float = 0.5) -> Dict:
        """
        测试单张图片
        
        Args:
            model_path: 模型文件路径
            image_path: 图片路径
            confidence_threshold: 置信度阈值
            
        Returns:
            Dict: 检测结果
        """
        try:
            # 加载模型
            model = YOLO(model_path)
            
            # 执行推理
            results = model(image_path, conf=confidence_threshold, verbose=False)
            
            if not results:
                return {"error": "推理失败"}
            
            result = results[0]
            
            # 提取检测结果
            detections = []
            if result.boxes is not None:
                for box in result.boxes:
                    # 获取边界框坐标
                    coords = box.xyxy[0].cpu().numpy()
                    
                    # 获取置信度和类别
                    confidence = float(box.conf[0].cpu().numpy())
                    class_id = int(box.cls[0].cpu().numpy())
                    
                    detection = {
                        'bbox': coords.tolist(),
                        'confidence': confidence,
                        'class_id': class_id,
                        'class_name': self.class_names.get(class_id, f"Unknown_{class_id}"),
                        'chinese_name': self.chinese_names.get(class_id, f"未知_{class_id}")
                    }
                    detections.append(detection)
            
            return {
                'image_path': image_path,
                'detections': detections,
                'detection_count': len(detections)
            }
            
        except Exception as e:
            self.logger.error(f"测试图片失败 {image_path}: {str(e)}")
            return {"error": str(e)}
    
    def batch_test_images(self, model_path: str, image_dir: str, 
                         confidence_threshold: float = 0.5) -> List[Dict]:
        """
        批量测试图片
        
        Args:
            model_path: 模型文件路径
            image_dir: 图片目录
            confidence_threshold: 置信度阈值
            
        Returns:
            List[Dict]: 批量测试结果
        """
        try:
            image_dir = Path(image_dir)
            if not image_dir.exists():
                self.logger.error(f"图片目录不存在: {image_dir}")
                return []
            
            # 获取所有图片文件
            image_files = []
            for ext in ['.jpg', '.jpeg', '.png', '.bmp']:
                image_files.extend(image_dir.glob(f'*{ext}'))
                image_files.extend(image_dir.glob(f'*{ext.upper()}'))
            
            if not image_files:
                self.logger.warning(f"目录中没有找到图片文件: {image_dir}")
                return []
            
            self.logger.info(f"开始批量测试 {len(image_files)} 张图片...")
            
            results = []
            for idx, image_file in enumerate(image_files):
                self.logger.debug(f"测试图片 {idx+1}/{len(image_files)}: {image_file.name}")
                
                result = self.test_single_image(
                    model_path, str(image_file), confidence_threshold
                )
                results.append(result)
            
            self.logger.info(f"批量测试完成，共测试 {len(results)} 张图片")
            return results
            
        except Exception as e:
            self.logger.error(f"批量测试失败: {str(e)}")
            return []
    
    def benchmark_model(self, model_path: str, test_images: int = 100) -> Dict:
        """
        模型性能基准测试
        
        Args:
            model_path: 模型文件路径
            test_images: 测试图片数量
            
        Returns:
            Dict: 基准测试结果
        """
        try:
            with LogContext(self.logger, f"模型基准测试 {model_path}"):
                # 加载模型
                model = YOLO(model_path)
                
                # 获取验证集图片
                val_dir = self.data_dir / "val" / "images"
                if not val_dir.exists():
                    self.logger.error(f"验证集目录不存在: {val_dir}")
                    return {}
                
                # 获取测试图片列表
                image_files = list(val_dir.glob("*.jpg"))[:test_images]
                if not image_files:
                    self.logger.error("没有找到验证集图片")
                    return {}
                
                # 性能统计
                inference_times = []
                detection_counts = []
                
                self.logger.info(f"开始基准测试，共 {len(image_files)} 张图片...")
                
                for image_file in image_files:
                    # 记录推理时间
                    start_time = time.time()
                    
                    # 执行推理
                    results = model(str(image_file), verbose=False)
                    
                    inference_time = time.time() - start_time
                    inference_times.append(inference_time)
                    
                    # 统计检测数量
                    if results and results[0].boxes is not None:
                        detection_count = len(results[0].boxes)
                    else:
                        detection_count = 0
                    detection_counts.append(detection_count)
                
                # 计算统计指标
                avg_inference_time = np.mean(inference_times)
                min_inference_time = np.min(inference_times)
                max_inference_time = np.max(inference_times)
                fps = 1.0 / avg_inference_time if avg_inference_time > 0 else 0
                
                avg_detections = np.mean(detection_counts)
                total_detections = np.sum(detection_counts)
                
                benchmark_results = {
                    'test_images': len(image_files),
                    'avg_inference_time': avg_inference_time,
                    'min_inference_time': min_inference_time,
                    'max_inference_time': max_inference_time,
                    'fps': fps,
                    'avg_detections_per_image': avg_detections,
                    'total_detections': total_detections,
                    'detection_rate': (np.sum(np.array(detection_counts) > 0) / len(detection_counts)) * 100
                }
                
                self.logger.info(f"基准测试完成，平均推理时间: {avg_inference_time:.3f}s, FPS: {fps:.1f}")
                return benchmark_results
                
        except Exception as e:
            self.logger.error(f"基准测试失败: {str(e)}")
            return {}
    
    def compare_models(self, model_paths: List[str]) -> Dict:
        """
        比较多个模型的性能
        
        Args:
            model_paths: 模型文件路径列表
            
        Returns:
            Dict: 模型比较结果
        """
        try:
            self.logger.info(f"开始比较 {len(model_paths)} 个模型...")
            
            comparison_results = {}
            
            for model_path in model_paths:
                model_name = Path(model_path).stem
                self.logger.info(f"评估模型: {model_name}")
                
                # 验证模型
                validation_metrics = self.validate_model(model_path)
                
                # 基准测试
                benchmark_results = self.benchmark_model(model_path, test_images=50)
                
                # 合并结果
                model_results = {
                    'validation': validation_metrics,
                    'benchmark': benchmark_results
                }
                
                comparison_results[model_name] = model_results
            
            self.logger.info("模型比较完成")
            return comparison_results
            
        except Exception as e:
            self.logger.error(f"模型比较失败: {str(e)}")
            return {}
    
    def analyze_prediction_confidence(self, model_path: str, 
                                    image_dir: str) -> Dict:
        """
        分析预测置信度分布
        
        Args:
            model_path: 模型文件路径
            image_dir: 图片目录
            
        Returns:
            Dict: 置信度分析结果
        """
        try:
            # 批量测试获取结果
            results = self.batch_test_images(model_path, image_dir)
            
            # 收集所有置信度
            all_confidences = []
            class_confidences = {class_id: [] for class_id in self.class_names.keys()}
            
            for result in results:
                if 'detections' in result:
                    for detection in result['detections']:
                        confidence = detection['confidence']
                        class_id = detection['class_id']
                        
                        all_confidences.append(confidence)
                        if class_id in class_confidences:
                            class_confidences[class_id].append(confidence)
            
            # 计算统计指标
            analysis = {
                'total_detections': len(all_confidences),
                'overall_confidence': {
                    'mean': float(np.mean(all_confidences)) if all_confidences else 0.0,
                    'std': float(np.std(all_confidences)) if all_confidences else 0.0,
                    'min': float(np.min(all_confidences)) if all_confidences else 0.0,
                    'max': float(np.max(all_confidences)) if all_confidences else 0.0,
                    'median': float(np.median(all_confidences)) if all_confidences else 0.0
                },
                'class_confidence': {}
            }
            
            # 按类别统计
            for class_id, confidences in class_confidences.items():
                if confidences:
                    class_name = self.class_names.get(class_id, f"Class_{class_id}")
                    analysis['class_confidence'][class_name] = {
                        'count': len(confidences),
                        'mean': float(np.mean(confidences)),
                        'std': float(np.std(confidences)),
                        'min': float(np.min(confidences)),
                        'max': float(np.max(confidences))
                    }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"置信度分析失败: {str(e)}")
            return {}
    
    def generate_validation_report(self, model_path: str) -> str:
        """
        生成验证报告
        
        Args:
            model_path: 模型文件路径
            
        Returns:
            str: 验证报告文本
        """
        try:
            model_name = Path(model_path).name
            
            # 获取各种指标
            validation_metrics = self.validate_model(model_path)
            benchmark_results = self.benchmark_model(model_path, test_images=50)
            
            # 生成报告
            report = f"""
📊 模型验证报告
模型名称: {model_name}
生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}

═══════════════════════════════════════

🎯 验证指标:
- mAP@0.5: {validation_metrics.get('map50', 0.0):.4f}
- mAP@0.75: {validation_metrics.get('map75', 0.0):.4f}
- mAP@0.5:0.95: {validation_metrics.get('map50_95', 0.0):.4f}
- 精确率: {validation_metrics.get('precision', 0.0):.4f}
- 召回率: {validation_metrics.get('recall', 0.0):.4f}
- F1分数: {validation_metrics.get('f1_score', 0.0):.4f}

⚡ 性能基准:
- 平均推理时间: {benchmark_results.get('avg_inference_time', 0.0):.3f}s
- FPS: {benchmark_results.get('fps', 0.0):.1f}
- 检测率: {benchmark_results.get('detection_rate', 0.0):.1f}%
- 平均检测数/图: {benchmark_results.get('avg_detections_per_image', 0.0):.1f}

═══════════════════════════════════════

📈 评估总结:
"""
            
            # 添加性能评级
            map50 = validation_metrics.get('map50', 0.0)
            if map50 >= 0.9:
                report += "🌟 优秀 - 模型性能非常好\n"
            elif map50 >= 0.8:
                report += "✅ 良好 - 模型性能较好\n"
            elif map50 >= 0.6:
                report += "⚠️ 中等 - 模型性能一般，建议优化\n"
            else:
                report += "❌ 较差 - 模型性能不足，需要重新训练\n"
            
            return report
            
        except Exception as e:
            self.logger.error(f"生成验证报告失败: {str(e)}")
            return f"生成报告失败: {str(e)}" 