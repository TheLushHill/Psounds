# 该文件夹中定义前端向后端发送文件/请求，后端判断是哪种文件类型并调用该文件的api

# import logging, warnings
# from modelscope.utils.logger import get_logger
# logging.basicConfig(level=logging.WARNING)
# modelscope_logger = get_logger()
# modelscope_logger.setLevel(logging.ERROR)  # 设置为 ERROR 或更高
# modelscope_logger.propagate = False

from flask import Flask, request, jsonify, Response
from io import BytesIO
import os, sys, io, requests, json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from GetWord.docx.DocxWord import get_docxtext
from GetWord.pptx.PPTWord import get_ppttext
print("工作目录：", os.getcwd())

app = Flask(__name__)

ALLOWED_EXTENSIONS = {'docx', 'pptx'}
ALLOWED_MIME_TYPES = {  # 这些是HTTPmime类型,特定文件的代号
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
}

# 适配中文的扩展名！
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload', methods=['POST'])                             # JS的AJAX请求，fetch("/upload", {...})
def upload_file():

    file = request.files['file']
    filename = file.filename

    # 检查文件名是否为空
    if file.filename == '':
        return jsonify({"error": "空文件名"}), 400

    # 校验扩展名
    if not allowed_file(filename):
        return jsonify({"error": "文件扩展名不合法"}), 400

    # 删除文件内容检测部分，直接通过扩展名匹配
    file_extension = filename.rsplit('.', 1)[1].lower()
    detected_type = ALLOWED_MIME_TYPES.get(file_extension)
    # 如果扩展名不在允许列表中，直接拦截
    if not detected_type:
        return jsonify({"error": "文件类型不合法"}), 400
    file.seek(0)   # 重置文件指针

    # 6. 如果文件过大(大于1G)，则保存在本地文件
    # 先创建缓存文件夹以保存文件
    # if( >= 1000*1024):
    #   path1 = os.getcwd()
    #   os.makedirs(".Cache\Input", exist_ok=True)
    #   os.makedirs(".Cache\Output", exist_ok=True)
    #   UPLOAD_FOLDER = os.path.join(path1, ".Cache\Input")
    #   POST_FOLDER = os.path.join(path1, ".Cache\Output")
    #
    # 判断文件夹生成是否成功
    #   if not os.path.exists(UPLOAD_FOLDER):
    #       os.makedirs(UPLOAD_FOLDER)
    # 在本地保存
    #   file.save(os.path.join(UPLOAD_FOLDER, filename))


# 在这里判断文件类型，并调用各类型的api   后续在这里判断一下内存大小
    if detected_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        return get_docxtext(file)
    elif detected_type == 'application/vnd.openxmlformats-officedocument.presentationml.presentation':
        return get_ppttext(file)


# # 解析成功返回前端。前端发送一段文字后，在这里进行预处理
# import argparse
# import logging
# import os,sys
# from multiprocessing import freeze_support
# sys.path.append(os.path.join(os.path.dirname(__file__), "Model"))

# from Model.Tools.uvr5.uvrmain import uvr
# from Model.Tools.slice_audio.slice_audio import slice_audio
# from Model.Tools.cmd_denoise.cmd_denoise import execute_denoise
# from Model.Tools.asr.funasr_asr import execute_asr
# import Model.Tools.subfix.subfix as subfix
# import gradio as gr

# ALLOWED_EXTENSIONS = {'wav', 'mp3', 'm4a'}
# def allowed_audio_file(filename):
#     return '.' in filename and \
#            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# # 前端发送过来的人物音频，先保存到Model\\input_audio
# @app.route('/save', methods=['POST'])
# def save():
#     audio_file = request.files['file']
#     audio_filename = audio_file.filename
#     save_dir = os.path.abspath("Model\\input_audio")
#     save_path = os.path.join(save_dir, audio_filename)
#     if not allowed_audio_file(audio_file.filename):
#         return "文件类型不支持", 400
#     if os.path.exists("Model\\input_audio"):
#         audio_file.save(save_path)
#     else:
#         os.makedirs("Model\\input_audio")
#         audio_file.save(save_path)

#     if os.path.exists(f"Model\\input_audio\\{audio_file.filename}"):       
#         return jsonify({"log": "音频保存成功"}), 200


# ##数据集的预处理
# @app.route('/preprocess', methods=['POST'])
# def preprocess():
#     result1 = uvr("Model\\input_audio",
#                  "Model\\Tools\\output_cache\\uvr5_opt\\vocal",
#                  "Model\\Tools\\output_cache\\uvr5_opt\\instrumental"
#                  )
#     print(result1)

