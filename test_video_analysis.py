#!/usr/bin/env python3
"""
测试生成的视频字幕是否正常
"""

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from moviepy.editor import VideoFileClip
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def analyze_video_composition():
    """分析生成的视频构成"""
    logger.info("🎬 分析生成的视频文件")
    
    video_path = "/Users/zhouzhongtian/Movies/arxiv_video/20250821/2508.14891/2508.14891v1_res.mp4"
    card_path = "/Users/zhouzhongtian/Movies/arxiv_video/20250821/2508.14891/2508.14891v1.json"
    
    if not os.path.exists(video_path):
        logger.error(f"❌ 视频文件不存在: {video_path}")
        return
    
    if not os.path.exists(card_path):
        logger.error(f"❌ 卡片文件不存在: {card_path}")
        return
    
    # 读取卡片信息
    with open(card_path, 'r', encoding='utf-8') as f:
        card_data = json.load(f)
    
    logger.info(f"📋 卡片信息:")
    logger.info(f"   ArXiv ID: {card_data.get('arXivID', 'Unknown')}")
    logger.info(f"   中文句子数: {len(card_data.get('info_CN', []))}")
    
    # 分析每句话的内容和语言
    for i, sentence in enumerate(card_data.get('info_CN', [])):
        # 简单的语言检测
        if any('\u4e00' <= char <= '\u9fff' for char in sentence):
            lang = "中文"
        else:
            lang = "英文"
        logger.info(f"   句子 {i+1}: [{lang}] {sentence[:50]}...")
    
    # 分析视频文件
    try:
        video = VideoFileClip(video_path)
        
        logger.info(f"🎥 视频信息:")
        logger.info(f"   时长: {video.duration:.2f} 秒")
        logger.info(f"   尺寸: {video.size}")
        logger.info(f"   FPS: {video.fps}")
        
        # 检查视频是否是合成视频
        logger.info(f"   是否合成视频: {hasattr(video, 'clips')}")
        if hasattr(video, 'clips'):
            logger.info(f"   子片段数量: {len(video.clips)}")
            
            # 分析每个子片段
            for i, clip in enumerate(video.clips):
                clip_type = type(clip).__name__
                start_time = getattr(clip, 'start', 'N/A')
                end_time = getattr(clip, 'end', 'N/A')
                logger.info(f"     片段 {i+1}: {clip_type} (时间: {start_time}-{end_time})")
        
        video.close()
        
    except Exception as e:
        logger.error(f"❌ 分析视频文件失败: {str(e)}")

def create_test_subtitle_video():
    """创建一个简单的测试字幕视频来验证字幕功能"""
    logger.info("🧪 创建测试字幕视频")
    
    from moviepy.editor import TextClip, ColorClip, CompositeVideoClip
    
    try:
        # 创建简单的测试文本
        test_text = "测试中文字幕显示\nTest English subtitle display"
        
        # 使用当前的字体配置
        text_clip = TextClip(
            test_text,
            fontsize=50,
            color='black',
            font="SimHei",
            align='center'
        ).set_duration(5)
        
        # 创建背景
        bgcolor_clip = ColorClip(
            size=text_clip.size,
            color=(250, 250, 210, 200),
            ismask=False
        ).set_duration(5)
        
        # 创建一个简单的视频背景
        video_bg = ColorClip(
            size=(1280, 720),
            color=(0, 0, 0),
            ismask=False
        ).set_duration(5)
        
        # 合并字幕和背景
        subtitle_composite = CompositeVideoClip([bgcolor_clip, text_clip])
        
        # 将字幕定位到视频底部
        final_video = CompositeVideoClip([
            video_bg,
            subtitle_composite.set_position(('center', 'bottom')).set_margin(bottom=50)
        ])
        
        # 输出测试视频
        output_path = "/tmp/test_subtitle_display.mp4"
        final_video.write_videofile(
            output_path,
            fps=24,
            codec='libx264',
            temp_audiofile=None,
            remove_temp=True
        )
        
        logger.info(f"✅ 测试字幕视频已生成: {output_path}")
        
        # 清理资源
        text_clip.close()
        bgcolor_clip.close()
        video_bg.close()
        subtitle_composite.close()
        final_video.close()
        
    except Exception as e:
        logger.error(f"❌ 创建测试字幕视频失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 分析生成的视频
    analyze_video_composition()
    
    print("\n" + "="*60)
    
    # 创建测试字幕视频
    create_test_subtitle_video()
