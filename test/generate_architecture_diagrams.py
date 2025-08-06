#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AutoFish架构图生成器
用于生成项目的各种架构图表和框架图

功能：
1. 系统整体架构图
2. 模块关系图  
3. 数据流向图
4. 技术栈图
5. 状态机图

依赖：
pip install matplotlib graphviz networkx plotly pandas seaborn
"""

import os
import sys
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import networkx as nx
import json
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False


class AutoFishArchitectureGenerator:
    """AutoFish架构图生成器"""
    
    def __init__(self, output_dir="test/diagrams"):
        """
        初始化架构图生成器
        
        Args:
            output_dir: 输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # 项目结构定义
        self.project_structure = {
            "main": {
                "name": "主程序入口",
                "file": "main.py",
                "description": "模块选择和启动界面",
                "color": "#2E86AB"
            },
            "data_collector": {
                "name": "数据采集模块",
                "components": [
                    "屏幕截图", "区域标注", "数据管理", "热键监听",
                    "UI管理器", "业务逻辑", "配置管理"
                ],
                "color": "#A23B72"
            },
            "model_trainer": {
                "name": "模型训练模块", 
                "components": [
                    "数据预处理", "YOLO训练", "模型验证", "结果分析",
                    "训练监控", "配置管理", "桌面测试"
                ],
                "color": "#F18F01"
            },
            "fisher": {
                "name": "自动钓鱼模块",
                "components": [
                    "状态机控制", "模型推理", "输入控制", "多线程协调",
                    "YOLO检测", "OCR识别", "热键管理"
                ],
                "color": "#C73E1D"
            },
            "shared": {
                "name": "共享组件",
                "components": [
                    "统一日志系统", "配置管理", "图像工具", "文件工具",
                    "OCR工具", "热键工具"
                ],
                "color": "#4A5568"
            }
        }
        
        # 数据流向定义
        self.data_flow = [
            ("原始截图", "data/raw/images/"),
            ("标注数据", "data/raw/labels/"), 
            ("训练数据集", "data/train/ & data/val/"),
            ("YOLO模型", "runs/fishing_model_latest.pt"),
            ("实时推理", "fisher模块"),
            ("自动控制", "游戏操作")
        ]
        
        # 技术栈定义
        self.tech_stack = {
            "深度学习": ["Ultralytics YOLO", "PyTorch", "torchvision"],
            "计算机视觉": ["OpenCV", "PIL/Pillow", "MSS"],
            "文字识别": ["Tesseract OCR", "pytesseract"],
            "界面开发": ["Tkinter", "customtkinter"],
            "自动化控制": ["PyAutoGUI", "pynput", "keyboard", "mouse"],
            "数据处理": ["NumPy", "pandas", "PyYAML"],
            "可视化": ["matplotlib", "seaborn"],
            "系统工具": ["pathlib", "psutil", "threading"]
        }
        
        # 状态机定义
        self.fishing_states = {
            "STOPPED": {"name": "停止状态", "color": "#6C757D"},
            "WAITING_INITIAL": {"name": "等待初始状态", "color": "#17A2B8"},
            "WAITING_HOOK": {"name": "等待上钩状态", "color": "#FFC107"},
            "FISH_HOOKED": {"name": "鱼上钩状态", "color": "#FD7E14"},
            "PULLING_NORMAL": {"name": "提线中_耐力未到二分之一", "color": "#DC3545"},
            "PULLING_HALFWAY": {"name": "提线中_耐力已到二分之一", "color": "#E83E8C"},
            "SUCCESS": {"name": "钓鱼成功状态", "color": "#28A745"},
            "CASTING": {"name": "抛竿状态", "color": "#007BFF"}
        }
        
        print(f"架构图生成器初始化完成，输出目录: {self.output_dir}")
    
    def generate_system_architecture(self):
        """生成系统整体架构图"""
        fig, ax = plt.subplots(figsize=(20, 14))
        ax.set_xlim(0, 12)
        ax.set_ylim(0, 12)
        ax.axis('off')
        
        # 标题
        ax.text(6, 11.2, 'AutoFish v2.3 系统架构图', 
                fontsize=32, fontweight='bold', ha='center')
        
        # 主程序入口
        main_box = FancyBboxPatch(
            (1.5, 9.5), 9, 1,
            boxstyle="round,pad=0.1",
            facecolor=self.project_structure["main"]["color"],
            edgecolor='black',
            linewidth=2
        )
        ax.add_patch(main_box)
        ax.text(6, 10.1, '主程序入口 (main.py)', 
                fontsize=20, fontweight='bold', ha='center', color='white')
        ax.text(6, 9.7, '模块选择和启动界面', 
                fontsize=16, ha='center', color='white')
        
        # 三大核心模块
        modules = [
            ("data_collector", 1.5, 7),
            ("model_trainer", 4.5, 7),
            ("fisher", 7.5, 7)
        ]
        
        for module_key, x, y in modules:
            module = self.project_structure[module_key]
            
            # 模块主框
            module_box = FancyBboxPatch(
                (x-0.6, y-1.2), 3.2, 2.4,
                boxstyle="round,pad=0.1",
                facecolor=module["color"],
                edgecolor='black',
                linewidth=2,
                alpha=0.8
            )
            ax.add_patch(module_box)
            
            # 模块标题
            ax.text(x+1, y+0.8, module["name"], 
                    fontsize=18, fontweight='bold', ha='center', color='white')
            
            # 组件列表
            components = module["components"][:4]  # 只显示前4个组件
            for i, comp in enumerate(components):
                ax.text(x+1, y+0.3-i*0.3, f"• {comp}", 
                        fontsize=14, ha='center', color='white')
            
            if len(module["components"]) > 4:
                ax.text(x+1, y-0.9, "...", 
                        fontsize=16, ha='center', color='white')
            
            # 连接线到主程序
            arrow = ConnectionPatch(
                (x+1, y+1.2), (6, 9.5),
                "data", "data",
                arrowstyle="->",
                shrinkA=0, shrinkB=0,
                mutation_scale=20,
                fc="black"
            )
            ax.add_patch(arrow)
        
        # 共享组件
        shared_box = FancyBboxPatch(
            (1.5, 4), 9, 1.5,
            boxstyle="round,pad=0.1",
            facecolor=self.project_structure["shared"]["color"],
            edgecolor='black',
            linewidth=2,
            alpha=0.8
        )
        ax.add_patch(shared_box)
        
        ax.text(6, 5, '共享组件', 
                fontsize=20, fontweight='bold', ha='center', color='white')
        
        shared_components = self.project_structure["shared"]["components"]
        for i, comp in enumerate(shared_components[:3]):
            ax.text(2.5+i*3, 4.5, comp, 
                    fontsize=15, ha='center', color='white')
        
        # 数据目录
        data_dirs = [
            ("data/raw/", 1.5, 2.5),
            ("data/train/", 3.5, 2.5), 
            ("runs/", 5.5, 2.5),
            ("config/", 7.5, 2.5),
            ("logs/", 9.5, 2.5)
        ]
        
        for dir_name, x, y in data_dirs:
            dir_box = FancyBboxPatch(
                (x-0.6, y-0.4), 2.2, 0.8,
                boxstyle="round,pad=0.05",
                facecolor='#E9ECEF',
                edgecolor='#6C757D',
                linewidth=1
            )
            ax.add_patch(dir_box)
            ax.text(x+0.5, y, dir_name, 
                    fontsize=15, ha='center', color='#495057')
        
        # 底部说明
        ax.text(6, 1, '数据流向: 原始截图 → 标注数据 → 训练模型 → 实时推理 → 自动控制', 
                fontsize=18, ha='center', style='italic')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'system_architecture.png', 
                   dpi=300, bbox_inches='tight')
        print(f"✅ 系统架构图已保存: {self.output_dir / 'system_architecture.png'}")
        plt.close()
    
    def generate_module_relationship(self):
        """生成模块关系图"""
        fig, ax = plt.subplots(figsize=(14, 10))
        
        # 创建有向图
        G = nx.DiGraph()
        
        # 添加节点
        modules = {
            'main': {'pos': (0, 0), 'color': '#2E86AB'},
            'data_collector': {'pos': (-2, -1), 'color': '#A23B72'},
            'model_trainer': {'pos': (0, -1), 'color': '#F18F01'},
            'fisher': {'pos': (2, -1), 'color': '#C73E1D'},
            'logger': {'pos': (-1, -2), 'color': '#4A5568'},
            'config_manager': {'pos': (0, -2), 'color': '#4A5568'},
            'utils': {'pos': (1, -2), 'color': '#4A5568'},
            'data_raw': {'pos': (-3, -2.5), 'color': '#6C757D'},
            'data_train': {'pos': (-1.5, -2.5), 'color': '#6C757D'},
            'runs': {'pos': (0.5, -2.5), 'color': '#6C757D'},
            'config': {'pos': (2.5, -2.5), 'color': '#6C757D'}
        }
        
        for node, attrs in modules.items():
            G.add_node(node, **attrs)
        
        # 添加边（表示依赖关系）
        edges = [
            ('main', 'data_collector'),
            ('main', 'model_trainer'),
            ('main', 'fisher'),
            ('data_collector', 'logger'),
            ('data_collector', 'config_manager'),
            ('data_collector', 'utils'),
            ('data_collector', 'data_raw'),
            ('model_trainer', 'logger'),
            ('model_trainer', 'config_manager'),
            ('model_trainer', 'data_train'),
            ('model_trainer', 'runs'),
            ('fisher', 'logger'),
            ('fisher', 'config_manager'),
            ('fisher', 'utils'),
            ('fisher', 'runs'),
            ('data_collector', 'data_train'),
            ('model_trainer', 'fisher'),
        ]
        
        G.add_edges_from(edges)
        
        # 设置布局
        pos = nx.get_node_attributes(G, 'pos')
        colors = [modules[node]['color'] for node in G.nodes()]
        
        # 绘制图
        nx.draw_networkx_nodes(G, pos, node_color=colors, 
                              node_size=3000, alpha=0.8, ax=ax)
        nx.draw_networkx_edges(G, pos, edge_color='gray', 
                              arrows=True, arrowsize=20, 
                              arrowstyle='->', ax=ax)
        
        # 添加标签
        labels = {
            'main': '主程序',
            'data_collector': '数据采集',
            'model_trainer': '模型训练', 
            'fisher': '自动钓鱼',
            'logger': '日志系统',
            'config_manager': '配置管理',
            'utils': '工具类库',
            'data_raw': 'data/raw/',
            'data_train': 'data/train/',
            'runs': 'runs/',
            'config': 'config/'
        }
        
        nx.draw_networkx_labels(G, pos, labels, font_size=14, 
                               font_color='white', font_weight='bold', ax=ax)
        
        ax.set_title('AutoFish 模块关系图', fontsize=22, fontweight='bold', pad=20)
        ax.axis('off')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'module_relationship.png', 
                   dpi=300, bbox_inches='tight')
        print(f"✅ 模块关系图已保存: {self.output_dir / 'module_relationship.png'}")
        plt.close()
    
    def generate_data_flow_diagram(self):
        """生成数据流向图"""
        fig, ax = plt.subplots(figsize=(20, 10))
        ax.set_xlim(0, 14)
        ax.set_ylim(0, 8)
        ax.axis('off')
        
        # 标题
        ax.text(7, 7.5, 'AutoFish 数据流向图', 
                fontsize=28, fontweight='bold', ha='center')
        
        # 数据流步骤
        steps = [
            {"name": "原始截图", "desc": "屏幕截图\n区域选择", "x": 1.5, "color": "#E3F2FD"},
            {"name": "数据标注", "desc": "YOLO格式\n标注生成", "x": 3.5, "color": "#F3E5F5"},
            {"name": "数据预处理", "desc": "8:2分割\n数据增强", "x": 5.5, "color": "#FFF3E0"},
            {"name": "模型训练", "desc": "YOLO训练\n性能优化", "x": 7.5, "color": "#FFEBEE"},
            {"name": "模型部署", "desc": "实时推理\n状态检测", "x": 9.5, "color": "#E8F5E8"},
            {"name": "自动控制", "desc": "游戏操作\n智能响应", "x": 11.5, "color": "#F0F4FF"}
        ]
        
        for i, step in enumerate(steps):
            # 绘制步骤框
            step_box = FancyBboxPatch(
                (step["x"]-0.8, 4), 1.6, 2,
                boxstyle="round,pad=0.1",
                facecolor=step["color"],
                edgecolor='#1976D2',
                linewidth=2
            )
            ax.add_patch(step_box)
            
            # 步骤标题
            ax.text(step["x"], 5.2, step["name"], 
                    fontsize=17, fontweight='bold', ha='center')
            
            # 步骤描述
            ax.text(step["x"], 4.5, step["desc"], 
                    fontsize=15, ha='center', va='center')
            
            # 绘制箭头（除了最后一个）
            if i < len(steps) - 1:
                arrow = patches.FancyArrowPatch(
                    (step["x"]+0.8, 5), (steps[i+1]["x"]-0.8, 5),
                    arrowstyle='->',
                    mutation_scale=25,
                    color='#1976D2',
                    linewidth=3
                )
                ax.add_patch(arrow)
        
        # 底部数据目录映射
        directories = [
            ("data/raw/images/", 1.5),
            ("data/raw/labels/", 3.5),
            ("data/train/ & data/val/", 5.5),
            ("runs/fishing_train_*/", 7.5),
            ("runs/fishing_model_latest.pt", 9.5),
            ("实时游戏控制", 11.5)
        ]
        
        for dir_name, x in directories:
            dir_box = FancyBboxPatch(
                (x-0.8, 2), 1.6, 0.8,
                boxstyle="round,pad=0.05",
                facecolor='#F5F5F5',
                edgecolor='#9E9E9E',
                linewidth=1
            )
            ax.add_patch(dir_box)
            ax.text(x, 2.4, dir_name, 
                    fontsize=14, ha='center', va='center')
            
            # 连接线
            ax.plot([x, x], [2.8, 4], 'k--', alpha=0.5, linewidth=1)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'data_flow_diagram.png', 
                   dpi=300, bbox_inches='tight')
        print(f"✅ 数据流向图已保存: {self.output_dir / 'data_flow_diagram.png'}")
        plt.close()
    
    def generate_tech_stack_diagram(self):
        """生成技术栈图"""
        fig, ax = plt.subplots(figsize=(14, 10))
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        ax.axis('off')
        
        # 标题
        ax.text(5, 9.5, 'AutoFish 技术栈架构', 
                fontsize=24, fontweight='bold', ha='center')
        
        # 技术栈层级
        layers = [
            {"name": "应用层", "color": "#1976D2", "y": 8, "techs": ["数据采集", "模型训练", "自动钓鱼"]},
            {"name": "AI框架层", "color": "#388E3C", "y": 6.5, "techs": ["Ultralytics YOLO", "PyTorch", "Tesseract OCR"]},
            {"name": "计算机视觉层", "color": "#F57C00", "y": 5, "techs": ["OpenCV", "PIL", "MSS", "NumPy"]},
            {"name": "界面控制层", "color": "#7B1FA2", "y": 3.5, "techs": ["Tkinter", "PyAutoGUI", "pynput", "keyboard"]},
            {"name": "系统基础层", "color": "#5D4037", "y": 2, "techs": ["Python 3.8+", "Windows API", "Threading", "YAML"]}
        ]
        
        for layer in layers:
            # 绘制层级背景
            layer_box = FancyBboxPatch(
                (0.5, layer["y"]-0.4), 9, 1,
                boxstyle="round,pad=0.1",
                facecolor=layer["color"],
                edgecolor='black',
                linewidth=1,
                alpha=0.8
            )
            ax.add_patch(layer_box)
            
            # 层级名称
            ax.text(1, layer["y"], layer["name"], 
                    fontsize=16, fontweight='bold', ha='left', va='center', color='white')
            
            # 技术组件
            tech_x = 3
            for tech in layer["techs"]:
                tech_box = FancyBboxPatch(
                    (tech_x-0.4, layer["y"]-0.2), len(tech)*0.1+0.8, 0.4,
                    boxstyle="round,pad=0.05",
                    facecolor='white',
                    edgecolor=layer["color"],
                    linewidth=1,
                    alpha=0.9
                )
                ax.add_patch(tech_box)
                ax.text(tech_x, layer["y"], tech, 
                        fontsize=13, ha='left', va='center', color=layer["color"])
                tech_x += len(tech)*0.1 + 1.2
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'tech_stack_diagram.png', 
                   dpi=300, bbox_inches='tight')
        print(f"✅ 技术栈图已保存: {self.output_dir / 'tech_stack_diagram.png'}")
        plt.close()
    
    def generate_state_machine_diagram(self):
        """生成钓鱼状态机图"""
        fig, ax = plt.subplots(figsize=(18, 12))
        ax.set_xlim(0, 14)
        ax.set_ylim(0, 12)
        ax.axis('off')
        
        # 标题
        ax.text(7, 11.5, '钓鱼状态机转换图', 
                fontsize=28, fontweight='bold', ha='center')
        
        # 状态位置定义
        state_positions = {
            "STOPPED": (2.5, 9.5),
            "WAITING_INITIAL": (7, 9.5),
            "WAITING_HOOK": (11.5, 9.5),
            "FISH_HOOKED": (11.5, 6.5),
            "PULLING_NORMAL": (7, 4.5),
            "PULLING_HALFWAY": (11.5, 4.5),
            "SUCCESS": (7, 2.5),
            "CASTING": (2.5, 2.5)
        }
        
        # 绘制状态节点
        for state_key, (x, y) in state_positions.items():
            state_info = self.fishing_states[state_key]
            
            # 状态圆圈
            circle = plt.Circle((x, y), 1.2, 
                              facecolor=state_info["color"], 
                              edgecolor='black', 
                              linewidth=2,
                              alpha=0.8)
            ax.add_patch(circle)
            
            # 状态名称（分两行显示）
            name_parts = state_info["name"].split('_')
            if len(name_parts) > 1:
                ax.text(x, y+0.3, name_parts[0], 
                        fontsize=15, fontweight='bold', ha='center', va='center', color='white')
                ax.text(x, y-0.3, '_'.join(name_parts[1:]), 
                        fontsize=14, ha='center', va='center', color='white')
            else:
                ax.text(x, y, state_info["name"], 
                        fontsize=16, fontweight='bold', ha='center', va='center', color='white')
        
        # 状态转换箭头
        transitions = [
            ("STOPPED", "WAITING_INITIAL", "开始钓鱼"),
            ("WAITING_INITIAL", "WAITING_HOOK", "检测到初始状态"),
            ("WAITING_HOOK", "FISH_HOOKED", "鱼上钩"),
            ("FISH_HOOKED", "PULLING_NORMAL", "开始提线"),
            ("PULLING_NORMAL", "PULLING_HALFWAY", "耐力到一半"),
            ("PULLING_HALFWAY", "PULLING_NORMAL", "耐力恢复"),
            ("PULLING_NORMAL", "SUCCESS", "钓鱼成功"),
            ("PULLING_HALFWAY", "SUCCESS", "钓鱼成功"),
            ("SUCCESS", "CASTING", "确认成功"),
            ("CASTING", "WAITING_INITIAL", "重新抛竿"),
            ("WAITING_INITIAL", "STOPPED", "停止钓鱼"),
            ("FISH_HOOKED", "STOPPED", "紧急停止"),
        ]
        
        for from_state, to_state, label in transitions:
            from_pos = state_positions[from_state]
            to_pos = state_positions[to_state]
            
            # 计算箭头位置（避开圆圈）
            dx = to_pos[0] - from_pos[0]
            dy = to_pos[1] - from_pos[1]
            distance = (dx**2 + dy**2)**0.5
            
            if distance > 0:
                unit_x = dx / distance
                unit_y = dy / distance
                
                start_x = from_pos[0] + unit_x * 1.2
                start_y = from_pos[1] + unit_y * 1.2
                end_x = to_pos[0] - unit_x * 1.2
                end_y = to_pos[1] - unit_y * 1.2
                
                # 特殊处理循环箭头
                if from_state == "PULLING_NORMAL" and to_state == "PULLING_HALFWAY":
                    arrow = patches.FancyArrowPatch(
                        (start_x, start_y), (end_x, end_y),
                        arrowstyle='->',
                        mutation_scale=15,
                        color='#2E86AB',
                        linewidth=2,
                        connectionstyle="arc3,rad=0.3"
                    )
                elif from_state == "PULLING_HALFWAY" and to_state == "PULLING_NORMAL":
                    arrow = patches.FancyArrowPatch(
                        (start_x, start_y), (end_x, end_y),
                        arrowstyle='->',
                        mutation_scale=15,
                        color='#2E86AB',
                        linewidth=2,
                        connectionstyle="arc3,rad=-0.3"
                    )
                else:
                    arrow = patches.FancyArrowPatch(
                        (start_x, start_y), (end_x, end_y),
                        arrowstyle='->',
                        mutation_scale=15,
                        color='#2E86AB',
                        linewidth=2
                    )
                
                ax.add_patch(arrow)
                
                # 添加转换标签
                mid_x = (start_x + end_x) / 2
                mid_y = (start_y + end_y) / 2
                
                # 只为主要转换添加标签
                if label in ["开始钓鱼", "鱼上钩", "钓鱼成功", "重新抛竿"]:
                    ax.text(mid_x, mid_y+0.3, label, 
                            fontsize=7, ha='center', va='bottom',
                            bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.8))
        
        # 添加说明
        ax.text(6, 0.5, '主流程: STOPPED → WAITING_INITIAL → WAITING_HOOK → FISH_HOOKED → PULLING → SUCCESS → CASTING → 循环', 
                fontsize=16, ha='center', style='italic')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'state_machine_diagram.png', 
                   dpi=300, bbox_inches='tight')
        print(f"✅ 状态机图已保存: {self.output_dir / 'state_machine_diagram.png'}")
        plt.close()
    
    def generate_performance_chart(self):
        """生成性能指标图表"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(18, 12))
        fig.suptitle('AutoFish 性能指标图表', fontsize=24, fontweight='bold')
        
        # 1. 模型性能指标
        metrics = ['mAP50', 'mAP50-95', 'Precision', 'Recall']
        values = [99.5, 99.1, 99.8, 100.0]
        colors = ['#1976D2', '#388E3C', '#F57C00', '#7B1FA2']
        
        bars1 = ax1.bar(metrics, values, color=colors, alpha=0.8)
        ax1.set_title('模型性能指标 (%)', fontweight='bold', fontsize=18)
        ax1.set_ylabel('准确率 (%)', fontsize=16)
        ax1.set_ylim(95, 100.5)
        ax1.tick_params(axis='both', which='major', labelsize=14)
        
        # 添加数值标签
        for bar, value in zip(bars1, values):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                    f'{value}%', ha='center', va='bottom', fontweight='bold', fontsize=14)
        
        # 2. 各类别检测精度
        classes = ['waiting_hook', 'hooked_no_pull', 'pulling_low', 'pulling_half', 'success_txt']
        class_precision = [99.7, 99.9, 99.6, 99.7, 100.0]
        
        bars2 = ax2.bar(range(len(classes)), class_precision, 
                       color='#4CAF50', alpha=0.8)
        ax2.set_title('各类别检测精度 (%)', fontweight='bold', fontsize=18)
        ax2.set_ylabel('精确率 (%)', fontsize=16)
        ax2.set_xticks(range(len(classes)))
        ax2.set_xticklabels(classes, rotation=45, ha='right', fontsize=13)
        ax2.set_ylim(99, 100.2)
        ax2.tick_params(axis='y', which='major', labelsize=14)
        
        for bar, value in zip(bars2, class_precision):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                    f'{value}%', ha='center', va='bottom', fontsize=13)
        
        # 3. 系统性能指标
        perf_metrics = ['推理速度\n(ms)', '训练时间\n(分钟)', 'GPU显存\n(GB)', '模型大小\n(MB)']
        perf_values = [1.8, 35, 2.12, 6.2]
        perf_colors = ['#FF5722', '#9C27B0', '#607D8B', '#795548']
        
        bars3 = ax3.bar(perf_metrics, perf_values, color=perf_colors, alpha=0.8)
        ax3.set_title('系统性能指标', fontweight='bold', fontsize=18)
        ax3.set_ylabel('数值', fontsize=16)
        ax3.tick_params(axis='both', which='major', labelsize=14)
        
        for bar, value in zip(bars3, perf_values):
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(perf_values)*0.02,
                    f'{value}', ha='center', va='bottom', fontweight='bold', fontsize=14)
        
        # 4. 项目规模统计
        scale_metrics = ['代码行数\n(千行)', '模块数量', '配置文件', '文档数量']
        scale_values = [5.6, 28, 6, 30]
        
        bars4 = ax4.bar(scale_metrics, scale_values, 
                       color='#3F51B5', alpha=0.8)
        ax4.set_title('项目规模统计', fontweight='bold', fontsize=18)
        ax4.set_ylabel('数量', fontsize=16)
        ax4.tick_params(axis='both', which='major', labelsize=14)
        
        for bar, value in zip(bars4, scale_values):
            ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(scale_values)*0.02,
                    f'{value}', ha='center', va='bottom', fontweight='bold', fontsize=14)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'performance_charts.png', 
                   dpi=300, bbox_inches='tight')
        print(f"✅ 性能图表已保存: {self.output_dir / 'performance_charts.png'}")
        plt.close()
    
    def generate_all_diagrams(self):
        """生成所有架构图"""
        print("🎨 开始生成AutoFish架构图...")
        print("=" * 50)
        
        try:
            self.generate_system_architecture()
            self.generate_module_relationship()
            self.generate_data_flow_diagram()
            self.generate_tech_stack_diagram()
            self.generate_state_machine_diagram()
            self.generate_performance_chart()
            
            print("=" * 50)
            print(f"🎉 所有架构图生成完成！")
            print(f"📁 输出目录: {self.output_dir}")
            print("\n生成的图表:")
            print("  1. system_architecture.png - 系统整体架构图")
            print("  2. module_relationship.png - 模块关系图")
            print("  3. data_flow_diagram.png - 数据流向图")
            print("  4. tech_stack_diagram.png - 技术栈图")
            print("  5. state_machine_diagram.png - 状态机图")
            print("  6. performance_charts.png - 性能指标图表")
            
        except Exception as e:
            print(f"❌ 生成过程中出现错误: {str(e)}")
            print("请检查依赖库是否正确安装:")
            print("pip install matplotlib networkx numpy")


def main():
    """主函数"""
    print("AutoFish 架构图生成器")
    print("Author: AutoFish Team")
    print("Version: v1.0")
    print("-" * 40)
    
    # 创建生成器
    generator = AutoFishArchitectureGenerator()
    
    # 生成所有图表
    generator.generate_all_diagrams()


if __name__ == "__main__":
    main() 