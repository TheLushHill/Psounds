# 该文件夹中定义前端向后端发送文件/请求，后端判断是哪种文件类型并调用该文件的api

import logging, warnings
from modelscope.utils.logger import get_logger
logging.basicConfig(level=logging.WARNING)
modelscope_logger = get_logger()
modelscope_logger.setLevel(logging.ERROR)  # 设置为 ERROR 或更高
modelscope_logger.propagate = False

from flask import Flask, request, jsonify
from io import BytesIO
import os, sys, requests, json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from GetWord.docx.DocxWord import get_docxtext
from GetWord.pptx.PPTWord import get_ppttext

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


# 解析成功返回前端。前端发送一段文字后，在这里进行预处理
import argparse
import logging
import os,sys
from multiprocessing import freeze_support
sys.path.append(os.path.join(os.path.dirname(__file__), "Model"))

from Model.Tools.uvr5.uvrmain import uvr
from Model.Tools.slice_audio.slice_audio import slice_audio
from Model.Tools.cmd_denoise.cmd_denoise import execute_denoise
from Model.Tools.asr.funasr_asr import execute_asr
import Model.Tools.subfix.subfix as subfix
import gradio as gr

ALLOWED_EXTENSIONS = {'wav', 'mp3', 'm4a'}
def allowed_audio_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 前端发送过来的人物音频，先保存到Model\\input_audio
@app.route('/save', methods=['POST'])
def save():
    audio_file = request.files['file']
    audio_filename = audio_file.filename
    save_dir = os.path.abspath("Model\\input_audio")
    save_path = os.path.join(save_dir, audio_filename)
    if not allowed_audio_file(audio_file.filename):
        return "文件类型不支持", 400
    if os.path.exists("Model\\input_audio"):
        audio_file.save(save_path)
    else:
        os.makedirs("Model\\input_audio")
        audio_file.save(save_path)

    if os.path.exists(f"Model\\input_audio\\{audio_file.filename}"):       
        return jsonify({"log": "音频保存成功"}), 200


##数据集的预处理
@app.route('/preprocess', methods=['POST'])
def preprocess():
    result1 = uvr("Model\\input_audio",
                 "Model\\Tools\\output_cache\\uvr5_opt\\vocal",
                 "Model\\Tools\\output_cache\\uvr5_opt\\instrumental"
                 )
    print(result1)

    result2 = slice_audio("Model\\Tools\\output_cache\\uvr5_opt\\vocal", "Model\\Tools\\output_cache\\slicer_opt")
    print(result2)

    result3 = execute_denoise("Model\\Tools\\output_cache\\slicer_opt", "Model\\Tools\\output_cache\\denoise_opt")
    print(result3)

    result4 = execute_asr("Model\\Tools\\output_cache\\denoise_opt", "Model\\Tools\\output_cache\\asr_opt")
    print(result4)

    return jsonify({"log": "预处理完成"}), 200


##之后要重定向到打标界面，手动进行修正
@app.route('/subfix', methods=['POST'])
def subfix_editor():
    subfix.start()


# 训练模型
import os, sys
from pathlib import Path
sys.path.append(str(Path("Model/Training/Gs_Model")))

from Model.Training.GS_Model.s1_train import parse_args, main as s1_main
from Model.Training.GS_Model.s2_train import main as s2_main

@app.route('/train', methods=['POST'])
def train():

    #调用 s1_train 的 main 函数
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--config_file",
        type=str,
        default="configs/s1longer_v2.yaml",
        help="path of config file",
    )
    args = parser.parse_args()
    exp_name = request.json.get("exp_name") 

    # GPT模型训练
    s1_main(args, exp_name)

    # SoVITS模型训练
    s2_main(exp_name)

    if os.path.exists("Model/Training/GPT_weights/%s_e%s.ckpt" % (exp_name, 12)):
        if os.path.exists("Model/Training/SoVITS_weights/*e12*.ckpt"):
            return jsonify({"log": "训练完成"}), 200


# 训练完成后，在GPT_weights、SoVITS_weights中提取模型，进行TTS
# @app.route('/tts', methods=['POST'])
# def tts():



