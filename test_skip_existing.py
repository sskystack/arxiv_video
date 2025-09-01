#!/usr/bin/env python3
"""测试跳过已存在视频功能"""

import sys
import os
import tempfile
import shutil
sys.path.append('/Users/zhouzhongtian/vscode/paperfindvideo')

from core.crawler import ArxivVideoCrawler

def test_skip_existing_functionality():
    """测试跳过已存在视频的功能"""
    print("=== 测试跳过已存在视频功能 ===")
    
    # 创建临时目录进行测试
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"使用临时目录: {temp_dir}")
        
        # 测试数据
        arxiv_id = "2508.10774"
        target_date = "20250821"
        
        # 创建爬虫实例（启用跳过功能）
        crawler_skip = ArxivVideoCrawler(
            download_folder=temp_dir,
            max_workers=1,
            skip_existing=True
        )
        
        # 创建爬虫实例（不启用跳过功能）
        crawler_no_skip = ArxivVideoCrawler(
            download_folder=temp_dir,
            max_workers=1,
            skip_existing=False
        )
        
        # 测试1: 没有现有视频时的行为
        print("\n--- 测试1: 没有现有视频 ---")
        result_skip = crawler_skip._check_existing_res_video(arxiv_id, target_date)
        print(f"跳过检查结果 (无现有视频): {result_skip}")
        
        if not result_skip:
            print("✅ 正确：没有现有视频时返回False")
        else:
            print("❌ 错误：应该返回False")
        
        # 测试2: 创建模拟的res视频文件
        print("\n--- 测试2: 创建模拟视频文件 ---")
        paper_folder = os.path.join(temp_dir, target_date, arxiv_id)
        os.makedirs(paper_folder, exist_ok=True)
        res_video_path = os.path.join(paper_folder, f"{arxiv_id}_res.mp4")
        
        # 创建一个足够大的文件（模拟真实视频）
        with open(res_video_path, 'wb') as f:
            f.write(b'0' * 2048)  # 2KB的文件
        
        print(f"创建模拟视频文件: {res_video_path}")
        print(f"文件大小: {os.path.getsize(res_video_path)} 字节")
        
        # 测试3: 有现有视频时的行为
        print("\n--- 测试3: 有现有视频时的检查 ---")
        result_skip = crawler_skip._check_existing_res_video(arxiv_id, target_date)
        print(f"跳过检查结果 (有现有视频): {result_skip}")
        
        if result_skip:
            print("✅ 正确：有现有视频时返回True")
        else:
            print("❌ 错误：应该返回True")
        
        # 测试4: 测试太小的文件（可能损坏）
        print("\n--- 测试4: 测试损坏的小文件 ---")
        with open(res_video_path, 'wb') as f:
            f.write(b'0' * 100)  # 只有100字节，太小
        
        result_skip = crawler_skip._check_existing_res_video(arxiv_id, target_date)
        print(f"跳过检查结果 (小文件): {result_skip}")
        print(f"文件大小: {os.path.getsize(res_video_path)} 字节")
        
        if not result_skip:
            print("✅ 正确：太小的文件被认为无效，返回False")
        else:
            print("❌ 错误：小文件应该返回False")
        
        # 测试5: 验证skip_existing参数在初始化中的作用
        print("\n--- 测试5: 验证参数设置 ---")
        print(f"crawler_skip.skip_existing = {crawler_skip.skip_existing}")
        print(f"crawler_no_skip.skip_existing = {crawler_no_skip.skip_existing}")
        
        if crawler_skip.skip_existing and not crawler_no_skip.skip_existing:
            print("✅ 正确：skip_existing参数设置正确")
        else:
            print("❌ 错误：skip_existing参数设置有问题")
        
        print("\n✅ 跳过已存在视频功能测试完成")

if __name__ == "__main__":
    test_skip_existing_functionality()
