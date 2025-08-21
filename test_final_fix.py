#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证最终修复效果
"""

import os
import json
from moviepy.editor import TextClip, ColorClip, CompositeVideoClip

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

def test_final_fix():
    """测试最终修复效果"""
    
    # 测试几个包含中英文的句子
    test_sentences = [
        "减论Agent通过算法为您推荐",
        "浙江大学推出了Tinker方法", 
        "2025年8月21日arXiv,cs.CV,发文量约97篇"
    ]
    
    for i, sentence in enumerate(test_sentences):
        print(f"\n=== 测试句子 {i+1}: '{sentence}' ===")
        
        # 使用修复后的完整路径
        formatted_sentence = _devideSentence(sentence)
        
        text_clip = TextClip(
            formatted_sentence,
            fontsize=50,
            color='black',
            font="/Library/Fonts/Arial Unicode.ttf",  # 使用完整路径确保中英文支持
            align='center'
        )
        
        print(f"TextClip尺寸: {text_clip.size}")
        
        if text_clip.w > 0 and text_clip.h > 0:
            # 创建背景
            bgcolor_clip = ColorClip(
                size=text_clip.size,
                color=(250, 250, 210, 200),
                ismask=False
            )
            
            # 合并
            composite_clip = CompositeVideoClip([bgcolor_clip, text_clip])
            
            # 保存
            output_path = f"final_test_{i}.png"
            composite_clip.save_frame(output_path, t=0.5)
            
            print(f"✅ 保存成功: {output_path}")
            
            # 清理
            text_clip.close()
            bgcolor_clip.close()
            composite_clip.close()
        else:
            print("❌ TextClip尺寸为0")

if __name__ == "__main__":
    test_final_fix()