from flask import jsonify
from pptx import Presentation
from io import BytesIO
from collections import OrderedDict

def get_ppttext(file):
    try:
        file_stream = BytesIO(file.read())
        prs = Presentation(file_stream)

        # 创建按幻灯片分组的字典
        result = {}

        # 提取本页所有文本内容（包含标题和正文）
        for slide_idx, slide in enumerate(prs.slides, 1):
            texts = []
            slide_key = f"{slide_idx:03d}"  # 生成三位补零键名，得以有效排序

            # 统一处理所有文本框的形状
            for shape in slide.shapes:
                # 若为占位符文本（标题/副标题）
                if shape.is_placeholder and shape.placeholder_format.type in [1, 2]:
                    if text := shape.text.strip():
                        texts.append(text)

                # 若为常规文本框
                if shape.has_text_frame and not shape.is_placeholder:
                    for para in shape.text_frame.paragraphs:
                        if text := para.text.strip():
                            texts.append(text)

            # 存储到结果字典
            if texts:
                result[slide_key] = texts

        # 按数字顺序排序后生成有序字典
        ordered_result = OrderedDict(
            sorted(result.items(), key=lambda x: int(x[0]))
        )

        return jsonify(ordered_result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        file_stream.close()

# 有些ppt里的格式是透明的图片框，里面可以写入文字，这种的本程序识别不了，待解决
