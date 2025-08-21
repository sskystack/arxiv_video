#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字体支持测试脚本
"""

import os
import platform
from moviepy.editor import TextClip

def test_font_with_chinese(font_name: str) -> dict:
    """测试字体对中文的支持"""
    result = {
        'font': font_name,
        'chinese_supported': False,
        'english_supported': False,
        'error': None
    }
    
    try:
        # 测试中文
        chinese_clip = TextClip("测试中文字幕", font=font_name, fontsize=50, color='white')
        result['chinese_supported'] = chinese_clip.w > 0 and chinese_clip.h > 0
        chinese_clip.close()
        
        # 测试英文
        english_clip = TextClip("Test English Subtitle", font=font_name, fontsize=50, color='white')
        result['english_supported'] = english_clip.w > 0 and english_clip.h > 0
        english_clip.close()
        
    except Exception as e:
        result['error'] = str(e)
    
    return result

def get_system_fonts():
    """获取系统推荐的字体列表"""
    system = platform.system()
    
    font_lists = {
        'Darwin': [  # macOS
            'Arial Unicode MS',
            'PingFang SC',  
            'Songti SC',
            'Hiragino Sans GB',
            'STHeiti',
            'Arial',
            'Helvetica'
        ],
        'Windows': [
            'Microsoft YaHei',
            'SimHei',  # 黑体
            'SimSun',
            'Arial Unicode MS',
            'Arial'
        ],
        'Linux': [
            'Noto Sans CJK SC',
            'WenQuanYi Micro Hei',
            'DejaVu Sans',
            'Arial'
        ]
    }
    
    return font_lists.get(system, font_lists['Linux'])

def main():
    print(f"🖥️  当前系统: {platform.system()}")
    print(f"🔍 测试字体对中英文的支持情况...")
    print("=" * 60)
    
    # 获取推荐字体列表
    fonts_to_test = get_system_fonts()
    
    # 额外测试当前使用的字体
    fonts_to_test.insert(0, 'SimHei')  # 当前项目中使用的字体
    
    working_fonts = []
    
    for font in fonts_to_test:
        result = test_font_with_chinese(font)
        
        status = "❌"
        if result['chinese_supported'] and result['english_supported']:
            status = "✅"
            working_fonts.append(font)
        elif result['chinese_supported'] or result['english_supported']:
            status = "⚠️ "
        
        print(f"{status} {font:<20} | 中文: {'✓' if result['chinese_supported'] else '✗'} | 英文: {'✓' if result['english_supported'] else '✗'}")
        
        if result['error']:
            print(f"    错误: {result['error']}")
    
    print("=" * 60)
    print(f"🎯 推荐字体 (支持中英文): {working_fonts}")
    
    if working_fonts:
        print(f"🔧 建议将video_composer.py中的font参数改为: '{working_fonts[0]}'")
    else:
        print("⚠️  警告: 未找到支持中英文的字体!")

if __name__ == "__main__":
    main()