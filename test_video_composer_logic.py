#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完全复制video_composer.py字幕逻辑的测试脚本
"""

import os
import logging
from moviepy.editor import TextClip, ColorClip, CompositeVideoClip

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _devideSentence(text: str) -> str:
    """完全按照参考代码的换行函数"""
    res = ''
    for i, ch in enumerate(text):
        res += ch
        if i % 16 == 15:
            res += '\n'
    if res.endswith('\n'):
        res = res[:-1]
    return res

def test_subtitle_creation(sentence: str, output_prefix: str):
    """完全按照video_composer.py的逻辑创建字幕"""
    try:
        print(f"\n=== 测试句子: '{sentence}' ===")
        
        # 1. 使用参考代码的换行函数
        formatted_sentence = _devideSentence(sentence)
        print(f"格式化后: '{formatted_sentence}'")
        
        # 2. 创建字幕文本 - 完全按照video_composer.py
        text_clip = TextClip(
            formatted_sentence,
            fontsize=50,
            color='black',
            font="SimHei",  # 使用黑体
            align='center'
        )
        
        print(f"text_clip尺寸: {text_clip.size}")
        
        # 先保存原始文本clip
        text_clip.save_frame(f"{output_prefix}_text_only.png", t=0.5)
        
        # 3. 创建背景 - 完全按照参考代码
        bgcolor_clip = ColorClip(
            size=text_clip.size,
            color=(250, 250, 210, 200),  # 参考代码的RGBA值
            ismask=False
        )
        
        print(f"bgcolor_clip尺寸: {bgcolor_clip.size}")
        
        # 先保存背景clip
        bgcolor_clip.save_frame(f"{output_prefix}_background_only.png", t=0.5)
        
        # 4. 合并文本和背景 - 完全按照参考代码
        composite_clip = CompositeVideoClip([bgcolor_clip, text_clip])
        
        print(f"composite_clip尺寸: {composite_clip.size}")
        
        # 保存合成结果
        composite_clip.save_frame(f"{output_prefix}_composite.png", t=0.5)
        
        # 清理
        text_clip.close()
        bgcolor_clip.close()
        composite_clip.close()
        
        print(f"✅ 测试完成，文件保存为: {output_prefix}_*.png")
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")

def main():
    test_cases = [
        ("This is English", "test_en"),
        ("这是中文测试", "test_cn"),
        ("Mixed 混合内容", "test_mixed"),
    ]
    
    for sentence, prefix in test_cases:
        test_subtitle_creation(sentence, prefix)

if __name__ == "__main__":
    main()