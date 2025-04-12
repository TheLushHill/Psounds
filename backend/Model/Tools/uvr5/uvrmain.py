import os, sys;
sys.path.append(os.path.dirname(__file__));
import traceback
import logging
import subprocess
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
        file_list = []
        if os.path.isdir(paths):
            for filename in os.listdir(paths):
                file_list.append(os.path.join(paths, filename)) 
        elif os.path.isfile(paths):
            file_list = [paths]
        else:
            raise ValueError(f"Invalid path: {paths}")
        # path = clean_path(os.path.join(paths, path));
        # save_root_vocal = clean_path(save_root_vocal)
        # save_root_ins = clean_path(save_root_ins)
        func = AudioPre
        pre_fun = func(
            agg=10,
            model_path=os.path.join(weight_uvr5_root, model_name + ".pth"),
            device=device,
            is_half=is_half,
        )
        
        for path in file_list: 
            try:
                need_reformat = 1
                done = 0
                # 检查文件格式
                try:
                    info = ffmpeg.probe(path, cmd=f"{os.getcwd()}\\Model\\ffprobe.exe")
                    if (
                        info["streams"][0]["channels"] == 2
                        and info["streams"][0]["sample_rate"] == "44100"
                    ):
                        need_reformat = 0
                        pre_fun._path_audio_(
                            path, save_root_ins, save_root_vocal, format0, False
                        )
                        done = 1
                except Exception as e:
                    infos.append(f"File {os.path.basename(path)} probe error: {str(e)}")
                    continue

                # 格式转换逻辑
                if need_reformat == 1:
                    tmp_path = os.path.join(
                        os.environ["TEMP"],
                        f"{os.path.basename(path)}.reformatted.wav"
                    )

                    subprocess.run([
                        f"{os.getcwd()}\\Model\\ffmpeg.exe",
                        "-i", path,
                        "-vn",
                        "-acodec", "pcm_s16le",
                        "-ac", "2",
                        "-ar", "44100",
                        tmp_path,
                        "-y"
                        ], check=True)
                    # os.system(
                    #     f'"{os.getcwd()}\\Model\\ffmpeg.exe" -i "{path}" -vn -acodec pcm_s16le -ac 2 -ar 44100 "{tmp_path}" -y'
                    # )
                    path = tmp_path

                # 处理音频
                if done == 0:
                    pre_fun._path_audio_(
                        path, save_root_ins, save_root_vocal, format0, False
                    )
                infos.append(f"{os.path.basename(path)} -> Success")

            except Exception as e:
                infos.append(f"{os.path.basename(path)} -> Error: {traceback.format_exc()}")
                continue

        return "\n".join(infos)
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
    