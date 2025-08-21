#!/usr/bin/env python3
"""
专门测试长英文句子的字幕显示
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

def test_long_english_subtitle():
    """测试长英文句子的字幕显示"""
    logger.info("🔤 测试长英文句子字幕显示")
    
    # 创建VideoComposer实例
    composer = VideoComposer()
    
    # 测试原视频中出现的长句子
    long_sentence = "and Beijing Academy of Artificial Intelligence presented a unified representation that jointly"
    
    logger.info(f"📝 测试句子: '{long_sentence}'")
    logger.info(f"句子长度: {len(long_sentence)} 字符")
    
    # 使用修复后的换行函数
    formatted_text = composer._devideSentence(long_sentence)
    logger.info(f"换行后: '{formatted_text}'")
    
    # 判断文本类型
    is_english = composer._is_mainly_english(long_sentence)
    logger.info(f"文本类型: {'主要英文' if is_english else '主要中文'}")
    
    try:
        # 创建字幕文本
        text_clip = TextClip(
            formatted_text,
            fontsize=50,
            color='black',
            font="STHeiti",
            align='center'
        ).set_duration(5)
        
        text_width, text_height = text_clip.size
        logger.info(f"文本尺寸: {text_width}x{text_height}")
        
        # 使用新的背景框逻辑
        if is_english:
            base_multiplier = 1.2
            if len(formatted_text) > 60:
                base_multiplier = 1.1
            bg_width = int(text_width * base_multiplier)
            bg_height = int(text_height * 1.3)
        else:
            bg_width = int(text_width * 1.3)
            bg_height = int(text_height * 1.2)
        
        # 应用最小最大限制
        bg_width = max(bg_width, 300)
        bg_width = min(bg_width, 1200)
        bg_height = max(bg_height, 60)
        
        logger.info(f"背景框尺寸: {bg_width}x{bg_height}")
        
        # 创建背景
        bgcolor_clip = ColorClip(
            size=(bg_width, bg_height),
            color=(250, 250, 210, 200)
        ).set_duration(5)
        
        # 创建1280x720的视频背景（模拟实际视频尺寸）
        video_bg = ColorClip(
            size=(1280, 720),
            color=(50, 50, 50)  # 深灰色背景，更接近实际视频
        ).set_duration(5)
        
        # 合成字幕 - 文本在背景框中居中
        subtitle_comp = CompositeVideoClip([
            bgcolor_clip,
            text_clip.set_position('center')
        ])
        
        # 将字幕放在视频底部（距离底部100像素）
        final_comp = CompositeVideoClip([
            video_bg,
            subtitle_comp.set_position(('center', 580))  # 距离底部140像素
        ])
        
        # 输出测试视频
        output_dir = Path("/tmp/test_long_subtitle")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "long_english_subtitle_test.mp4"
        
        final_comp.write_videofile(
            str(output_path),
            fps=24,
            codec='libx264',
            temp_audiofile=None,
            remove_temp=True,
            verbose=False,
            logger=None
        )
        
        logger.info(f"✅ 长句子字幕测试视频已生成: {output_path}")
        
        # 检查是否会被截断
        if bg_width >= 1200:
            logger.warning("⚠️ 背景框已达到最大宽度限制，可能需要进一步优化")
        
        if subtitle_comp.w + 40 > 1280:  # 40像素边距
            logger.warning("⚠️ 字幕可能超出视频边界")
        else:
            logger.info("✅ 字幕在视频边界内")
        
        # 清理资源
        text_clip.close()
        bgcolor_clip.close()
        video_bg.close()
        subtitle_comp.close()
        final_comp.close()
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_long_english_subtitle()
