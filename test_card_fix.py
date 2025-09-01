#!/usr/bin/env python3
"""测试卡片生成修复效果"""

import sys
import os
sys.path.append('/Users/zhouzhongtian/vscode/paperfindvideo')

from core.card_generator import CardGenerator

def test_card_content():
    """测试卡片内容是否不再包含开场白和结束语"""
    print("=== 测试卡片内容修复 ===")
    
    # 模拟论文详情数据
    class MockPaperDetail:
        def __init__(self):
            self.cn_script = "这是一篇关于机器学习的论文。本文提出了一种新的算法。"
            self.eng_script = "This paper presents a novel approach to machine learning. The method shows significant improvements."
    
    class MockPaper:
        def __init__(self):
            self.publication_date = None
    
    # 创建卡片生成器
    generator = CardGenerator()
    
    # 创建模拟卡片
    arxiv_id = "2024.12345"
    paper_detail = MockPaperDetail()
    paper = MockPaper()
    
    card = generator._create_card_from_paper_detail(arxiv_id, paper_detail, paper)
    
    print(f"生成的中文内容:")
    for i, sentence in enumerate(card.info_CN, 1):
        print(f"  {i}. {sentence}")
    
    print(f"\n生成的英文内容:")
    for i, sentence in enumerate(card.info_EN, 1):
        print(f"  {i}. {sentence}")
    
    # 检查是否包含不应该存在的内容
    all_content = ' '.join(card.info_CN)
    
    forbidden_patterns = [
        "arXiv,cs.CV,发文量",
        "减论Agent通过算法为您推荐", 
        "欢迎关注减论，用科技链接个体",
        "This paper presents",  # 检查英文内容
        "novel approach",
        "machine learning"
    ]
    
    print(f"\n=== 内容检查 ===")
    for pattern in forbidden_patterns:
        if pattern in all_content:
            print(f"❌ 发现不应该存在的内容: {pattern}")
        else:
            print(f"✅ 未发现: {pattern}")
    
    print(f"\n总句子数: {len(card.info_CN)}")
    print(f"英文内容条目数: {len(card.info_EN)} (应该为0)")
    
    if len(card.info_EN) == 0:
        print("✅ 英文脚本已成功移除")
    else:
        print("❌ 英文脚本仍然存在")
    
    print("✅ 卡片生成修复测试完成")

def test_font_paths():
    """测试字体文件是否存在"""
    print("\n=== 测试字体文件 ===")
    
    font_paths = [
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/Library/Fonts/Arial Unicode.ttf"
    ]
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            print(f"✅ 字体文件存在: {font_path}")
        else:
            print(f"❌ 字体文件不存在: {font_path}")

if __name__ == "__main__":
    test_card_content()
    test_font_paths()
