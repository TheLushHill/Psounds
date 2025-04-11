import os, sys, numpy as np
import traceback
from scipy.io import wavfile
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from my_utils import load_audio
from slicer2 import Slicer

def slice_audio(inp, opt_root):
    """
    切分音频文件并返回生成的音频文件路径列表。

    :param inp: 输入音频文件路径或文件夹路径
    :param opt_root: 输出切分后的音频文件夹路径
    :return: 切分后的音频文件路径列表或错误信息
    """
    os.makedirs(opt_root, exist_ok=True)
    if os.path.isfile(inp):
        input_files = [inp]
    elif os.path.isdir(inp):
        input_files = [os.path.join(inp, name) for name in sorted(list(os.listdir(inp)))]
    else:
        return "输入路径存在但既不是文件也不是文件夹"

    slicer = Slicer(
        sr=32000,  # 长音频采样率
        threshold=-34,  # 音量小于这个值视作静音的备选切割点
        min_length=4000,  # 每段最小长度（毫秒）
        min_interval=300,  # 最短切割间隔（毫秒）
        hop_size=10,  # 音量曲线的帧长度（毫秒）
        max_sil_kept=500,  # 切分后静音最多保留的长度（毫秒）
    )
    _max = 0.9  # 音频最大幅度
    alpha = 0.25  # 音频幅度调整参数
    i_part = 0  # 当前分片索引（用于多线程或分片处理）
    all_part = 1  # 总分片数（用于多线程或分片处理）

    output_files = []  # 用于存储生成的音频文件路径
    for inp_path in input_files[int(i_part)::int(all_part)]:
        try:
            name = os.path.basename(inp_path)   
            audio = load_audio(inp_path, 32000)
            for chunk, start, end in slicer.slice(audio):  # start 和 end 是帧数
                tmp_max = np.abs(chunk).max()
                if tmp_max > 1:
                    chunk /= tmp_max
                chunk = (chunk / tmp_max * (_max * alpha)) + (1 - alpha) * chunk
                output_path = "%s/%s_%010d_%010d.wav" % (opt_root, name, start, end)
                wavfile.write(
                    output_path,
                    32000,
                    (chunk * 32767).astype(np.int16),
                )
                output_files.append(output_path)  # 将生成的音频文件路径添加到列表中
        except Exception as e:
            print(f"{inp_path} -> fail -> {traceback.format_exc()}")

    return output_files if output_files else "未生成任何音频文件，请检查输入文件是否有效。"
