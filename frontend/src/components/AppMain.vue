<script>
    import PreviewPanel from "./PreviewPanel.vue"
    import TrainPanel from "./TrainPanel.vue"
    import TrainPanelButton from "./TrainPanelButton.vue"
    import ConvertPanel from "./ConvertPanel.vue"
    import ConvertPanelButton from "./ConvertPanelButton.vue"
    import UploadFileButton from "./UploadFileButton.vue"
    import FileList from "./FileList.vue";
    import axios from "axios"

    import { moveToHead, parseWavHeader, pcmToFloat32} from "../utils/utils.js"

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
                leftover: null,

                fileList: [],
                hadFile: false,
                character: "Hutao",
                CharacterList: [ {
                    name: "胡桃",
                    value: "Hutao",
                },
                {
                    name: "永雏塔菲",
                    value: "永雏塔菲",
                },
                {
                    name: "嘉然",
                    value: "嘉然",
                },
                {
                    name: "孙笑川",
                    value: "孙笑川",
                }],

                // 测试用
                // filetest: null,

                // 用于每次切换文件时重置复选框
                resetCheckbox: false,

                convertText: [],
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
                    // 文件添加至头部
                    this.fileList.unshift(newFile);

                    this.resetCheckbox = true;
                    this.convertText = [];
                }
                else {
                    // 文件添加至头部
                    this.fileList.unshift(newFile);

                    this.resetCheckbox = true;
                    this.convertText = [];
                }


                if (!this.hadFile) {
                    this.hadFile = true;
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

                    // 重置选中的文本
                    this.resetCheckbox = true;
                    this.convertText = [];
                }
            },

            // 处理预览按钮，更新面板
            handleTrainButton() {
                this.updatePanel("train");
            },

            // 处理转换按钮，更新面板
            handleConvertButton() {
                this.updatePanel("convert");
            },

            // 处理列表中的按钮，根据 str 的值来更新面板
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

            //  用于预览界面试听获取文本,直接发送给后端
            getUploadText(type, index) {
                if (type == "pptx") {
                    return this.fileList[0].content[index].join();
                }
                else if (type == "docx") {
                    return this.fileList[0].content[index];
                   
                }
            },

            async getStreamAudio(type, index) { 
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
                            "text": this.getUploadText(type, index),
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

            // 调度文本至转换面板 
            getConvertText(object) {
                let file = this.fileList[0];
                let { index, checked} = object;
                if (file.type == "docx") {
                    if (checked) {
                        if (!this.convertText.includes(file.content[index]))
                            this.convertText.push(file.content[index]);
                    }
                    else {
                        this.convertText = this.convertText.filter((item) => {
                            return item != file.content[index];
                        })
                    }

                    
                    let order = file.content.map((item) => {
                        return item;
                    })
                    this.convertText = order.filter((item) => {
                        let b = this.convertText.includes(item);
                        return b;
                    })
                } 
                else {
                    if (checked) {
                        if (!this.convertText.includes(file.content[index]))
                            this.convertText.push(file.content[index]);
                    }
                    else {
                        this.convertText = this.convertText.filter((item) => {
                            return item != file.content[index];
                        })
                    }

                    
                    let order = file.content.map((item) => {
                        return item;
                    })
                    this.convertText = order.filter((item) => {
                        let b = this.convertText.includes(item);
                        return b;
                    })
                }
            },

            // 更新角色
            updateCharacter(character) {
                this.character = character;
            },

            // test(event) {
            //     console.log(event.target.files[0]);
            //     let formData = new FormData();
            //     console.log(formData);
            //     formData.append("file", event.target.files[0]);
            //     formData.append("character", "Hutao");
            //     console.log(formData);

            //     axios.post("/api/test", formData);
            // }
            
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
            },

            getType() {
                if (this.hadFile) {
                    return this.fileList[0].type;
                }
                else {
                    return "docx";
                }
            },

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
            <div class="button">
                <UploadFileButton 
                    @get-file="handleFileUploaded"
                ></UploadFileButton>
    
                <ConvertPanelButton
                    @update-panel="handleConvertButton"
                ></ConvertPanelButton>
        
                <TrainPanelButton
                    @update-panel="handleTrainButton"
                ></TrainPanelButton>
                <!-- <input type="file" @change="test"/> -->
            </div>
            
            <FileList
                :fileList="fileList"
                @file-select="handleFileSelect"
            ></FileList>
        </div>
        <div class="content-container">
            <PreviewPanel
                :isVisible="state.previewPanel"
                :character="character"
                :uploaded="hadFile"
                :file="getFile"
                :resetCheckbox="resetCheckbox"
                @checkCanceled="this.resetCheckbox = false"
                @play-stream="getStreamAudio"
                @checked="getConvertText"
            ></PreviewPanel>

            <ConvertPanel
                :isVisible="state.convertPanel"
                :type="getType"
                :text="convertText" 
                :file="fileList[0]"
                :character="character"
                :characterList="CharacterList"
                @update-character="updateCharacter"
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

.side-list .button {
    gap: 4px;
    display: flex;
    flex-direction: column;
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
    flex: 1 1 auto;
    margin-top: 8px;
    margin-bottom: 8px;
    display: flex;
    margin-right: 16px;
}

</style>