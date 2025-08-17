#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试卡片生成功能
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.card_generator import generate_video_script_card

def test_card_generation():
    """测试卡片生成功能"""
    
    # 测试用的 ArXiv ID（你可以替换为数据库中真实存在的ID）
    test_arxiv_ids = [
        "2024.12345",  # 示例ID，请替换为真实ID
        "2024.12346",  # 示例ID，请替换为真实ID
    ]
    
    print("🧪 开始测试卡片生成功能...")
    print("=" * 50)
    
    for arxiv_id in test_arxiv_ids:
        print(f"\n📄 测试 ArXiv ID: {arxiv_id}")
        
        try:
            card = generate_video_script_card(arxiv_id)
            
            if card:
                print(f"✅ 成功生成卡片!")
                print(f"   - ArXiv ID: {card.arXivID}")
                print(f"   - 中文句子数: {len(card.info_CN)}")
                print(f"   - 英文句子数: {len(card.info_EN)}")
                print(f"   - 中文解说预览: {card.info_CN[0][:50]}..." if card.info_CN else "   - 无中文解说")
                print(f"   - 英文解说预览: {card.info_EN[0][:50]}..." if card.info_EN else "   - 无英文解说")
            else:
                print(f"❌ 无法生成卡片 (可能该论文不存在或没有解说脚本)")
                
        except Exception as e:
            print(f"❌ 测试失败: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 测试完成!")

if __name__ == "__main__":
    test_card_generation()
