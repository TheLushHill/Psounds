简介：

本后端接口启动一次，与前端实现两次交互，前后实现文档转文字、流式转换生成语言功能



项目原理：

1、文档转文字：

判断文档：依据HTTP的MIME类型（媒体类型）判断文档，以分别调用对应的转文字接口

功能扩展：检查请求中是否包含文件，检查文件名是否为空，安全处理文件名，校验后缀名合法，获取文件实际扩展名对应的MIME类型后判断

word文档接口：使用python-docx库，依照二进制流读取，提取并过滤段落para.text.strip()，列表存储

pptx文档接口：使用python-pptx库，依照二进制流读取，将标题视为新的段落储存，引入三位补零键名以创建有序字典来存储



进一步优化：

1）考虑文本的大小，若为1G以下则用二进制流处理，若为1G以上则要保存到本地新建的缓存文件夹。

2）docx的手动增加标题可能无法识别

3）pptx的形状中，有一些透明的图片框内可以加入文字框写文字，这种的无法识别，暂不知道原因

依赖库：  
Flask                             3.0.3  
Flask-Login                       0.6.3  
Flask-WTF                         1.2.1  
httpcore                          1.0.7  
httpx                             0.27.2  
inference                         0.34.0  
inference-server                  1.3.2  
inference-tools                   0.13.4  
Jinja2                            3.1.3  
libmagic                          1.0  
numba                             0.57.1  
numpy                             1.24.1  
python-docx                       1.1.2  
python-magic                      0.4.27  
python-magic-bin                  0.4.14  
python-pptx                       1.0.2  
requests                          2.32.3  
requests-file                     2.1.0  
requests-toolbelt                 1.0.0  
route                             2025.2.23.1  