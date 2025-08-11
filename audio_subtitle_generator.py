"""
音频与字幕生成模块
"""
import asyncio
import edge_tts
from edge_tts import SubMaker
import os

def format_time(seconds):
    """将秒转换为 SRT 时间码格式 (HH:MM:SS,ms)"""
    millisec = int((seconds - int(seconds)) * 1000)
    seconds = int(seconds)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millisec:03d}"

async def _generate_tts_and_subs(script_text, audio_path, subtitle_path):
    """使用 edge-tts 生成音频和字幕的核心异步函数"""
    # 选择一个中文语音
    voice = "zh-CN-XiaoxiaoNeural"
    
    sub_maker = SubMaker()
    communicate = edge_tts.Communicate(script_text, voice)
    
    # 生成音频并保存
    with open(audio_path, "wb") as file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                sub_maker.create_sub((chunk["offset"], chunk["duration"]), chunk["text"])

    # 将字幕转换为 SRT 格式并保存
    with open(subtitle_path, "w", encoding="utf-8") as file:
        subs = sub_maker.generate_subs()
        for i, sub in enumerate(subs):
            start_time = format_time(sub[0] / 10000000)
            end_time = format_time(sub[1] / 10000000)
            text = sub[2]
            file.write(f"{i + 1}\n")
            file.write(f"{start_time} --> {end_time}\n")
            file.write(f"{text}\n\n")

def generate_audio_and_subtitles(script_text, output_audio_path, output_subtitle_path):
    """
    将解说词文本转换为语音和字幕文件。
    这是一个同步的包装器，方便在主流程中调用。

    :param script_text: 解说词文本。
    :param output_audio_path: 输出音频文件的路径 (e.g., 'output/audio/paper.mp3')。
    :param output_subtitle_path: 输出字幕文件的路径 (e.g., 'output/subtitles/paper.srt')。
    :return: 如果成功，返回 True，否则返回 False。
    """
    print(f"🎤 正在生成音频和字幕...")
    try:
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_audio_path), exist_ok=True)
        os.makedirs(os.path.dirname(output_subtitle_path), exist_ok=True)

        # 运行异步函数
        asyncio.run(_generate_tts_and_subs(script_text, output_audio_path, output_subtitle_path))
        
        print(f"✅ 音频文件已保存至: {output_audio_path}")
        print(f"✅ 字幕文件已保存至: {output_subtitle_path}")
        return True
    except Exception as e:
        print(f"❌ 生成音频和字幕时出错: {e}")
        return False
