#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频字幕调试脚本
"""

import os
import json
import logging
import platform
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, ColorClip

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_font_availability(font_name: str) -> bool:
    """测试字体是否可用"""
    try:
        test_clip = TextClip("测试中文", font=font_name, fontsize=20, color='white')
        width = test_clip.w
        test_clip.close()
        return width > 0
    except Exception as e:
        return False

def get_suitable_font():
    """获取合适的中文字体"""
    font_candidates = {
        'Darwin': ['Arial Unicode MS', 'PingFang SC', 'Songti SC', 'Arial'],
        'Windows': ['Arial Unicode MS', 'Microsoft YaHei', 'SimSun', 'Arial'],
        'Linux': ['Arial Unicode MS', 'Noto Sans CJK SC', 'WenQuanYi Micro Hei', 'Arial']
    }
    
    current_platform = platform.system()
    candidates = font_candidates.get(current_platform, font_candidates['Linux'])
    
    for font in candidates:
        if test_font_availability(font):
            logger.info(f"选择字体: {font}")
            return font
    
    return 'Arial'

def add_subtitle_to_video(video_path: str, card_data: dict, output_path: str):
    """为视频添加字幕"""
    try:
        # 加载视频
        video = VideoFileClip(video_path)
        logger.info(f"视频时长: {video.duration:.2f}秒")
        
        # 获取中文解说内容
        sentences = card_data.get('info_CN', [])
        logger.info(f"中文句子数量: {len(sentences)}")
        
        if not sentences:
            logger.warning("没有中文解说内容")
            return
        
        # 简单的时间分配：平均分配
        total_duration = video.duration
        sentence_duration = total_duration / len(sentences)
        logger.info(f"每个句子平均时长: {sentence_duration:.2f}秒")
        
        # 获取字体
        font_name = get_suitable_font()
        
        subtitle_clips = []
        current_time = 0.0
        
        for i, sentence in enumerate(sentences):
            start_time = current_time
            end_time = current_time + sentence_duration
            current_time = end_time
            
            logger.info(f"句子 {i+1}: '{sentence}' ({start_time:.2f}s - {end_time:.2f}s)")
            
            # 创建字幕
            text_clip = TextClip(
                sentence,
                fontsize=50,              # 大字体
                color='yellow',           # 黄色字体
                font=font_name,
                align='center',
                stroke_color='black',     # 黑色描边
                stroke_width=3
            )
            
            # 背景
            bg_clip = ColorClip(
                size=(text_clip.w + 40, text_clip.h + 20),
                color=(0, 0, 0),
                ismask=False
            ).set_opacity(0.8)
            
            # 合并
            subtitle_clip = CompositeVideoClip([bg_clip, text_clip])
            subtitle_clip = subtitle_clip.set_position(('center', 0.8)).set_start(start_time).set_end(end_time)
            subtitle_clips.append(subtitle_clip)
        
        # 合成最终视频
        logger.info("开始合成带字幕的视频...")
        final_video = CompositeVideoClip([video] + subtitle_clips)
        
        # 输出
        final_video.write_videofile(
            output_path,
            fps=24,
            codec="libx264",
            verbose=False,
            logger=None
        )
        
        logger.info(f"字幕视频生成完成: {output_path}")
        
        # 清理
        video.close()
        final_video.close()
        for clip in subtitle_clips:
            clip.close()
            
    except Exception as e:
        logger.error(f"添加字幕失败: {str(e)}")
        raise

if __name__ == "__main__":
    # 测试参数
    demo_video = "/tmp/test_final_subtitle/20250820/2508.14037/2508.14037v1_demo.mp4"
    card_file = "/tmp/test_final_subtitle/20250820/2508.14037/2508.14037v1.json"
    output_video = "/tmp/debug_subtitle_test.mp4"
    
    print("=== 字幕调试测试 ===")
    
    # 读取卡片数据
    with open(card_file, 'r', encoding='utf-8') as f:
        card_data = json.load(f)
    
    print(f"卡片数据: {card_data}")
    
    # 添加字幕
    add_subtitle_to_video(demo_video, card_data, output_video)
    
    print(f"✅ 测试完成，请查看: {output_video}")
