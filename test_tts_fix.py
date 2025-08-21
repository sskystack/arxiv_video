#!/usr/bin/env python3
"""
测试TTS语言检测和语音合成修复的脚本
"""

import sys
import os
import json
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.tts_service import TTSService
from core.Card import ReductCard

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_language_detection():
    """测试语言检测功能"""
    logger.info("🔍 测试语言检测功能")
    
    tts = TTSService()
    
    test_cases = [
        "中央大学提出了MoCHA-former方法",
        "The Chung-Ang University proposed the Moiré Conditioned Hybrid Adaptive Transformer",
        "该方法通过解耦和时空自适应机制",
        "which integrates Decoupled Moiré Adaptive Demoiréing",
        "欢迎关注减论",
        "用科技链接个体"
    ]
    
    for text in test_cases:
        language = tts._detect_language(text)
        logger.info(f"文本: '{text}' -> 检测结果: {language}")

def test_mixed_language_tts():
    """测试混合语言的TTS处理"""
    logger.info("🎵 测试混合语言TTS处理")
    
    # 读取测试卡片
    test_card_path = "/Users/zhouzhongtian/vscode/arxiv_video/cards/2508.14423v1.json"
    if not os.path.exists(test_card_path):
        logger.error(f"测试卡片文件不存在: {test_card_path}")
        return
    
    with open(test_card_path, 'r', encoding='utf-8') as f:
        card_data = json.load(f)
    
    # 创建ReductCard对象
    card = ReductCard(
        arXivID=card_data['arXivID'],
        info_CN=card_data['info_CN'],
        info_EN=card_data['info_EN']
    )
    
    logger.info(f"卡片ID: {card.arXivID}")
    logger.info(f"中文解说句子数: {len(card.info_CN)}")
    
    # 分析每个句子的语言
    tts = TTSService()
    for i, sentence in enumerate(card.info_CN):
        language = tts._detect_language(sentence)
        logger.info(f"句子 {i+1}: {language} - '{sentence[:50]}...'")
    
    # 测试TTS生成（只生成前3个句子）
    test_output_dir = "/tmp/test_tts_fix"
    os.makedirs(test_output_dir, exist_ok=True)
    
    logger.info("🔊 开始测试TTS生成（前3个句子）")
    try:
        test_sentences = card.info_CN[:3]  # 只测试前3个句子
        audio_paths = tts.generate_speech_segments(test_sentences, test_output_dir)
        logger.info(f"✅ 成功生成 {len(audio_paths)} 个音频文件")
        for path in audio_paths:
            logger.info(f"音频文件: {path}")
    except Exception as e:
        logger.error(f"❌ TTS生成失败: {str(e)}")

def main():
    """主函数"""
    logger.info("🚀 开始TTS修复测试")
    
    try:
        # 测试语言检测
        test_language_detection()
        
        print("-" * 50)
        
        # 测试混合语言TTS
        test_mixed_language_tts()
        
        logger.info("✅ 测试完成")
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {str(e)}")
        raise

if __name__ == "__main__":
    main()
