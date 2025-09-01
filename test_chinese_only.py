#!/usr/bin/env python3
"""测试移除英文逻辑后的字幕换行效果"""

import sys
sys.path.append('/Users/zhouzhongtian/vscode/paperfindvideo')

from core.video_composer import VideoComposer

def test_chinese_only_subtitles():
    """测试只保留中文逻辑的字幕换行"""
    print("=== 测试纯中文字幕换行 ===")
    
    composer = VideoComposer()
    
    # 测试用例 - 只有中文
    test_cases = [
        "这是一个短中文句子。",
        "这是一个中等长度的中文句子，用于测试换行功能是否正常工作。",
        "这是一个很长的中文句子，包含很多字符，用于测试中文字幕的换行功能是否能够正确地按照十六个字符进行换行处理，确保显示效果良好。",
        "这是一个超级长的中文句子，包含大量的汉字字符，专门用来测试中文字幕系统在处理长文本时的换行逻辑是否能够稳定工作，并且保持良好的显示效果和用户体验。"
    ]
    
    for i, text in enumerate(test_cases, 1):
        print(f"\n--- 测试 {i} ---")
        print(f"原文: {text}")
        print(f"长度: {len(text)} 字符")
        
        result = composer._devideSentence(text)
        lines = result.split('\n')
        
        print(f"换行结果 ({len(lines)} 行):")
        for j, line in enumerate(lines, 1):
            print(f"  第{j}行 ({len(line)}字符): {line}")
        
        # 验证每行字符数
        for j, line in enumerate(lines, 1):
            if j < len(lines):  # 不是最后一行
                if len(line) == 16:
                    print(f"✅ 第{j}行字符数正确 (16字符)")
                else:
                    print(f"❌ 第{j}行字符数异常 ({len(line)}字符)")
            else:  # 最后一行
                if len(line) <= 16:
                    print(f"✅ 最后一行字符数合理 ({len(line)}字符)")
                else:
                    print(f"❌ 最后一行字符数异常 ({len(line)}字符)")

def test_methods_removed():
    """测试英文相关方法是否已被移除"""
    print("\n=== 测试英文方法移除 ===")
    
    composer = VideoComposer()
    
    # 检查方法是否存在
    methods_to_check = [
        '_is_mainly_english',
        '_smart_english_wrap'
    ]
    
    for method_name in methods_to_check:
        if hasattr(composer, method_name):
            print(f"❌ 方法 {method_name} 仍然存在")
        else:
            print(f"✅ 方法 {method_name} 已成功移除")

if __name__ == "__main__":
    test_chinese_only_subtitles()
    test_methods_removed()
    print("\n✅ 中文字幕测试完成")