if __name__ == '__main__':
    app.run(host="127.0.0.1", port=8000, debug=True)


# 或许能成功的subfix后端接口
# from flask import send_from_directory
# from threading import Lock
# import argparse,os, uuid, librosa, numpy as np, soundfile
# # 全局状态管理
# class GlobalState:
#     def __init__(self):
#         self.lock = Lock()
#         self.initialized = False
#         self.data = {
#             'json_key_text': 'text',
#             'json_key_path': 'wav_path',
#             'batch_size': 10,
#             'data_source': None,
#             'max_index': 0,
#             'current_index': 0,
#             'dataset': []
#         }

#     def initialize(self, config):
#         with self.lock:
#             # 参数验证
#             if not self._validate_config(config):
#                 raise ValueError("Invalid initialization config")

#             # 加载数据
#             if config['load_json'] != "None":
#                 self._load_json(config['load_json'])
#             elif config['load_list'] != "None":
#                 self._load_list(config['load_list'])
            
#             # 更新配置
#             self.data.update({
#                 'json_key_text': config.get('json_key_text', 'text'),
#                 'json_key_path': config.get('json_key_path', 'wav_path'),
#                 'batch_size': int(config.get('g_batch', 10)),
#                 'initialized': True
#             })

#     def _validate_config(self, config):
#         required_keys = {'load_json', 'load_list'}
#         if not any(config.get(key) != "None" for key in required_keys):
#             raise ValueError("Must provide either load_json or load_list")
#         return True

#     def _load_json(self, path):
#         abs_path = os.path.abspath(path)
#         with open(abs_path, 'r', encoding='utf-8') as f:
#             self.data['dataset'] = [json.loads(line) for line in f]
#         self._update_metadata()

#     def _load_list(self, path):
#         self.data['dataset'] = []
#         with open(path, 'r', encoding='utf-8') as f:
#             for line in f:
#                 parts = line.strip().split('|')
#                 if len(parts) == 4:
#                     self.data['dataset'].append({
#                         'wav_path': parts[0],
#                         'speaker_name': parts[1],
#                         'language': parts[2],
#                         'text': parts[3]
#                     })
#         self._update_metadata()

#     def _update_metadata(self):
#         self.data['max_index'] = len(self.data['dataset']) - 1
#         self.data['current_index'] = 0

# global_state = GlobalState()

# # 初始化端点
# @app.route('/subfix/initialize', methods=['POST'])
# def initialize():
#     try:
#         config = request.json
#         global_state.initialize(config)
#         return jsonify({
#             "status": "success",
#             "metadata": {
#                 "total_items": len(global_state.data['dataset']),
#                 "batch_size": global_state.data['batch_size']
#             }
#         })
#     except Exception as e:
#         return jsonify({"error": str(e)}), 400

# # 数据操作端点
# @app.route('/subfix/change-index', methods=['POST'])
# def handle_change_index():
#     if not global_state.data['initialized']:
#         return jsonify({"error": "System not initialized"}), 412

#     data = request.json
#     new_index = data['index']
#     batch_size = global_state.data['batch_size']

#     with global_state.lock:
#         # 边界检查
#         new_index = max(0, min(new_index, global_state.data['max_index']))
#         end_index = min(new_index + batch_size, global_state.data['max_index'])
        
#         # 获取批次数据
#         batch_data = global_state.data['dataset'][new_index:end_index]
#         global_state.data['current_index'] = new_index

#         # 构建响应
#         response = {
#             "current_index": new_index,
#             "texts": [item[global_state.data['json_key_text']] for item in batch_data],
#             "audio_paths": [item[global_state.data['json_key_path']] for item in batch_data],
#             "checkboxes": [False] * len(batch_data)
#         }
        
#         # 填充不足批次的部分
#         while len(response['texts']) < global_state.data['batch_size']:
#             response['texts'].append("")
#             response['audio_paths'].append(None)
#             response['checkboxes'].append(False)

#     return jsonify(response)

# # 文件访问端点
# @app.route('/subfix/audio/<path:filename>')
# def serve_audio(filename):
#     base_dir = os.path.abspath("audio_files")  # 设置安全访问目录
#     requested_path = os.path.abspath(os.path.join(base_dir, filename))
    
