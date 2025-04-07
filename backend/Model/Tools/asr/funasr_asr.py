# -*- coding:utf-8 -*-
import argparse
import os
import traceback
from tqdm import tqdm
from funasr import AutoModel

fixed_model_size = 'large-v3'
fixed_language = 'zh'
fixed_precision = 'float16'

path_asr  = 'Model/Tools/asr/models/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch'
path_vad  = 'Model/Tools/asr/models/speech_fsmn_vad_zh-cn-16k-common-pytorch'
path_punc = 'Model/Tools/asr/models/punc_ct-transformer_zh-cn-common-vocab272727-pytorch'


model = AutoModel(
    model               = path_asr,
    model_revision      = "v2.0.4",
    vad_model           = path_vad,
    vad_model_revision  = "v2.0.4",
    punc_model          = path_punc,
    punc_model_revision = "v2.0.4",
)

def only_asr(input_file):
    try:
        text = model.generate(input=input_file)[0]["text"]
    except:
        text = ''
        print(traceback.format_exc())
    return text

def execute_asr(input_folder, output_folder):
    language=fixed_language
    input_file_names = os.listdir(input_folder)
    input_file_names.sort()
    
    output = []
    output_file_name = os.path.basename(input_folder)

    for file_name in tqdm(input_file_names):
        try:
            file_path = os.path.join(input_folder, file_name)
            text = model.generate(input=file_path)[0]["text"]
            output.append(f"{file_path}|{output_file_name}|{language.upper()}|{text}")
        except:
            print(traceback.format_exc())

    output_folder = output_folder or "output/asr_opt"
    os.makedirs(output_folder, exist_ok=True)
    output_file_path = os.path.abspath(f'{output_folder}/{output_file_name}.list')

    with open(output_file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(output))
        print(f"ASR 任务完成->标注文件路径: {output_file_path}\n")
    return output_file_path
