# 该文件夹中定义前端向后端发送文件/请求，后端判断是哪种文件类型并调用该文件的api

from flask import Flask, request, jsonify

import sys
sys.path.append('..')
from GetWord.docx.DocxWord import get_docxtext
from GetWord.pptx.PPTWord import get_ppttext

app = Flask(__name__)
ALLOWED_EXTENSIONS = {'docx', 'pptx', 'txt'}
ALLOWED_MIME_TYPES = {  # 这些是HTTPmime类型,特定文件的代号
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
}

# 适配中文的扩展名！
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload', methods=['POST'])  # JS的AJAX请求，fetch("/upload", {...})
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

# 转换函数
# def ():

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=8000, debug=True)
