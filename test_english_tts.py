#!/usr/bin/env python3
"""
测试英文句子的TTS处理
"""

import sys
import os
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.tts_service import TTSService

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_english_tts():
    """测试英文句子的TTS生成"""
    logger.info("🎵 测试英文句子TTS处理")
    
    tts = TTSService()
    
    # 从2508.14423v1卡片中提取的英文句子
    english_sentences = [
        "The Chung-Ang University proposed the Moiré Conditioned Hybrid Adaptive Transformer",
        "which integrates Decoupled Moiré Adaptive Demoiréing and Spatio-Temporal Adaptive Demoiréing",
        "large-scale structures"
    ]
    
    test_output_dir = "/tmp/test_english_tts"
    os.makedirs(test_output_dir, exist_ok=True)
    
    logger.info("🔊 开始测试英文TTS生成")
    try:
        audio_paths = tts.generate_speech_segments(english_sentences, test_output_dir)
        logger.info(f"✅ 成功生成 {len(audio_paths)} 个英文音频文件")
        for i, path in enumerate(audio_paths):
            logger.info(f"英文音频文件 {i+1}: {path}")
    except Exception as e:
        logger.error(f"❌ 英文TTS生成失败: {str(e)}")
        raise

def main():
    """主函数"""
    logger.info("🚀 开始英文TTS测试")
    
    try:
        test_english_tts()
        logger.info("✅ 英文TTS测试完成")
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {str(e)}")
        raise

if __name__ == "__main__":
    main()
