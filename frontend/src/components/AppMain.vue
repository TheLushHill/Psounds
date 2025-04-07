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

                audioContext: null,
                audioParams: null, // { sampleRate, channels, bitDepth }
                pcmBuffer: new Uint8Array(), // 累积的PCM数据
                isStreaming: false,

                fileList: [],

                modelList: modelConfig,
            }
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
                    let response = await fetch("/api/stream", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                        },
                        body: JSON.stringify({
                            "text": "在我周围也有相同的魔法，只不过温度更低，效果也不那么激烈：一大堆斜槽和吞吐口挤在四周的隔离壁上，其中几个开口之大，足可塞进我的拳头，有一两个甚至能把我整个人吞下去。忒修斯的制造车间可以造出任何东西，无论是刀叉还是驾驶室。只要有足够的物质储备，它甚至能一点一点地造出另一艘忒修斯，只不过时间当然会拖得很长。有人怀疑它甚至能造出另一批船员，不过我们得到的保证是这是不可能的。尽管这些机械代表了最前沿的技术，但它们的手指仍然不够精密，无法在人类头骨的狭小空间内重建好几兆的神经突触。至少现在还不行。这话我信。因为如果真有更便宜的替代方案，他们绝不会让我们这样组装完好地上路。我面朝前方，把后脑勺枕在那扇密闭的舱门上，这样一来我几乎能看到忒修斯的船头。我的视线一路畅通无阻，直看到三十米开外，尽头是仿佛飞镖盘红心的小小黑点。我就好像盯着一个环环相套的巨大靶子，包裹在隔离壁里的舱门是白色和灰色的同心圆，一个套一个，形成一条完美的直线。舱门全都开着，毫不理会过去几代人严防死守的安全规程。其实也可以把它们关起来，如果我们觉得关门能让自己更安心的话，但这样做的作用也仅止于此。实践早已证明，关闭舱门丝毫不会增加我们的生存几率。如果遇上麻烦，这些舱门会在瞬间关闭，而人类的感官还要多花好几毫秒才能明白警报的含义。这些门甚至并非电脑控制。忒修斯的身体里包含反射神经。"
                        })
                    });

                    let reader = response.body.getReader();
                    let audioContext = new (window.AudioContext || window.webkitAudioContext)();
                    let isFirstChunk = true;
                    let sampleRate = 32000; // 默认采样率
                    
                    let pump = async () => {
                        let { done, value } = await reader.read();
                        if (done) return;

                        if (isFirstChunk) {
                            // 解析 WAV 头
                            let header = new DataView(value.buffer, 0, 44);
                            sampleRate = header.getUint32(24, true);
                            isFirstChunk = false;
                        }

                        // 解码 PCM 数据
                        let audioBuffer = await audioContext.decodeAudioData(value.buffer);
                        let source = audioContext.createBufferSource();
                        source.buffer = audioBuffer;
                        source.connect(audioContext.destination);
                        source.start(0);

                        pump();
                    };

                    pump();
                        
                    // console.log(response.data);
                    // let audio = new Audio();
                    // audio.src = URL.createObjectURL(new Blob([response.data], { type: "audio/wav" }));
                    // audio.play();
                    // this.$refs.audio.src = audioUrl;
                    // this.$refs.audio.load();
                    // this.$refs.audio.play();
                } catch (error) {
                    console.error('请求错误:', error);    
                    alert('流式音频请求失败: ' + error.message);
                }
            },

            async startStream() {
                if (this.isStreaming) return;
                this.isStreaming = true;
                
                try {
                    // 初始化音频环境 
                    this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
                    
                    // 请求流式音频接口 
                    const response = await fetch('/api/stream-audio');
                    const reader = response.body.getReader();
                    let isFirstChunk = true;

                    while (this.isStreaming) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    if (isFirstChunk) {
                        // 处理首帧（含WAV头） 
                        this.parseWavHeader(value.slice(0, 44));
                        this.pcmBuffer = new Uint8Array(value.slice(44));
                        isFirstChunk = false;
                    } else {
                        // 追加后续PCM数据 
                        this.pcmBuffer = this.mergeBuffers(this.pcmBuffer, new Uint8Array(value));
                    }

                    // 动态生成WAV并播放 
                    await this.playDynamicWav();
                    }
                } catch (error) {
                    console.error('流式音频错误:', error);
                } finally {
                    this.isStreaming = false;
                }
            },
            parseWavHeader(headerData) {
                const view = new DataView(headerData);
                this.audioParams = {
                    sampleRate: view.getUint32(24, true),
                    channels: view.getUint16(22, true),
                    bitDepth: view.getUint16(34, true)
                };
            },
            mergeBuffers(existing, newChunk) {
                const merged = new Uint8Array(existing.length + newChunk.length);
                merged.set(existing);
                merged.set(newChunk, existing.length);
                return merged;
            },
            async playDynamicWav() {
                const wavData = this.generateWavWithHeader();
                try {
                    const audioBuffer = await this.audioContext.decodeAudioData(wavData.buffer);
                    const source = this.audioContext.createBufferSource();
                    source.buffer = audioBuffer;
                    source.connect(this.audioContext.destination);
                    source.start(0);
                    
                    // 清空已播放数据（保留未播放部分需更复杂逻辑）
                    this.pcmBuffer = new Uint8Array(0); 
                } catch (error) {
                    console.error('音频解码失败:', error);
                }
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