#     result2 = slice_audio("Model\\Tools\\output_cache\\uvr5_opt\\vocal", "Model\\Tools\\output_cache\\slicer_opt")
#     print(result2)

#     result3 = execute_denoise("Model\\Tools\\output_cache\\slicer_opt", "Model\\Tools\\output_cache\\denoise_opt")
#     print(result3)

#     result4 = execute_asr("Model\\Tools\\output_cache\\denoise_opt", "Model\\Tools\\output_cache\\asr_opt")
#     print(result4)

#     return jsonify({"log": "预处理完成"}), 200


# ##之后要重定向到打标界面，手动进行修正
# @app.route('/subfix', methods=['POST'])
# def subfix_editor():
#     subfix.start()

# # 格式化音频
# from Model.Training.prepare_datasets.gettext1 import slice2bert
# from Model.Training.prepare_datasets.gethubert2 import get_hubert
# from Model.Training.prepare_datasets.getsemanic3 import get_semanic
# @app.route('/format', methods=['POST'])
# def format_audio():
#     global exp_name
#     exp_name = request.json.get("exp_name")
#     slice2bert("Model/Tools/output_cache/asr_opt/denoise_opt.list",exp_name)
#     get_hubert(exp_name)
#     get_semanic(exp_name)
    
#     return jsonify({"log": "音频格式化成功，可以训练模型"}), 200


# # 训练模型
# import os, sys
# from pathlib import Path
# sys.path.append(str(Path("Model/Training/Gs_Model")))

# from Model.Training.GS_Model.s1_train import parse_args, main as s1_main
# from Model.Training.GS_Model.s2_train import main as s2_main

# @app.route('/train', methods=['POST'])
# def train():

#     #调用 s1_train 的 main 函数
#     parser = argparse.ArgumentParser()
#     parser.add_argument(
#         "-c",
#         "--config_file",
#         type=str,
#         default="configs/s1longer_v2.yaml",
#         help="path of config file",
#     )
#     args = parser.parse_args()
#     exp_name = request.json.get("exp_name") 

#     # GPT模型训练
#     s1_main(args, exp_name)

#     # SoVITS模型训练
#     s2_main(exp_name)

#     if os.path.exists("Model/Training/GPT_weights/%s_e%s.ckpt" % (exp_name, 12)):
#         if os.path.exists("Model/Training/SoVITS_weights/*e12*.ckpt"):
#             return jsonify({"log": "训练完成"}), 200
        

# tts 开始
# 使用soundfile库处理音频数据
# tts 库
from Model.tts_main import get_audio
import soundfile as sf
def process_audio_sf(sr, audio_data):
    with io.BytesIO() as buffer:
        sf.write(buffer, audio_data, sr, format='WAV')
        return buffer.getvalue()

# 获取处理后的音频数据
def get_processed_audio(data, streaming=False):
    """获取处理后的音频数据"""
    raw_audio = get_audio(data, streaming=streaming)
    
    if not streaming:
        for sr, audio_data in raw_audio:
            yield process_audio_sf(sr, audio_data)
    else:
        # 处理流式音频
        for chunk in raw_audio:
            yield chunk

# 返回整个 wav 文件
@app.route("/tts", methods=["POST"])
def handletts():
    data = request.json;  

    data = {
        "text": data.get("text", "你好，世界"),
        "character": data.get("character", "Hutao"),
        "prompt_text": data.get("prompt_text", "我说白术，你不会看不出来吧？难不成你师父，忘了教你这门功夫"),
        "ref_audio_path": data.get("ref_audio_path", "Model/trained/Hutao/我说白术，你不会看不出来吧？难不成你师父，忘了教你这门功夫？.wav"),
    }
    
    def generate():
        for chunk in get_processed_audio(data):
            yield chunk;

    return Response(generate(), status=200,mimetype="audio/wav");

# 流式返回
@app.route("/tts_stream", methods=["POST"])
def handletts_stream():
    data = request.json;
    
    data = {
        "text": data.get("text", "你好，世界"),
        "character": data.get("character", "Hutao"),
        "prompt_text": data.get("prompt_text", "我说白术，你不会看不出来吧？难不成你师父，忘了教你这门功夫"),
        "ref_audio_path": data.get("ref_audio_path", "Model/trained/Hutao/我说白术，你不会看不出来吧？难不成你师父，忘了教你这门功夫？.wav"),
    }

    def generate():
        for chunk in get_processed_audio(data, streaming=True):
            print(f"Yielding chunk of size: {len(chunk)}")  # 打印每个块的大小
            yield chunk;

    return Response(generate(), status=200,mimetype="audio/wav");
# tts 结束


if __name__ == '__main__':
    app.run(host="127.0.0.1", port=8000, debug=True, use_reloader=False)
