import os
import json
import subprocess
from typing import List
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips, TextClip, CompositeVideoClip, ColorClip
from .Card import ReductCard
from .tts_service import TTSService
import logging

logger = logging.getLogger(__name__)

class VideoComposer:
    """视频合成器：将下载的演示视频与解说词卡片合成为最终视频"""
    
    def __init__(self):
        self.tts_service = TTSService()
    
    def compose_paper_video(self, paper_dir: str, external_id: str) -> str:
        """
        为单个论文合成完整视频
        
        Args:
            paper_dir: 论文目录路径 (包含下载的视频文件和卡片)
            external_id: 论文的external_id
            
        Returns:
            str: 生成的视频文件路径
        """
        try:
            logger.info(f"开始为论文 {external_id} 合成视频")
            
            # 1. 加载解说卡片
            card_path = os.path.join(paper_dir, f"{external_id}.json")
            if not os.path.exists(card_path):
                raise FileNotFoundError(f"未找到解说卡片文件: {card_path}")
            
            card = self._load_card_from_json(card_path)
            
            # 2. 收集所有演示视频文件
            video_files = self._collect_video_files(paper_dir)
            if not video_files:
                logger.warning(f"论文 {external_id} 没有找到演示视频文件")
                return ""
            
            # 3. 合并演示视频
            demo_video_path = self._merge_demo_videos(video_files, paper_dir, external_id)
            
            # 4. 生成解说语音
            narration_audio_path = self._generate_narration_audio(card, paper_dir)
            
            # 5. 合成最终视频（演示视频 + 解说语音 + 字幕）
            final_video_path = self._compose_final_video(
                demo_video_path, narration_audio_path, card, paper_dir, external_id
            )
            
            logger.info(f"成功为论文 {external_id} 生成合成视频: {final_video_path}")
            return final_video_path
            
        except Exception as e:
            logger.error(f"合成论文 {external_id} 视频失败: {str(e)}")
            return ""
    
    def _load_card_from_json(self, card_path: str) -> ReductCard:
        """从JSON文件加载解说卡片"""
        with open(card_path, 'r', encoding='utf-8') as f:
            card_data = json.load(f)
        
        return ReductCard(
            arXivID=card_data.get('arXivID', 'Unknown'),
            info_CN=card_data.get('info_CN', []),
            info_EN=card_data.get('info_EN', [])
        )
    
    def _collect_video_files(self, paper_dir: str) -> List[str]:
        """收集目录中的所有视频文件"""
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
        video_files = []
        
        for file in os.listdir(paper_dir):
            if any(file.lower().endswith(ext) for ext in video_extensions):
                # 排除已生成的结果文件
                if not (file.endswith('_res.mp4') or file.endswith('_demo.mp4')):
                    video_files.append(os.path.join(paper_dir, file))
        
        # 按文件名排序确保顺序一致
        video_files.sort()
        return video_files
    
    def _merge_demo_videos(self, video_files: List[str], output_dir: str, external_id: str) -> str:
        """合并多个演示视频为一个，使用FFmpeg直接处理，保持16:9比例"""
        demo_video_path = os.path.join(output_dir, f"{external_id}_demo.mp4")
        
        try:
            logger.info(f"使用FFmpeg合并 {len(video_files)} 个演示视频并清除原音频，保持16:9比例")
            
            # 创建文件列表
            list_file = os.path.join(output_dir, "video_list.txt")
            with open(list_file, 'w', encoding='utf-8') as f:
                for video_file in video_files:
                    # 使用相对路径避免路径问题
                    rel_path = os.path.relpath(video_file, output_dir)
                    f.write(f"file '{rel_path}'\n")
            
            # 使用FFmpeg合并视频，去除音频，并设置16:9比例
            ffmpeg_cmd = [
                "ffmpeg",
                "-f", "concat",
                "-safe", "0",
                "-i", list_file,
                "-c:v", "libx264",  # 重新编码视频
                "-an",  # 去除音频
                "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black",  # 16:9比例，黑边填充
                "-preset", "medium",
                "-crf", "23",
                demo_video_path,
                "-y"
            ]
            
            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"FFmpeg合并视频失败: {result.stderr}")
            
            logger.info(f"成功使用FFmpeg合并视频: {demo_video_path}")
            return demo_video_path
            
        except Exception as e:
            logger.error(f"合并演示视频失败: {str(e)}")
            raise
    
    def _generate_narration_audio(self, card: ReductCard, output_dir: str) -> str:
        """生成解说语音"""
        try:
            logger.info(f"为论文 {card.arXivID} 生成解说语音")
            
            # 创建音频输出目录
            audio_dir = os.path.join(output_dir, "audio")
            os.makedirs(audio_dir, exist_ok=True)
            
            # 生成语音片段
            audio_segments = self.tts_service.generate_speech_segments(card.info_CN, audio_dir)
            
            # 合并音频片段
            final_audio_path = os.path.join(audio_dir, "narration.wav")
            self._concatenate_audio_segments(audio_segments, final_audio_path, audio_dir)
            
            return final_audio_path
            
        except Exception as e:
            logger.error(f"生成解说语音失败: {str(e)}")
            raise
    
    def _concatenate_audio_segments(self, segment_paths: List[str], output_path: str, work_dir: str):
        """使用FFmpeg合并音频片段"""
        try:
            # 创建文件列表
            list_file = os.path.join(work_dir, "audio_list.txt")
            with open(list_file, 'w', encoding='utf-8') as f:
                for path in segment_paths:
                    # 使用相对路径避免路径问题
                    rel_path = os.path.relpath(path, work_dir)
                    f.write(f"file '{rel_path}'\n")
            
            # 使用FFmpeg合并
            ffmpeg_cmd = [
                "ffmpeg",
                "-f", "concat",
                "-safe", "0",
                "-i", list_file,
                "-c", "copy",
                output_path,
                "-y"
            ]
            
            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"FFmpeg合并音频失败: {result.stderr}")
            
        except Exception as e:
            logger.error(f"合并音频片段失败: {str(e)}")
            raise
    
    def _compose_final_video(self, demo_video_path: str, narration_audio_path: str, 
                           card: ReductCard, output_dir: str, external_id: str) -> str:
        """合成最终视频（演示视频 + 解说语音 + 字幕）"""
        try:
            logger.info(f"合成最终视频 {external_id}")
            
            # 加载演示视频和解说音频
            demo_video = VideoFileClip(demo_video_path)
            narration_audio = AudioFileClip(narration_audio_path)
            
            logger.info(f"演示视频时长: {demo_video.duration:.2f}秒, 解说音频时长: {narration_audio.duration:.2f}秒")
            
            # 确定最终视频时长：以较长的时长为准
            final_duration = max(demo_video.duration, narration_audio.duration)
            
            # 如果演示视频较短，循环播放
            if demo_video.duration < final_duration:
                loops_needed = int(final_duration / demo_video.duration) + 1
                logger.info(f"演示视频需要循环 {loops_needed} 次以匹配时长")
                demo_video = concatenate_videoclips([demo_video] * loops_needed)
            
            # 截取到最终时长
            demo_video = demo_video.subclip(0, final_duration)
            
            # 如果解说音频较短，添加静音
            if narration_audio.duration < final_duration:
                from moviepy.editor import concatenate_audioclips, AudioClip
                silence_duration = final_duration - narration_audio.duration
                logger.info(f"添加 {silence_duration:.2f} 秒静音以匹配视频时长")
                
                # 创建静音片段
                silence = AudioClip(lambda t: [0, 0], duration=silence_duration)
                narration_audio = concatenate_audioclips([narration_audio, silence])
            
            # 添加解说音频到视频
            final_video = demo_video.set_audio(narration_audio)
            
            # 添加字幕
            final_video = self._add_subtitles(final_video, card)
            
            # 输出最终视频
            output_path = os.path.join(output_dir, f"{external_id}_res.mp4")
            final_video.write_videofile(
                output_path,
                fps=24,
                codec="libx264",
                audio_codec="aac",
                preset="medium",
                bitrate="5000k",
                audio_bitrate="192k"
            )
            
            # 清理临时对象
            demo_video.close()
            narration_audio.close()
            final_video.close()
            
            logger.info(f"最终视频时长: {final_duration:.2f}秒")
            return output_path
            
        except Exception as e:
            logger.error(f"合成最终视频失败: {str(e)}")
            raise
    
    def _add_subtitles(self, video: VideoFileClip, card: ReductCard) -> CompositeVideoClip:
        """为视频添加字幕"""
        try:
            # 简化字幕处理：暂时跳过字幕，直接返回原视频
            logger.info("字幕功能暂时跳过（需要安装ImageMagick）")
            return video
            
            # 以下代码为完整字幕功能，需要ImageMagick支持
            # 计算每个句子的时长
            total_duration = video.duration
            sentences = card.info_CN
            sentence_duration = total_duration / len(sentences) if sentences else total_duration
            
            subtitle_clips = []
            
            for i, sentence in enumerate(sentences):
                start_time = i * sentence_duration
                end_time = (i + 1) * sentence_duration
                
                # 处理长句子，自动换行
                formatted_sentence = self._format_subtitle_text(sentence)
                
                # 创建字幕文本
                text_clip = TextClip(
                    formatted_sentence,
                    fontsize=40,
                    color='white',
                    font='SimHei',
                    align='center',
                    stroke_color='black',
                    stroke_width=2
                )
                
                # 创建半透明背景
                bg_clip = ColorClip(
                    size=(text_clip.w + 20, text_clip.h + 10),
                    color=(0, 0, 0),
                    ismask=False
                ).set_opacity(0.7)
                
                # 合并背景和文字
                subtitle_clip = CompositeVideoClip([bg_clip, text_clip])
                
                # 设置位置和时间
                subtitle_clip = subtitle_clip.set_position(('center', 'bottom')).set_start(start_time).set_end(end_time)
                subtitle_clips.append(subtitle_clip)
            
            # 将字幕添加到视频
            return CompositeVideoClip([video] + subtitle_clips)
            
        except Exception as e:
            logger.error(f"添加字幕失败: {str(e)}")
            return video
    
    def _format_subtitle_text(self, text: str, max_chars_per_line: int = 20) -> str:
        """格式化字幕文本，自动换行"""
        if len(text) <= max_chars_per_line:
            return text
        
        # 简单的换行逻辑
        lines = []
        current_line = ""
        
        for char in text:
            current_line += char
            if len(current_line) >= max_chars_per_line:
                lines.append(current_line)
                current_line = ""
        
        if current_line:
            lines.append(current_line)
        
        return '\n'.join(lines)
