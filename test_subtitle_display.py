#!/usr/bin/env python3
"""
快速测试字幕显示功能
"""

import os
import sys
import logging
import json
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.video_composer import VideoComposer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_subtitle_display():
    """快速测试字幕显示功能"""
    logger.info("🎬 快速测试字幕显示功能")
    
    # 创建测试目录
    test_dir = Path("/tmp/test_subtitle_display")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建测试卡片
    card_data = {
        "arXivID": "test.subtitle.v1",
        "info_CN": [
            "这是一个测试中文字幕显示的句子",
            "This is a test English subtitle that should display properly at the bottom",
            "混合中英文测试 Mixed language test for subtitle display functionality"
        ],
        "info_EN": ["Test subtitle"],
        "created_at": "2025-08-21T19:10:00.000000",
        "version": "1.0"
    }
    
    # 保存卡片文件
    card_path = test_dir / "test.subtitle.v1.json"
    with open(card_path, 'w', encoding='utf-8') as f:
        json.dump(card_data, f, ensure_ascii=False, indent=2)
    
    # 复制演示视频
    demo_video_source = "/Users/zhouzhongtian/Movies/arxiv_video/20250821/2508.14891/video_0.mp4"
    demo_video_dest = test_dir / "demo_video.mp4"
    
    if os.path.exists(demo_video_source):
        import shutil
        shutil.copy2(demo_video_source, demo_video_dest)
        logger.info(f"📹 演示视频已复制")
    else:
        logger.error("❌ 未找到演示视频源文件")
        return
    
    try:
        # 使用VideoComposer生成视频
        composer = VideoComposer()
        composer._current_paper_dir = str(test_dir)
        
        # 生成完整视频
        output_path = composer.compose_paper_video(str(test_dir), "test.subtitle.v1")
        
        if output_path and os.path.exists(output_path):
            file_size = os.path.getsize(output_path) / (1024 * 1024)
            logger.info(f"✅ 字幕测试视频生成成功!")
            logger.info(f"📁 输出路径: {output_path}")
            logger.info(f"📁 文件大小: {file_size:.2f} MB")
            
            # 打开视频文件查看
            logger.info("🎥 可以打开视频查看字幕效果:")
            logger.info(f"   open '{output_path}'")
        else:
            logger.error("❌ 视频生成失败")
            
    except Exception as e:
        logger.error(f"❌ 测试过程出错: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_subtitle_display()
