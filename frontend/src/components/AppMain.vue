<script>
    import PreviewPanel from "./PreviewPanel.vue"
    import TrainPanel from "./TrainPanel.vue"
    import TrainPanelButton from "./TrainPanelButton.vue"
    import ConvertPanel from "./ConvertPanel.vue"
    import ConvertPanelButton from "./ConvertPanelButton.vue"
    import UploadFileButton from "./UploadFileButton.vue"
    import modelConfig from "../config/model.json";
    import FileList from "./FileList.vue";
    import axios from "axios";

    import { moveToHead } from "../utils/utils.js"

    export default {
        data() {
            return {
                state: {
                    previewPanel: true,
                    convertPanel: false,
                    trainPanel: false,
                },
                
                isStreaming: false,
                abortController: null,
                test: Number,

                fileList: [],

                modelList: modelConfig,
            }
        },
        mounted() {
            this.audioCtx = new AudioContext();
            this.playTime =this.audioCtx.currentTime;
        },

        methods : {
            handleFileUploaded(file) {
                let newFile = {
                    ...file,
                }

                if (this.fileList.length >= 10) {
                    this.fileList.pop();
                    this.fileList.unshift(newFile);
                }
                else {
                    this.fileList.unshift(newFile);
                }

                if (!this.state.previewPanel) {
                    this.updatePanel("preview");
                }
            },

            // 处理文件选择，将选中的文件放到fileLIs中的第一个位置
            handleFileSelect(index) {
                if (index === 0) {
                    this.updatePanel("preview");
                }
                else {
                    moveToHead(this.fileList, index);
                    this.updatePanel("preview");
                }
            },

            handleTrainButton() {
                this.updatePanel("train");
            },

            handleConvertButton() {
                this.updatePanel("convert");
            },

            updatePanel(str) {
                switch (str) {
                    case "preview": {
                        this.state.previewPanel = true;
                        this.state.trainPanel = false;
                        this.state.convertPanel = false;
                        break;
                    }
                    case "convert": {
                        this.state.convertPanel = true;
                        this.state.trainPanel = false;
                        this.state.previewPanel = false;
                        break;
                    }

                    case "train": {
                        this.state.trainPanel = true;
                        this.state.previewPanel = false;
                        this.state.convertPanel = false;
                        break;
                    }
                }
            },

            async handleTestClick() { 
                try {
                    if (this.isStreaming) return
                    this.isStreaming = true
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
                            "text": "你说的对，但是《原神》是由米哈游自主研发的一款全新开放世界冒险游戏。游戏发生在一个被称作「提瓦特」的幻想世界，在这里，被神选中的人将被授予「神之眼」，导引元素之力。你将扮演一位名为「旅行者」的神秘角色，在自由的旅行中邂逅性格各异、能力独特的同伴们，和他们一起击败强敌，找回失散的亲人——同时，逐步发掘「原神」的真相。",
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
                            header = this.parseWavHeader(value.buffer)
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
            parseWavHeader(buffer) {
                const dv = new DataView(buffer);
                const numChannels   = dv.getUint16(22, true);
                const sampleRate    = dv.getUint32(24, true);
                const bitsPerSample = dv.getUint16(34, true);
                return { numChannels, sampleRate, bitsPerSample };
            },
            pcmToFloat32(pcmBuffer, bitsPerSample) {
                const dv = new DataView(pcmBuffer.buffer, pcmBuffer.byteOffset, pcmBuffer.byteLength)
                const count = pcmBuffer.byteLength / (bitsPerSample / 8)
                const float32 = new Float32Array(count)
                for (let i = 0; i < count; i++) {
                    let sample = 0
                    if (bitsPerSample === 16) {
                    sample = dv.getInt16(i * 2, true) / 0x8000
                    } else if (bitsPerSample === 8) {
                    sample = (dv.getUint8(i) - 128) / 128
                    }
                    float32[i] = sample
                }
                return float32
            },

            scheduleAudio(pcmChunk, header) {
                const { numChannels, sampleRate, bitsPerSample } = header;

                const bytesPerSample = bitsPerSample / 8;
                const frameBytes     = bytesPerSample * numChannels;

                // 如果 chunk 太短，直接跳过
                if (pcmChunk.byteLength < frameBytes) return;

                // 丢弃尾部不完整的字节
                const remainder = pcmChunk.byteLength % frameBytes;
                if (remainder !== 0) {
                    // 丢掉最后 remainder 字节
                    pcmChunk = pcmChunk.slice(0, pcmChunk.byteLength - remainder);
                }

                // PCM → Float32Array
                const float32 = this.pcmToFloat32(pcmChunk, bitsPerSample);
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

        computed: {
            getFile() {
                if (this.fileList.length > 0) {
                    return this.fileList[0];
                }
                else {
                    return {
                    "name": "default",
                    "type": "docx",
                    "size": 0,
                    "url": "",
                    "content" : null,
                    };
                }
            }
        },

        components: {
            UploadFileButton,
            PreviewPanel,
            TrainPanel,
            TrainPanelButton,
            FileList,
            ConvertPanel,
            ConvertPanelButton,
        }
    }
</script>

<template>
    <div class="main">
        <div class="side-list">
            <UploadFileButton 
                @get-file="handleFileUploaded"
            ></UploadFileButton>

            <ConvertPanelButton
                @update-panel="handleConvertButton"
            ></ConvertPanelButton>
    
            <TrainPanelButton
                @update-panel="handleTrainButton"
            ></TrainPanelButton>
            
            <div >
                <button 
                    @click="handleTestClick"
                >
                    test
                </button>
                <audio ref="audio" controls>

                </audio>
            </div>

            <FileList
                :fileList="fileList"
                @file-select="handleFileSelect"
            ></FileList>
        </div>
        <div class="content-container">
            <PreviewPanel
                :isVisible="state.previewPanel"
                :file="getFile"
            ></PreviewPanel>

            <ConvertPanel
                :isVisible="state.convertPanel"
            ></ConvertPanel>

            <TrainPanel 
                :isVisible="state.trainPanel"
            ></TrainPanel>

        </div>
    </div>
</template>

<style>
.main {
    height: 100%;
    width: 100%;
    display: flex;
}

.side-list {
    width: 16.7%;
    margin-right: 16px;
    display: flex;
    flex-direction: column;
    background-color: #E5DEE2;
}

.content-container {
    width: 100%;
    height: 100%; 
    flex: 1 1 auto;
    display: flex;
    margin-right: 16px;
}

</style>