#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字幕测试脚本 - 用于诊断中文字幕显示问题
"""

import os
import sys
import logging
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, ColorClip
import platform

# 设置日志
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
        logger.error(f"字体 {font_name} 不可用: {str(e)}")
        return False

def get_suitable_font():
    """获取合适的中文字体"""
    font_candidates = {
        'Darwin': [  # macOS
            'Arial Unicode MS',
            'PingFang SC',
            'Songti SC',
            'Heiti SC',
            'Arial',
        ],
        'Windows': [
            'Arial Unicode MS',
            'Microsoft YaHei',
            'SimSun',
            'Arial',
        ],
        'Linux': [
            'Arial Unicode MS',
            'Noto Sans CJK SC',
            'WenQuanYi Micro Hei',
            'Arial',
        ]
    }
    
    current_platform = platform.system()
    candidates = font_candidates.get(current_platform, font_candidates['Linux'])
    
    for font in candidates:
        if test_font_availability(font):
            logger.info(f"选择字体: {font}")
            return font
    
    logger.warning("未找到合适的中文字体，使用默认字体")
    return 'Arial'

def create_test_subtitle_video():
    """创建测试字幕视频"""
    try:
        # 测试文本
        test_texts = [
            "这是第一段中文字幕测试",
            "曼彻斯特大学、大湾大学和中山大学",
            "基于多教师模型知识蒸馏的方法",
            "Distilled-3DGS算法研究"
        ]
        
        # 创建简单的背景视频（5秒）
        from moviepy.editor import ColorClip
        background = ColorClip(size=(640, 480), color=(100, 100, 100), duration=8)
        
        # 获取字体
        font_name = get_suitable_font()
        logger.info(f"使用字体: {font_name}")
        
        subtitle_clips = []
        
        for i, text in enumerate(test_texts):
            start_time = i * 2.0
            end_time = start_time + 2.0
            
            logger.info(f"创建字幕: {text} (时间: {start_time}-{end_time})")
            
            # 测试多种字幕样式
            
            # 样式1: 白字黑边（底部）
            text_clip_1 = TextClip(
                text,
                fontsize=30,
                color='white',
                font=font_name,
                align='center',
                stroke_color='black',
                stroke_width=2
            )
            
            bg_clip_1 = ColorClip(
                size=(text_clip_1.w + 20, text_clip_1.h + 10),
                color=(0, 0, 0),
                ismask=False
            ).set_opacity(0.8)
            
            subtitle_1 = CompositeVideoClip([bg_clip_1, text_clip_1])
            subtitle_1 = subtitle_1.set_position(('center', 'bottom')).set_start(start_time).set_end(end_time)
            subtitle_clips.append(subtitle_1)
            
            # 样式2: 黑字白边（顶部，用于对比）
            text_clip_2 = TextClip(
                f"[对比] {text}",
                fontsize=25,
                color='black',
                font=font_name,
                align='center',
                stroke_color='white',
                stroke_width=2
            )
            
            bg_clip_2 = ColorClip(
                size=(text_clip_2.w + 20, text_clip_2.h + 10),
                color=(255, 255, 255),
                ismask=False
            ).set_opacity(0.8)
            
            subtitle_2 = CompositeVideoClip([bg_clip_2, text_clip_2])
            subtitle_2 = subtitle_2.set_position(('center', 0.1)).set_start(start_time).set_end(end_time)
            subtitle_clips.append(subtitle_2)
        
        # 合成最终视频
        final_video = CompositeVideoClip([background] + subtitle_clips)
        
        # 输出路径
        output_path = "/tmp/subtitle_test.mp4"
        
        logger.info(f"开始渲染测试视频到: {output_path}")
        final_video.write_videofile(
            output_path,
            fps=24,
            audio=False,
            verbose=False,
            logger=None
        )
        
        logger.info(f"测试视频创建完成: {output_path}")
        logger.info("请播放该视频检查字幕显示效果")
        
        # 清理资源
        final_video.close()
        background.close()
        for clip in subtitle_clips:
            clip.close()
        
        return output_path
        
    except Exception as e:
        logger.error(f"创建测试视频失败: {str(e)}")
        return None

if __name__ == "__main__":
    print("=== 字幕测试脚本 ===")
    print("测试系统字体支持情况...")
    
    # 测试字体
    font = get_suitable_font()
    print(f"选定字体: {font}")
    
    # 创建测试视频
    print("\n创建测试字幕视频...")
    test_video_path = create_test_subtitle_video()
    
    if test_video_path:
        print(f"\n✅ 测试视频已创建: {test_video_path}")
        print("请播放此视频检查中文字幕是否正常显示")
        print("视频包含多种字幕样式用于对比测试")
    else:
        print("\n❌ 测试视频创建失败")
