# 检测思想：在文本之间，出现 换行('/n')则为分段，段数num++
# 连接主程序：已知文件名与文件路径

# docx文档默认是是UTF-8编码

from docx import Document
from io import BytesIO
from flask import jsonify

# 小文本，则是二进制文本流式输出
def get_docxtext(file):
    try:
        file_stream = BytesIO(file.read())
        doc = Document(file_stream)

        # 提取并过滤段落
        # paragraphs = [
        #     para.text.strip()           # .text提取文本, .strip去除空白符号, replace('\n', '').replace('\r', '')加在后面去除换行符
        #     for para in enumerate(doc.paragraphs, 1)
        #     if para.text.strip()        # 过滤空段落
        # ]
        paragraphs = [
            para.text.strip()
            for para in doc.paragraphs    # 删除 enumerate，直接遍历 paragraphs
            if para.text.strip()          # 保留非空段落
        ]

        # 生成标准JSON格式
        return jsonify(paragraphs)

    except Exception as e:
        # 异常处理
        return jsonify({
            "error": "文件处理失败",
            "detail": str(e)
        }), 500