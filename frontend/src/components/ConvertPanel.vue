<script>
    import axios from "axios"
    import { parseWavHeader, pcmToFloat32, makeWavHeader} from "../utils/utils.js"
    export default {
        data() {
            return {
                blobUrl: null,

                isPlaying: false,
                isStreaming: false,
                abortController: null,
                leftover: null,
                audioCtx: null,
                playTime: null,

                buffer: [],

                // 课件的blobUrl
                pptxblob: null
            }
        },

        computed: {
            fullText() {
                if (this.type === "docx") {
                    return this.text.join();
                }
                else if (this.type === "pptx") {
                    let t = "";
                    for (let items of this.text) {
                        t += items.join()
                    }
                    return t;
                }
            },

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
                // console.log(response.data)
                let blob = new Blob([response.data], { type: "audio/wav" });
                this.blobUrl = URL.createObjectURL(blob);
                this.$refs.audio.src = this.blobUrl;
                this.$refs.audio.play();
            },

            // 获取流式音频，音频解码，音频调度，音频拼接
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
                            "text": this.fullText,
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
                            this.buffer.push(value);
                            this.scheduleAudio(value, header)
                        }
                    }
                } catch (error) {
                    console.error("Error:", error);
                    alert("Error: " + error.message);
                } finally {
                    this.isStreaming = false;

                    const pcmBytes = this.buffer.reduce((acc, buf) => acc + buf.byteLength, 0);
                    const pcmAll = new Uint8Array(pcmBytes);
                    let offset = 0;
                    for (const buf of this.buffer) {
                        pcmAll.set(new Uint8Array(buf), offset);
                        offset += buf.byteLength;
                    }

                    const wavHeader = makeWavHeader({
                        pcmByteLength: pcmBytes,
                        sampleRate: 32000,       // 与后端保持一致
                        numChannels: 1,          // 与后端保持一致
                        bytesPerSample: 2,       // 16 位 → 2 字节
                    });

                    let blob = new Blob([wavHeader, pcmAll], { type: "audio/wav" });
                    this.blobUrl = URL.createObjectURL(blob);
                    this.$refs.audio.src = this.blobUrl;
                    this.$refs.url.href = this.blobUrl;
                    
                    this.buffer = [];
                }
            },

            // 音频调度
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
                this.isPlaying = true;

                // 推进播放指针
                this.playTime += frameCount / sampleRate;
            },

            // 更新角色模型
            updateCharacter(event) {
                let character = event.target.value;
                this.$emit("update-character", character);
            },

            // 下载完整音频
            handleDownload() {
                if (this.blobUrl) {
                    this.$refs.url.click()
                }
                else {
                    alert("请先获取音频")
                }
            },

            // 触发暂停/播放
            async togglePlayPause() {
                if (this.audioCtx === null) {
                    alert("请先获取音频");
                    return
                }
                else if (this.audioCtx.state === "running") {
                    this.audioCtx.suspend();
                    this.isPlaying = false;
                } else if (this.audioCtx.state === "suspended") {
                    this.audioCtx.resume();
                    this.isPlaying = true;
                }
            },

            // 停止流式音频播放
            stopStreamPlaying() {
                this.togglePlayPause();
            },

            // 制作有声课件
            async makePptx() {
                if (!this.file) {
                    alert("请先上传文件")
                    return
                }
                else if (this.file.type != "pptx") {
                    alert("当前选择的文件不是pptx,请切换到pptx文件")
                    return 
                }
                else {
                    let formData = new FormData()
                    formData.append("file", this.file.file)
                    formData.append("character", this.character)

                    let response = await axios.post("/api/PPTaudio", formData, {
                        responseType: "blob"
                    })

                    this.pptxblob = response.data
                }
            },
            
            // 下载课件
            downloadPptx() {
                const url = URL.createObjectURL(this.pptxblob);
                const a = document.createElement("a")
                a.href = url
                a.download = 'modified_' + this.file.name
                a.click()
            }
        },
        props: {
            isVisible: Boolean,
            text: {
                type: Array,
            },
            type: String,
            character: String,
            characterList: Array,
            file: Object,
        },

    }
</script>

<template>
    <div class="convert-panel" v-show="isVisible">
        <div class="view" v-if="text.length === 0">暂无内容，请上传文件后在文件预览界面中选择内容。</div>
        <div class="view"v-else>
            <div v-for="(item, index) in text" :key="index" class="text-line">
                <span>{{ item }}</span>
            </div>
        </div>
        <div class="panel">
            <div class="full-audio-bar">
                <div class="select">
                    <span>当前角色模型：</span>
                    <select @change="updateCharacter">
                        <template v-for="(item, index) in characterList">
                            <option :value="item.value" :selected="index === 0">{{ item.name }}</option>
                        </template>
                    </select>
                </div>
                <button @click="getFullAudio" class="get-full-audio">获取完整音频</button>
                <audio ref="audio" controls></audio>
            </div>
            <div class="stream">
                <button @click="getStreamAudio" class="item">获取流式音频</button>
                <button :disabled="isPlaying" class="item" @click="togglePlayPause">播放流式音频</button>
                <button :disabled="!isPlaying" class="item" @click="stopStreamPlaying">暂停流式音频</button>
            </div>
            <div class="bar">
                <button class="item" @click="handleDownload">
                    <a :href="blobUrl" download="audio.wav" ref="url"></a>
                    下载完整音频
                </button>
                <button @click="makePptx">制作有声课件</button>
                <button @click="downloadPptx" :disabled="!pptxblob">下载课件</button>
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
    align-self: auto;
    justify-content: space-around;
    width: 15em;
}

.select {
    border-radius: 12px;
    background-color: #DCDAF5;
    border: none;
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 0 8px;
    flex-grow: 1;
}

.full-audio-bar button {
    height: 3em;
    
    border-radius: 12px;
    background-color: #DCDAF5;
    border: none;
    margin: 0px;
}

.full-audio-bar button:hover {
    background-color: #D1CEE9;
}

.full-audio-bar audio {
    width: 100%;
}

.stream {
    width: 12em;
    display: flex;
    flex-direction: column;
    justify-content: space-around;
}

.bar {
    display: flex;
    flex-direction: column;
    padding: 8px;
    gap: 8px;
    width: 12em;
}

.bar .item {
    border-radius: 12px;
    background-color: #DCDAF5;
    border: none;
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 0 8px;
    flex-grow: 1;
}

span {
    font-size: 16px; 
    font-weight: bold; 
    color: #333; 
}

select {
    padding: 4px 8px; 
    font-size: 14px; 
    border: 1px solid #CCC; 
    border-radius: 4px; 
    background-color: #FFF; 
    color: #333; 
    transition: border-color 0.3s ease; 
}

select:hover {
    border-color: #888; 
}

select:focus {
    outline: none; 
    border-color: #5B9BD5; 
    box-shadow: 0 0 4px rgba(91, 155, 213, 0.5); 
}

.character-bar button:hover {
    background-color: #D1CEE9;}
</style>