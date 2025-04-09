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