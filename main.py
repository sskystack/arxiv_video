"""
运行 ArXiv 视频生成流程的主脚本。
"""
import os
import glob
import argparse
from collections import defaultdict

# 导入我们创建的模块
from video_merger import merge_videos_for_paper
from content_generator import get_paper_details, generate_commentary
from audio_subtitle_generator import generate_audio_and_subtitles
# 假设 VideoGenarate.py 中有最终合成的函数
# from VideoGenarate import generate_final_video

def setup_directories(input_dir, output_dir):
    """检查并创建输入/输出目录，如果输入目录为空则提供指导。"""
    # 如果输出目录不存在，则创建它
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"创建了输出目录: '{output_dir}'")

    # 为所有类型的输出创建子目录
    for dir_name in ["merged_videos", "scripts", "audio", "subtitles", "final_videos"]:
        path = os.path.join(output_dir, dir_name)
        if not os.path.exists(path):
            os.makedirs(path)
    
    # 检查输入目录
    if not os.path.exists(input_dir):
        os.makedirs(input_dir)
        print(f"创建了输入目录 '{input_dir}'。")
        # 创建一些空的占位文件用于演示
        open(os.path.join(input_dir, "2401.12345_clip1.mp4"), 'a').close()
        open(os.path.join(input_dir, "2401.12345_clip2.mp4"), 'a').close()
        open(os.path.join(input_dir, "2402.54321_main.mp4"), 'a').close()
        print("创建了一些空的示例文件用于演示，你需要用真实的视频文件替换它们。")

def main(args):
    """
    主函数，用于协调整个视频生成过程。
    """
    print("🚀 开始运行 ArXiv 视频生成流程...")

    # --- 准备工作: 设置目录 ---
    input_dir = args.input_dir
    output_dir = args.output_dir
    setup_directories(input_dir, output_dir)
    
    merged_videos_dir = os.path.join(output_dir, "merged_videos")
    scripts_dir = os.path.join(output_dir, "scripts")
    audio_dir = os.path.join(output_dir, "audio")
    subtitles_dir = os.path.join(output_dir, "subtitles")

    # --- 步骤 1: 扫描本地视频文件 ---
    print(f"\n--- 步骤 1: 扫描视频文件 ---")
    print(f"📂 从 '{input_dir}' 目录读取视频。")
    
    # 按论文ID对视频文件进行分组
    paper_videos = defaultdict(list)
    for video_path in glob.glob(os.path.join(input_dir, "*.mp4")):
        filename = os.path.basename(video_path)
        try:
            paper_id = filename.split('_')[0]
            paper_videos[paper_id].append(video_path)
        except IndexError:
            print(f"⚠️ 文件名 '{filename}' 不符合格式，已跳过。")

    if not paper_videos:
        print(f"❌ 在 '{input_dir}' 目录中没有找到符合格式的视频文件。流程终止。")
        return

    print(f"✅ 找到了 {len(paper_videos)} 篇论文的视频。")
    for paper_id, files in paper_videos.items():
        print(f"  - 论文 {paper_id}: {len(files)} 个视频片段")

    # --- 步骤 2: 合并视频片段 ---
    print("\n--- 步骤 2: 合并视频片段 ---")
    processed_videos = {}
    for paper_id, files in paper_videos.items():
        if len(files) > 1:
            # 有多个视频，需要合并
            merged_path = merge_videos_for_paper(paper_id, files, output_dir=merged_videos_dir)
            if merged_path:
                processed_videos[paper_id] = merged_path
        elif files:
            # 只有一个视频，无需合并，直接使用
            print(f"论文 {paper_id} 只有一个视频，无需合并。")
            processed_videos[paper_id] = files[0]

    if not processed_videos:
        print("❌ 没有可处理的视频。流程终止。")
        return
    
    print("✅ 视频合并（或整理）完成。")

    # --- 步骤 3: 为每篇论文生成解说词 ---
    print("\n--- 步骤 3: 内容生成 ---")
    generated_scripts = {}
    for paper_id, video_path in processed_videos.items():
        print(f"\n处理论文: {paper_id}")
        # 1. 获取论文信息
        paper_details = get_paper_details(paper_id)
        if not paper_details:
            continue # 获取失败，跳过这篇论文

        # 2. 生成解说词
        script_content = generate_commentary(paper_details)
        if not script_content:
            continue # 生成失败，跳过这篇论文
        
        # 3. 保存解说词到文件
        script_path = os.path.join(scripts_dir, f"{paper_id}_script.txt")
        try:
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)
            print(f"📝 解说词已保存至: {script_path}")
            generated_scripts[paper_id] = script_path
        except IOError as e:
            print(f"❌ 保存解说词文件时出错: {e}")

    print("✅ 内容生成步骤完成。")

    # --- 步骤 4: 音频和字幕生成 ---
    print("\n--- 步骤 4: 音频和字幕生成 ---")
    generated_media = {}
    for paper_id, script_path in generated_scripts.items():
        print(f"\n处理论文: {paper_id}")
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                script_text = f.read()
            
            audio_path = os.path.join(audio_dir, f"{paper_id}.mp3")
            subtitle_path = os.path.join(subtitles_dir, f"{paper_id}.srt")

            success = generate_audio_and_subtitles(script_text, audio_path, subtitle_path)
            
            if success:
                generated_media[paper_id] = {
                    "audio": audio_path,
                    "subtitle": subtitle_path
                }
        except FileNotFoundError:
            print(f"❌ 找不到脚本文件: {script_path}")
        except Exception as e:
            print(f"❌ 处理脚本 {script_path} 时发生未知错误: {e}")

    print("✅ 音频和字幕生成步骤完成。")

    # --- 步骤 5: 最终视频生成 (待实现) ---
    print("\n--- 步骤 5: 最终视频生成 (待实现) ---")
    # generate_final_video(processed_videos, generated_media)

    print("\n🎉 流程已结束。")

if __name__ == "__main__":
    # --- 设置命令行参数解析 ---
    parser = argparse.ArgumentParser(description="自动生成 ArXiv 论文讲解视频的流程。")
    parser.add_argument(
        '--input-dir', 
        type=str, 
        default='downloaded_videos', 
        help='存放原始视频片段的输入目录。'
    )
    parser.add_argument(
        '--output-dir', 
        type=str, 
        default='output', 
        help='存放所有输出文件（合并视频、脚本、最终视频等）的目录。'
    )
    
    args = parser.parse_args()
    main(args)
