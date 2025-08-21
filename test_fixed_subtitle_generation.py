#!/usr/bin/env python3
"""
使用修复后的字体配置重新测试卡片视频生成
"""

import os
import sys
import logging
import json
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.Card import ReductCard
from core.video_composer import VideoComposer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_fixed_subtitle_generation():
    """使用修复后的字体配置测试字幕生成"""
    logger.info("🚀 测试修复后的字幕生成")
    
    # 创建测试目录
    test_dir = Path("/tmp/test_fixed_subtitle")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建一个包含中英文混合的测试卡片文件
    card_data = {
        "arXivID": "test.fixed.v1",
        "info_CN": [
            "2025年8月21日arXiv,cs.CV,发文量约97篇",
            "减论Agent通过算法为您推荐",
            "The Tsinghua University proposed a method",
            "该方法显著提升了模型性能",
            "achieving state-of-the-art results",
            "欢迎关注减论，用科技链接个体"
        ],
        "info_EN": [
            "2025 arXiv cs.CV papers",
            "Tsinghua University method",
            "State-of-the-art results"
        ],
        "created_at": "2025-08-21T18:41:00.000000",
        "version": "1.0"
    }
    
    # 保存卡片文件
    card_path = test_dir / "test.fixed.v1.json"
    with open(card_path, 'w', encoding='utf-8') as f:
        json.dump(card_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"📋 测试卡片已保存: {card_path}")
    
    # 创建demo视频文件（复制现有的演示视频）
    demo_video_source = "/Users/zhouzhongtian/Movies/arxiv_video/20250821/2508.14891/video_0.mp4"
    demo_video_dest = test_dir / "demo_video.mp4"
    
    if os.path.exists(demo_video_source):
        import shutil
        shutil.copy2(demo_video_source, demo_video_dest)
        logger.info(f"📹 演示视频已复制: {demo_video_dest}")
    else:
        logger.warning("⚠️ 未找到演示视频源文件，将跳过视频合成")
        return
    
    # 创建VideoComposer并生成视频
    try:
        composer = VideoComposer()
        
        # 设置工作目录
        composer._current_paper_dir = str(test_dir)
        
        # 加载卡片
        card = composer._load_card_from_json(str(card_path))
        
        # 生成音频
        logger.info("🎵 开始生成音频...")
        audio_files = composer.tts_service.generate_speech_segments(card.info_CN, str(test_dir))
        
        if audio_files:
            logger.info(f"✅ 成功生成 {len(audio_files)} 个音频片段")
            
            # 合成视频（只使用一个演示视频文件）
            logger.info("🎬 开始合成视频...")
            output_path = composer.compose_paper_video(str(test_dir), "test.fixed.v1")
            
            if output_path and os.path.exists(output_path):
                file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
                logger.info(f"✅ 修复后的视频生成成功!")
                logger.info(f"📁 输出路径: {output_path}")
                logger.info(f"📁 文件大小: {file_size:.2f} MB")
            else:
                logger.error("❌ 视频生成失败")
        else:
            logger.error("❌ 音频生成失败")
            
    except Exception as e:
        logger.error(f"❌ 测试过程出错: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fixed_subtitle_generation()
