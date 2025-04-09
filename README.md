frontend 前端代码文件夹  
使用 npm install 命令安装 package.json 内所需依赖  
安装完成后使用 npm run dev 启动 vite 开发服务器  

backend 后端代码文件夹  

tts 功能说明：
backend/Model/trained 文件夹为角色模型  
backend\Model\GPT_SoVITS\pretrained_models 为预训练模型文件夹  
需保证两个文件夹内有模型才能启动相关功能。在群里下载或者整合包内复制。

预训练功能说明：
backend/Model/Tools/ 为上传音频进行预训练的文件夹  
其中： uvr5文件夹中有uvr5_weights文件夹，存放人声分离及去混响的预训练模型  
      cmd_denoise文件夹中有denoise-model文件夹，存放语音降噪的预训练模型  
      asr文件夹下有models文件夹，用于存放语音合成的预训练模型  
本文件夹下有output_cache文件夹，用于存放预训练中各步骤生成的音频文件，最后生成.list文件  

训练模型功能说明：  
backend/Model/Training/ 为进行格式化及模型训练的文件夹  
其中：pretrained_models为模型的预训练生成模型，用于第一次生成模型时的启动  
本文件夹下有GPT_weights、SoVITS_weights文件夹，用于分别存储GPT模型、SoVITS模型。还有List_file文件夹存放格式化中各步骤生成的文件，用于生成模型。  

backend/Model 本文件夹下：  
input_audio用于存放同一个角色的所有音频。Final_output是最终TTS输出的人物音频。  
ffmpeg文件夹、ffmpeg.exe、ffprobe.exe是处理音频的必要工具，不可能不要。  

其他均与github仓库所示代码相同，不再赘述。  
