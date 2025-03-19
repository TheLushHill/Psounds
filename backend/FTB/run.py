# 该文件夹中定义前端向后端发送文件/请求，后端判断是哪种文件类型并调用该文件的api

from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
import magic

app = Flask(__name__)
# UPLOAD_FOLDER = 'G:/TTS/api1/cache/Input'
# ALLOWED_EXTENSIONS = {'docx', 'pptx', 'txt'}
# ALLOWED_MIME_TYPES = {    # 这些是mime类型
#     'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
#     'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
#     'txt': 'text/plain'
# }

# # 确保上传目录存在
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 校验文件扩展名是否合法
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/api/upload', methods=['POST'])        # JS的AJAX请求，fetch("/upload", {...})
def upload_file():
    return jsonify([
    "第一段的文字",
    "第二段的文字",
    "第三段的文字",
    "...剩下的段落依次以数组格式存储"
]), 200;
    # 1. 检查请求中是否包含文件
    if 'file' not in request.files:
        return jsonify({"error": "未选择文件"}), 400

    file = request.files['file']

    # 2. 检查文件名是否为空
    if file.filename == '':
        return jsonify({"error": "空文件名"}), 400

    # 3. 安全处理文件名
    filename = secure_filename(file.filename)

    # 4. 校验扩展名
    if not allowed_file(filename):
        return jsonify({"error": "文件扩展名不合法"}), 400

    # 5. 校验文件内容类型（防止伪造扩展名）
    file_data = file.read(2048)
    mime = magic.Magic(mime=True)
    detected_type = mime.from_buffer(file_data)

    # 获取文件实际扩展名对应的MIME类型
    file_extension = filename.rsplit('.', 1)[1].lower()
    expected_mime = ALLOWED_MIME_TYPES.get(file_extension)

    if detected_type != expected_mime:
        return jsonify({"error": f"文件内容类型不匹配 ({detected_type} vs {expected_mime})"}), 400
    file.seek(0)  # 重置文件指针

    # 6. 保存文件
    try:
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        # 上面，保存原格式文件
        return jsonify({
            "message": "文件上传成功",
            "filename": filename,
            "detected_type": detected_type
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 在这里判断文件类型，并调用各类型的api
# if detected_type == 'text/plain':
#     # 处理文本文件
# elif detected_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
#     # 处理 .docx 文件
# elif detected_type == 'application/vnd.openxmlformats-officedocument.presentationml.presentation':
#     # 处理.pptx文件

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=8000, debug=True)