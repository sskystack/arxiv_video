#!/usr/bin/env python3
"""
测试问题卡片2508.14423v1的音频生成
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

def test_problem_card_14423():
    """测试问题卡片2508.14423v1的音频生成"""
    logger.info("🚀 开始测试问题卡片2508.14423v1")
    
    # 从JSON文件加载卡片
    card_path = "/Users/zhouzhongtian/vscode/arxiv_video/cards/2508.14423v1.json"
    
    with open(card_path, 'r', encoding='utf-8') as f:
        card_data = json.load(f)
    
    # 创建ReductCard对象
    card = ReductCard(
        arXivID=card_data["arXivID"],
        info_CN=card_data["info_CN"],
        info_EN=card_data["info_EN"]
    )
    
    logger.info(f"📋 卡片信息:")
    logger.info(f"   ID: {card.arXivID}")
    logger.info(f"   中文句子数: {len(card.info_CN)}")
    logger.info(f"   英文句子数: {len(card.info_EN)}")
    
    # 分析info_CN中的语言分布
    chinese_count = 0
    english_count = 0
    for i, sentence in enumerate(card.info_CN):
        # 简单的语言检测
        if any('\u4e00' <= char <= '\u9fff' for char in sentence):
            chinese_count += 1
            lang = "中文"
        else:
            english_count += 1
            lang = "英文"
        logger.info(f"   句子 {i+1}: [{lang}] {sentence[:50]}...")
    
    logger.info(f"📊 语言分布: {chinese_count}句中文, {english_count}句英文")
    
    # 创建输出目录
    output_dir = Path("/tmp/test_card_14423")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建TTSService
    tts_service = TTSService()
    
    try:
        # 生成音频
        logger.info("🎵 开始生成音频")
        audio_files = tts_service.generate_speech_segments(card.info_CN, str(output_dir))
        
        if audio_files and len(audio_files) > 0:
            logger.info(f"✅ 成功生成 {len(audio_files)} 个音频片段")
            
            # 检查哪些音频文件生成成功
            success_count = 0
            total_size = 0
            for i, audio_file in enumerate(audio_files):
                if os.path.exists(audio_file):
                    size = os.path.getsize(audio_file) / 1024  # KB
                    total_size += size
                    success_count += 1
                    # 确定对应的句子语言
                    sentence = card.info_CN[i] if i < len(card.info_CN) else "未知"
                    if any('\u4e00' <= char <= '\u9fff' for char in sentence):
                        lang = "中文"
                    else:
                        lang = "英文"
                    logger.info(f"   ✅ {i+1}. [{lang}] {os.path.basename(audio_file)} ({size:.1f} KB)")
                else:
                    logger.error(f"   ❌ {i+1}. {os.path.basename(audio_file)} - 文件不存在")
            
            logger.info(f"📁 成功率: {success_count}/{len(audio_files)} ({success_count/len(audio_files)*100:.1f}%)")
            logger.info(f"📁 总音频大小: {total_size/1024:.2f} MB")
        else:
            logger.error("❌ 音频生成失败")
            
    except Exception as e:
        logger.error(f"❌ 音频生成过程出错: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_problem_card_14423()
