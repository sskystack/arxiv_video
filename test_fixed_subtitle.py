#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证修复后的字幕渲染
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

def test_fixed_subtitle():
    """测试修复后的字幕创建逻辑"""
    
    # 加载一个实际的卡片文件测试
    card_file = "cards/2508.14811v1.json"
    if os.path.exists(card_file):
        with open(card_file, 'r', encoding='utf-8') as f:
            card_data = json.load(f)
        
        sentences = card_data.get('info_CN', [])
        print(f"测试句子数量: {len(sentences)}")
        
        # 测试前3个句子
        for i, sentence in enumerate(sentences[:3]):
            print(f"\n测试句子 {i+1}: '{sentence}'")
            
            # 使用修复后的逻辑
            formatted_sentence = _devideSentence(sentence)
            
            # 创建字幕文本 - 使用Arial Unicode MS字体
            text_clip = TextClip(
                formatted_sentence,
                fontsize=50,
                color='black',
                font="Arial Unicode MS",  # macOS上最佳中英文字体
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
                
                # 合并文本和背景
                composite_clip = CompositeVideoClip([bgcolor_clip, text_clip])
                
                # 保存测试结果
                output_path = f"fixed_subtitle_test_{i}.png"
                composite_clip.save_frame(output_path, t=0.5)
                
                print(f"✅ 修复测试成功: {output_path}")
                
                # 清理
                text_clip.close()
                bgcolor_clip.close() 
                composite_clip.close()
            else:
                print("❌ TextClip尺寸为0")
    
    else:
        print("未找到测试卡片文件")

if __name__ == "__main__":
    test_fixed_subtitle()