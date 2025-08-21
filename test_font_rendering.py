#!/usr/bin/env python3
"""
快速测试字体渲染效果
"""

import os
import sys
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from moviepy.editor import TextClip, ColorClip, CompositeVideoClip

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_font_rendering():
    """测试实际的字体渲染效果"""
    logger.info("🔤 测试字体渲染效果")
    
    test_text = "测试中文字幕\nTest English"
    
    fonts_to_test = [
        "STHeiti",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
        "/System/Library/Fonts/PingFang.ttc"
    ]
    
    for i, font in enumerate(fonts_to_test):
        try:
            logger.info(f"🧪 测试字体 {i+1}: {font}")
            
            # 创建文本片段
            text_clip = TextClip(
                test_text,
                fontsize=50,
                color='black',
                font=font,
                align='center'
            ).set_duration(2)
            
            # 创建背景
            bgcolor_clip = ColorClip(
                size=text_clip.size,
                color=(250, 250, 210, 200)
            ).set_duration(2)
            
            # 创建黑色背景
            bg_clip = ColorClip(
                size=(800, 200),
                color=(0, 0, 0)
            ).set_duration(2)
            
            # 合成
            subtitle_comp = CompositeVideoClip([bgcolor_clip, text_clip])
            final_comp = CompositeVideoClip([
                bg_clip,
                subtitle_comp.set_position('center')
            ])
            
            # 输出测试视频
            output_path = f"/tmp/font_test_{i+1}.mp4"
            final_comp.write_videofile(
                output_path,
                fps=1,  # 低帧率快速生成
                codec='libx264',
                temp_audiofile=None,
                remove_temp=True,
                verbose=False,
                logger=None
            )
            
            logger.info(f"  ✅ 字体 {font} 测试成功: {output_path}")
            logger.info(f"     文本大小: {text_clip.size}")
            
            # 清理资源
            text_clip.close()
            bgcolor_clip.close()
            bg_clip.close()
            subtitle_comp.close()
            final_comp.close()
            
        except Exception as e:
            logger.error(f"  ❌ 字体 {font} 测试失败: {str(e)}")

if __name__ == "__main__":
    test_font_rendering()
