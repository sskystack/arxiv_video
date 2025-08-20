#!/usr/bin/env python3
"""
跨平台字体检测脚本
用于验证各种字体在不同平台上的可用性
"""

import platform
from moviepy.editor import TextClip

def test_font(font_name):
    """测试字体是否可用"""
    try:
        test_clip = TextClip("测试 Test", font=font_name, fontsize=20, color='white')
        width = test_clip.w
        test_clip.close()
        return width > 0
    except Exception as e:
        return False

def main():
    print(f"当前平台: {platform.system()}")
    print("=" * 50)
    
    # 常见字体列表
    fonts_to_test = [
        'Arial Unicode MS',
        'Arial',
        'PingFang SC',
        'Heiti SC', 
        'Songti SC',
        'STSong',
        'Microsoft YaHei',
        'SimSun',
        'SimHei',
        'Noto Sans CJK SC',
        'WenQuanYi Micro Hei',
        'WenQuanYi Zen Hei',
        'DejaVu Sans',
        'Liberation Sans'
    ]
    
    available_fonts = []
    
    for font in fonts_to_test:
        print(f"测试字体: {font}...", end=" ")
        if test_font(font):
            print("✅ 可用")
            available_fonts.append(font)
        else:
            print("❌ 不可用")
    
    print("\n" + "=" * 50)
    print("可用字体列表:")
    for font in available_fonts:
        print(f"  - {font}")
    
    print(f"\n推荐字体: {available_fonts[0] if available_fonts else 'None'}")

if __name__ == "__main__":
    main()
