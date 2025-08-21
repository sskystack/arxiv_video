#!/usr/bin/env python3
"""
测试混合语言音频生成功能
"""

import os
import sys
import logging
import json
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.Card import ReductCard
from core.tts_service import TTSService

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_mixed_language_audio():
    """测试混合语言音频生成"""
    logger.info("🚀 开始混合语言音频生成测试")
    
    # 创建测试卡片（模拟包含中英文混合的info_CN）
    card = ReductCard(
        arXivID="test.mixed.v1",
        info_CN=[
            "2025年8月21日arXiv,cs.CV,发文量约97篇",  # 中文
            "减论Agent通过算法为您推荐",  # 中文
            "The Chung-Ang University proposed MoCHA-former method",  # 英文
            "which integrates Decoupled MoE and Hypergraph Attention",  # 英文
            "该方法显著提升了模型性能",  # 中文
            "achieving state-of-the-art results on multiple benchmarks",  # 英文
            "欢迎关注减论，用科技链接个体"  # 中文
        ],
        info_EN=[
            "2025 arXiv cs.CV paper recommendation",
            "Chung-Ang University MoCHA-former",
            "Decoupled MoE and Hypergraph Attention"
        ]
    )
    
    # 创建输出目录
    output_dir = Path("/tmp/test_mixed_language_audio")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建TTSService
    tts_service = TTSService()
    
    try:
        # 生成音频
        logger.info("🎵 开始生成混合语言音频")
        audio_files = tts_service.generate_speech_segments(card.info_CN, str(output_dir))
        
        if audio_files and len(audio_files) > 0:
            logger.info(f"✅ 成功生成 {len(audio_files)} 个混合语言音频片段")
            
            # 显示每个文件的信息
            total_size = 0
            for i, audio_file in enumerate(audio_files):
                if os.path.exists(audio_file):
                    size = os.path.getsize(audio_file) / 1024  # KB
                    total_size += size
                    logger.info(f"   {i+1}. {os.path.basename(audio_file)} ({size:.1f} KB)")
                else:
                    logger.warning(f"   {i+1}. {os.path.basename(audio_file)} - 文件不存在")
            
            logger.info(f"📁 总音频大小: {total_size/1024:.2f} MB")
        else:
            logger.error("❌ 音频生成失败")
            
    except Exception as e:
        logger.error(f"❌ 音频生成过程出错: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_mixed_language_audio()
