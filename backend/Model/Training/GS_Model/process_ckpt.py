# 处理模型检查点文件，支持：LoRA 权重合并，量化压缩，版本兼容性修复

import traceback
from collections import OrderedDict
from time import time as ttime
import shutil,os
import torch
from Tools.i18n.i18n import I18nAuto

i18n = I18nAuto()

def my_save(fea,path):#####fix issue: torch.save doesn't support chinese path
    dir=os.path.dirname(path)
    name=os.path.basename(path)
    tmp_path="%s.pth"%(ttime())
    torch.save(fea,tmp_path)
    shutil.move(tmp_path,"%s/%s"%(dir,name))

def savee(exp_name,ckpt, name, epoch, steps, hps):
    try:
        opt = OrderedDict()
        opt["weight"] = {}
        for key in ckpt.keys():
            if "enc_q" in key:
                continue
            opt["weight"][key] = ckpt[key].half()
        opt["config"] = hps
        opt["info"] = "%sepoch_%siteration" % (epoch, steps)
        # torch.save(opt, "%s/%s.pth" % (hps.save_weight_dir, name))
        my_save(opt, "%s/%s.pth" % (f"Model\\trained\\{exp_name}", name))
        return "Success."
    except:
        return traceback.format_exc()
