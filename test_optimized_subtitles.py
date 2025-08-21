#!/usr/bin/env python3
"""
测试优化后的字幕系统：
1. 底部对齐定位
2. 更高的文本密度（减少换行）
3. 更紧凑的背景框
"""

import sys
import os
sys.path.append('/Users/zhouzhongtian/vscode/arxiv_video')

import logging
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, ColorClip
from core.video_composer import VideoComposer

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_subtitle_optimization():
    """测试优化后的字幕系统"""
    
    # 创建测试句子 - 包含长英文和中文
    test_sentences = [
        # 长英文句子 - 应该单行显示或最多两行
        "This is a very long English sentence that should be displayed more efficiently with fewer line breaks to maximize text utilization in the subtitle background box.",
        
        # 中文句子 - 也应该更紧凑
        "这是一个相对较长的中文句子，希望能够在字幕背景框中更有效地显示，减少不必要的换行，提高文本的利用率和显示效果。",
        
        # 混合语言句子
        "This paper introduces a novel approach 本文介绍了一种新颖的方法 for machine learning applications in computer vision.",
        
        # 短句子测试
        "Short sentence.",
        "短句测试。"
    ]
    
    # 创建简单的测试视频（黑色背景）
    from moviepy.editor import ColorClip as BgColorClip
    test_video = BgColorClip(size=(1280, 720), color=(0, 0, 0), duration=2)
    
    composer = VideoComposer()
    
    results = []
    
    for i, sentence in enumerate(test_sentences):
        print(f"\n=== 测试句子 {i+1}: {sentence[:50]}... ===")
        
        try:
            # 使用VideoComposer的内部方法测试文本分割
            formatted_text = composer._devideSentence(sentence, test_video)
            print(f"格式化后的文本:\n{formatted_text}")
            print(f"行数: {len(formatted_text.split(chr(10)))}")
            
            # 测试字幕创建（模拟_add_subtitles的部分逻辑）
            text_clip = TextClip(
                formatted_text,
                fontsize=48,
                color='black',
                font='STHeiti',  # 使用兼容的字体
                stroke_color='white',
                stroke_width=1
            ).set_duration(2)
            
            # 获取文本尺寸
            text_width, text_height = text_clip.size
            print(f"文本尺寸: {text_width} x {text_height}")
            
            # 计算背景框尺寸（模拟优化后的逻辑）
            if composer._is_mainly_english(sentence):
                bg_width = int(text_width * 1.15)
                bg_height = int(text_height * 1.1)
                print(f"英文文本 - 背景框: {bg_width} x {bg_height}")
            else:
                bg_width = int(text_width * 1.2)
                bg_height = int(text_height * 1.1)
                print(f"中文文本 - 背景框: {bg_width} x {bg_height}")
            
            # 计算文本填充率
            text_area = text_width * text_height
            bg_area = bg_width * bg_height
            fill_rate = (text_area / bg_area) * 100 if bg_area > 0 else 0
            print(f"文本填充率: {fill_rate:.1f}%")
            
            # 计算底部对齐位置
            subtitle_y = test_video.h - bg_height - 20
            print(f"字幕Y位置: {subtitle_y} (距离底部: 20px)")
            
            results.append({
                'sentence': sentence[:50] + '...' if len(sentence) > 50 else sentence,
                'lines': len(formatted_text.split('\n')),
                'fill_rate': fill_rate,
                'bg_size': (bg_width, bg_height),
                'text_size': (text_width, text_height)
            })
            
        except Exception as e:
            print(f"测试失败: {e}")
            results.append({
                'sentence': sentence[:50] + '...',
                'error': str(e)
            })
    
    # 总结报告
    print(f"\n{'='*60}")
    print("字幕优化测试总结报告")
    print(f"{'='*60}")
    
    for i, result in enumerate(results):
        print(f"\n句子 {i+1}: {result['sentence']}")
        if 'error' in result:
            print(f"  ❌ 错误: {result['error']}")
        else:
            print(f"  📏 行数: {result['lines']}")
            print(f"  📊 填充率: {result['fill_rate']:.1f}%")
            print(f"  📐 背景框: {result['bg_size'][0]}x{result['bg_size'][1]}")
            print(f"  📝 文本框: {result['text_size'][0]}x{result['text_size'][1]}")
    
    # 计算平均填充率
    valid_results = [r for r in results if 'fill_rate' in r]
    if valid_results:
        avg_fill_rate = sum(r['fill_rate'] for r in valid_results) / len(valid_results)
        print(f"\n🎯 平均文本填充率: {avg_fill_rate:.1f}%")
        
        if avg_fill_rate > 70:
            print("✅ 文本利用率优秀！")
        elif avg_fill_rate > 60:
            print("⚠️ 文本利用率良好，还有改进空间")
        else:
            print("❌ 文本利用率需要进一步优化")

if __name__ == "__main__":
    test_subtitle_optimization()
