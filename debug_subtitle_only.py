#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化字幕测试 - 只生成字幕视频
"""

from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, ColorClip
import json

def create_subtitle_only_video():
    """创建仅有字幕的测试视频"""
    
    # 读取卡片数据
    with open('/tmp/test_final_subtitle/20250820/2508.14037/2508.14037v1.json', 'r', encoding='utf-8') as f:
        card_data = json.load(f)
    
    sentences = card_data['info_CN']
    print(f"处理 {len(sentences)} 个句子")
    
    # 加载原视频
    demo_video = VideoFileClip('/tmp/test_final_subtitle/20250820/2508.14037/2508.14037v1_demo.mp4')
    print(f"视频尺寸: {demo_video.w}x{demo_video.h}")
    
    # 音频时长
    audio_durations = [6.228, 3.456, 8.928, 4.248, 7.92, 2.196, 1.908, 15.948, 1.8, 2.52]
    
    subtitle_clips = []
    start_time = 0
    
    for i, (sentence, seg_time) in enumerate(zip(sentences[:3], audio_durations[:3])):  # 只测试前3个
        end_time = start_time + seg_time
        
        print(f"\\n处理句子 {i+1}: {sentence}")
        
        # 换行处理
        def devideSentence(text: str) -> str:
            res = ''
            for j, ch in enumerate(text):
                res += ch
                if j % 16 == 15:
                    res += '\\n'
            if res.endswith('\\n'):
                res = res[:-1]
            return res
        
        formatted_sentence = devideSentence(sentence)
        print(f"格式化后: {repr(formatted_sentence)}")
        
        # 创建字幕
        try:
            text_clip = TextClip(
                formatted_sentence,
                fontsize=50,
                color='black',
                font="SimHei",
                align='center'
            )
            print(f"文本剪辑创建成功: {text_clip.w}x{text_clip.h}")
            
            # 创建背景
            bgcolor_clip = ColorClip(
                size=text_clip.size,
                color=(250, 250, 210, 200),
                ismask=False
            )
            print(f"背景剪辑创建成功: {bgcolor_clip.w}x{bgcolor_clip.h}")
            
            # 合成
            subtitle_clip = CompositeVideoClip([bgcolor_clip, text_clip])
            print(f"合成剪辑创建成功: {subtitle_clip.w}x{subtitle_clip.h}")
            
            # 设置时间和位置
            subtitle_y = int(0.8 * demo_video.h)
            subtitle_clip = subtitle_clip.set_position(('center', subtitle_y))
            subtitle_clip = subtitle_clip.set_start(start_time).set_end(end_time)
            
            subtitle_clips.append(subtitle_clip)
            print(f"字幕 {i+1} 添加成功，位置: center, {subtitle_y}")
            
        except Exception as e:
            print(f"字幕 {i+1} 创建失败: {e}")
            import traceback
            traceback.print_exc()
        
        start_time += seg_time
    
    # 合成最终视频
    print(f"\\n开始合成最终视频，字幕数量: {len(subtitle_clips)}")
    
    try:
        # 截取前20秒用于测试
        short_video = demo_video.subclip(0, min(20, demo_video.duration))
        final_video = CompositeVideoClip([short_video] + subtitle_clips)
        
        output_path = "/tmp/debug_subtitle_only.mp4"
        final_video.write_videofile(
            output_path,
            fps=24,
            codec="libx264",
            verbose=False,
            logger=None
        )
        
        print(f"\\n✅ 测试视频生成成功: {output_path}")
        
        # 清理
        demo_video.close()
        final_video.close()
        for clip in subtitle_clips:
            clip.close()
            
    except Exception as e:
        print(f"\\n❌ 视频合成失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_subtitle_only_video()