#     if not requested_path.startswith(base_dir):
#         return jsonify({"error": "Unauthorized path access"}), 403
    
#     return send_from_directory(base_dir, filename)

# @app.route('/subfix/submit-changes', methods=['POST'])
# def handle_submit_changes():
#     if not global_state.data['initialized']:
#         return jsonify({"error": "System not initialized"}), 412

#     data = request.json
#     text_list = data.get('text_list', [])
    
#     with global_state.lock:
#         current_index = global_state.data['current_index']
#         batch_size = global_state.data['batch_size']
#         changed = False
        
#         # 更新文本内容
#         for i, text in enumerate(text_list):
#             actual_index = current_index + i
#             if actual_index <= global_state.data['max_index']:
#                 key = global_state.data['json_key_text']
#                 if global_state.data['dataset'][actual_index][key] != text:
#                     global_state.data['dataset'][actual_index][key] = text
#                     changed = True
        
#         # 如果需要保存修改
#         if changed:
#             _save_data_source()
        
#         # 获取更新后的数据
#         return _build_batch_response(current_index)

# # 合并音频端点
# @app.route('/subfix/merge-audio', methods=['POST'])
# def handle_merge_audio():
#     if not global_state.data['initialized']:
#         return jsonify({"error": "System not initialized"}), 412

#     data = request.json
#     interval = data['interval']
#     selected_indexes = data.get('selected_indexes', [])
    
#     with global_state.lock:
#         dataset = global_state.data['dataset']
#         current_index = global_state.data['current_index']
#         key_path = global_state.data['json_key_path']
#         key_text = global_state.data['json_key_text']
        
#         # 转换为实际索引
#         actual_indexes = [current_index + i for i in selected_indexes 
#                          if (current_index + i) <= global_state.data['max_index']]
        
#         if len(actual_indexes) >= 2:
#             base_index = actual_indexes[0]
#             base_item = dataset[base_index]
            
#             # 合并音频
#             audio_list = []
#             sample_rate = None
#             merged_text = []
            
#             for idx in actual_indexes:
#                 item = dataset[idx]
#                 data, sr = librosa.load(item[key_path], sr=32000, mono=True)
#                 sample_rate = sample_rate or sr
#                 audio_list.append(data)
#                 merged_text.append(item[key_text])
#                 if idx != base_index:
#                     audio_list.append(np.zeros(int(sample_rate * interval)))
            
#             # 生成新音频
#             merged_audio = np.concatenate(audio_list)
#             output_path = _get_next_path(base_item[key_path])
#             soundfile.write(output_path, merged_audio, sample_rate)
            
#             # 更新数据集
#             base_item[key_path] = output_path
#             base_item[key_text] = ' '.join(merged_text)
            
#             # 删除合并的条目
#             for idx in reversed(actual_indexes[1:]):
#                 del dataset[idx]
            
#             _update_metadata()
#             _save_data_source()
        
#         return _build_batch_response(current_index)

# # 删除音频端点
# @app.route('/subfix/delete-audio', methods=['POST'])
# def handle_delete_audio():
#     if not global_state.data['initialized']:
#         return jsonify({"error": "System not initialized"}), 412

#     data = request.json
#     selected_indexes = data.get('selected_indexes', [])
    
#     with global_state.lock:
#         current_index = global_state.data['current_index']
#         dataset = global_state.data['dataset']
        
#         # 转换为实际索引并排序
#         actual_indexes = sorted(
#             [current_index + i for i in selected_indexes 
#              if (current_index + i) <= global_state.data['max_index']],
#             reverse=True
#         )
        
#         # 删除条目
#         for idx in actual_indexes:
#             if 0 <= idx < len(dataset):
#                 del dataset[idx]
        
#         _update_metadata()
#         _save_data_source()
        
#         # 调整当前索引
#         new_index = min(current_index, global_state.data['max_index'])
#         global_state.data['current_index'] = new_index
        
#         return _build_batch_response(new_index)

# # 音频分割端点
# @app.route('/subfix/split-audio', methods=['POST'])
# def handle_split_audio():
#     if not global_state.data['initialized']:
#         return jsonify({"error": "System not initialized"}), 412

