#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对比PIL和MoviePy的字体渲染效果
"""

from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import TextClip
import os

def compare_font_rendering():
    """对比PIL和MoviePy的字体渲染"""
    
    test_text = "中文测试123English"
    
    # 可用的字体路径
    font_paths = [
        "/Library/Fonts/Arial Unicode.ttf",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
    ]
    
    for i, font_path in enumerate(font_paths):
        if os.path.exists(font_path):
            print(f"\n=== 测试字体: {font_path} ===")
            
            # 1. PIL测试
            try:
                img = Image.new('RGB', (600, 100), color='white')
                draw = ImageDraw.Draw(img)
                font = ImageFont.truetype(font_path, 50)
                draw.text((10, 25), test_text, font=font, fill='black')
                pil_output = f"pil_test_{i}.png"
                img.save(pil_output)
                print(f"✅ PIL成功: {pil_output}")
            except Exception as e:
                print(f"❌ PIL失败: {e}")
            
            # 2. MoviePy测试 - 使用完整路径
            try:
                clip = TextClip(
                    test_text,
                    fontsize=50,
                    color='black',
                    font=font_path  # 使用完整路径
                )
                if clip.w > 0 and clip.h > 0:
                    moviepy_output = f"moviepy_path_test_{i}.png"
                    clip.save_frame(moviepy_output, t=0.5)
                    print(f"✅ MoviePy(路径)成功: {moviepy_output}, 尺寸: {clip.w}x{clip.h}")
                else:
                    print("❌ MoviePy(路径): 尺寸为0")
                clip.close()
            except Exception as e:
                print(f"❌ MoviePy(路径)失败: {e}")
            
            # 3. MoviePy测试 - 使用字体名称
            font_name = "Arial Unicode MS" if "Arial" in font_path else "Hiragino Sans GB"
            try:
                clip = TextClip(
                    test_text,
                    fontsize=50,
                    color='black',
                    font=font_name  # 使用字体名称
                )
                if clip.w > 0 and clip.h > 0:
                    moviepy_name_output = f"moviepy_name_test_{i}.png"
                    clip.save_frame(moviepy_name_output, t=0.5)
                    print(f"✅ MoviePy(名称)成功: {moviepy_name_output}, 尺寸: {clip.w}x{clip.h}")
                else:
                    print("❌ MoviePy(名称): 尺寸为0")
                clip.close()
            except Exception as e:
                print(f"❌ MoviePy(名称)失败: {e}")

if __name__ == "__main__":
    compare_font_rendering()