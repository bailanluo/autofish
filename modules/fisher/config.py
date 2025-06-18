"""
Fisher钓鱼模块配置管理器
负责加载和管理所有配置项，包括系统配置、热键配置、模型参数等

作者: AutoFish Team
版本: v1.0
创建时间: 2024-12-28
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ModelConfig:
    """模型配置类"""
    model_path: str = "runs/fishing_model_latest.pt"  # 模型文件路径
    confidence_threshold: float = 0.5  # 置信度阈值
    device: str = "auto"  # 设备选择: auto/cpu/cuda
    detection_interval: float = 0.1  # 检测间隔(秒)

@dataclass 
class OCRConfig:
    """OCR配置类"""
    tesseract_path: str = r"D:\Python\tool\Tesseract-OCR"  # Tesseract路径
    language: str = "chi_sim+eng"  # 识别语言
    confidence_threshold: int = 60  # 置信度阈值
    detection_interval: float = 0.2  # OCR检测间隔(秒)

@dataclass
class TimingConfig:
    """时间配置类"""
    initial_timeout: int = 180  # 初始状态超时时间(秒) - 3分钟
    
    # 新版鼠标点击时间控制 (v1.0.10)
    mouse_press_time_min: float = 0.08  # 鼠标按下时间最小值(秒)
    mouse_press_time_max: float = 0.12  # 鼠标按下时间最大值(秒)
    mouse_release_time_min: float = 0.05  # 鼠标释放后等待时间最小值(秒)
    mouse_release_time_max: float = 0.08  # 鼠标释放后等待时间最大值(秒)
    click_interval_min: float = 0.18  # 点击间隔最小值(秒)
    click_interval_max: float = 0.25  # 点击间隔最大值(秒)
    
    # 兼容旧版配置 (保留用于其他地方)
    click_delay_min: float = 0.054  # 鼠标点击最小间隔(秒) - 兼容性保留
    click_delay_max: float = 0.127  # 鼠标点击最大间隔(秒) - 兼容性保留
    
    # 其他时间配置
    state3_pause_time: float = 1.0  # 状态3暂停时间(秒)
    success_wait_time: float = 1.5  # 钓鱼成功等待时间(秒)
    cast_hold_time: float = 2.0  # 抛竿长按时间(秒)
    key_press_time: float = 1.5  # 按键持续时间(秒) - a/d键
    key_pause_time: float = 0.5  # 按键暂停时间(秒) - a/d键间隔

@dataclass
class HotkeyConfig:
    """热键配置类"""
    start_fishing: str = "ctrl+alt+s"  # 开始钓鱼快捷键
    stop_fishing: str = "ctrl+alt+x"  # 停止钓鱼快捷键
    emergency_stop: str = "ctrl+alt+q"  # 紧急停止快捷键

@dataclass
class UIConfig:
    """UI配置类"""
    show_status_window: bool = True  # 是否显示状态窗口
    status_window_position: tuple = (10, 10)  # 状态窗口位置
    status_window_color: str = "blue"  # 状态窗口文字颜色
    main_window_size: tuple = (400, 300)  # 主窗口大小

class FisherConfig:
    """Fisher钓鱼模块配置管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径，默认为模块目录下的config.yaml
        """
        if config_path is None:
            config_path = Path(__file__).parent / "config.yaml"
        
        self.config_path = Path(config_path)
        
        # 初始化各配置类
        self.model = ModelConfig()
        self.ocr = OCRConfig()
        self.timing = TimingConfig()
        self.hotkey = HotkeyConfig()
        self.ui = UIConfig()
        
        # 加载配置文件
        self.load_config()
    
    def load_config(self) -> None:
        """从配置文件加载配置"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f) or {}
                
                # 更新各配置类
                self._update_config_from_dict(self.model, config_data.get('model', {}))
                self._update_config_from_dict(self.ocr, config_data.get('ocr', {}))
                self._update_config_from_dict(self.timing, config_data.get('timing', {}))
                self._update_config_from_dict(self.hotkey, config_data.get('hotkey', {}))
                self._update_config_from_dict(self.ui, config_data.get('ui', {}))
                
                print(f"配置加载成功: {self.config_path}")
            else:
                print(f"配置文件不存在，使用默认配置: {self.config_path}")
                self.save_config()  # 保存默认配置
                
        except Exception as e:
            print(f"配置加载失败，使用默认配置: {e}")
    
    def save_config(self) -> None:
        """保存配置到文件"""
        try:
            # 确保配置目录存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            config_data = {
                'model': self._config_to_dict(self.model),
                'ocr': self._config_to_dict(self.ocr),
                'timing': self._config_to_dict(self.timing),
                'hotkey': self._config_to_dict(self.hotkey),
                'ui': self._config_to_dict(self.ui)
            }
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, 
                         allow_unicode=True, indent=2)
            
            print(f"配置保存成功: {self.config_path}")
            
        except Exception as e:
            print(f"配置保存失败: {e}")
    
    def _update_config_from_dict(self, config_obj: object, data: Dict[str, Any]) -> None:
        """从字典更新配置对象"""
        for key, value in data.items():
            if hasattr(config_obj, key):
                setattr(config_obj, key, value)
    
    def _config_to_dict(self, config_obj: object) -> Dict[str, Any]:
        """将配置对象转换为字典"""
        return {k: v for k, v in config_obj.__dict__.items() 
                if not k.startswith('_')}
    
    def get_model_path(self) -> str:
        """获取模型文件绝对路径"""
        if os.path.isabs(self.model.model_path):
            return self.model.model_path
        else:
            # 相对于项目根目录
            project_root = Path(__file__).parent.parent.parent
            return str(project_root / self.model.model_path)
    
    def validate_paths(self) -> bool:
        """验证关键路径是否存在"""
        # 验证模型文件
        model_path = self.get_model_path()
        if not os.path.exists(model_path):
            print(f"模型文件不存在: {model_path}")
            return False
        
        # 验证Tesseract路径
        tesseract_exe = os.path.join(self.ocr.tesseract_path, "tesseract.exe")
        if not os.path.exists(tesseract_exe):
            print(f"Tesseract执行文件不存在: {tesseract_exe}")
            return False
        
        return True
    
    def get_state_names(self) -> Dict[int, str]:
        """获取状态名称映射"""
        return {
            0: "等待上钩状态",
            1: "鱼上钩末提线状态",
            2: "提线中_耐力未到二分之一状态", 
            3: "提线中_耐力已到二分之一状态",
            4: "钓鱼成功状态_txt"
        }
    
    def update_hotkey(self, key_name: str, key_combination: str) -> None:
        """更新热键配置"""
        if hasattr(self.hotkey, key_name):
            setattr(self.hotkey, key_name, key_combination)
            self.save_config()
            print(f"热键 {key_name} 已更新为: {key_combination}")
        else:
            print(f"未知的热键名称: {key_name}")

# 全局配置实例
fisher_config = FisherConfig() 