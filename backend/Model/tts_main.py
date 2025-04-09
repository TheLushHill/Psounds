from datetime import datetime
import json, os
import requests
import numpy as np
from string import Template
import wave, io
import gradio as gr

# 在开头加入路径
import os, sys
now_dir = os.getcwd()
sys.path.insert(0, now_dir)
sys.path.append(os.path.dirname(__file__))

import logging
logging.getLogger("markdown_it").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("httpcore").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("asyncio").setLevel(logging.ERROR)
logging.getLogger("charset_normalizer").setLevel(logging.ERROR)
logging.getLogger("torchaudio._extension").setLevel(logging.ERROR)

from Model.Synthesizers.base import Base_TTS_Synthesizer, Base_TTS_Task, get_wave_header_chunk
# from Model.src.common_config_manager import app_config, __version__

from importlib import import_module

def load_character_emotions(character_name, characters_and_emotions):
    emotion_options = ["default"]
    emotion_options = characters_and_emotions.get(character_name, ["default"])

    return gr.Dropdown(emotion_options, value="default")

synthesizer_name = "gsv_fast"

# 动态导入合成器模块, 此处可写成 from Synthesizers.xxx import TTS_Synthesizer, TTS_Task
synthesizer_module = import_module(f"Model.Synthesizers.{synthesizer_name}")
TTS_Synthesizer = synthesizer_module.TTS_Synthesizer
TTS_Task = synthesizer_module.TTS_Task


# 创建合成器实例
tts_synthesizer:Base_TTS_Synthesizer = TTS_Synthesizer(debug_mode=True)

from time import time as ttime

default_data = {
        "text": "我是一个粉刷匠，粉刷本领强。我要把那新房子，刷得更漂亮。刷了房顶又刷墙，刷子像飞一样。哎呀我的小鼻子，变呀变了样。",
        "character": None,
        "ref_audio_path": None,
        "text_language": "auto",
        "prompt_text": None,
        "prompt_language": "auto",
        "batch_size": 1,
        "speed": 1.0,
        "top_k": 12,
        "top_p": 0.6,
        "temperature": 0.6,
        "cut_method": "auto_cut",
        "max_cut_length": 100,
        "seed": -1,
        "stream": False,
        "parallel_infer": True,
        "repetition_penalty": 1.35,
    }

def get_audio(data, streaming=False):

    data["stream"] = streaming
    
    if data.get("text") in ["", None]:
        return None, None
    try:
        task: Base_TTS_Task= tts_synthesizer.params_parser(data)
        t2 = ttime()
        
        if not streaming:
            if synthesizer_name == "remote":
                save_path = tts_synthesizer.generate(task, return_type="filepath")
                yield save_path
            else:
                gen = tts_synthesizer.generate(task, return_type="numpy")
                yield next(gen)
        else:
            gen = tts_synthesizer.generate(task, return_type="numpy")
            # sample_rate = 32000 if task.sample_rate in [None, 0] else task.sample_rate
            # yield get_wave_header_chunk(sample_rate=sample_rate)
            for chunk in gen:
                yield chunk
        
    except Exception as e:
        print(f"Error: {e}")


from functools import partial
get_streaming_audio = partial(get_audio, streaming=True)

def stopAudioPlay():
    return


global characters_and_emotions_dict
characters_and_emotions_dict = {}

def get_characters_and_emotions():
    global characters_and_emotions_dict
    # 直接检查字典是否为空，如果不是，直接返回，避免重复获取
    if characters_and_emotions_dict == {}:
        characters_and_emotions_dict = tts_synthesizer.get_characters()
        print(characters_and_emotions_dict)
   
    return characters_and_emotions_dict

def change_character_list(
    character="", emotion="default"
):
    characters_and_emotions = {}

    try:
        characters_and_emotions = get_characters_and_emotions()
        character_names = [i for i in characters_and_emotions]
        if len(character_names) != 0:
            if character in character_names:
                character_name_value = character
            else:
                character_name_value = character_names[0]
        else:
            character_name_value = ""
        emotions = characters_and_emotions.get(character_name_value, ["default"])
        emotion_value = emotion

    except:
        character_names = []
        character_name_value = ""
        emotions = ["default"]
        emotion_value = "default"
        characters_and_emotions = {}

    return (
        gr.Dropdown(character_names, value=character_name_value, label=i18n("选择角色")),
        gr.Dropdown(emotions, value=emotion_value, label=i18n("情感列表"), interactive=True),
        characters_and_emotions,
    )


def cut_sentence_multilang(text, max_length=30):
    if max_length == -1:
        return text, ""
    # 初始化计数器
    word_count = 0
    in_word = False
    
    
    for index, char in enumerate(text):
        if char.isspace():  # 如果当前字符是空格
            in_word = False
        elif char.isascii() and not in_word:  # 如果是ASCII字符（英文）并且不在单词内
            word_count += 1  # 新的英文单词
            in_word = True
        elif not char.isascii():  # 如果字符非英文
            word_count += 1  # 每个非英文字符单独计为一个字
        if word_count > max_length:
            return text[:index], text[index:]
    
    return text, ""


default_text = "我是一个粉刷匠，粉刷本领强。我要把那新房子，刷得更漂亮。刷了房顶又刷墙，刷子像飞一样。哎呀我的小鼻子，变呀变了样。"


information = ""

try:
    with open("Information.md", "r", encoding="utf-8") as f:
        information = f.read()
except:
    pass
try:    
    max_text_length = app_config.max_text_length
except:
    max_text_length = -1

ref_settings = tts_synthesizer.ui_config.get("ref_settings", [])
basic_settings = tts_synthesizer.ui_config.get("basic_settings", [])
advanced_settings = tts_synthesizer.ui_config.get("advanced_settings", [])
url_setting = tts_synthesizer.ui_config.get("url_settings", [])

tts_task_example : Base_TTS_Task = TTS_Task()
params_config = tts_task_example.params_config

has_character_param = True if "character" in params_config else False


# 生成一句话充当测试，减少第一次请求的等待时间

