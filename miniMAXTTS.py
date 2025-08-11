import time

import requests
import json
import os
from pydub import AudioSegment

group_id = "1887488082316366180"

api_key = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJHcm91cE5hbWUiOiLmtbfonrrnlKjmiLdfMzQ0NDM4MjQxMTMwMTE5MTczIiwiVXNlck5hbWUiOiLmtbfonrrnlKjmiLdfMzQ0NDM4MjQxMTMwMTE5MTczIiwiQWNjb3VudCI6IiIsIlN1YmplY3RJRCI6IjE4ODc0ODgwODIzMjg5NDkwOTIiLCJQaG9uZSI6IjE1ODUwNTI2MDg5IiwiR3JvdXBJRCI6IjE4ODc0ODgwODIzMTYzNjYxODAiLCJQYWdlTmFtZSI6IiIsIk1haWwiOiIiLCJDcmVhdGVUaW1lIjoiMjAyNS0wMi0wOCAwOToxNToxMCIsIlRva2VuVHlwZSI6MSwiaXNzIjoibWluaW1heCJ9.Rq5HQYxEljZaTceSWJaKx_36n9-8k8XtvpCkNWvumwGA5PAaRtnnMDCWEfSq5NKrS6scnckRW_0SSuwQPhyJuRIEImNrCH4AhytrMimFsPGNxY5ljI6Rf6tewxq5K4VYyi0o4wx-jSjb70mU-Ki4nUmw4RNp2bdUE_JT0kGXqADnPwc2375OIuByxyFUjT0ziKSYEEnO27uXiQsRtvesFFNY2jOQyuEwZK_VAEk_EQ6oERydz-W5jhvRJmghkxHUxINiYssP0cHrfO6lI26s1JhM2pOnnNCvErGOy0ZujsNgqdYSnu1Anw0ae60uN_XEFKSHRZCydzi1mtd4KXmLPg"

url = f"https://api.minimax.chat/v1/t2a_v2?GroupId={group_id}"

def miniMAX_API(text : str, path : str) -> None:
    payload = json.dumps({
      "model": "speech-01-turbo",
      #"text": "真正的危险不是计算机开始像人一样思考，而是人开始像计算机一样思考。计算机只是可以帮我们处理一些简单事务。",
      "text": text,

      "stream": False,
      "voice_setting": {
        "voice_id": "Chinese (Mandarin)_Gentleman",
        "speed": 1.0,
        "vol": 1,
        "pitch": 0,
        "emotion":"happy"
      },
      "pronunciation_dict": {
        "tone": [
            "处理/(chu4)(li3)",
            "重识别/(chong2)(shi2)(bie2)",
            "框架/(kuang1)(jia4)"
        ]
      },
      "audio_setting": {
        "sample_rate": 32000,
        "bitrate": 128000,
        "format": "mp3",
        "channel": 1
      }
    })
    headers = {
      'Authorization': f'Bearer {api_key}',
      'Content-Type': 'application/json'
    }

    while True:
        Success = False
        try:
            response = requests.request("POST", url, stream=True, headers=headers, data=payload)
            print(f"状态码：{response.status_code}")
            parsed_json = json.loads(response.text)
            data_value = parsed_json.get('data')
            if data_value is not None:
                # 存在 data 字段时继续操作
                audio_value = bytes.fromhex(data_value['audio'])
                Success = True
            else:
                print("JSON 中不存在 'data' 字段")
                print(parsed_json)
                print("程序暂停5s")
                time.sleep(5)
        except json.JSONDecodeError as e:
            print(f"JSON解析失败：{e}")
            print(response)
        if(Success):
            break

    with open(f'{path}', 'wb') as f:
        f.write(audio_value)

def TextToSpeech(sentences : list[str], storagePath) -> list[str]:
    PathList = []

    silencePath = storagePath.replace("audio", "audio_with_silence")
    # print(silencePath)
    if not os.path.exists(storagePath):
        os.makedirs(storagePath)
    if not os.path.exists(silencePath):
        os.makedirs(silencePath)

    for i,sentence in enumerate(sentences):
        path = f"{storagePath}sentence_{i}.mp3"
        path_with_silence = f"{silencePath}sentence_{i}.mp3"
        PathList.append(path_with_silence)

        miniMAX_API(sentence, path)
        if i != len(sentences) - 1:
            add_silence(path, path_with_silence, 0.005)
        else:
            add_silence(path, path_with_silence, 0.8)

    return PathList

def add_silence(fromPath : str, toPath : str, time: float):
    # 加载原始 MP3 文件
    audio = AudioSegment.from_mp3(fromPath)

    silence = AudioSegment.silent(duration= time * 1000)  # 持续时间以毫秒为单位

    # 将静音片段添加到音频末尾
    audio_with_silence = audio + silence

    # 导出新的音频文件
    audio_with_silence.export(toPath, format="mp3", codec="libmp3lame")