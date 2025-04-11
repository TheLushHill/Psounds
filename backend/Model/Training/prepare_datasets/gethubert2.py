import sys, os
from Model.Training.GS_Model.feature_extractor import cnhubert
import pdb, traceback, numpy as np, logging
from scipy.io import wavfile
import librosa, torch
sys.path.append(os.getcwd())
from Model.Training.my_utils import load_audio
import shutil, subprocess  # 添加 subprocess 用于检查 ffmpeg 路径
from time import time as ttime

def get_hubert(exp_name):
    inp_dir = os.path.abspath("Model/Training/List_file/list1")  # 输入目录
    inp_text = os.path.abspath("Model\\Training\\List_file\\list1\\2_name2text_0.txt")
    inp_wav_dir = os.path.abspath("Model/Tools/output_cache/slicer_opt")
    i_part = 0
    all_parts = 1
    opt_dir = "Model\\Training\\List_file\\list2"
    cnhubert.cnhubert_base_path = "Model\\Training\\pretrained_models\\chinese-hubert-base"
    is_half = False
    os.environ["CUDA_VISIBLE_DEVICES"] = os.environ.get("_CUDA_VISIBLE_DEVICES", "0")

    def my_save(fea,path):#####fix issue: torch.save doesn't support chinese path
        dir=os.path.dirname(path)
        name=os.path.basename(path)
        # tmp_path="%s/%s%s.pth"%(dir,ttime(),i_part)
        tmp_path="%s%s.pth"%(ttime(),i_part)
        torch.save(fea,tmp_path)
        shutil.move(tmp_path,"%s/%s"%(dir,name))

    hubert_dir="%s/4_cnhubert"%(opt_dir)
    wav32dir="%s/5_wav32k"%(opt_dir)
    os.makedirs(opt_dir,exist_ok=True)
    os.makedirs(hubert_dir,exist_ok=True)
    os.makedirs(wav32dir,exist_ok=True)

    maxx=0.95
    alpha=0.5
    if torch.cuda.is_available():
        device = "cuda:0"
    # elif torch.backends.mps.is_available():
    #     device = "mps"
    else:
        device = "cpu"
    model=cnhubert.get_model()
    # is_half=False
    if(is_half==True):
        model=model.half().to(device)
    else:
        model = model.to(device)

    nan_fails=[]
    def name2go(wav_name,wav_path):
        hubert_path="%s/%s.pt"%(hubert_dir,wav_name)
        if(os.path.exists(hubert_path)):return
        tmp_audio = load_audio(wav_path, 32000)
        tmp_max = np.abs(tmp_audio).max()
        if tmp_max > 2.2:
            print("%s-filtered,%s" % (wav_name, tmp_max))
            return
        tmp_audio32 = (tmp_audio / tmp_max * (maxx * alpha*32768)) + ((1 - alpha)*32768) * tmp_audio
        tmp_audio32b = (tmp_audio / tmp_max * (maxx * alpha*1145.14)) + ((1 - alpha)*1145.14) * tmp_audio
        tmp_audio = librosa.resample(
            tmp_audio32b, orig_sr=32000, target_sr=16000
        )#不是重采样问题
        tensor_wav16 = torch.from_numpy(tmp_audio)
        if (is_half == True):
            tensor_wav16=tensor_wav16.half().to(device)
        else:
            tensor_wav16 = tensor_wav16.to(device)
        ssl=model.model(tensor_wav16.unsqueeze(0))["last_hidden_state"].transpose(1,2).cpu()#torch.Size([1, 768, 215])
        if np.isnan(ssl.detach().numpy()).sum()!= 0:
            nan_fails.append((wav_name,wav_path))
            print("nan filtered:%s"%wav_name)
            return
        wavfile.write(
            "%s/%s"%(wav32dir,wav_name),
            32000,
            tmp_audio32.astype("int16"),
        )
        my_save(ssl,hubert_path)

    with open(inp_text,"r",encoding="utf8")as f:
        lines=f.read().strip("\n").split("\n")

    for line in lines[int(i_part)::int(all_parts)]:
        try:
            # 使用制表符分割四个字段（适配slice2bert的输出格式）
            parts = line.strip().split("\t")
            if len(parts) != 4:
                print(f"格式错误行：{line}")
                continue
                
            wav_name, phones, word2ph, norm_text = parts  # 按顺序解包
            
            # 处理音频路径（保持原有逻辑）
            if inp_wav_dir:
                base_name = os.path.basename(wav_name)
                wav_path = os.path.join(inp_wav_dir, base_name)
            else:
                wav_path = wav_name
                
            name2go(os.path.basename(wav_name), wav_path)
        except Exception as e:
            print(f"处理行时出错：{line}")
            print(traceback.format_exc())
    print("hubert提取完成")
