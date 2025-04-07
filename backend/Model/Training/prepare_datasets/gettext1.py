import os
import sys, numpy as np, traceback
import os.path
from glob import glob
from tqdm import tqdm
import torch
from transformers import AutoModelForMaskedLM, AutoTokenizer
from time import time as ttime
import shutil
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "Modle/Training/text/cleaner")))
from Model.Training.text.cleaner import clean_text

def slice2bert(inp_list, exp_name):
    inp_wav_dir = "Model\\Tools\\output_cache\\slicer_opt"  # 切分音频文件的目录
    i_part = 0
    all_parts = 1
    opt_dir = "Model\\Training\\List_file\\list1"       # 生成文本文件，每行包含音频文件名、音素序列、单词到音素的映射和规范化文本。
    bert_pretrained_dir = "Model\\Training\\pretrained_models\\chinese-roberta-wwm-ext-large"  # 输出BERT
    is_half = True
    os.environ["CUDA_VISIBLE_DEVICES"] = os.environ.get("_CUDA_VISIBLE_DEVICES", "0")
    failed_audio_log = "%s/failed_audio_%s.log" % (opt_dir, i_part)  # 记录处理失败的音频

    #保存张量fea到指定路径path，解决 torch.save 不支持中文路径的问题。使用 shutil.move 将临时文件移动到目标路径
    def my_save(fea,path):                
        dir=os.path.dirname(path)
        name=os.path.basename(path)
        tmp_path="%s%s.pth"%(ttime(),i_part)
        torch.save(fea,tmp_path)
        shutil.move(tmp_path,"%s/%s"%(dir,name))
        os.remove(tmp_path)

    txt_path = "%s/2_name2text_%s.txt" % (opt_dir, i_part)
    if os.path.exists(txt_path) == False:
        bert_dir = "%s/3_bert" % (opt_dir)
        os.makedirs(opt_dir, exist_ok=True)
        os.makedirs(bert_dir, exist_ok=True)
        if torch.cuda.is_available():
            device = "cuda:0"
        # elif torch.backends.mps.is_available():
        #     device = "mps"
        else:
            device = "cpu"
        tokenizer = AutoTokenizer.from_pretrained(bert_pretrained_dir)
        bert_model = AutoModelForMaskedLM.from_pretrained(bert_pretrained_dir)
        if is_half == True:
            bert_model = bert_model.half().to(device)
        else:
            bert_model = bert_model.to(device)

        #根据输入文本text和单词到音素的映射word2ph，生成 BERT 特征，返回fea给my_save函数保存
        def get_bert_feature(text, word2ph):
            with torch.no_grad():
                inputs = tokenizer(text, return_tensors="pt")
                for i in inputs:
                    inputs[i] = inputs[i].to(device)
                res = bert_model(**inputs, output_hidden_states=True)
                res = torch.cat(res["hidden_states"][-3:-2], -1)[0].cpu()[1:-1]

            assert len(word2ph) == len(text)
            phone_level_feature = []
            for i in range(len(word2ph)):
                repeat_feature = res[i].repeat(word2ph[i], 1)
                phone_level_feature.append(repeat_feature)

            phone_level_feature = torch.cat(phone_level_feature, dim=0)

            return phone_level_feature.T

        # 处理输入数据，生成音素序列、BERT 特征等，并保存结果。
        # 遍历输入数据（data）。
        # 使用 clean_text 清理文本并生成音素序列、单词到音素的映射和规范化文本。
        # 如果语言为中文（lan == "zh"），调用 get_bert_feature 生成 BERT 特征并保存。
        # 将结果追加到 res 空列表。
        def process(data, res):
            failed_audio = []  # 用于记录处理失败的音频
            for name, text, lan in data:
                try:
                    name = os.path.basename(name)
                    phones, word2ph, norm_text = clean_text(
                        text.replace("%", "-").replace("￥", ","), lan
                    )
                    path_bert = "%s/%s.pt" % (bert_dir, name)
                    if os.path.exists(path_bert) == False and lan == "zh":
                        bert_feature = get_bert_feature(norm_text, word2ph)
                        assert bert_feature.shape[-1] == len(phones)
                        my_save(bert_feature, path_bert)
                    phones = " ".join(phones)
                    res.append([name, phones, word2ph, norm_text])
                except Exception as e:
                    failed_audio.append(f"{name}\t{text}\t{lan}\t{str(e)}")
                    print(name, text, traceback.format_exc())
            
            # 将处理失败的音频记录到日志文件
            if failed_audio:
                with open(failed_audio_log, "w", encoding="utf8") as f:
                    f.write("\n".join(failed_audio) + "\n")

        todo = []
        res = []
        with open(inp_list, "r", encoding="utf8") as f:
            lines = f.read().strip("\n").split("\n")

        language_map = {
            "ZH": "zh",
            "zh": "zh",
            "EN": "en",
            "en": "en",
            "En": "en",
        }
        for line in lines[int(i_part) :: int(all_parts)]:
            try:
                wav_name, spk_name, language, text = line.split("|")
                # todo.append([name,text,"zh"])
                if language in language_map.keys():
                    todo.append(
                        [wav_name, text, language_map.get(language, language)]
                    )
                else:
                    print(f"\033[33m[Waring] The {language = } of {wav_name} is not supported for training.\033[0m")
            except:
                print(line, traceback.format_exc())

        process(todo, res)
        opt = []
        for name, phones, word2ph, norm_text in res:
            opt.append("%s\t%s\t%s\t%s" % (name, phones, word2ph, norm_text))
        with open(txt_path, "w", encoding="utf8") as f:
            f.write("\n".join(opt) + "\n")

        # 如果没有任何音频被处理，提示用户检查输入文件或日志
        if not res:
            print(f"\033[31m[Error] No audio was processed. Check {failed_audio_log} for details.\033[0m")
    print("text提取完成")
