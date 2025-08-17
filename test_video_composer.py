#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试视频合成功能
"""

import os
import sys
import json
from core.video_composer import VideoComposer
from core.Card import ReductCard

def test_video_composer():
    """测试视频合成器"""
    print("🧪 测试视频合成功能")
    print("="*50)
    
    # 检查测试视频目录
    test_dir = "/Users/zhouzhongtian/Movies/arxiv_video/20250814/2508.10898v1"
    if not os.path.exists(test_dir):
        print(f"❌ 测试目录不存在: {test_dir}")
        return False
    
    # 检查是否有解说卡片文件
    card_file = os.path.join(test_dir, "2508.10898v1.json")
    if not os.path.exists(card_file):
        print(f"❌ 解说卡片文件不存在: {card_file}")
        return False
    
    # 检查是否有视频文件
    video_files = []
    for file in os.listdir(test_dir):
        if file.endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')) and not file.endswith('_res.mp4'):
            video_files.append(file)
    
    if not video_files:
        print(f"❌ 测试目录中没有找到视频文件")
        return False
    
    print(f"✅ 找到 {len(video_files)} 个视频文件")
    print(f"✅ 找到解说卡片文件")
    
    # 显示卡片内容
    with open(card_file, 'r', encoding='utf-8') as f:
        card_data = json.load(f)
    
    print(f"\n📄 解说卡片内容:")
    print(f"   ArXiv ID: {card_data.get('arxiv_id')}")
    print(f"   内容句数: {len(card_data.get('content', []))}")
    for i, sentence in enumerate(card_data.get('content', [])[:3], 1):
        print(f"   {i}. {sentence[:50]}...")
    
    # 创建视频合成器并测试
    try:
        print(f"\n🎬 开始视频合成...")
        composer = VideoComposer()
        result_path = composer.compose_paper_video(test_dir, "2508.10898v1")
        
        if result_path and os.path.exists(result_path):
            print(f"✅ 视频合成成功！")
            print(f"   输出文件: {result_path}")
            print(f"   文件大小: {os.path.getsize(result_path) / (1024*1024):.2f} MB")
            return True
        else:
            print(f"❌ 视频合成失败")
            return False
            
    except Exception as e:
        print(f"❌ 视频合成出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tts_service():
    """测试语音合成服务"""
    print("\n🔊 测试语音合成功能")
    print("="*50)
    
    try:
        from core.tts_service import TTSService
        
        tts = TTSService()
        test_sentences = ["这是一个测试句子。", "语音合成功能正常。"]
        
        # 创建临时目录
        test_output_dir = "/tmp/tts_test"
        os.makedirs(test_output_dir, exist_ok=True)
        
        print(f"🎤 生成测试语音...")
        audio_paths = tts.generate_speech_segments(test_sentences, test_output_dir)
        
        if audio_paths and all(os.path.exists(path) for path in audio_paths):
            print(f"✅ 语音合成成功！生成 {len(audio_paths)} 个音频文件")
            for path in audio_paths:
                print(f"   - {path}")
            return True
        else:
            print(f"❌ 语音合成失败")
            return False
            
    except Exception as e:
        print(f"❌ 语音合成测试出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🚀 视频合成功能测试")
    print("="*60)
    
    # 检查环境
    try:
        import moviepy
        print(f"✅ MoviePy 版本: {moviepy.__version__}")
    except ImportError:
        print("❌ MoviePy 未安装，请运行: pip install moviepy")
        return
    
    try:
        import pydub
        print(f"✅ Pydub 已安装")
    except ImportError:
        print("❌ Pydub 未安装，请运行: pip install pydub")
        return
    
    # 检查 FFmpeg
    import subprocess
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ FFmpeg 已安装")
        else:
            print("❌ FFmpeg 未正确安装")
            return
    except FileNotFoundError:
        print("❌ FFmpeg 未安装，请先安装 FFmpeg")
        return
    
    print("\n" + "="*60)
    
    # 运行测试
    tests_passed = 0
    total_tests = 2
    
    # 测试语音合成
    if test_tts_service():
        tests_passed += 1
    
    # 测试视频合成
    if test_video_composer():
        tests_passed += 1
    
    # 总结
    print("\n" + "="*60)
    print(f"📊 测试结果: {tests_passed}/{total_tests} 通过")
    
    if tests_passed == total_tests:
        print("🎉 所有测试通过！视频合成功能准备就绪")
    else:
        print("⚠️  部分测试失败，请检查错误信息")

if __name__ == "__main__":
    main()
