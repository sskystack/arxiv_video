import os.path

from moviepy.video.io.VideoFileClip import VideoFileClip
from Card import *
from miniMAXTTS import *
import subprocess
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, TextClip, CompositeVideoClip, concatenate_audioclips, ColorClip, VideoClip
# elevenlabs公司
# ali的cosyvoice 特别的慢
# f5-tts

def Genaratevideo(Cards : list[ReductCard], inputPath : str, outputPath, videoName: str = "null"):
    images = []
    for i,card in enumerate(Cards):
        # 对每幅图片进行tts
        path = f'{inputPath}/' + card.arXivID + '.png'
        curCard = ImageClip(path)

        # 这里的分辨率设置得是一个有限小数
        images.append(curCard.resize(height = int(2058*0.7)))
        # images.append(curCard)
        path_CN = f'{outputPath}/audio/' + card.arXivID + '_CN/'
        PathList = TextToSpeech(card.info_CN, path_CN)
        duration = []
        for ele in PathList:
            duration.append(AudioFileClip(ele).duration)
        finalAudioPath = path_CN + 'final_audio.wav'

        concatenate_segments(PathList, finalAudioPath, outputPath)
    
        audio = AudioFileClip(finalAudioPath)

        # 设置每张卡片的时间与音频
        images[-1] = images[-1].set_duration(sum(duration))
        images[-1] = images[-1].set_audio(audio)

        # 处理字幕
        startTime = 0
        subtitleClips = []
        for sentence,segTime in zip(card.info_CN, duration):
            sentence = devideSentence(sentence)
            endTime = startTime + segTime
            textClip = TextClip(sentence, fontsize=50, color='black', font="SimHei", align='center')

            # 创建一个带有所需背景颜色和透明度的 ColorClip这里使用 RGBA元组设置颜色和透明度
            bgcolor_clip = ColorClip(size=textClip.size, color=(250, 250, 210, 200), ismask=False)
            # 将文本剪辑和背景剪辑合并
            textClip = CompositeVideoClip([bgcolor_clip, textClip])

            textClip = textClip.set_position(('center', 0.8 * images[-1].size[1]))  # 字幕位置
            textClip = textClip.set_start(startTime).set_end(endTime)  # 设置显示时间
            subtitleClips.append(textClip)
            startTime += segTime

            # print(sentence)

        images[-1] = CompositeVideoClip([images[-1]] + subtitleClips)
        print(f'card duration : {images[-1].duration}')

    videoClip = concatenate_videoclips(images, method="compose")

    # 整体加速
    videoClip = accelerate_video(videoClip, 1.5, outputPath)
    # videoClip = videoClip.resize((1014, 1440))

    if videoName == "null":
        videoName = Cards[0].info_CN[0][5:10]
        if videoName[-1] != '日':
            videoName = videoName[ :-1]
        videoName += ".mov"
    videoClip.write_videofile(os.path.join(outputPath, videoName),
    fps = 24, codec="h264_nvenc", audio_codec="aac", threads=4, preset="medium",
                             bitrate="5000k", audio_bitrate="192k",
                             ffmpeg_params=["-metadata:s:v:0", "handler=VideoTrack"])

def devideSentence(text : str) -> str:
    res = ''
    for i,ch in enumerate(text):
        res += ch
        if(i % 16 == 15):
            res += '\n'
    if(res[-1] == '\n'):
        res = res[:-1]
    return res

def accelerate_video(video: VideoClip, speed_factor, outputPath) -> VideoClip:
    audio = video.audio
    audio = audio.set_fps(44100)

    video = video.without_audio()
    accelerated_video = video.fl_time(lambda t: speed_factor * t).set_duration(video.duration / speed_factor)

    # Step2: 使用FFmpeg处理音频(保持音调):ml-citation{ref="3,4" data="citationList"}
    audio.write_audiofile(os.path.join(outputPath,"audio1.0.wav"))
    audio_output = os.path.join(outputPath,"audio{speed_factor}.wav")
    ffmpeg_cmd = [
        "ffmpeg",
        "-i", f"{outputPath}/audio1.0.wav",
        "-filter:a", f"atempo={speed_factor}" if speed_factor <= 2 else "atempo=2.0,atempo={}".format(speed_factor / 2),
        "-vn", audio_output,
        "-y"
    ]
    subprocess.run(ffmpeg_cmd, check=True)

    # Step3: 合并音视频‌:ml-citation{ref="5,6" data="citationList"}
    final_clip = accelerated_video.set_audio(AudioFileClip(audio_output))
    return final_clip

def concatenate_segments(segment_paths : list[str], audioOutput_path : str, outputPath) -> None:
    # Here we use ffmpeg command line directly, because moviepy's concatenate_videoclips method creates audio artifacts when combining clips

    with open(f'{outputPath}/clip_paths.txt', 'w', encoding='gbk') as file:
        for path in segment_paths:
            print(path)
            file.write(f"file '{path[(len(outputPath) + 1):]}'\n")
    ffmpeg_command = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", f"{outputPath}/clip_paths.txt",
        "-c", "copy",
        audioOutput_path
    ]
    # result = subprocess.run(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    result = subprocess.run(ffmpeg_command, input=b'y\n')
    if result.returncode != 0:
        raise Exception(f"Video concatenation failed. Error: {result.stderr}")
