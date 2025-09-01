#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的英文字幕换行功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.video_composer import VideoComposer

def test_english_subtitle_wrapping():
    """测试英文字幕换行功能"""
    print("🔤 测试英文字幕换行功能")
    
    # 创建VideoComposer实例
    composer = VideoComposer()
    
    # 测试不同类型的句子
    test_sentences = [
        # 长英文句子 - 应该被限制为最多两行
        "The Tsinghua University and Beijing Academy of Artificial Intelligence presented a unified representation that jointly models geometry and motion for high-quality 3D scene generation from sparse camera views.",
        
        # 中等长度英文句子
        "This method achieves state-of-the-art results on multiple benchmarks with impressive performance improvements.",
        
        # 短英文句子
        "Short English sentence.",
        
        # 中文句子 - 应该保持原有的16字符换行逻辑
        "2025年8月21日arXiv,cs.CV,发文量约97篇，减论Agent通过算法为您推荐优质论文内容",
        
        # 中英文混合
        "This paper introduces 一种新颖的方法 for machine learning applications in computer vision and natural language processing."
    ]
    
    print("\n" + "="*80)
    
    for i, sentence in enumerate(test_sentences, 1):
        print(f"\n📝 测试句子 {i}:")
        print(f"原文: {sentence}")
        print(f"长度: {len(sentence)} 字符")
        
        # 检测文本类型
        is_english = composer._is_mainly_english(sentence)
        print(f"文本类型: {'主要英文' if is_english else '主要中文/混合'}")
        
        # 应用换行
        formatted_text = composer._devideSentence(sentence)
        lines = formatted_text.split('\n')
        print(f"换行后行数: {len(lines)}")
        print("换行结果:")
        for j, line in enumerate(lines, 1):
            print(f"  第{j}行: {line}")
        
        if is_english and len(lines) > 2:
            print("⚠️ 警告: 英文文本超过2行!")
        elif is_english and len(lines) <= 2:
            print("✅ 英文文本符合2行限制")
        
        print("-" * 40)

if __name__ == "__main__":
    test_english_subtitle_wrapping()
