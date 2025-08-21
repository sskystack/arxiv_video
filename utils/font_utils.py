#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动检测并选择最佳中文字体的工具函数
"""

import os
import platform
from moviepy.editor import TextClip

def get_best_chinese_font():
    """自动检测并返回最佳的中文字体"""
    
    def test_font_chinese_support(font_name):
        """测试字体是否支持中文"""
        try:
            clip = TextClip("测试中文", font=font_name, fontsize=20, color='white')
            supported = clip.w > 0 and clip.h > 0
            clip.close()
            return supported
        except:
            return False
    
    # 根据系统推荐字体
    system = platform.system()
    
    if system == "Darwin":  # macOS
        font_candidates = [
            "Arial Unicode MS",  # 最佳选择，支持中英文
            "Hiragino Sans GB",
            "PingFang SC",
            "Songti SC", 
            "STHeiti",
            "Arial"
        ]
    elif system == "Windows":
        font_candidates = [
            "Microsoft YaHei",
            "SimHei", 
            "SimSun",
            "Arial Unicode MS",
            "Arial"
        ]
    else:  # Linux
        font_candidates = [
            "Noto Sans CJK SC",
            "WenQuanYi Micro Hei",
            "DejaVu Sans",
            "Arial"
        ]
    
    # 测试每个字体
    for font in font_candidates:
        if test_font_chinese_support(font):
            print(f"✅ 选择字体: {font}")
            return font
    
    # 如果都不行，返回Arial作为后备
    print("⚠️ 未找到合适的中文字体，使用Arial")
    return "Arial"

if __name__ == "__main__":
    best_font = get_best_chinese_font()
    print(f"推荐字体: {best_font}")