"""
数据管理模块 v2.1 - YOLO格式数据支持
处理全屏图像数据的保存、YOLO标注文件生成和管理
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Tuple
from PIL import Image
from datetime import datetime

# 添加主项目路径以使用logger
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from modules.logger import setup_logger, LogContext


class DataManager:
    """数据管理器 - 支持YOLO格式数据保存"""
    
    def __init__(self, data_dir: str = 'data'):
        """
        初始化数据管理器
        
        Args:
            data_dir: 数据保存目录
        """
        self.logger = setup_logger('DataManager')  # 日志记录器
        
        # 数据目录 - 使用 data/raw/images 和 data/raw/labels 结构
        self.base_dir = Path(data_dir)
        self.raw_dir = self.base_dir / 'raw'
        self.images_dir = self.raw_dir / 'images'
        self.labels_dir = self.raw_dir / 'labels'
        
        # 创建目录结构
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.labels_dir.mkdir(parents=True, exist_ok=True)
        
        # 类别计数器缓存，避免重复扫描目录
        self.category_counters = {}
        
        # YOLO类别映射（类别名 -> 类别ID）
        self.class_mapping = {}
        self._load_class_mapping()
    
    def _load_class_mapping(self):
        """加载或创建类别映射文件"""
        # 使用数据采集工具专用的映射文件，避免与模型训练冲突
        mapping_file = self.raw_dir / 'data_collector_mapping.txt'
        
        if mapping_file.exists():
            try:
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        # 跳过注释行和空行
                        if line and not line.startswith('#') and ':' in line:
                            class_id_str, class_name = line.split(':', 1)
                            self.class_mapping[class_name.strip()] = int(class_id_str.strip())
                self.logger.info(f"已加载类别映射: {self.class_mapping}")
            except Exception as e:
                self.logger.error(f"加载类别映射失败: {e}")
                # 如果映射文件损坏，尝试重新扫描
                self._rebuild_mapping_from_labels()
        else:
            # 映射文件不存在，扫描已有的标注文件来重建映射
            self.logger.info("映射文件不存在，正在扫描标注文件重建映射...")
            self._rebuild_mapping_from_labels()
    
    def _rebuild_mapping_from_labels(self):
        """通过扫描data/raw/labels目录重建类别映射"""
        try:
            self.class_mapping = {}
            
            # 扫描每个类别目录
            for category_dir in self.labels_dir.iterdir():
                if category_dir.is_dir():
                    category_name = category_dir.name
                    
                    # 寻找该类别下的第一个标注文件
                    label_files = list(category_dir.glob('*.txt'))
                    if label_files:
                        # 读取第一个标注文件获取类别ID
                        first_label_file = label_files[0]
                        try:
                            with open(first_label_file, 'r', encoding='utf-8') as f:
                                first_line = f.readline().strip()
                                if first_line:
                                    # YOLO格式第一个数字是类别ID
                                    class_id = int(first_line.split()[0])
                                    self.class_mapping[category_name] = class_id
                                    self.logger.info(f"从标注文件发现类别: {category_name} -> ID {class_id}")
                        except Exception as e:
                            self.logger.warning(f"读取标注文件 {first_label_file} 失败: {e}")
            
            # 保存重建的映射
            if self.class_mapping:
                self._save_class_mapping()
                self.logger.info(f"成功重建类别映射，共{len(self.class_mapping)}个类别")
            else:
                self.logger.warning("未找到任何有效的标注文件，映射为空")
                
        except Exception as e:
            self.logger.error(f"重建类别映射失败: {e}")
    
    def _save_class_mapping(self):
        """保存类别映射文件"""
        # 使用数据采集工具专用的映射文件
        mapping_file = self.raw_dir / 'data_collector_mapping.txt'
        try:
            with open(mapping_file, 'w', encoding='utf-8') as f:
                # 添加文件头注释说明
                f.write("# 数据采集工具类别映射文件\n")
                f.write("# 格式: 类别ID: 类别名称\n")
                f.write("# 此文件由数据采集工具自动维护，请勿手动编辑\n")
                f.write("#\n")
                
                # 按类别ID排序保存
                for class_name, class_id in sorted(self.class_mapping.items(), key=lambda x: x[1]):
                    f.write(f"{class_id}: {class_name}\n")
            self.logger.info(f"类别映射已保存到: {mapping_file}")
        except Exception as e:
            self.logger.error(f"保存类别映射失败: {e}")
    
    def _get_class_id(self, category: str) -> int:
        """获取类别ID，如果不存在则创建新的"""
        if category not in self.class_mapping:
            # 分配新的类别ID
            if self.class_mapping:
                new_id = max(self.class_mapping.values()) + 1
            else:
                new_id = 0
            self.class_mapping[category] = new_id
            self._save_class_mapping()
            self.logger.info(f"新类别 '{category}' 分配ID: {new_id}")
        
        return self.class_mapping[category]
    
    def save_fullscreen_with_annotation(self, image: Image.Image, category: str, 
                                      target_region: Dict, image_format: str = 'jpg', 
                                      image_quality: int = 95) -> Tuple[str, str]:
        """
        保存全屏图像和对应的YOLO标注文件
        
        Args:
            image: PIL Image对象（全屏截图）
            category: 类别名称
            target_region: 目标区域 {'left': x, 'top': y, 'width': w, 'height': h}
            image_format: 图像格式 ('jpg', 'png')
            image_quality: JPEG质量 (1-100)
            
        Returns:
            (图像文件路径, 标注文件路径)，失败返回('', '')
        """
        try:
            with LogContext(self.logger, f"保存{category}类别全屏数据"):
                # 创建类别目录
                category_images_dir = self.images_dir / category
                category_labels_dir = self.labels_dir / category
                category_images_dir.mkdir(exist_ok=True)
                category_labels_dir.mkdir(exist_ok=True)
                
                # 获取下一个序号
                next_number = self._get_next_number(category)
                
                # 生成文件名（统一格式）
                base_filename = f"{category}{next_number:03d}"
                image_filename = f"{base_filename}.{image_format.lower()}"
                label_filename = f"{base_filename}.txt"
                
                image_path = category_images_dir / image_filename
                label_path = category_labels_dir / label_filename
                
                # 保存图像
                if image_format.lower() in ['jpg', 'jpeg']:
                    # JPEG格式需要转换为RGB模式
                    if image.mode in ('RGBA', 'LA', 'P'):
                        image = image.convert('RGB')
                    image.save(image_path, format='JPEG', quality=image_quality)
                else:
                    # PNG格式保持原有模式
                    image.save(image_path, format='PNG')
                
                # 生成YOLO标注
                yolo_annotation = self._create_yolo_annotation(
                    image.size, target_region, category
                )
                
                # 保存标注文件
                with open(label_path, 'w', encoding='utf-8') as f:
                    f.write(yolo_annotation)
                
                # 更新计数器缓存
                self.category_counters[category] = next_number
                
                self.logger.info(f"全屏数据已保存: {image_path} + {label_path}")
                return str(image_path), str(label_path)
                
        except Exception as e:
            self.logger.error(f"保存全屏数据失败: {e}")
            return "", ""
    
    def _create_yolo_annotation(self, image_size: Tuple[int, int], 
                               target_region: Dict, category: str) -> str:
        """
        创建YOLO格式标注
        
        Args:
            image_size: 图像尺寸 (width, height)
            target_region: 目标区域 {'left': x, 'top': y, 'width': w, 'height': h}
            category: 类别名称
            
        Returns:
            YOLO格式标注字符串
        """
        img_width, img_height = image_size
        
        # 获取类别ID
        class_id = self._get_class_id(category)
        
        # 计算YOLO格式坐标（归一化坐标）
        # YOLO格式: class_id center_x center_y width height
        center_x = (target_region['left'] + target_region['width'] / 2) / img_width
        center_y = (target_region['top'] + target_region['height'] / 2) / img_height
        norm_width = target_region['width'] / img_width
        norm_height = target_region['height'] / img_height
        
        # 确保坐标在0-1范围内
        center_x = max(0, min(1, center_x))
        center_y = max(0, min(1, center_y))
        norm_width = max(0, min(1, norm_width))
        norm_height = max(0, min(1, norm_height))
        
        return f"{class_id} {center_x:.6f} {center_y:.6f} {norm_width:.6f} {norm_height:.6f}"
    
    def save_image(self, image: Image.Image, category: str, image_format: str = 'png', 
                   image_quality: int = 95) -> str:
        """
        保存图像到指定类别目录
        
        Args:
            image: PIL Image对象
            category: 类别名称
            image_format: 图像格式 ('png', 'jpg')
            image_quality: JPEG质量 (1-100)
            
        Returns:
            保存的文件路径，失败返回空字符串
        """
        try:
            with LogContext(self.logger, f"保存{category}类别图像"):
                # 创建类别目录 - 保存到 data/images/类别名/
                category_dir = self.images_dir / category
                category_dir.mkdir(exist_ok=True)
                
                # 获取下一个序号
                next_number = self._get_next_number(category)
                
                # 生成文件名
                filename = f"{category}_{next_number:03d}.{image_format.lower()}"
                file_path = category_dir / filename
                
                # 保存图像
                if image_format.lower() == 'jpg' or image_format.lower() == 'jpeg':
                    # JPEG格式需要转换为RGB模式
                    if image.mode in ('RGBA', 'LA', 'P'):
                        image = image.convert('RGB')
                    image.save(file_path, format='JPEG', quality=image_quality)
                else:
                    # PNG格式保持原有模式
                    image.save(file_path, format='PNG')
                
                # 更新计数器缓存
                self.category_counters[category] = next_number
                
                self.logger.info(f"图像已保存: {file_path}")
                return str(file_path)
                
        except Exception as e:
            self.logger.error(f"保存图像失败: {e}")
            return ""
    
    def _get_next_number(self, category: str) -> int:
        """
        获取类别的下一个序号（适配新目录结构）
        
        Args:
            category: 类别名称
            
        Returns:
            下一个可用的序号
        """
        # 如果缓存中没有，则扫描目录获取
        if category not in self.category_counters:
            category_images_dir = self.images_dir / category
            if category_images_dir.exists():
                # 获取现有文件的最大序号
                max_number = 0
                # 扫描新格式的文件名: category001.jpg
                for file_path in category_images_dir.glob(f"{category}*.jpg"):
                    try:
                        # 从文件名中提取序号
                        name_without_ext = file_path.stem
                        if name_without_ext.startswith(category):
                            number_str = name_without_ext[len(category):]
                            if number_str.isdigit():
                                number = int(number_str)
                                max_number = max(max_number, number)
                    except ValueError:
                        continue
                
                # 检查PNG格式的文件
                for file_path in category_images_dir.glob(f"{category}*.png"):
                    try:
                        name_without_ext = file_path.stem
                        if name_without_ext.startswith(category):
                            number_str = name_without_ext[len(category):]
                            if number_str.isdigit():
                                number = int(number_str)
                                max_number = max(max_number, number)
                    except ValueError:
                        continue
                
                self.category_counters[category] = max_number
            else:
                self.category_counters[category] = 0
        
        # 返回下一个序号
        return self.category_counters[category] + 1
    
    def get_statistics(self) -> Dict[str, int]:
        """
        获取各类别的图像统计信息（适配新目录结构）
        
        Returns:
            字典，键为类别名，值为图像数量
        """
        try:
            with LogContext(self.logger, "获取数据统计"):
                stats = {}
                
                # 扫描data/raw/images目录下的所有子目录
                if self.images_dir.exists():
                    for category_dir in self.images_dir.iterdir():
                        if category_dir.is_dir():
                            category = category_dir.name
                            # 统计PNG和JPG文件数量
                            png_count = len(list(category_dir.glob("*.png")))
                            jpg_count = len(list(category_dir.glob("*.jpg")))
                            jpeg_count = len(list(category_dir.glob("*.jpeg")))
                            
                            total_count = png_count + jpg_count + jpeg_count
                            stats[category] = total_count
                
                self.logger.info(f"统计完成，共{len(stats)}个类别")
                return stats
                
        except Exception as e:
            self.logger.error(f"获取统计信息失败: {e}")
            return {}
    
    def get_category_count(self, category: str) -> int:
        """
        获取指定类别的图像数量（适配新目录结构）
        
        Args:
            category: 类别名称
            
        Returns:
            图像数量
        """
        category_dir = self.images_dir / category
        if not category_dir.exists():
            return 0
        
        # 统计所有支持的图像格式
        count = 0
        for pattern in ["*.png", "*.jpg", "*.jpeg"]:
            count += len(list(category_dir.glob(pattern)))
        
        return count
    
    def validate_category_name(self, category: str) -> bool:
        """
        验证类别名称是否有效
        
        Args:
            category: 类别名称
            
        Returns:
            是否有效
        """
        if not category or not category.strip():
            return False
        
        # 检查是否包含非法字符
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '/', '\\']
        for char in invalid_chars:
            if char in category:
                return False
        
        return True
    
    def get_category_max_number(self, category: str) -> int:
        """
        获取指定类别的最大编号（用于增量数据采集）
        
        Args:
            category: 类别名称
            
        Returns:
            最大编号，如果类别不存在返回0
        """
        category_dir = self.images_dir / category
        if not category_dir.exists():
            return 0
        
        max_number = 0
        
        # 扫描所有支持的图像格式，查找新格式：category001.jpg
        for extension in ['*.png', '*.jpg', '*.jpeg']:
            for file_path in category_dir.glob(extension):
                try:
                    # 从文件名中提取序号 (新格式: category001.jpg)
                    name_without_ext = file_path.stem
                    if name_without_ext.startswith(category):
                        # 提取类别名后的数字部分
                        number_str = name_without_ext[len(category):]
                        if number_str.isdigit():
                            number = int(number_str)
                            max_number = max(max_number, number)
                except (ValueError, IndexError):
                    # 跳过格式不正确的文件名
                    continue
        
        # 同时检查旧格式：category_001.png (向后兼容)
        for extension in ['*.png', '*.jpg', '*.jpeg']:
            for file_path in category_dir.glob(extension):
                try:
                    # 从文件名中提取序号 (旧格式: category_001.png)
                    name_parts = file_path.stem.split('_')
                    if len(name_parts) >= 2 and name_parts[0] == category:
                        # 获取最后一个下划线后的数字
                        number_str = name_parts[-1]
                        if number_str.isdigit():
                            number = int(number_str)
                            max_number = max(max_number, number)
                except (ValueError, IndexError):
                    # 跳过格式不正确的文件名
                    continue
        
        return max_number
    
    def setup_category_counter(self, category: str) -> int:
        """
        设置类别计数器（支持增量采集）
        
        Args:
            category: 类别名称
            
        Returns:
            当前计数器值（已存在数据的最大编号）
        """
        max_number = self.get_category_max_number(category)
        self.category_counters[category] = max_number
        
        if max_number > 0:
            self.logger.info(f"类别 '{category}' 继续采集，当前最大编号: {max_number}")
        else:
            self.logger.info(f"类别 '{category}' 开始新采集")
        
        return max_number
    
    def cleanup_empty_directories(self):
        """清理空的类别目录"""
        try:
            if self.images_dir.exists():
                for category_dir in self.images_dir.iterdir():
                    if category_dir.is_dir():
                        # 检查目录是否为空
                        if not any(category_dir.iterdir()):
                            category_dir.rmdir()
                            self.logger.info(f"删除空目录: {category_dir}")
        except Exception as e:
            self.logger.error(f"清理空目录失败: {e}")
    
    def get_data_info(self) -> Dict[str, Any]:
        """
        获取完整的数据信息
        
        Returns:
            包含总数、类别数、最后更新时间等信息的字典
        """
        stats = self.get_statistics()
        total_images = sum(stats.values())
        
        return {
            'total_images': total_images,
            'total_categories': len(stats),
            'categories': stats,
            'data_dir': str(self.images_dir),
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def get_annotation_info(self) -> Dict[str, Any]:
        """
        获取标注文件统计信息
        
        Returns:
            包含标注统计的字典
        """
        try:
            stats = {
                'total_annotations': 0,
                'categories': {},
                'class_mapping': self.class_mapping.copy()
            }
            
            if self.labels_dir.exists():
                for category_dir in self.labels_dir.iterdir():
                    if category_dir.is_dir():
                        category = category_dir.name
                        txt_count = len(list(category_dir.glob("*.txt")))
                        stats['categories'][category] = txt_count
                        stats['total_annotations'] += txt_count
            
            return stats
            
        except Exception as e:
            self.logger.error(f"获取标注统计失败: {e}")
            return {'total_annotations': 0, 'categories': {}, 'class_mapping': {}} 