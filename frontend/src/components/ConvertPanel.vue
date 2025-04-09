<script>
    import axios from "axios"
    import { parseWavHeader, pcmToFloat32} from "../utils/utils.js"
    export default {
        data() {
            return {
                character: "Hutao",
                blobUrl: null,

                isStreaming: false,
                abortController: null,
                leftover: null,
            }
        },

        mounted() {
            this.audioCtx = new AudioContext();
            this.playTime =this.audioCtx.currentTime;
        },

        methods: {
            async getFullAudio() {
                let input = this.text.join();
                let response = await axios.post("/api/tts", {
                    text: input,
                    character: this.character,

                }, {
                    responseType: "blob",
                })
                let blob = new Blob([response.data], { type: "audio/wav" });
                this.blobUrl = URL.createObjectURL(blob);
                this.$refs.audio.src = this.blobUrl;
                this.$refs.audio.play();
            },

            async getStreamAudio() { 
                try {
                    if (this.isStreaming) return
                    this.isStreaming = true
                    if (this.audioCtx) {
                        await this.audioCtx.close();
                    }
                    this.audioCtx = new AudioContext()
                    this.abortController = new AbortController()
                    // 重置播放指针
                    this.playTime = this.audioCtx.currentTime

                    let response = await fetch("/api/tts_stream", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                        },
                        body: JSON.stringify({
                            "text": this.text.join(),
                            "character": this.character,
                        }),
                        responseType: "audio/wav",
                        
                    });
                    let reader = response.body.getReader();
                    let isFirstChunk = true;
                    let header = null;

                    while (this.isStreaming) {
                        const { done, value } = await reader.read()
                        if (done) break

                        if (isFirstChunk) {
                            // 解析 WAV 头，取出通道数、采样率、位深
                            header = parseWavHeader(value.buffer)
                            isFirstChunk = false
                        } else {
                            this.scheduleAudio(value, header)
                        }
                    }
                } catch (error) {
                    console.error("Error:", error);
                    alert("Error: " + error.message);
                } finally {
                    this.isStreaming = false;
                }
            },
            scheduleAudio(pcmChunk, header) {
                const { numChannels, sampleRate, bitsPerSample } = header;

                const bytesPerSample = bitsPerSample / 8;
                const frameBytes     = bytesPerSample * numChannels;

                // 如果 chunk 太短，直接跳过
                if (pcmChunk.byteLength < frameBytes) return;

                // —— 先把上次剩余的半帧拼接回来 ——
                if (this.leftover && this.leftover.byteLength) {
                    const combined = new Uint8Array(this.leftover.byteLength + pcmChunk.byteLength);
                    combined.set(this.leftover, 0);
                    combined.set(pcmChunk, this.leftover.byteLength);
                    pcmChunk = combined;
                    this.leftover = null;
                }

                // 如果连一帧都不够，直接缓存并返回
                if (pcmChunk.byteLength < frameBytes) {
                    this.leftover = pcmChunk;
                    return;
                }

                // 丢弃尾部不完整的字节
                const remainder = pcmChunk.byteLength % frameBytes;
                if (remainder !== 0) {
                    this.leftover = pcmChunk.slice(pcmChunk.byteLength - remainder);
                    pcmChunk = pcmChunk.slice(0, pcmChunk.byteLength - remainder);
                }

                if (!this.playTime || this.playTime < this.audioCtx.currentTime) {
                    this.playTime = this.audioCtx.currentTime;
                }

                // PCM → Float32Array
                const float32 = pcmToFloat32(pcmChunk, bitsPerSample);
                const frameCount = float32.length / numChannels;

                // 创建 AudioBuffer
                const buffer = this.audioCtx.createBuffer(
                    numChannels,
                    frameCount,
                    sampleRate
                );
                for (let ch = 0; ch < numChannels; ch++) {
                    const channelData = buffer.getChannelData(ch);
                    for (let i = 0; i < frameCount; i++) {
                    channelData[i] = float32[i * numChannels + ch];
                    }
                }

                // 建立播放节点并排队播放
                const src = this.audioCtx.createBufferSource();
                src.buffer = buffer;
                src.connect(this.audioCtx.destination);
                src.start(this.playTime);

                // 推进播放指针
                this.playTime += frameCount / sampleRate;
                
            },
        },
        props: {
            isVisible: Boolean,
            text: {
                type: Array,
                default: () => [],
            },
        }
    }
</script>

<template>
    <div class="convert-panel" v-show="isVisible">
        <div class="view" v-if="text.length === 0">暂无内容，请在预览面板中选择内容。</div>
        <div class="view"v-else>
            <div v-for="(item, index) in text" :key="index" class="text-line">
                <span>{{ item }}</span>
            </div>
        </div>
        <div class="panel">
            <div class="full-audio-bar">
                <button @click="getFullAudio" class="get-full-audio">获取完整音频</button>
                <button @click="getStreamAudio" class="get-stream-audio">获取流式音频</button>
                <audio ref="audio" controls></audio>
            </div>
            <div class="character-bar">
                <span>当前角色模型：</span>
                <select class="character" v-model="character">
                    <option value="Hutao" selected>胡桃</option>
                    <option value="才羽桃井">才羽桃井</option>
                    <option value="神里绫华">神里绫华</option>
                </select>
            </div>
        </div>
    </div>
</template>

<style>
.convert-panel {
    display: flex;
    flex: 1 1 auto;
    flex-direction: column;
    height: 100%; 
    background-color: #fff;
}

.view {
    margin-bottom: 16px;
    overflow-y: auto;
    height: 75%;
}

.text-line {
    display: flex;
    flex-direction: row;
    margin-top: 1em;
    margin-left: 1em;
    line-height: 1.5;
    align-items: flex-start;
}

.panel {
    display: flex;
    background-color: #E5DEE2;
    height:25%;
    margin: 8px;
}

.full-audio-bar {
    display: flex;
    flex-direction: column;
    padding: 8px;
    gap: 16px;
    justify-content: center;
}

.full-audio-bar button {
    height: 3em;
    border-radius: 12px;
    background-color: #DCDAF5;
    border: none;
}

.full-audio-bar button:hover {
    background-color: #D1CEE9;
}

.character-bar {
    background-color: #F0F0F5;
    padding: 12px; 
    height: 15%; 
    display: flex;
    align-items: center; 
    border-radius: 8px;  
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); 
    margin-top: 10px;
    gap: 8px; 
}

.character-bar span {
    font-size: 16px; /* 调整字体大小 */
    font-weight: bold; /* 加粗文字 */
    color: #333; /* 深色文字 */
}

.character-bar select {
    flex: 1; /* 让下拉框占据剩余空间 */
    padding: 8px; /* 增加内边距 */
    font-size: 14px; /* 调整字体大小 */
    border: 1px solid #CCC; /* 添加边框 */
    border-radius: 4px; /* 圆角边框 */
    background-color: #FFF; /* 白色背景 */
    color: #333; /* 深色文字 */
    transition: border-color 0.3s ease; /* 添加交互动画 */
}

.character-bar select:hover {
    border-color: #888; /* 鼠标悬停时改变边框颜色 */
}

.character-bar select:focus {
    outline: none; /* 移除默认的聚焦样式 */
    border-color: #5B9BD5; /* 聚焦时的边框颜色 */
    box-shadow: 0 0 4px rgba(91, 155, 213, 0.5); /* 聚焦时的阴影效果 */
}
</style>