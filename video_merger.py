"""
视频合并模块
"""
import os
from moviepy.editor import VideoFileClip, concatenate_videoclips

def merge_videos_for_paper(paper_id, video_files, output_dir="merged_videos"):
    """
    将属于同一篇论文的多个视频片段合并成一个视频。

    :param paper_id: 论文ID，用于命名合并后的视频。
    :param video_files: 视频文件路径列表。
    :param output_dir: 合并后视频的输出目录。
    :return: 合并后视频的路径，如果失败则返回 None。
    """
    if not video_files:
        print(f"论文 {paper_id} 没有找到可合并的视频。")
        return None

    print(f"正在为论文 {paper_id} 合并 {len(video_files)} 个视频...")

    try:
        # 创建输出目录
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 加载所有视频片段
        clips = [VideoFileClip(file) for file in video_files]

        # 合并视频
        final_clip = concatenate_videoclips(clips, method="compose")

        # 定义输出路径
        merged_video_path = os.path.join(output_dir, f"{paper_id}_merged.mp4")

        # 写入最终文件
        final_clip.write_videofile(merged_video_path, codec="libx264", audio_codec="aac")

        # 关闭所有片段
        for clip in clips:
            clip.close()
        final_clip.close()

        print(f"视频合并完成，输出到: {merged_video_path}")
        return merged_video_path

    except Exception as e:
        print(f"为论文 {paper_id} 合并视频时出错: {e}")
        # 确保在出错时也关闭可能已打开的片段
        if 'clips' in locals():
            for clip in clips:
                clip.close()
        if 'final_clip' in locals():
            final_clip.close()
        return None
