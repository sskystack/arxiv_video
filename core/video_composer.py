import os
import json
import subprocess
import logging
import platform
from typing import List
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips, TextClip, CompositeVideoClip, ColorClip
from .Card import ReductCard
from .tts_service import TTSService

logger = logging.getLogger(__name__)


class VideoComposer:
    """视频合成器 - 负责合成演示视频、解说语音和字幕"""
    
    def __init__(self):
        """初始化视频合成器"""
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
        """收集目录中的所有视频文件，优先使用主视频"""
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
        video_files = []
        primary_video = None
        
        for file in os.listdir(paper_dir):
            if any(file.lower().endswith(ext) for ext in video_extensions):
                # 排除已生成的结果文件
                if not (file.endswith('_res.mp4') or file.endswith('_demo.mp4')):
                    full_path = os.path.join(paper_dir, file)
                    
                    # 检查是否为主视频
                    if file.startswith('primary_video'):
                        primary_video = full_path
                        logger.info(f"找到主视频: {file}")
                    else:
                        video_files.append(full_path)
        
        # 如果有主视频，优先使用主视频
        if primary_video:
            return [primary_video]
        
        # 否则按文件名排序确保顺序一致
        video_files.sort()
        return video_files
    
    def _merge_demo_videos(self, video_files: List[str], output_dir: str, external_id: str) -> str:
        """合并多个演示视频为一个，使用FFmpeg直接处理，保持16:9比例"""
        demo_video_path = os.path.join(output_dir, f"{external_id}_demo.mp4")
        
        try:
            if len(video_files) == 1:
                # 如果只有一个视频文件，直接处理这个文件
                logger.info(f"只有一个演示视频，直接处理并清除原音频，保持16:9比例")
                single_video = video_files[0]
                
                # 使用FFmpeg处理单个视频，去除音频，并设置16:9比例
                ffmpeg_cmd = [
                    "ffmpeg",
                    "-i", single_video,
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
                    raise Exception(f"FFmpeg处理单个视频失败: {result.stderr}")
                
                logger.info(f"成功使用FFmpeg处理单个视频: {demo_video_path}")
                return demo_video_path
            
            else:
                # 多个视频文件的处理逻辑
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
            logger.error(f"处理演示视频失败: {str(e)}")
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
            
            # 🎯 正确逻辑：保持演示视频的原始时长，不做任何修改
            logger.info(f"保持演示视频原始时长: {demo_video.duration:.2f}秒")
            
            # 直接将音频叠加到视频上，不修改视频时长
            final_video = demo_video.set_audio(narration_audio)
            
            # 添加字幕（字幕完全基于音频时长，与视频时长无关）
            logger.info("🎬 准备添加字幕...")
            final_video = self._add_subtitles(final_video, card, output_dir)
            logger.info("🎬 字幕添加流程完成")
            
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
            
            logger.info(f"最终视频时长: {demo_video.duration:.2f}秒 (保持原始演示视频时长)")
            return output_path
            
        except Exception as e:
            logger.error(f"合成最终视频失败: {str(e)}")
            raise
    
    def _add_subtitles(self, video: VideoFileClip, card: ReductCard, paper_dir: str) -> CompositeVideoClip:
        """为视频添加字幕 - 修复版本，正确处理音频片段与句子的映射关系"""
        try:
            sentences = card.info_CN
            logger.info(f"🎬 开始添加字幕，共 {len(sentences) if sentences else 0} 条句子")
            
            if not sentences:
                logger.warning("❌ 没有中文解说内容，跳过字幕添加")
                return video
            
            # 打印所有句子内容
            for i, sentence in enumerate(sentences):
                logger.info(f"📝 句子 {i+1}: '{sentence}'")
            
            # 获取音频片段的实际时长信息
            audio_durations = self._get_audio_segment_durations(paper_dir)
            
            if not audio_durations:
                # 🎯 关键修复：字幕时长应该完全基于音频，与视频无关！
                logger.error(f"❌ 无法获取音频时长信息，字幕生成失败")
                logger.error(f"❌ 字幕必须严格基于音频时长，不能使用视频时长")
                return video  # 返回原视频，不添加字幕
            else:
                logger.info(f"🎵 获取到音频时长信息: {[f'{d:.1f}s' for d in audio_durations]}")
                
                # 关键修复：检查音频片段是否比句子多（由于句子被拆分）
                if len(audio_durations) > len(sentences):
                    logger.info(f"🔧 检测到音频片段({len(audio_durations)})比句子({len(sentences)})多，进行智能合并")
                    
                    # 计算每个句子应该对应多少个音频片段
                    sentence_audio_groups = self._group_audio_segments_to_sentences(sentences, audio_durations)
                    logger.info(f"🎯 音频片段分组结果: {sentence_audio_groups}")
                    
                    # 重新计算每个句子的总时长
                    new_audio_durations = []
                    audio_index = 0
                    for group_count in sentence_audio_groups:
                        sentence_duration = sum(audio_durations[audio_index:audio_index + group_count])
                        new_audio_durations.append(sentence_duration)
                        audio_index += group_count
                    
                    audio_durations = new_audio_durations
                    logger.info(f"🎵 重新计算后的句子时长: {[f'{d:.1f}s' for d in audio_durations]}")
                
                # 🎯 字幕时长完全基于音频，无需与视频时长比较或调整
                total_audio_duration = sum(audio_durations)
                logger.info(f"🎵 音频总时长: {total_audio_duration:.2f}秒，字幕将严格按此时长设置")
            
            # 字幕生成逻辑 - 只处理有对应音频的句子
            subtitle_clips = []
            start_time = 0
            
            # 只为有对应音频时长的句子生成字幕
            effective_sentences = min(len(sentences), len(audio_durations))
            if effective_sentences < len(sentences):
                logger.warning(f"⚠️ 只有 {effective_sentences} 个音频片段，将跳过后面的 {len(sentences) - effective_sentences} 个句子")
            
            for i in range(effective_sentences):
                sentence = sentences[i]
                seg_time = audio_durations[i]
                end_time = start_time + seg_time
                
                logger.info(f"🎬 添加字幕 {i+1}/{effective_sentences}: '{sentence}' ({start_time:.1f}s - {end_time:.1f}s, 时长:{seg_time:.1f}s)")
                
                # 使用中文换行函数
                formatted_sentence = self._devideSentence(sentence)
                
                # 创建字幕文本 - 使用本地字体路径确保中文显示正常
                try:
                    # 优先使用STHeiti字体路径
                    text_clip = TextClip(
                        formatted_sentence,
                        fontsize=50,
                        color='black',
                        font="/System/Library/Fonts/STHeiti Light.ttc",
                        align='center'
                    )
                    logger.debug(f"成功使用STHeiti字体路径创建字幕")
                except Exception as font_error:
                    logger.warning(f"使用STHeiti字体路径失败: {font_error}，尝试Arial Unicode")
                    try:
                        # 回退到Arial Unicode字体路径
                        text_clip = TextClip(
                            formatted_sentence,
                            fontsize=50,
                            color='black',
                            font="/Library/Fonts/Arial Unicode.ttf",
                            align='center'
                        )
                        logger.debug(f"成功使用Arial Unicode字体路径创建字幕")
                    except Exception as fallback_error:
                        logger.warning(f"使用Arial Unicode字体路径失败: {fallback_error}，使用默认字体")
                        # 最后回退到默认字体
                        text_clip = TextClip(
                            formatted_sentence,
                            fontsize=50,
                            color='black',
                            align='center'
                        )
                        logger.debug(f"使用默认字体创建字幕")
                
                # 创建背景
                bgcolor_clip = ColorClip(
                    size=text_clip.size,
                    color=(250, 250, 210, 200),  # 淡黄色背景
                    ismask=False
                )
                
                # 合并文本和背景
                text_clip = CompositeVideoClip([bgcolor_clip, text_clip])
                
                # 设置位置和时间
                text_clip = text_clip.set_position(('center', 0.8 * video.h))
                text_clip = text_clip.set_start(start_time).set_end(end_time)
                
                subtitle_clips.append(text_clip)
                start_time += seg_time
            
            # 将字幕添加到视频
            logger.info(f"✅ 成功创建 {len(subtitle_clips)} 个字幕片段，总时长: {start_time:.1f}秒")
            final_video = CompositeVideoClip([video] + subtitle_clips)
            logger.info("🎬 字幕合成完成")
            return final_video
            
        except Exception as e:
            logger.error(f"❌ 添加字幕失败: {str(e)}")
            logger.exception("详细错误信息:")
            return video
    
    def _devideSentence(self, text: str) -> str:
        """中文换行函数 - 按16字符换行"""
        # 只处理中文，使用原来的16字符换行逻辑
        res = ''
        for i, ch in enumerate(text):
            res += ch
            if i % 16 == 15:
                res += '\n'
        if res.endswith('\n'):
            res = res[:-1]
        return res
    
    def _format_subtitle_text(self, text: str, max_chars_per_line: int = 16) -> str:
        """格式化字幕文本，自动换行（参考代码样式）"""
        if len(text) <= max_chars_per_line:
            return text
        
        # 使用参考代码的换行逻辑
        result = ''
        for i, char in enumerate(text):
            result += char
            if i % max_chars_per_line == max_chars_per_line - 1:
                result += '\n'
        
        # 移除末尾的换行符
        if result.endswith('\n'):
            result = result[:-1]
            
        return result
    
    def _get_audio_segment_durations(self, paper_dir: str) -> List[float]:
        """获取音频片段的时长信息 - 改进版本，提高健壮性"""
        try:
            durations = []
            
            audio_dir = os.path.join(paper_dir, "audio")
            
            # 检查此唯一路径是否存在
            if not os.path.exists(audio_dir) or not os.path.isdir(audio_dir):
                logger.warning(f"在预期的路径中未找到音频目录: {audio_dir}")
                logger.warning(f"请检查TTS服务是否成功生成了位于该目录的音频文件.")
                return []
            
            logger.info(f"使用明确的路径查找音频: {audio_dir}")
            
            # 获取所有音频文件的时长
            i = 0
            failed_count = 0
            max_consecutive_failures = 3  # 允许连续失败的最大次数
            
            while True:
                audio_file = os.path.join(audio_dir, f"sentence_{i}.mp3")
                if not os.path.exists(audio_file):
                    logger.info(f"音频文件 sentence_{i}.mp3 不存在，停止检测")
                    break
                
                # 使用ffprobe获取音频时长
                try:
                    cmd = [
                        "ffprobe", "-v", "quiet", 
                        "-show_entries", "format=duration", 
                        "-of", "csv=p=0", 
                        audio_file
                    ]
                    
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                    if result.returncode == 0 and result.stdout.strip():
                        duration = float(result.stdout.strip())
                        durations.append(duration)
                        failed_count = 0  # 重置失败计数
                        logger.info(f"音频文件 {audio_file} 时长: {duration:.2f}秒")
                    else:
                        failed_count += 1
                        logger.warning(f"无法获取音频文件 {audio_file} 的时长: {result.stderr}")
                        if failed_count >= max_consecutive_failures:
                            logger.error(f"连续 {max_consecutive_failures} 次获取音频时长失败，停止处理")
                            break
                        # 对于失败的文件，使用平均时长或默认时长
                        default_duration = 3.0 if not durations else sum(durations) / len(durations)
                        durations.append(default_duration)
                        
                except Exception as e:
                    failed_count += 1
                    logger.warning(f"处理音频文件 {audio_file} 时出错: {str(e)}")
                    if failed_count >= max_consecutive_failures:
                        logger.error(f"连续 {max_consecutive_failures} 次处理失败，停止处理")
                        break
                    # 使用默认时长
                    default_duration = 3.0 if not durations else sum(durations) / len(durations)
                    durations.append(default_duration)
                
                i += 1
                
                # 防止无限循环
                if i > 100:  # 假设最多100个音频片段
                    logger.warning(f"音频片段数量超过100个，停止检测")
                    break
            
            if durations:
                total_duration = sum(durations)
                logger.info(f"成功获取 {len(durations)} 个音频片段的时长，总时长: {total_duration:.2f}秒")
                logger.debug(f"各片段时长: {[f'{d:.2f}s' for d in durations]}")
            else:
                logger.warning(f"未能获取任何音频片段的时长信息")
            
            return durations
            
        except Exception as e:
            logger.error(f"获取音频片段时长失败: {str(e)}")
            return []

    def _group_audio_segments_to_sentences(self, sentences: List[str], audio_durations: List[float]) -> List[int]:
        """
        将音频片段智能分组到句子
        
        Args:
            sentences: 原始句子列表
            audio_durations: 音频片段时长列表
            
        Returns:
            List[int]: 每个句子对应的音频片段数量
        """
        try:
            # 导入分割函数
            from core.Card import splitSentence
            
            # 计算每个句子被拆分成多少个片段
            sentence_groups = []
            
            for sentence in sentences:
                # 使用相同的拆分逻辑来估算片段数
                sub_sentences = splitSentence(sentence)
                segment_count = len(sub_sentences)
                sentence_groups.append(segment_count)
                logger.debug(f"句子 '{sentence[:20]}...' 预计拆分为 {segment_count} 个片段: {sub_sentences}")
            
            # 验证总数是否匹配
            total_predicted = sum(sentence_groups)
            actual_segments = len(audio_durations)
            
            if total_predicted == actual_segments:
                logger.info(f"✅ 音频片段分组预测准确: {sentence_groups}")
                return sentence_groups
            
            # 如果预测不准确，使用简单的平均分配策略
            logger.warning(f"⚠️ 预测的片段数({total_predicted})与实际({actual_segments})不匹配，使用平均分配")
            
            segments_per_sentence = actual_segments // len(sentences)
            remainder = actual_segments % len(sentences)
            
            groups = [segments_per_sentence] * len(sentences)
            
            # 将余数分配给前几个句子
            for i in range(remainder):
                groups[i] += 1
            
            logger.info(f"🔧 使用平均分配策略: {groups}")
            return groups
            
        except Exception as e:
            logger.error(f"音频片段分组失败: {str(e)}")
            # 回退到简单平均分配
            segments_per_sentence = len(audio_durations) // len(sentences)
            remainder = len(audio_durations) % len(sentences)
            
            groups = [segments_per_sentence] * len(sentences)
            for i in range(remainder):
                groups[i] += 1
                
            return groups
