import os, argparse
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks
from tqdm import tqdm

path_denoise = 'Model/Tools/cmd_denoisw/denoise-model/speech_frcrn_ans_cirm_16k'
path_denoise = path_denoise if os.path.exists(path_denoise) else "damo/speech_frcrn_ans_cirm_16k"
ans = pipeline(Tasks.acoustic_noise_suppression, model=path_denoise)

def execute_denoise(input_folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    print(f"开始降噪处理，输入文件夹：{input_folder}，输出文件夹：{output_folder}")
    
    for name in tqdm(os.listdir(input_folder)):
        input_path = os.path.join(input_folder, name)
        output_path = os.path.join(output_folder, name)
        try:
            ans(input_path, output_path=output_path)
            print(f"处理完成：{input_path} -> {output_path}")
        except Exception as e:
            print(f"处理失败：{input_path}，错误信息：{e}")
    
    # 检查输出文件夹是否有文件
    if os.listdir(output_folder):
        print("降噪任务完成，输出文件夹中有文件。")
        return "成功"
    else:
        print("降噪任务失败，输出文件夹为空。")
        return "失败"

# if __name__ == '__main__':
#     parser = argparse.ArgumentParser()
#     parser.add_argument("-i", "--input_folder", type=str, required=True,
#                         help="Path to the folder containing WAV files.")
#     parser.add_argument("-o", "--output_folder", type=str, required=True, 
#                         help="Output folder to store transcriptions.")
#     parser.add_argument("-p", "--precision", type=str, default='float16', choices=['float16','float32'],
#                         help="fp16 or fp32")#还没接入
#     cmd = parser.parse_args()
#     execute_denoise(
#         input_folder  = cmd.input_folder,
#         output_folder = cmd.output_folder,
#     )