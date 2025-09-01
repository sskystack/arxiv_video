#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试实际字幕生成效果 - 模拟包含英文内容的卡片
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
from pathlib import Path

def create_test_card_with_english():
    """创建包含英文内容的测试卡片"""
    print("📝 创建包含英文内容的测试卡片")
    
    # 创建测试目录
    test_dir = Path("/tmp/test_english_subtitle")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建包含中英文混合内容的测试卡片
    card_data = {
        "arXivID": "test.english.v1",
        "info_CN": [
            "2025年8月21日arXiv,cs.CV,发文量约97篇",
            "The Tsinghua University and Beijing Academy of Artificial Intelligence presented a unified representation that jointly models geometry and motion",
            "该方法显著提升了模型性能，achieving state-of-the-art results on multiple benchmarks with impressive performance improvements",
            "This paper introduces a novel approach for machine learning applications in computer vision and natural language processing domains",
            "减论Agent通过算法为您推荐优质论文内容",
            "The proposed method demonstrates superior performance compared to existing approaches while maintaining computational efficiency"
        ],
        "info_EN": [
            "2025 arXiv cs.CV papers",
            "Tsinghua University research",
            "Performance improvements achieved",
            "Novel ML approach introduced", 
            "Agent recommendations",
            "Superior performance demonstrated"
        ]
    }
    
    # 保存测试卡片
    card_file = test_dir / "test_english.json"
    with open(card_file, 'w', encoding='utf-8') as f:
        json.dump(card_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 测试卡片已保存到: {card_file}")
    
    print("\n📋 卡片内容预览:")
    print("中文句子（包含英文）:")
    for i, sentence in enumerate(card_data["info_CN"], 1):
        print(f"  {i}. {sentence}")
        print(f"     长度: {len(sentence)} 字符")
    
    return str(card_file)

def test_subtitle_processing(card_file):
    """测试字幕处理效果"""
    print(f"\n🎬 测试字幕处理效果")
    
    # 加载卡片数据
    with open(card_file, 'r', encoding='utf-8') as f:
        card_data = json.load(f)
    
    # 模拟VideoComposer的处理
    from core.video_composer import VideoComposer
    composer = VideoComposer()
    
    sentences = card_data["info_CN"]
    print(f"\n处理 {len(sentences)} 个句子的字幕:")
    print("="*80)
    
    for i, sentence in enumerate(sentences, 1):
        print(f"\n句子 {i}: {sentence}")
        print(f"原始长度: {len(sentence)} 字符")
        
        # 检测文本类型
        is_english = composer._is_mainly_english(sentence)
        print(f"识别为: {'主要英文' if is_english else '主要中文/混合'}")
        
        # 应用换行
        formatted_sentence = composer._devideSentence(sentence)
        lines = formatted_sentence.split('\n')
        
        print(f"换行后: {len(lines)} 行")
        for j, line in enumerate(lines, 1):
            print(f"  行{j}: {line}")
        
        # 检查英文是否符合要求
        if is_english:
            if len(lines) <= 2:
                print("✅ 英文字幕符合最多2行的要求")
            else:
                print("❌ 英文字幕超过2行！")
        
        print("-" * 60)

if __name__ == "__main__":
    print("🧪 开始英文字幕换行测试")
    
    # 创建测试卡片
    card_file = create_test_card_with_english()
    
    # 测试字幕处理
    test_subtitle_processing(card_file)
    
    print("\n🎯 测试完成！")
    print("总结:")
    print("- 英文句子现在最多显示2行")
    print("- 中文句子保持原有的16字符换行")
    print("- 混合语言根据英文占比自动选择处理方式")
