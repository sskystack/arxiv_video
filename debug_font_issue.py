#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深度调试MoviePy TextClip中文字体问题
"""

import os
import platform
import logging
from moviepy.editor import TextClip
from PIL import Image, ImageDraw, ImageFont

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_pil_font_directly():
    """直接测试PIL是否支持中文字体"""
    print("=== 测试PIL字体支持 ===")
    
    # 创建图片
    img = Image.new('RGB', (400, 100), color='white')
    draw = ImageDraw.Draw(img)
    
    # 测试不同字体
    fonts_to_test = [
        "SimHei",
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/Arial Unicode.ttf",
        None  # 默认字体
    ]
    
    y_offset = 0
    for font_name in fonts_to_test:
        try:
            if font_name and os.path.exists(font_name):
                font = ImageFont.truetype(font_name, 20)
            elif font_name:
                font = ImageFont.truetype(font_name, 20)
            else:
                font = ImageFont.load_default()
            
            text = f"中文测试 {font_name or 'default'}"
            draw.text((10, y_offset), text, font=font, fill='black')
            print(f"✅ {font_name or 'default'}: PIL支持")
            
        except Exception as e:
            print(f"❌ {font_name or 'default'}: {e}")
            
        y_offset += 20
    
    img.save("pil_font_test.png")
    print("PIL测试结果已保存到: pil_font_test.png")

def find_system_fonts():
    """查找系统中的中文字体"""
    print("\n=== 查找系统字体 ===")
    
    if platform.system() == "Darwin":  # macOS
        font_dirs = [
            "/System/Library/Fonts/",
            "/Library/Fonts/",
            os.path.expanduser("~/Library/Fonts/")
        ]
    elif platform.system() == "Windows":
        font_dirs = ["C:/Windows/Fonts/"]
    else:  # Linux
        font_dirs = ["/usr/share/fonts/", "/usr/local/share/fonts/"]
    
    chinese_fonts = []
    for font_dir in font_dirs:
        if os.path.exists(font_dir):
            for file in os.listdir(font_dir):
                if any(keyword in file.lower() for keyword in ['chinese', 'cjk', 'pingfang', 'hiragino', 'songti', 'simhei', 'arial']):
                    full_path = os.path.join(font_dir, file)
                    chinese_fonts.append(full_path)
                    print(f"发现字体: {full_path}")
    
    return chinese_fonts

def test_moviepy_with_different_fonts():
    """测试MoviePy使用不同字体"""
    print("\n=== 测试MoviePy不同字体 ===")
    
    fonts_to_test = find_system_fonts()[:5]  # 测试前5个
    fonts_to_test.extend([
        "SimHei",
        "PingFang SC", 
        "Arial Unicode MS",
        "Songti SC",
    ])
    
    test_text = "中文测试文本"
    
    for i, font_path in enumerate(fonts_to_test):
        try:
            print(f"测试字体: {font_path}")
            
            clip = TextClip(
                test_text,
                fontsize=50,
                color='black',
                font=font_path
            )
            
            if clip.w > 0 and clip.h > 0:
                clip.save_frame(f"moviepy_test_{i}.png", t=0.5)
                print(f"  ✅ 成功: 尺寸 {clip.w}x{clip.h}")
            else:
                print(f"  ❌ 失败: 尺寸为0")
            
            clip.close()
            
        except Exception as e:
            print(f"  ❌ 错误: {e}")

def check_imagemagick():
    """检查ImageMagick配置"""
    print("\n=== 检查ImageMagick ===")
    import subprocess
    
    try:
        # 检查convert命令
        result = subprocess.run(["convert", "-version"], capture_output=True, text=True)
        print("Convert版本信息:")
        print(result.stdout[:200])
        
        # 检查字体列表
        result = subprocess.run(["convert", "-list", "font"], capture_output=True, text=True)
        fonts = result.stdout
        chinese_fonts = []
        for line in fonts.split('\n'):
            if any(keyword in line.lower() for keyword in ['chinese', 'cjk', 'ping', 'hiragino', 'simhei', 'arial']):
                chinese_fonts.append(line.strip())
        
        print(f"找到中文相关字体 {len(chinese_fonts)} 个:")
        for font in chinese_fonts[:10]:  # 只显示前10个
            print(f"  {font}")
            
    except Exception as e:
        print(f"ImageMagick检查失败: {e}")

if __name__ == "__main__":
    test_pil_font_directly()
    check_imagemagick()
    test_moviepy_with_different_fonts()