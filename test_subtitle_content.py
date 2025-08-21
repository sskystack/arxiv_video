#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字幕内容和编码测试脚本
"""

import os
import json
import logging
from moviepy.editor import TextClip, ColorClip, CompositeVideoClip

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_text_content(text: str):
    """分析文本内容的编码和字符"""
    print(f"原始文本: '{text}'")
    print(f"文本长度: {len(text)}")
    print(f"文本类型: {type(text)}")
    print(f"编码后的bytes: {text.encode('utf-8')}")
    
    # 检查每个字符
    print("字符分析:")
    for i, char in enumerate(text):
        print(f"  [{i}] '{char}' (Unicode: U+{ord(char):04X})")
        
    # 检查是否包含不可见字符
    import string
    printable_chars = set(string.printable)
    non_printable = [c for c in text if c not in printable_chars and not ord(c) > 127]
    if non_printable:
        print(f"发现非打印字符: {non_printable}")

def test_single_subtitle(text: str, output_path: str):
    """测试单个字幕的渲染"""
    try:
        print(f"\n=== 测试文本: '{text}' ===")
        analyze_text_content(text)
        
        # 创建字幕
        text_clip = TextClip(
            text,
            fontsize=50,
            color='black',
            font="SimHei",
            align='center'
        )
        
        print(f"TextClip 尺寸: {text_clip.size}")
        print(f"TextClip 宽度: {text_clip.w}, 高度: {text_clip.h}")
        
        if text_clip.w == 0 or text_clip.h == 0:
            print("⚠️  警告: TextClip尺寸为0，可能无法正常显示")
            return False
        
        # 创建背景
        bgcolor_clip = ColorClip(
            size=(text_clip.w + 100, text_clip.h + 50),
            color=(250, 250, 210),
            ismask=False
        )
        
        # 合并
        final_clip = CompositeVideoClip([bgcolor_clip, text_clip.set_position('center')])
        final_clip = final_clip.set_duration(3.0)  # 3秒测试
        
        # 输出图片进行检查
        final_clip.save_frame(output_path, t=0.5)
        print(f"✅ 字幕图片已保存到: {output_path}")
        
        # 清理
        text_clip.close()
        bgcolor_clip.close()
        final_clip.close()
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

def load_and_test_card_content():
    """加载并测试实际的卡片内容"""
    # 寻找一个实际的卡片文件进行测试
    cards_dir = "cards"
    if os.path.exists(cards_dir):
        for filename in os.listdir(cards_dir):
            if filename.endswith('.json'):
                card_path = os.path.join(cards_dir, filename)
                print(f"\n📋 测试卡片文件: {card_path}")
                
                with open(card_path, 'r', encoding='utf-8') as f:
                    card_data = json.load(f)
                
                # 获取中英文内容
                info_cn = card_data.get('info_CN', [])
                info_en = card_data.get('info_EN', [])
                
                print(f"中文句子数量: {len(info_cn)}")
                print(f"英文句子数量: {len(info_en)}")
                
                # 测试前几个句子
                test_count = min(3, len(info_cn))
                for i in range(test_count):
                    if i < len(info_cn):
                        chinese_text = info_cn[i]
                        output_path = f"test_chinese_{i}.png"
                        test_single_subtitle(chinese_text, output_path)
                
                # 测试英文句子
                test_count = min(3, len(info_en))
                for i in range(test_count):
                    if i < len(info_en):
                        english_text = info_en[i]
                        output_path = f"test_english_{i}.png"
                        test_single_subtitle(english_text, output_path)
                
                break  # 只测试第一个文件
    else:
        print("❌ 未找到cards目录")

def test_mixed_content():
    """测试混合中英文内容"""
    test_texts = [
        "This is English text",
        "这是中文文本",
        "Mixed 混合 Content 内容",
        "数字123和English",
        "",  # 空字符串
        "   ",  # 空白字符
    ]
    
    for i, text in enumerate(test_texts):
        output_path = f"test_mixed_{i}.png"
        test_single_subtitle(text, output_path)

if __name__ == "__main__":
    print("🔍 开始字幕内容测试...")
    
    # 测试混合内容
    print("\n" + "="*50)
    print("测试混合中英文内容")
    test_mixed_content()
    
    # 测试实际卡片内容
    print("\n" + "="*50)
    print("测试实际卡片内容")
    load_and_test_card_content()
    
    print("\n✅ 测试完成！请检查生成的PNG文件查看字幕渲染效果")