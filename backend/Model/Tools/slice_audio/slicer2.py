import numpy as np  # 导入NumPy库，用于数值计算

# This function is obtained from librosa.
def get_rms(
    y,
    frame_length=2048,  # 帧长度，默认为2048
    hop_length=512,  # 帧移长度，默认为512
    pad_mode="constant",  # 填充模式，默认为"constant"
):
    padding = (int(frame_length // 2), int(frame_length // 2))  # 计算填充长度
    y = np.pad(y, padding, mode=pad_mode)  # 对信号进行填充

    axis = -1  # 选择最后一个轴
    out_strides = y.strides + tuple([y.strides[axis]])  # 计算输出的步长
    x_shape_trimmed = list(y.shape)  # 获取输入信号的形状
    x_shape_trimmed[axis] -= frame_length - 1  # 调整形状以适应帧长度
    out_shape = tuple(x_shape_trimmed) + tuple([frame_length])  # 计算输出形状
    xw = np.lib.stride_tricks.as_strided(y, shape=out_shape, strides=out_strides)  # 创建滑动窗口
    if axis < 0:
        target_axis = axis - 1  # 计算目标轴
    else:
        target_axis = axis + 1
    xw = np.moveaxis(xw, -1, target_axis)  # 移动轴以匹配目标轴
    slices = [slice(None)] * xw.ndim  # 创建切片对象
    slices[axis] = slice(0, None, hop_length)  # 设置切片步长
    x = xw[tuple(slices)]  # 应用切片

    power = np.mean(np.abs(x) ** 2, axis=-2, keepdims=True)  # 计算功率

    return np.sqrt(power)  # 返回RMS值


class Slicer:
    def __init__(
        self,
        sr: int,  # 采样率
        threshold: float = -40.0,  # 静音检测的dB阈值
        min_length: int = 5000,  # 最小音频片段长度（毫秒）
        min_interval: int = 300,  # 最小静音间隔（毫秒）
        hop_size: int = 20,  # 帧移长度（毫秒）
        max_sil_kept: int = 5000,  # 最大保留静音长度（毫秒）
    ):
        if not min_length >= min_interval >= hop_size:  # 检查参数是否满足条件
            raise ValueError(
                "The following condition must be satisfied: min_length >= min_interval >= hop_size"
            )
        if not max_sil_kept >= hop_size:  # 检查最大静音保留长度是否满足条件
            raise ValueError(
                "The following condition must be satisfied: max_sil_kept >= hop_size"
            )
        min_interval = sr * min_interval / 1000  # 将静音间隔从毫秒转换为采样点
        self.threshold = 10 ** (threshold / 20.0)  # 将dB阈值转换为线性比例
        self.hop_size = round(sr * hop_size / 1000)  # 将帧移长度从毫秒转换为采样点
        self.win_size = min(round(min_interval), 4 * self.hop_size)  # 计算窗口大小
        self.min_length = round(sr * min_length / 1000 / self.hop_size)  # 计算最小片段长度（帧数）
        self.min_interval = round(min_interval / self.hop_size)  # 计算最小静音间隔（帧数）
        self.max_sil_kept = round(sr * max_sil_kept / 1000 / self.hop_size)  # 计算最大静音保留长度（帧数）

    def _apply_slice(self, waveform, begin, end):  # 应用切片操作
        if len(waveform.shape) > 1:  # 如果是多通道音频
            return waveform[
                :, begin * self.hop_size : min(waveform.shape[1], end * self.hop_size)
            ]  # 返回切片后的音频
        else:  # 如果是单通道音频
            return waveform[
                begin * self.hop_size : min(waveform.shape[0], end * self.hop_size)
            ]  # 返回切片后的音频

    # @timeit
    def slice(self, waveform):  # 切片主函数
        if len(waveform.shape) > 1:  # 如果是多通道音频
            samples = waveform.mean(axis=0)  # 取平均值作为单通道信号
        else:
            samples = waveform  # 单通道信号直接使用
        if samples.shape[0] <= self.min_length:  # 如果音频长度小于最小片段长度
            return [waveform]  # 返回原始音频
        rms_list = get_rms(
            y=samples, frame_length=self.win_size, hop_length=self.hop_size
        ).squeeze(0)  # 计算RMS值列表
        sil_tags = []  # 初始化静音标签列表
        silence_start = None  # 初始化静音开始位置
        clip_start = 0  # 初始化片段开始位置
        for i, rms in enumerate(rms_list):  # 遍历RMS值
            # Keep looping while frame is silent.
            if rms < self.threshold:  # 如果RMS值小于阈值
                # Record start of silent frames.
                if silence_start is None:  # 如果静音开始位置未记录
                    silence_start = i  # 记录静音开始位置
                continue
            # Keep looping while frame is not silent and silence start has not been recorded.
            if silence_start is None:  # 如果静音开始位置未记录
                continue
            # Clear recorded silence start if interval is not enough or clip is too short
            is_leading_silence = silence_start == 0 and i > self.max_sil_kept  # 判断是否为前导静音
            need_slice_middle = (
                i - silence_start >= self.min_interval
                and i - clip_start >= self.min_length
            )  # 判断是否需要在中间切片
            if not is_leading_silence and not need_slice_middle:  # 如果不需要切片
                silence_start = None  # 清除静音开始位置
                continue
            # Need slicing. Record the range of silent frames to be removed.
            if i - silence_start <= self.max_sil_kept:  # 如果静音长度小于最大保留长度
                pos = rms_list[silence_start : i + 1].argmin() + silence_start  # 找到静音最小值位置
                if silence_start == 0:
                    sil_tags.append((0, pos))  # 添加静音标签
                else:
                    sil_tags.append((pos, pos))  # 添加静音标签
                clip_start = pos  # 更新片段开始位置
            elif i - silence_start <= self.max_sil_kept * 2:  # 如果静音长度小于最大保留长度的两倍
                pos = rms_list[
                    i - self.max_sil_kept : silence_start + self.max_sil_kept + 1
                ].argmin()
                pos += i - self.max_sil_kept
                pos_l = (
                    rms_list[
                        silence_start : silence_start + self.max_sil_kept + 1
                    ].argmin()
                    + silence_start
                )
                pos_r = (
                    rms_list[i - self.max_sil_kept : i + 1].argmin()
                    + i
                    - self.max_sil_kept
                )
                if silence_start == 0:
                    sil_tags.append((0, pos_r))
                    clip_start = pos_r
                else:
                    sil_tags.append((min(pos_l, pos), max(pos_r, pos)))
                    clip_start = max(pos_r, pos)
            else:
                pos_l = (
                    rms_list[
                        silence_start : silence_start + self.max_sil_kept + 1
                    ].argmin()
                    + silence_start
                )
                pos_r = (
                    rms_list[i - self.max_sil_kept : i + 1].argmin()
                    + i
                    - self.max_sil_kept
                )
                if silence_start == 0:
                    sil_tags.append((0, pos_r))
                else:
                    sil_tags.append((pos_l, pos_r))
                clip_start = pos_r
            silence_start = None
        # Deal with trailing silence.
        total_frames = rms_list.shape[0]  # 获取总帧数
        if (
            silence_start is not None
            and total_frames - silence_start >= self.min_interval
        ):  # 如果存在尾部静音且长度满足条件
            silence_end = min(total_frames, silence_start + self.max_sil_kept)  # 计算静音结束位置
            pos = rms_list[silence_start : silence_end + 1].argmin() + silence_start  # 找到静音最小值位置
            sil_tags.append((pos, total_frames + 1))  # 添加静音标签
        # Apply and return slices.
        ####音频+起始时间+终止时间
        if len(sil_tags) == 0:  # 如果没有静音标签
            return [[waveform, 0, int(total_frames * self.hop_size)]]  # 返回完整音频
        else:
            chunks = []  # 初始化音频片段列表
            if sil_tags[0][0] > 0:  # 如果第一个静音标签的起始位置大于0
                chunks.append([self._apply_slice(waveform, 0, sil_tags[0][0]), 0, int(sil_tags[0][0] * self.hop_size)])  # 添加第一个片段
            for i in range(len(sil_tags) - 1):  # 遍历静音标签
                chunks.append(
                    [self._apply_slice(waveform, sil_tags[i][1], sil_tags[i + 1][0]), int(sil_tags[i][1] * self.hop_size), int(sil_tags[i + 1][0] * self.hop_size)]
                )  # 添加中间片段
            if sil_tags[-1][1] < total_frames:  # 如果最后一个静音标签的结束位置小于总帧数
                chunks.append(
                    [self._apply_slice(waveform, sil_tags[-1][1], total_frames), int(sil_tags[-1][1] * self.hop_size), int(total_frames * self.hop_size)]
                )  # 添加最后一个片段
            return chunks  # 返回所有片段


def main():
    import os.path
    from argparse import ArgumentParser

    import librosa
    import soundfile

    parser = ArgumentParser()
    parser.add_argument("audio", type=str, help="The audio to be sliced")
    parser.add_argument(
        "--out", type=str, help="Output directory of the sliced audio clips"
    )
    parser.add_argument(
        "--db_thresh",
        type=float,
        required=False,
        default=-40,
        help="The dB threshold for silence detection",
    )
    parser.add_argument(
        "--min_length",
        type=int,
        required=False,
        default=5000,
        help="The minimum milliseconds required for each sliced audio clip",
    )
    parser.add_argument(
        "--min_interval",
        type=int,
        required=False,
        default=300,
        help="The minimum milliseconds for a silence part to be sliced",
    )
    parser.add_argument(
        "--hop_size",
        type=int,
        required=False,
        default=10,
        help="Frame length in milliseconds",
    )
    parser.add_argument(
        "--max_sil_kept",
        type=int,
        required=False,
        default=500,
        help="The maximum silence length kept around the sliced clip, presented in milliseconds",
    )
    args = parser.parse_args()
    out = args.out
    if out is None:
        out = os.path.dirname(os.path.abspath(args.audio))
    audio, sr = librosa.load(args.audio, sr=None, mono=False)
    slicer = Slicer(
        sr=sr,
        threshold=args.db_thresh,
        min_length=args.min_length,
        min_interval=args.min_interval,
        hop_size=args.hop_size,
        max_sil_kept=args.max_sil_kept,
    )
    chunks = slicer.slice(audio)
    if not os.path.exists(out):
        os.makedirs(out)
    for i, chunk in enumerate(chunks):
        if len(chunk.shape) > 1:
            chunk = chunk.T
        soundfile.write(
            os.path.join(
                out,
                f"%s_%d.wav"
                % (os.path.basename(args.audio).rsplit(".", maxsplit=1)[0], i),
            ),
            chunk,
            sr,
        )


if __name__ == "__main__":
    main()