#     data = request.json
#     split_point = data['split_point']
#     selected_index = data['selected_index']
    
#     with global_state.lock:
#         current_index = global_state.data['current_index']
#         actual_index = current_index + selected_index
        
#         if actual_index > global_state.data['max_index']:
#             return jsonify({"error": "Invalid index"}), 400
        
#         item = global_state.data['dataset'][actual_index]
#         key_path = global_state.data['json_key_path']
#         key_text = global_state.data['json_key_text']
        
#         # 加载音频
#         audio, sr = librosa.load(item[key_path], sr=None, mono=True)
#         split_frame = int(split_point * sr)
        
#         if 0 < split_frame < len(audio):
#             # 分割音频
#             part1 = audio[:split_frame]
#             part2 = audio[split_frame:]
            
#             # 保存新文件
#             new_path = _get_next_path(item[key_path])
#             soundfile.write(new_path, part2, sr)
            
#             # 更新原始文件
#             soundfile.write(item[key_path], part1, sr)
            
#             # 插入新条目
#             new_item = {
#                 key_path: new_path,
#                 key_text: item[key_text]
#             }
#             global_state.data['dataset'].insert(actual_index + 1, new_item)
            
#             _update_metadata()
#             _save_data_source()
        
#         return _build_batch_response(current_index)

# # 保存文件端点
# @app.route('/subfix/save-file', methods=['POST'])
# def handle_save_file():
#     if not global_state.data['initialized']:
#         return jsonify({"error": "System not initialized"}), 412
    
#     _save_data_source()
#     return jsonify({"status": "success"})

# # 反向选择端点
# @app.route('/subfix/invert-selection', methods=['POST'])
# def handle_invert_selection():
#     if not global_state.data['initialized']:
#         return jsonify({"error": "System not initialized"}), 412

#     data = request.json
#     checkboxes = data.get('checkboxes', [])
#     inverted = [not val for val in checkboxes]
#     return jsonify({"checkboxes": inverted})

# # 辅助函数
# def _build_batch_response(index):
#     """构建标准批次响应"""
#     batch_size = global_state.data['batch_size']
#     key_text = global_state.data['json_key_text']
#     key_path = global_state.data['json_key_path']
    
#     batch_data = global_state.data['dataset'][index:index + batch_size]
#     response = {
#         "current_index": index,
#         "texts": [item[key_text] for item in batch_data],
#         "audio_paths": [item[key_path] for item in batch_data],
#         "checkboxes": [False] * len(batch_data)
#     }
    
#     # 填充空白
#     while len(response['texts']) < batch_size:
#         response['texts'].append("")
#         response['audio_paths'].append(None)
#         response['checkboxes'].append(False)
    
#     return jsonify(response)

# def _get_next_path(path):
#     """生成不重复的文件路径"""
#     base_dir = os.path.dirname(path)
#     base_name = os.path.splitext(os.path.basename(path))[0]
#     for i in range(100):
#         new_path = os.path.join(base_dir, f"{base_name}_{i:02d}.wav")
#         if not os.path.exists(new_path):
#             return new_path
#     return os.path.join(base_dir, f"{uuid.uuid4()}.wav")

# def _save_data_source():
#     """保存到原始数据文件"""
#     if global_state.data['data_source'].endswith('.json'):
#         with open(global_state.data['data_source'], 'w', encoding='utf-8') as f:
#             for item in global_state.data['dataset']:
#                 f.write(json.dumps(item, ensure_ascii=False) + '\n')
#     elif global_state.data['data_source'].endswith('.list'):
#         with open(global_state.data['data_source'], 'w', encoding='utf-8') as f:
#             for item in global_state.data['dataset']:
#                 parts = [
#                     item['wav_path'],
#                     item.get('speaker_name', ''),
#                     item.get('language', ''),
#                     item.get('text', '')
#                 ]
#                 f.write('|'.join(parts) + '\n')

# def _update_metadata():
#     """更新元数据"""
#     global_state.data['max_index'] = len(global_state.data['dataset']) - 1
#     global_state.data['current_index'] = min(
#         global_state.data['current_index'],
#         global_state.data['max_index']
#     )
