#!/usr/bin/env python3
"""
测试视频时长过滤功能
"""

import os
import sys
from unittest.mock import Mock, patch
import tempfile

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.video_composer import VideoComposer
from core.Card import ReductCard

def test_video_duration_filtering():
    """测试视频时长过滤功能"""
    print("🧪 测试视频时长过滤功能...")
    
    # 创建模拟的 ReductCard
    mock_card = Mock(spec=ReductCard)
    mock_card.title = "Test Paper"
    mock_card.subtitle_cn = "测试论文"
    mock_card.paragraphs = [
        {
            "heading": "摘要",
            "content": "这是一个测试摘要。"
        }
    ]
    
    # 创建 VideoComposer 实例
    composer = VideoComposer()
    
    # 测试时长检查函数
    print("\n📏 测试视频时长检测:")
    
    # 模拟不同时长的视频
    test_cases = [
        (300, True),   # 5分钟 - 应该通过
        (480, True),   # 8分钟 - 应该通过
        (600, True),   # 10分钟 - 边界情况，应该通过
        (720, False),  # 12分钟 - 应该被过滤
        (1200, False), # 20分钟 - 应该被过滤
    ]
    
    with patch.object(composer, '_get_video_duration') as mock_duration:
        # 测试每个时长案例
        for duration, should_pass in test_cases:
            mock_duration.return_value = duration
            
            # 创建临时目录和文件
            with tempfile.TemporaryDirectory() as temp_dir:
                test_video = os.path.join(temp_dir, f"test_{duration}s.mp4")
                with open(test_video, 'w') as f:
                    f.write("dummy video file")
                
                # 测试收集文件
                video_files = composer._collect_video_files(temp_dir)
                
                minutes = duration / 60
                if should_pass:
                    assert len(video_files) == 1, f"时长 {minutes:.1f} 分钟的视频应该通过过滤"
                    print(f"  ✅ {minutes:.1f} 分钟视频通过过滤")
                else:
                    assert len(video_files) == 0, f"时长 {minutes:.1f} 分钟的视频应该被过滤"
                    print(f"  🚫 {minutes:.1f} 分钟视频被正确过滤")
    
    print("\n📊 测试时长检测异常情况:")
    
    # 测试无法获取时长的情况
    with patch.object(composer, '_get_video_duration') as mock_duration:
        mock_duration.return_value = None
        
        with tempfile.TemporaryDirectory() as temp_dir:
            test_video = os.path.join(temp_dir, "invalid.mp4")
            with open(test_video, 'w') as f:
                f.write("invalid video file")
            
            video_files = composer._collect_video_files(temp_dir)
            assert len(video_files) == 0, "无法获取时长的视频应该被跳过"
            print("  ⚠️ 无法获取时长的视频被正确跳过")
    
    print("\n✅ 所有视频时长过滤测试通过！")

def test_duration_detection_methods():
    """测试时长检测方法"""
    print("\n🔍 测试时长检测方法...")
    
    composer = VideoComposer()
    
    # 测试不存在的文件
    duration = composer._get_video_duration("/nonexistent/video.mp4")
    assert duration is None, "不存在的文件应该返回 None"
    print("  ✅ 不存在文件的处理正确")
    
    print("  ✅ 时长检测方法测试完成")

def main():
    """运行所有测试"""
    print("🎬 视频时长过滤功能测试")
    print("=" * 50)
    
    try:
        test_video_duration_filtering()
        test_duration_detection_methods()
        
        print("\n🎉 所有测试都通过了！")
        print("\n📋 功能总结:")
        print("- ✅ 视频时长检测功能正常")
        print("- ✅ 超过10分钟的视频被正确过滤")
        print("- ✅ 符合时长要求的视频正常收集")
        print("- ✅ 异常情况处理正确")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
