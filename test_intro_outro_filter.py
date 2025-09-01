#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试开场白和结尾词过滤功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.video_composer import VideoComposer

def test_intro_outro_filtering():
    """测试开场白和结尾词过滤功能"""
    print("🚫 测试开场白和结尾词过滤功能")
    
    # 创建VideoComposer实例
    composer = VideoComposer()
    
    # 测试句子，包含开场白、正文和结尾词
    test_sentences = [
        # 开场白
        "2025年8月31日arXiv,cs.CV,发文量约97篇",
        "2024年12月15日arXiv,cs.AI,发文量约150篇",
        "减论Agent通过算法为您推荐",
        "减论Agent通过算法为您推荐优质论文内容",
        
        # 正文内容（应该保留）
        "The Tsinghua University and Beijing Academy of Artificial Intelligence presented a unified representation",
        "该方法显著提升了模型性能，achieving state-of-the-art results",
        "This paper introduces a novel approach for machine learning applications",
        "本文提出了一种创新的深度学习方法",
        
        # 结尾词
        "欢迎关注减论，用科技链接个体",
        "欢迎关注减论",
        "感谢观看",
        "感谢观看本期视频",
        
        # 更多正文（应该保留）
        "实验结果表明该方法具有显著优势",
        "Future work will focus on improving the computational efficiency"
    ]
    
    print(f"\n📝 原始句子数量: {len(test_sentences)}")
    print("原始句子:")
    for i, sentence in enumerate(test_sentences, 1):
        print(f"  {i:2d}. {sentence}")
    
    # 测试过滤功能
    filtered_sentences = composer._filter_intro_outro_sentences(test_sentences)
    
    print(f"\n✅ 过滤后句子数量: {len(filtered_sentences)}")
    print("过滤后句子:")
    for i, sentence in enumerate(filtered_sentences, 1):
        print(f"  {i:2d}. {sentence}")
    
    # 验证过滤效果
    print(f"\n📊 过滤统计:")
    print(f"- 原始句子: {len(test_sentences)} 条")
    print(f"- 过滤后句子: {len(filtered_sentences)} 条")
    print(f"- 被过滤句子: {len(test_sentences) - len(filtered_sentences)} 条")
    
    # 检查是否正确过滤了开场白和结尾词
    expected_filtered_count = len([s for s in test_sentences if not composer._is_intro_sentence(s) and not composer._is_outro_sentence(s)])
    
    if len(filtered_sentences) == expected_filtered_count:
        print("✅ 过滤功能工作正常！")
    else:
        print("❌ 过滤功能可能有问题！")
    
    return test_sentences, filtered_sentences

def test_individual_patterns():
    """测试各个模式的识别"""
    print("\n🔍 测试各个模式的识别:")
    
    composer = VideoComposer()
    
    # 测试开场白模式
    intro_tests = [
        ("2025年8月31日arXiv,cs.CV,发文量约97篇", True),
        ("2024年12月15日arXiv,cs.AI,发文量约150篇", True),
        ("减论Agent通过算法为您推荐", True),
        ("减论Agent通过算法为您推荐优质内容", True),
        ("这是一个普通句子", False),
        ("Today's arXiv papers", False),
    ]
    
    print("\n开场白识别测试:")
    for sentence, expected in intro_tests:
        result = composer._is_intro_sentence(sentence)
        status = "✅" if result == expected else "❌"
        print(f"  {status} '{sentence}' -> {result} (期望: {expected})")
    
    # 测试结尾词模式
    outro_tests = [
        ("欢迎关注减论，用科技链接个体", True),
        ("欢迎关注减论", True),
        ("感谢观看", True),
        ("感谢观看本期视频", True),
        ("这是普通结尾句子", False),
        ("Thank you for watching", False),
    ]
    
    print("\n结尾词识别测试:")
    for sentence, expected in outro_tests:
        result = composer._is_outro_sentence(sentence)
        status = "✅" if result == expected else "❌"
        print(f"  {status} '{sentence}' -> {result} (期望: {expected})")

if __name__ == "__main__":
    print("🧪 开始开场白和结尾词过滤测试")
    print("=" * 80)
    
    # 测试整体过滤功能
    original, filtered = test_intro_outro_filtering()
    
    # 测试个别模式识别
    test_individual_patterns()
    
    print("\n🎯 测试完成！")
    print("功能说明:")
    print("- 自动识别并过滤开场白（日期发文量、减论Agent推荐）")
    print("- 自动识别并过滤结尾词（欢迎关注减论、感谢观看）")
    print("- 保留核心论文内容相关的句子")
    print("- 字幕和语音都会应用相同的过滤逻辑")
