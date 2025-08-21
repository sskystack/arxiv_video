#!/usr/bin/env python3
"""
快速测试一个实际的视频生成流程，验证所有优化的效果
"""

import sys
import os
sys.path.append('/Users/zhouzhongtian/vscode/arxiv_video')

import logging
from core.video_composer import VideoComposer

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_real_video_generation():
    """使用一个简短的测试数据生成视频来验证所有优化"""
    
    # 创建简单的测试数据
    test_data = {
        'title': 'Test Video Generation - 测试视频生成',
        'abstract': 'This is a comprehensive test of our optimized subtitle system. 这是我们优化字幕系统的综合测试。',
        'info_CN': [
            '欢迎观看这个测试视频！',
            'This video demonstrates the improved subtitle positioning and text density optimization.',
            '我们的新字幕系统现在可以更好地利用背景框空间，减少不必要的换行，并且字幕会贴着视频底部显示。',
            'The subtitles should now appear at the bottom edge of the video with better text utilization.',
            '测试完成。'
        ]
    }
    
    # 创建临时的测试图片文件夹
    test_images_dir = '/Users/zhouzhongtian/vscode/arxiv_video/test_images'
    os.makedirs(test_images_dir, exist_ok=True)
    
    # 创建一些简单的测试图片（纯色图片）
    from PIL import Image, ImageDraw, ImageFont
    
    for i in range(len(test_data['info_CN'])):
        # 创建简单的彩色背景图片
        img = Image.new('RGB', (1280, 720), color=(40 + i*30, 80 + i*20, 120 + i*25))
        draw = ImageDraw.Draw(img)
        
        # 添加一些文本标识
        try:
            # 尝试添加文本（如果字体可用）
            draw.text((50, 50), f"Test Image {i+1}", fill='white')
        except:
            # 如果字体不可用，跳过文本
            pass
        
        img_path = os.path.join(test_images_dir, f'test_image_{i}.png')
        img.save(img_path)
        print(f"创建测试图片: {img_path}")
    
    print(f"\n开始生成测试视频...")
    
    try:
        composer = VideoComposer()
        
        # 生成测试视频
        output_path = '/Users/zhouzhongtian/vscode/arxiv_video/test_optimized_video.mp4'
        
        # 使用VideoComposer生成视频
        result = composer.create_video(
            title=test_data['title'],
            abstract=test_data['abstract'],
            info_list=test_data['info_CN'],
            images_folder=test_images_dir,
            output_path=output_path
        )
        
        if result:
            print(f"✅ 测试视频生成成功!")
            print(f"📹 输出路径: {output_path}")
            print(f"🎯 这个视频应该展示:")
            print(f"   - 字幕位于视频底部（距离底边20px）")
            print(f"   - 更高的文本密度（英文65字符/行，中文32字符/行）")
            print(f"   - 更紧凑的背景框（英文15%边距，中文20%边距）")
            print(f"   - 平均文本填充率约78%")
            
            # 检查文件是否真正创建
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
                print(f"📊 文件大小: {file_size:.1f} MB")
            else:
                print(f"❌ 警告: 输出文件未找到")
                
        else:
            print(f"❌ 测试视频生成失败")
            
    except Exception as e:
        print(f"❌ 生成过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理测试图片
        print(f"\n清理测试文件...")
        try:
            import shutil
            if os.path.exists(test_images_dir):
                shutil.rmtree(test_images_dir)
                print(f"✅ 已清理测试图片文件夹")
        except Exception as e:
            print(f"⚠️ 清理测试文件时出错: {e}")

if __name__ == "__main__":
    test_real_video_generation()
