import os,sys, pdb
import math, traceback
import multiprocessing
now_dir = os.getcwd()
sys.path.append(now_dir)

from random import shuffle
import torch.multiprocessing as mp
from glob import glob
from tqdm import tqdm
import logging, librosa, Model.Training.GS_Model.utils, torch
from Model.Training.GS_Model.module.models import SynthesizerTrn

logging.getLogger("numba").setLevel(logging.WARNING)

def get_semanic(exp_name):
    inp_text = "Model\\Training\\List_file\\list1\\2_name2text_0.txt"
    inp_wav_dir = "Model\\Tools\\output_cache\\slicer_opt"
    i_part = 0
    all_parts = 1
    os.environ["CUDA_VISIBLE_DEVICES"] = os.environ.get("_CUDA_VISIBLE_DEVICES", "0")
    opt_dir = "Model\\Training\\List_file\\list3"
    pretrained_s2G = "Model\\Training\\pretrained_models\\gsv-v2final-pretrained\\s2G2333k.pth"
    s2config_path = "Model\\Training\\Gs_Model\\configs\\s2.json"
    is_half = False
    
    hubert_dir = "Model\\Training\\List_file\\list2\\4_cnhubert"
    semantic_path = "%s/6_name2semantic_%s.tsv" % (opt_dir, i_part)
    if os.path.exists(semantic_path) == False:
        os.makedirs(opt_dir, exist_ok=True)

        if torch.cuda.is_available():
            device = "cuda"
        # elif torch.backends.mps.is_available():
        #     device = "mps"
        else:
            device = "cpu"
        hps = Model.Training.GS_Model.utils.get_hparams_from_file(s2config_path)
        vq_model = SynthesizerTrn(
            hps.data.filter_length // 2 + 1,
            hps.train.segment_size // hps.data.hop_length,
            n_speakers=hps.data.n_speakers,
            **hps.model
        )
        if is_half == True:
            vq_model = vq_model.half().to(device)
        else:
            vq_model = vq_model.to(device)
        vq_model.eval()

        try:
            vq_model.load_state_dict(
                torch.load(pretrained_s2G, map_location="cpu"), strict=False
            )
            print("部分参数形状不匹配，已跳过加载。")
        except RuntimeError as e:
            print(f"模型权重加载失败: {e}")
            return

        def name2go(wav_name, lines):
            hubert_path = "%s/%s.pt" % (hubert_dir, wav_name)
            if os.path.exists(hubert_path) == False:
                return
            ssl_content = torch.load(hubert_path, map_location="cpu")
            if is_half == True:
                ssl_content = ssl_content.half().to(device)
            else:
                ssl_content = ssl_content.to(device)
            codes = vq_model.extract_latent(ssl_content)
            semantic = " ".join([str(i) for i in codes[0, 0, :].tolist()])
            lines.append("%s\t%s" % (wav_name, semantic))

        with open(inp_text, "r", encoding="utf8") as f:
            lines = f.read().strip("\n").split("\n")

        lines1 = []
        for line in lines[int(i_part) :: int(all_parts)]:
            # print(line)
            try:
                # wav_name,text=line.split("\t")
                wav_name, spk_name, language, text = line.strip().split("\t")
                wav_name = os.path.basename(wav_name)
                # name2go(name,lines1)
                name2go(wav_name, lines1)
            except:
                print(line, traceback.format_exc())
        with open(semantic_path, "w", encoding="utf8") as f:
            f.write("\n".join(lines1))
    print("sematic-token提取完成")
