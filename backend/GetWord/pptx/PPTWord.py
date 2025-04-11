from flask import jsonify
from pptx import Presentation
from io import BytesIO

def get_ppttext(file):
    try:
        file_stream = BytesIO(file.read())
        prs = Presentation(file_stream)

        # 创建按幻灯片分组的列表
        result = []

        # 提取本页所有文本内容（包含标题和正文）
        for slide_idx, slide in enumerate(prs.slides, 1):
            texts = []

            # 统一处理所有文本框的形状
            for shape in slide.shapes:
                # 1. 处理常规文本框和占位符
                if shape.has_text_frame:
                    for para in shape.text_frame.paragraphs:
                        if para.text.strip():
                            texts.append(para.text.strip())

                # 2. 处理表格
                elif shape.has_table:
                    table = shape.table
                    for row in table.rows:
                        for cell in row.cells:
                            if cell.text.strip():
                                texts.append(cell.text.strip())

                # 3. 处理组形状（递归遍历子形状）
                elif shape.shape_type == 6:
                    for sub_shape in shape.shapes:
                        if sub_shape.has_text_frame:
                            for para in sub_shape.text_frame.paragraphs:
                                if para.text.strip():
                                    texts.append(para.text.strip())

            if texts:
                result.append(texts)

        return result

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        file_stream.close()
