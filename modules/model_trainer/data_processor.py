"""
数据处理器 - 自动处理分类数据并转换为训练格式
负责数据扫描、切分、格式转换等功能
"""

import os
import sys
import shutil
import random
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from modules.logger import setup_logger, LogContext

logger = logging.getLogger(__name__)

class DataProcessor:
    """数据处理器 - 处理钓鱼状态检测数据"""
    
    def __init__(self, data_root: str = "data"):
        """
        初始化数据处理器
        
        Args:
            data_root: 数据根目录
        """
        self.data_root = Path(data_root)
        # 新的数据路径结构
        self.raw_dir = self.data_root / "raw"
        self.raw_images_dir = self.raw_dir / "images"
        self.raw_labels_dir = self.raw_dir / "labels"
        self.train_dir = self.data_root / "train"
        self.val_dir = self.data_root / "val"
        
        # 动态获取类别映射 - 从实际文件夹结构中获取
        self.class_mapping = self._build_class_mapping()
        
        # 英文类别名称映射 - 动态生成
        self.class_names = self._build_english_class_names()
        
        logger.info("数据处理器初始化完成")
        logger.info(f"数据源路径: {self.raw_images_dir}")
        logger.info(f"标注文件路径: {self.raw_labels_dir}")
        logger.info(f"发现 {len(self.class_mapping)} 个类别: {list(self.class_mapping.keys())}")
    
    def _build_class_mapping(self) -> Dict[str, int]:
        """
        动态构建类别映射 - 从data/raw/images/下的文件夹名称获取
        
        Returns:
            Dict[str, int]: 类别名称到ID的映射
        """
        class_mapping = {}
        
        if not self.raw_images_dir.exists():
            logger.warning(f"图片数据目录不存在: {self.raw_images_dir}")
            return class_mapping
        
        # 获取所有子目录名称作为类别
        class_dirs = [d for d in self.raw_images_dir.iterdir() if d.is_dir()]
        
        # 按名称排序确保一致性
        class_dirs.sort(key=lambda x: x.name)
        
        # 创建映射
        for idx, class_dir in enumerate(class_dirs):
            class_name = class_dir.name
            class_mapping[class_name] = idx
            logger.debug(f"类别映射: {class_name} -> {idx}")
        
        if not class_mapping:
            logger.warning("未找到任何类别目录")
        else:
            logger.info(f"构建类别映射完成: {len(class_mapping)} 个类别")
        
        return class_mapping
    
    def _build_english_class_names(self) -> Dict[int, str]:
        """
        动态构建英文类别名称映射
        
        Returns:
            Dict[int, str]: ID到英文名称的映射
        """
        english_names = {}
        
        for class_name, class_id in self.class_mapping.items():
            # 生成英文名称：将中文转换为拼音或简化英文描述
            english_name = self._chinese_to_english(class_name)
            english_names[class_id] = english_name
        
        return english_names
    
    def _chinese_to_english(self, chinese_name: str) -> str:
        """
        将中文类别名称转换为英文名称
        
        Args:
            chinese_name: 中文类别名称
            
        Returns:
            str: 英文类别名称
        """
        # 定义一些常见的转换规则
        translation_map = {
            '钓鱼成功状态_txt': 'fishing_success_txt',
            '向左拉_txt': 'pull_left_txt',
            '向右拉_txt': 'pull_right_txt',
            '提线中_耐力已到二分之一状态': 'pulling_stamina_half',
            '鱼上钩末提线状态': 'hooked_no_pull',
            '提线中_耐力未到二分之一状态': 'pulling_stamina_low',
            '等待上钩状态': 'waiting_hook',
            # 可以根据需要添加更多映射
        }
        
        # 如果有预定义的映射，使用它
        if chinese_name in translation_map:
            return translation_map[chinese_name]
        
        # 否则生成一个基于拼音的简化名称
        # 这里使用简单的规则：去除特殊字符，用下划线连接
        english_name = chinese_name.replace('_txt', '_txt')
        english_name = english_name.replace('_', '_')
        
        # 如果没有特殊处理，就使用原名称（可能包含中文）
        # 在实际使用中，YOLO可以处理中文类别名称
        return chinese_name.lower().replace(' ', '_')
    
    def scan_data(self) -> Dict[str, int]:
        """
        扫描数据目录，统计各类别的图片数量
        
        Returns:
            Dict[str, int]: 类别名称到图片数量的映射
        """
        try:
            if not self.raw_images_dir.exists():
                logger.warning(f"数据目录不存在: {self.raw_images_dir}")
                return {}
            
            class_counts = {}
            total_images = 0
            
            for class_name in self.class_mapping.keys():
                class_dir = self.raw_images_dir / class_name
                if not class_dir.exists():
                    logger.warning(f"类别目录不存在: {class_dir}")
                    class_counts[class_name] = 0
                    continue
                
                # 统计支持的图片格式
                image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
                image_count = 0
                
                for ext in image_extensions:
                    image_count += len(list(class_dir.glob(f'*{ext}')))
                    image_count += len(list(class_dir.glob(f'*{ext.upper()}')))
                
                class_counts[class_name] = image_count
                total_images += image_count
                
                logger.debug(f"类别 {class_name}: {image_count} 张图片")
            
            logger.info(f"数据扫描完成: {len(class_counts)}个类别, 共{total_images}张图片")
            return class_counts
            
        except Exception as e:
            logger.error(f"扫描数据失败: {str(e)}")
            return {}
    
    def prepare_detection_data(self, train_ratio: float = 0.8, 
                             val_ratio: float = 0.2,
                             force_recreate: bool = False) -> bool:
        """
        准备检测训练数据 - 将标注好的数据转换为YOLO训练格式
        从data/raw/images/和data/raw/labels/获取数据并分割
        
        Args:
            train_ratio: 训练集比例
            val_ratio: 验证集比例
            force_recreate: 是否强制重新创建数据
            
        Returns:
            bool: 成功返回True
        """
        try:
            # 检查是否需要重新创建数据
            if not force_recreate and self._check_detection_data_exists():
                logger.info("检测数据已存在，跳过数据准备")
                return True
            
            logger.info("开始准备检测训练数据...")
            logger.info(f"数据源目录: {self.raw_images_dir}")
            logger.info(f"标注源目录: {self.raw_labels_dir}")
            
            # 创建目录结构
            self._create_detection_directories()
            
            # 扫描原始数据
            class_counts = self.scan_data()
            if not class_counts:
                logger.error("没有找到可用的训练数据")
                logger.error(f"请确保 {self.raw_images_dir} 目录下有按类别命名的文件夹")
                return False
            
            # 显示数据统计
            total_images = sum(class_counts.values())
            logger.info(f"发现 {len(class_counts)} 个类别，共 {total_images} 张图片")
            for class_name, count in class_counts.items():
                logger.info(f"  - {class_name}: {count} 张")
            
            total_train = 0
            total_val = 0
            
            # 处理每个类别
            for class_name, count in class_counts.items():
                if count == 0:
                    logger.warning(f"跳过空类别: {class_name}")
                    continue
                
                logger.info(f"处理类别: {class_name} ({count} 张图片)")
                
                # 获取该类别的所有图片和标注文件
                image_files, label_files = self._get_class_data(class_name)
                if not image_files:
                    logger.warning(f"类别 {class_name} 没有有效的图片文件")
                    continue
                
                # 检查图片和标注文件是否匹配
                matched_pairs = self._match_image_label_pairs(image_files, label_files)
                if not matched_pairs:
                    logger.warning(f"类别 {class_name} 没有匹配的图片标注对")
                    continue
                
                logger.info(f"  找到 {len(matched_pairs)} 对匹配的图片标注文件")
                
                # 随机打乱并分割
                random.seed(42)  # 设置随机种子确保可重现
                random.shuffle(matched_pairs)
                split_idx = int(len(matched_pairs) * train_ratio)
                train_pairs = matched_pairs[:split_idx]
                val_pairs = matched_pairs[split_idx:]
                
                logger.info(f"  分割: 训练集 {len(train_pairs)}, 验证集 {len(val_pairs)}")
                
                # 处理训练集
                train_count = self._process_data_pairs_for_detection(
                    train_pairs, class_name, 'train')
                total_train += train_count
                
                # 处理验证集
                val_count = self._process_data_pairs_for_detection(
                    val_pairs, class_name, 'val')
                total_val += val_count
                
                logger.info(f"  完成: 训练集 {train_count}, 验证集 {val_count}")
            
            # 创建数据配置文件
            self._create_detection_config()
            
            logger.info("=" * 50)
            logger.info("检测数据准备完成!")
            logger.info(f"训练集: {total_train} 张图片")
            logger.info(f"验证集: {total_val} 张图片")
            logger.info(f"数据配置文件: {self.data_root / 'train_config.yaml'}")
            logger.info("=" * 50)
            
            return True
            
        except Exception as e:
            logger.error(f"准备检测数据失败: {str(e)}")
            return False
    
    def prepare_classification_data(self, train_ratio: float = 0.8,
                                  force_recreate: bool = False) -> bool:
        """
        准备分类训练数据 - 直接使用现有的分类数据结构
        
        Args:
            train_ratio: 训练集比例
            force_recreate: 是否强制重新创建数据
            
        Returns:
            bool: 成功返回True
        """
        try:
            # 检查是否需要重新创建数据
            if not force_recreate and self._check_classification_data_exists():
                logger.info("分类数据已存在，跳过数据准备")
                return True
            
            logger.info("开始准备分类训练数据...")
            
            # 创建分类数据目录结构
            self._create_classification_directories()
            
            # 扫描原始数据
            class_counts = self.scan_data()
            if not class_counts:
                logger.error("没有找到可用的训练数据")
                return False
            
            total_train = 0
            total_val = 0
            
            # 处理每个类别
            for class_name, count in class_counts.items():
                if count == 0:
                    continue
                
                logger.info(f"处理类别: {class_name} ({count} 张图片)")
                
                # 获取该类别的所有图片
                image_files = self._get_class_images(class_name)
                if not image_files:
                    continue
                
                # 随机打乱并分割
                random.shuffle(image_files)
                split_idx = int(len(image_files) * train_ratio)
                train_images = image_files[:split_idx]
                val_images = image_files[split_idx:]
                
                # 处理训练集
                train_count = self._process_images_for_classification(
                    train_images, class_name, 'train')
                total_train += train_count
                
                # 处理验证集
                val_count = self._process_images_for_classification(
                    val_images, class_name, 'val')
                total_val += val_count
                
                logger.info(f"类别 {class_name}: 训练集 {train_count}, 验证集 {val_count}")
            
            # 创建分类配置文件
            self._create_classification_config()
            
            logger.info(f"分类数据准备完成!")
            logger.info(f"训练集: {total_train} 张图片")
            logger.info(f"验证集: {total_val} 张图片")
            
            return True
            
        except Exception as e:
            logger.error(f"准备分类数据失败: {str(e)}")
            return False
    
    def _check_detection_data_exists(self) -> bool:
        """检查检测数据是否已存在"""
        train_images = self.train_dir / "images"
        train_labels = self.train_dir / "labels"
        val_images = self.val_dir / "images"
        val_labels = self.val_dir / "labels"
        
        return (train_images.exists() and train_labels.exists() and 
                val_images.exists() and val_labels.exists() and
                len(list(train_images.glob("*.png"))) > 0)
    
    def _check_classification_data_exists(self) -> bool:
        """检查分类数据是否已存在"""
        train_dir = self.train_dir
        val_dir = self.val_dir
        
        if not (train_dir.exists() and val_dir.exists()):
            return False
        
        # 检查是否有类别子目录
        for class_name in self.class_mapping.keys():
            train_class_dir = train_dir / class_name
            if train_class_dir.exists() and len(list(train_class_dir.glob("*.png"))) > 0:
                return True
        
        return False
    
    def _create_detection_directories(self):
        """创建检测数据目录结构"""
        directories = [
            self.train_dir / "images",
            self.train_dir / "labels", 
            self.val_dir / "images",
            self.val_dir / "labels"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"创建目录: {directory}")
    
    def _create_classification_directories(self):
        """创建分类数据目录结构"""
        # 为训练集和验证集创建类别子目录
        for split in ['train', 'val']:
            split_dir = self.data_root / split
            split_dir.mkdir(parents=True, exist_ok=True)
            
            for class_name in self.class_mapping.keys():
                class_dir = split_dir / class_name
                class_dir.mkdir(parents=True, exist_ok=True)
                logger.debug(f"创建目录: {class_dir}")
    
    def _get_class_images(self, class_name: str) -> List[Path]:
        """获取指定类别的所有图片文件（保持向后兼容）"""
        class_dir = self.raw_images_dir / class_name
        if not class_dir.exists():
            return []
        
        image_files = []
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
        
        for ext in image_extensions:
            image_files.extend(list(class_dir.glob(f'*{ext}')))
            image_files.extend(list(class_dir.glob(f'*{ext.upper()}')))
        
        return image_files
    
    def _get_class_data(self, class_name: str) -> Tuple[List[Path], List[Path]]:
        """
        获取指定类别的所有图片文件和对应的标注文件
        
        Args:
            class_name: 类别名称
            
        Returns:
            Tuple[List[Path], List[Path]]: (图片文件列表, 标注文件列表)
        """
        # 获取图片文件
        image_dir = self.raw_images_dir / class_name
        image_files = []
        if image_dir.exists():
            image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
            for ext in image_extensions:
                image_files.extend(list(image_dir.glob(f'*{ext}')))
                image_files.extend(list(image_dir.glob(f'*{ext.upper()}')))
        
        # 获取标注文件
        label_dir = self.raw_labels_dir / class_name
        label_files = []
        if label_dir.exists():
            label_files.extend(list(label_dir.glob('*.txt')))
            label_files.extend(list(label_dir.glob('*.TXT')))
        
        logger.debug(f"类别 {class_name}: {len(image_files)} 图片, {len(label_files)} 标注")
        return image_files, label_files
    
    def _match_image_label_pairs(self, image_files: List[Path], 
                                label_files: List[Path]) -> List[Tuple[Path, Path]]:
        """
        匹配图片文件和标注文件对
        
        Args:
            image_files: 图片文件列表
            label_files: 标注文件列表
            
        Returns:
            List[Tuple[Path, Path]]: 匹配的(图片文件, 标注文件)对列表
        """
        matched_pairs = []
        
        # 创建标注文件的快速查找字典
        label_dict = {}
        for label_file in label_files:
            label_stem = label_file.stem  # 不含扩展名的文件名
            label_dict[label_stem] = label_file
        
        # 为每个图片文件查找对应的标注文件
        for image_file in image_files:
            image_stem = image_file.stem
            if image_stem in label_dict:
                matched_pairs.append((image_file, label_dict[image_stem]))
            else:
                logger.warning(f"图片文件 {image_file.name} 没有对应的标注文件")
        
        logger.debug(f"成功匹配 {len(matched_pairs)} 对文件")
        return matched_pairs
    
    def _process_images_for_detection(self, image_files: List[Path], 
                                    class_name: str, split: str) -> int:
        """处理图片用于检测训练（旧版本方法，保持向后兼容）"""
        if class_name not in self.class_mapping:
            logger.error(f"未知类别: {class_name}")
            return 0
            
        class_id = self.class_mapping[class_name]
        images_dir = self.data_root / split / "images"
        labels_dir = self.data_root / split / "labels"
        
        # 确保目录存在
        images_dir.mkdir(parents=True, exist_ok=True)
        labels_dir.mkdir(parents=True, exist_ok=True)
        
        count = 0
        failed_count = 0
        
        for img_file in image_files:
            try:
                # 验证图片文件
                if not img_file.exists():
                    logger.warning(f"图片文件不存在: {img_file}")
                    failed_count += 1
                    continue
                
                # 验证图片格式
                if img_file.suffix.lower() not in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
                    logger.warning(f"不支持的图片格式: {img_file}")
                    failed_count += 1
                    continue
                
                # 生成新的文件名，避免重复
                base_name = img_file.stem
                extension = img_file.suffix
                new_img_name = f"{class_name}_{base_name}_{count:04d}{extension}"
                target_img_path = images_dir / new_img_name
                
                # 复制图片
                shutil.copy2(img_file, target_img_path)
                
                # 验证复制是否成功
                if not target_img_path.exists():
                    logger.error(f"图片复制失败: {img_file} -> {target_img_path}")
                    failed_count += 1
                    continue
                
                # 创建对应的标签文件 (YOLO格式)
                label_name = f"{new_img_name.rsplit('.', 1)[0]}.txt"
                label_file = labels_dir / label_name
                
                # 创建一个简单的边界框 (假设目标在图片中央)
                # YOLO格式: class_id center_x center_y width height (归一化坐标)
                with open(label_file, 'w', encoding='utf-8') as f:
                    f.write(f"{class_id} 0.5 0.5 0.8 0.8\n")
                
                # 验证标签文件是否创建成功
                if not label_file.exists():
                    logger.error(f"标签文件创建失败: {label_file}")
                    # 删除对应的图片文件
                    if target_img_path.exists():
                        target_img_path.unlink()
                    failed_count += 1
                    continue
                
                count += 1
                
            except Exception as e:
                logger.error(f"处理图片失败 {img_file}: {str(e)}")
                failed_count += 1
        
        if failed_count > 0:
            logger.warning(f"类别 {class_name} 处理完成: 成功 {count}, 失败 {failed_count}")
        else:
            logger.debug(f"类别 {class_name} 处理完成: {count} 张图片")
        
        return count
    
    def _process_data_pairs_for_detection(self, data_pairs: List[Tuple[Path, Path]], 
                                        class_name: str, split: str) -> int:
        """
        处理图片标注对用于检测训练
        
        Args:
            data_pairs: 图片标注文件对列表
            class_name: 类别名称
            split: 数据集分割类型 ('train' 或 'val')
            
        Returns:
            int: 成功处理的数据对数量
        """
        if class_name not in self.class_mapping:
            logger.error(f"未知类别: {class_name}")
            return 0
            
        images_dir = self.data_root / split / "images"
        labels_dir = self.data_root / split / "labels"
        
        # 确保目录存在
        images_dir.mkdir(parents=True, exist_ok=True)
        labels_dir.mkdir(parents=True, exist_ok=True)
        
        count = 0
        failed_count = 0
        
        for img_file, label_file in data_pairs:
            try:
                # 验证文件存在
                if not img_file.exists():
                    logger.warning(f"图片文件不存在: {img_file}")
                    failed_count += 1
                    continue
                    
                if not label_file.exists():
                    logger.warning(f"标注文件不存在: {label_file}")
                    failed_count += 1
                    continue
                
                # 验证图片格式
                if img_file.suffix.lower() not in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
                    logger.warning(f"不支持的图片格式: {img_file}")
                    failed_count += 1
                    continue
                
                # 生成新的文件名，避免重复
                base_name = img_file.stem
                img_extension = img_file.suffix
                new_img_name = f"{class_name}_{base_name}_{count:04d}{img_extension}"
                new_label_name = f"{class_name}_{base_name}_{count:04d}.txt"
                
                target_img_path = images_dir / new_img_name
                target_label_path = labels_dir / new_label_name
                
                # 复制图片文件
                shutil.copy2(img_file, target_img_path)
                if not target_img_path.exists():
                    logger.error(f"图片复制失败: {img_file} -> {target_img_path}")
                    failed_count += 1
                    continue
                
                # 复制并修正标注文件中的类别ID
                if not self._copy_and_fix_label_file(label_file, target_label_path, class_name):
                    logger.error(f"标注文件处理失败: {label_file} -> {target_label_path}")
                    # 删除对应的图片文件
                    if target_img_path.exists():
                        target_img_path.unlink()
                    failed_count += 1
                    continue
                
                # 验证标注文件内容格式
                if not self._validate_yolo_label(target_label_path):
                    logger.warning(f"标注文件格式验证失败: {target_label_path}")
                    # 可以选择继续或跳过，这里选择继续但记录警告
                
                count += 1
                
            except Exception as e:
                logger.error(f"处理数据对失败 {img_file}, {label_file}: {str(e)}")
                failed_count += 1
        
        if failed_count > 0:
            logger.warning(f"类别 {class_name} 处理完成: 成功 {count}, 失败 {failed_count}")
        else:
            logger.debug(f"类别 {class_name} 处理完成: {count} 对数据文件")
        
        return count
    
    def _copy_and_fix_label_file(self, source_label: Path, target_label: Path, class_name: str) -> bool:
        """
        复制标注文件并修正其中的类别ID，确保与我们的映射一致
        
        Args:
            source_label: 源标注文件路径
            target_label: 目标标注文件路径
            class_name: 当前处理的类别名称
            
        Returns:
            bool: 处理是否成功
        """
        try:
            if class_name not in self.class_mapping:
                logger.error(f"未知类别: {class_name}")
                return False
            
            # 获取正确的类别ID
            correct_class_id = self.class_mapping[class_name]
            
            # 读取源标注文件
            with open(source_label, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 处理每一行，修正类别ID
            fixed_lines = []
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line:
                    fixed_lines.append(line + '\n')
                    continue
                
                parts = line.split()
                if len(parts) != 5:
                    logger.warning(f"标注文件 {source_label} 第{line_num}行格式错误: 应有5个值")
                    continue
                
                try:
                    # 解析原始数据
                    original_class_id = int(parts[0])
                    x, y, w, h = parts[1:5]
                    
                    # 使用正确的类别ID替换原始ID
                    fixed_line = f"{correct_class_id} {x} {y} {w} {h}\n"
                    fixed_lines.append(fixed_line)
                    
                    # 如果类别ID发生了变化，记录日志
                    if original_class_id != correct_class_id:
                        logger.debug(f"修正类别ID: {original_class_id} -> {correct_class_id} ({class_name})")
                        
                except ValueError as e:
                    logger.warning(f"标注文件 {source_label} 第{line_num}行数值格式错误: {e}")
                    continue
            
            # 写入修正后的标注文件
            with open(target_label, 'w', encoding='utf-8') as f:
                f.writelines(fixed_lines)
            
            return True
            
        except Exception as e:
            logger.error(f"处理标注文件失败 {source_label}: {str(e)}")
            return False

    def _validate_yolo_label(self, label_file: Path) -> bool:
        """
        验证YOLO标注文件格式
        
        Args:
            label_file: 标注文件路径
            
        Returns:
            bool: 格式是否正确
        """
        try:
            with open(label_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if not lines:
                logger.debug(f"标注文件为空: {label_file}")
                return True  # 空文件也是合法的（表示无目标）
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line:
                    continue
                
                parts = line.split()
                if len(parts) != 5:
                    logger.warning(f"标注文件 {label_file} 第{line_num}行格式错误: 应有5个值")
                    return False
                
                try:
                    class_id = int(parts[0])
                    x, y, w, h = map(float, parts[1:5])
                    
                    # 验证坐标范围
                    if not (0 <= x <= 1 and 0 <= y <= 1 and 0 <= w <= 1 and 0 <= h <= 1):
                        logger.warning(f"标注文件 {label_file} 第{line_num}行坐标超出范围 [0,1]")
                        return False
                        
                except ValueError:
                    logger.warning(f"标注文件 {label_file} 第{line_num}行数值格式错误")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"验证标注文件失败 {label_file}: {str(e)}")
            return False
    
    def _process_images_for_classification(self, image_files: List[Path],
                                         class_name: str, split: str) -> int:
        """处理图片用于分类训练"""
        class_dir = self.data_root / split / class_name
        
        count = 0
        for img_file in image_files:
            try:
                # 复制图片到对应的类别目录
                shutil.copy2(img_file, class_dir / img_file.name)
                count += 1
                
            except Exception as e:
                logger.error(f"处理图片失败 {img_file}: {str(e)}")
        
        return count
    
    def _create_detection_config(self):
        """创建检测训练配置文件 - 确保YOLO使用我们指定的类别映射"""
        
        # 确保names是按照ID顺序排列的列表，而不是字典
        # 这样YOLO就会严格按照我们的顺序使用类别
        names_list = []
        chinese_names_list = []
        
        # 按照class_id顺序构建列表
        for class_id in sorted(self.class_mapping.values()):
            names_list.append(self.class_names[class_id])
            # 找到对应的中文名称
            for chinese_name, cid in self.class_mapping.items():
                if cid == class_id:
                    chinese_names_list.append(chinese_name)
                    break
        
        config = {
            'path': str(self.data_root),
            'train': 'train/images',
            'val': 'val/images',
            'nc': len(self.class_mapping),
            'names': names_list  # 使用列表而不是字典，确保顺序
        }
        
        # 添加详细的类别信息用于调试和记录
        config['class_details'] = {
            'chinese_names': {i: chinese_names_list[i] for i in range(len(chinese_names_list))},
            'english_names': {i: names_list[i] for i in range(len(names_list))},
            'class_mapping': self.class_mapping,
            'total_classes': len(self.class_mapping)
        }
        
        # 创建两个配置文件，保持兼容性
        config_files = [
            self.data_root / "train_config.yaml",  # 主要配置文件
            self.data_root / "train_simple.yaml"   # 保持向后兼容
        ]
        
        for config_file in config_files:
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            logger.info(f"检测配置文件已创建: {config_file}")
            
        # 额外创建一个类别映射文件用于记录
        mapping_file = self.data_root / "class_mapping.txt"
        with open(mapping_file, 'w', encoding='utf-8') as f:
            f.write("# 类别映射表 (自动生成 - 确保与YOLO训练一致)\n")
            f.write("# 格式: ID: 中文名称 -> 英文名称\n")
            f.write("# 注意: 此映射表与YOLO训练时使用的映射完全一致\n\n")
            for i in range(len(names_list)):
                f.write(f"{i}: {chinese_names_list[i]} -> {names_list[i]}\n")
        logger.info(f"类别映射文件已创建: {mapping_file}")
        
        # 输出映射信息到日志
        logger.info("类别映射确认:")
        for i in range(len(names_list)):
            logger.info(f"  {i}: {chinese_names_list[i]} -> {names_list[i]}")
    
    def _create_classification_config(self):
        """创建分类训练配置文件"""
        config = {
            'path': str(self.data_root),
            'train': 'train',
            'val': 'val', 
            'nc': len(self.class_mapping),
            'names': self.class_names,
            'chinese_names': {v: k for k, v in self.class_mapping.items()}
        }
        
        config_file = self.data_root / "classification_config.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        
        logger.info(f"分类配置文件已创建: {config_file}")
    
    def clean_processed_data(self):
        """清理已处理的数据"""
        try:
            directories_to_clean = [
                self.train_dir,
                self.val_dir
            ]
            
            for directory in directories_to_clean:
                if directory.exists():
                    shutil.rmtree(directory)
                    logger.info(f"已清理目录: {directory}")
            
            # 删除配置文件
            config_files = [
                self.data_root / "train_simple.yaml",
                self.data_root / "classification_config.yaml"
            ]
            
            for config_file in config_files:
                if config_file.exists():
                    config_file.unlink()
                    logger.info(f"已删除配置文件: {config_file}")
            
            logger.info("数据清理完成")
            
        except Exception as e:
            logger.error(f"清理数据失败: {str(e)}")

if __name__ == "__main__":
    # 测试数据处理器
    processor = DataProcessor()
    
    # 扫描数据
    class_counts = processor.scan_data()
    print("数据统计:")
    for class_name, count in class_counts.items():
        print(f"  {class_name}: {count} 张")
    
    # 准备检测数据
    success = processor.prepare_detection_data(force_recreate=True)
    print(f"检测数据准备: {'成功' if success else '失败'}") 