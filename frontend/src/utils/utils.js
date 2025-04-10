//交换数组中两个元素的位置
export function moveToHead(Array, index) {
    Array.unshift(Array.splice(index, 1)[0]);
}

export function parseWavHeader(buffer) {
    const dv = new DataView(buffer);
    const numChannels   = dv.getUint16(22, true);
    const sampleRate    = dv.getUint32(24, true);
    const bitsPerSample = dv.getUint16(34, true);
    return { numChannels, sampleRate, bitsPerSample };
}

export function pcmToFloat32(pcmBuffer, bitsPerSample) {
    const bytesPerSample = bitsPerSample / 8;
    // 用 Math.floor 保证整数个样本
    const sampleCount = Math.floor(pcmBuffer.byteLength / bytesPerSample);
    const float32 = new Float32Array(sampleCount);
    const dv = new DataView(pcmBuffer.buffer, pcmBuffer.byteOffset, sampleCount * bytesPerSample);

    for (let i = 0; i < sampleCount; i++) {
      let sample = 0;
      const offset = i * bytesPerSample;
      if (bitsPerSample === 16) {
        sample = dv.getInt16(offset, true) / 0x8000;
      } else if (bitsPerSample === 8) {
        sample = (dv.getUint8(offset) - 128) / 128;
      }
      float32[i] = sample;
    }
    return float32;
}

/**
 * @param {Object} opts
 * @param {number} opts.pcmByteLength  PCM 数据总字节数
 * @param {number} opts.sampleRate     采样率，例如 32000
 * @param {number} opts.numChannels    声道数，例如 1
 * @param {number} opts.bytesPerSample 每个采样点字节数，例如 2（16 位）
 * @returns {ArrayBuffer} 44 字节的 WAV 头
 */
export function makeWavHeader({ pcmByteLength, sampleRate, numChannels, bytesPerSample }) {
  const blockAlign = numChannels * bytesPerSample;
  const byteRate = sampleRate * blockAlign;
  const dataChunkSize = pcmByteLength;
  const riffChunkSize = 36 + dataChunkSize;

  const buf = new ArrayBuffer(44);
  const dv = new DataView(buf);

  // RIFF 标识符
  writeString(dv, 0, 'RIFF');
  dv.setUint32(4, riffChunkSize, true);       // 文件长度 − 8
  writeString(dv, 8, 'WAVE');

  // fmt 子块
  writeString(dv, 12, 'fmt ');
  dv.setUint32(16, 16, true);                  // PCM fmt 块大小
  dv.setUint16(20, 1, true);                   // 音频格式 = PCM
  dv.setUint16(22, numChannels, true);
  dv.setUint32(24, sampleRate, true);
  dv.setUint32(28, byteRate, true);
  dv.setUint16(32, blockAlign, true);
  dv.setUint16(34, bytesPerSample * 8, true);  // 位深度

  // data 子块
  writeString(dv, 36, 'data');
  dv.setUint32(40, dataChunkSize, true);

  return buf;
}

function writeString(dv, offset, str) {
  for (let i = 0; i < str.length; i++) {
    dv.setUint8(offset + i, str.charCodeAt(i));
  }
}