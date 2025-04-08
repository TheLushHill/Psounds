import os, sys;
sys.path.append(os.path.dirname(__file__));
import traceback
import logging
from Model.Tools.my_utils import clean_path

logger = logging.getLogger(__name__)
import librosa,ffmpeg
import soundfile as sf
import torch
from Model.config import infer_device,is_half,is_share;

from mdxnet import MDXNetDereverb
from vr import AudioPre, AudioPreDeEcho

weight_uvr5_root = os.path.join(os.path.dirname(__file__), "uvr5_weights");
model_name = "HP5_only_main_vocal";
format0 = "wav";

device=infer_device;

def uvr(paths, save_root_vocal, save_root_ins):
    infos = []
    try:
        if os.path.isdir(paths):
            for path in os.listdir(paths):
                path = path;
        elif os.path.isfile(paths):
            path = paths;
        else:
            raise ValueError(f"Invalid path: {paths}")
        path = clean_path(os.path.join(paths, path));
        save_root_vocal = clean_path(save_root_vocal)
        save_root_ins = clean_path(save_root_ins)
        func = AudioPre
        pre_fun = func(
            agg=10,
            model_path=os.path.join(weight_uvr5_root, model_name + ".pth"),
            device=device,
            is_half=is_half,
        )
        
        need_reformat = 1
        done = 0
        print(f"{os.getcwd()}\\Model\\ffprobe.exe")
        try:
            info = ffmpeg.probe(path, cmd=f"{os.getcwd()}\\Model\\ffprobe.exe")
            if (
                info["streams"][0]["channels"] == 2
                and info["streams"][0]["sample_rate"] == "44100"
            ):
                need_reformat = 0
                pre_fun._path_audio_(
                    path, save_root_ins, save_root_vocal, format0,False
                )
                done = 1
        except:
            need_reformat = 1
            traceback.print_exc()
        if need_reformat == 1:
            tmp_path = "%s/%s.reformatted.wav" % (
                os.path.join(os.environ["TEMP"]),
                os.path.basename(path),
            )
            os.system(
                f'{os.getcwd()}\\Model\\ffmpeg.exe -i "{path}" -vn -acodec pcm_s16le -ac 2 -ar 44100 "{tmp_path}" -y'
            )
            path = tmp_path
        try:
            if done == 0:
                pre_fun._path_audio_(
                    path, save_root_ins, save_root_vocal, format0,False
                )
            infos.append("%s->Success" % (os.path.basename(path)))
            return "Success"
        except:
            infos.append(
                "%s->%s" % (os.path.basename(path), traceback.format_exc())
            )
    except:
        infos.append(traceback.format_exc())
    finally:
        try:
            if model_name == "onnx_dereverb_By_FoxJoy":
                del pre_fun.pred.model
                del pre_fun.pred.model_
            else:
                del pre_fun.model
                del pre_fun
        except:
            traceback.print_exc()
        print("clean_empty_cache")
        print("\n".join(infos))
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    