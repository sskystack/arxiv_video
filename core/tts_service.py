import time
import requests
import json
import os
import re
from typing import List
import logging
from pydub import AudioSegment

logger = logging.getLogger(__name__)

class TTSService:
    """语音合成服务，基于MiniMax API"""
    
    def __init__(self):
        self.group_id = "1887488082316366180"
        self.api_key = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJHcm91cE5hbWUiOiLmtbfonrrnlKjmiLdfMzQ0NDM4MjQxMTMwMTE5MTczIiwiVXNlck5hbWUiOiLmtbfonrrnlKjmiLdfMzQ0NDM4MjQxMTMwMTE5MTczIiwiQWNjb3VudCI6IiIsIlN1YmplY3RJRCI6IjE4ODc0ODgwODIzMjg5NDkwOTIiLCJQaG9uZSI6IjE1ODUwNTI2MDg5IiwiR3JvdXBJRCI6IjE4ODc0ODgwODIzMTYzNjYxODAiLCJQYWdlTmFtZSI6IiIsIk1haWwiOiIiLCJDcmVhdGVUaW1lIjoiMjAyNS0wMi0wOCAwOToxNToxMCIsIlRva2VuVHlwZSI6MSwiaXNzIjoibWluaW1heCJ9.Rq5HQYxEljZaTceSWJaKx_36n9-8k8XtvpCkNWvumwGA5PAaRtnnMDCWEfSq5NKrS6scnckRW_0SSuwQPhyJuRIEImNrCH4AhytrMimFsPGNxY5ljI6Rf6tewxq5K4VYyi0o4wx-jSjb70mU-Ki4nUmw4RNp2bdUE_JT0kGXqADnPwc2375OIuByxyFUjT0ziKSYEEnO27uXiQsRtvesFFNY2jOQyuEwZK_VAEk_EQ6oERydz-W5jhvRJmghkxHUxINiYssP0cHrfO6lI26s1JhM2pOnnNCvErGOy0ZujsNgqdYSnu1Anw0ae60uN_XEFKSHRZCydzi1mtd4KXmLPg"
        self.url = f"https://api.minimax.chat/v1/t2a_v2?GroupId={self.group_id}"
        
        # 语音引擎配置
        self.voice_configs = {
            'chinese': {
                'voice_id': 'Chinese (Mandarin)_Gentleman',
                'speed': 1.0,
                'vol': 1,
                'pitch': 0,
                'emotion': 'happy'
            },
            'english': {
                # MiniMax可能不支持英文语音，暂时使用中文语音处理英文
                # 后续可以考虑集成其他TTS服务（如Azure TTS）处理英文
                'voice_id': 'Chinese (Mandarin)_Gentleman',
                'speed': 0.9,  # 稍微慢一点，让英文发音更清楚
                'vol': 1,
                'pitch': 0,
                'emotion': 'neutral'
            }
        }
    
    def generate_speech_segments(self, sentences: List[str], output_dir: str) -> List[str]:
        """
        为句子列表生成语音片段
        
        Args:
            sentences: 句子列表
            output_dir: 输出目录
            
        Returns:
            List[str]: 生成的音频文件路径列表
        """
        audio_paths = []
        silence_dir = os.path.join(output_dir, "with_silence")
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(silence_dir, exist_ok=True)
        
        for i, sentence in enumerate(sentences):
            try:
                logger.info(f"正在生成第 {i+1}/{len(sentences)} 句语音: {sentence[:30]}...")
                
                # 生成原始音频
                raw_audio_path = os.path.join(output_dir, f"sentence_{i}.mp3")
                self._generate_single_audio(sentence, raw_audio_path)
                
                # 添加静音间隔
                final_audio_path = os.path.join(silence_dir, f"sentence_{i}.mp3")
                silence_duration = 0.8 if i == len(sentences) - 1 else 0.005  # 最后一句加长静音
                self._add_silence(raw_audio_path, final_audio_path, silence_duration)
                
                audio_paths.append(final_audio_path)
                
            except Exception as e:
                logger.error(f"生成第 {i+1} 句语音失败: {str(e)}")
                raise
        
        logger.info(f"成功生成 {len(audio_paths)} 个语音片段")
        return audio_paths
    
    def _detect_language(self, text: str) -> str:
        """
        检测文本的主要语言
        
        Args:
            text: 待检测的文本
            
        Returns:
            str: 'chinese' 或 'english'
        """
        # 移除标点符号和空格
        clean_text = re.sub(r'[^\w\u4e00-\u9fff]', '', text)
        
        if not clean_text:
            return 'chinese'  # 默认返回中文
        
        # 统计中文字符数量
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', clean_text))
        # 统计英文字符数量
        english_chars = len(re.findall(r'[a-zA-Z]', clean_text))
        
        total_chars = chinese_chars + english_chars
        if total_chars == 0:
            return 'chinese'
        
        # 如果中文字符占比超过30%，认为是中文
        if chinese_chars / total_chars > 0.3:
            logger.debug(f"检测为中文: 中文{chinese_chars}字符, 英文{english_chars}字符, 文本: {text[:50]}...")
            return 'chinese'
        else:
            logger.debug(f"检测为英文: 中文{chinese_chars}字符, 英文{english_chars}字符, 文本: {text[:50]}...")
            return 'english'
    
    def _generate_single_audio(self, text: str, output_path: str):
        """使用MiniMax API生成单个音频文件，自动检测语言并选择合适的语音引擎"""
        
        # 检测语言并选择语音配置
        language = self._detect_language(text)
        voice_config = self.voice_configs[language]
        
        logger.info(f"文本语言检测: {language}, 使用语音: {voice_config['voice_id']}")
        
        payload = json.dumps({
            "model": "speech-01-turbo",
            "text": text,
            "stream": False,
            "voice_setting": voice_config,
            "pronunciation_dict": {
                "tone": [
                    "处理/(chu4)(li3)",
                    "重识别/(chong2)(shi2)(bie2)",
                    "框架/(kuang1)(jia4)"
                ]
            } if language == 'chinese' else {},  # 只为中文文本添加发音字典
            "audio_setting": {
                "sample_rate": 32000,
                "bitrate": 128000,
                "format": "mp3",
                "channel": 1
            }
        })
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(self.url, headers=headers, data=payload, stream=True)
                logger.debug(f"API响应状态码: {response.status_code}")
                
                if response.status_code == 200:
                    parsed_json = response.json()
                    data_value = parsed_json.get('data')
                    
                    if data_value and 'audio' in data_value:
                        audio_bytes = bytes.fromhex(data_value['audio'])
                        with open(output_path, 'wb') as f:
                            f.write(audio_bytes)
                        return
                    else:
                        logger.warning(f"API响应中缺少audio数据: {parsed_json}")
                else:
                    logger.warning(f"API请求失败，状态码: {response.status_code}")
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"第 {attempt + 1} 次请求失败: {str(e)}")
            except json.JSONDecodeError as e:
                logger.warning(f"JSON解析失败: {str(e)}")
            
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2  # 递增等待时间
                logger.info(f"等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
        
        raise Exception(f"生成语音失败，已重试 {max_retries} 次")
    
    def _add_silence(self, input_path: str, output_path: str, duration: float):
        """在音频末尾添加静音"""
        try:
            # 加载原始音频
            audio = AudioSegment.from_mp3(input_path)
            
            # 创建静音片段
            silence = AudioSegment.silent(duration=int(duration * 1000))  # 转换为毫秒
            
            # 合并音频和静音
            audio_with_silence = audio + silence
            
            # 导出
            audio_with_silence.export(output_path, format="mp3", codec="libmp3lame")
            
        except Exception as e:
            logger.error(f"添加静音失败: {str(e)}")
            # 如果添加静音失败，直接复制原文件
            import shutil
            shutil.copy2(input_path, output_path)
