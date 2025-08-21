#!/usr/bin/env python3
"""
测试修复后的字幕换行和背景框大小
"""

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from moviepy.editor import TextClip, ColorClip, CompositeVideoClip
from core.video_composer import VideoComposer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_subtitle_wrapping():
    """测试修复后的字幕换行功能"""
    logger.info("🔤 测试修复后的字幕换行功能")
    
    # 创建VideoComposer实例来使用其换行方法
    composer = VideoComposer()
    
    # 测试不同类型的文本
    test_texts = [
        "2025年8月21日arXiv,cs.CV,发文量约97篇",  # 中文
        "The Tsinghua University and Beijing Academy of Artificial Intelligence presented a unified representation",  # 长英文
        "该方法显著提升了模型性能",  # 短中文
        "achieving state-of-the-art results on multiple benchmarks with impressive performance improvements",  # 很长英文
        "中英文混合 with English mixed content testing the smart wrapping functionality"  # 中英文混合
    ]
    
    output_dir = Path("/tmp/test_subtitle_wrapping")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for i, text in enumerate(test_texts):
        try:
            logger.info(f"\n📝 测试文本 {i+1}: '{text}'")
            
            # 使用修复后的换行函数
            formatted_text = composer._devideSentence(text)
            logger.info(f"换行后: '{formatted_text}'")
            
            # 判断文本类型
            is_english = composer._is_mainly_english(text)
            logger.info(f"文本类型: {'主要英文' if is_english else '主要中文'}")
            
            # 创建字幕
            text_clip = TextClip(
                formatted_text,
                fontsize=50,
                color='black',
                font="STHeiti",
                align='center'
            ).set_duration(3)
            
            text_width, text_height = text_clip.size
            logger.info(f"文本尺寸: {text_width}x{text_height}")
            
            # 使用新的背景框逻辑
            if is_english:
                bg_width = int(text_width * 1.3)
                bg_height = int(text_height * 1.2)
            else:
                bg_width = int(text_width * 1.4)
                bg_height = int(text_height * 1.2)
            
            bg_width = max(bg_width, 200)
            logger.info(f"背景框尺寸: {bg_width}x{bg_height}")
            
            # 创建背景
            bgcolor_clip = ColorClip(
                size=(bg_width, bg_height),
                color=(250, 250, 210, 200)
            ).set_duration(3)
            
            # 创建视频背景
            video_bg = ColorClip(
                size=(1280, 720),
                color=(0, 0, 0)
            ).set_duration(3)
            
            # 合成字幕
            subtitle_comp = CompositeVideoClip([bgcolor_clip, text_clip.set_position('center')])
            
            # 将字幕放在视频底部
            final_comp = CompositeVideoClip([
                video_bg,
                subtitle_comp.set_position(('center', 600))  # 距离底部120像素
            ])
            
            # 输出测试视频
            output_path = output_dir / f"subtitle_test_{i+1}.mp4"
            final_comp.write_videofile(
                str(output_path),
                fps=1,
                codec='libx264',
                temp_audiofile=None,
                remove_temp=True,
                verbose=False,
                logger=None
            )
            
            logger.info(f"✅ 测试视频已生成: {output_path}")
            
            # 清理资源
            text_clip.close()
            bgcolor_clip.close()
            video_bg.close()
            subtitle_comp.close()
            final_comp.close()
            
        except Exception as e:
            logger.error(f"❌ 测试文本 {i+1} 失败: {str(e)}")
    
    logger.info(f"\n🎯 所有测试完成，输出目录: {output_dir}")

if __name__ == "__main__":
    test_subtitle_wrapping()
