<script>
    import axios from 'axios';

    export default {

        data() {
            return {
                audio: {
                    file: null,
                    name: null,
                },

                // 录音数据
                mediaRecorder: null,
                record: {
                    audio: null,
                    blob: null,
                    url: null,
                    chunks: [],
                },
                isRecording: false,

                // 模型名
                name: null,
            }
        },

        props: {
            isVisible: Boolean,
        },

        methods: {
            // 声音上传
            async audioUpload(event) {
                let file = event.target.files[0];
                try {
                    if (file) {
                        this.audio.name = file.name;
                        let formData = new FormData();
                        formData.append("file", file);
                        const response = await axios.post("/api/SaveAudio", formData, {
                            headers: {
                                "Content-Type": "multipart/form-data",
                            },
                            responseType: "json"
                        })

                        if (response.status === 200) {
                            alert("音频上传成功！");
                        }
                    }
                } catch (error) {
                    console.error("Error uploading audio:", error);
                }
            },

            // 开始录音
            async startRecord() {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    this.mediaRecorder = new MediaRecorder(stream);
                    let chunks = this.record.chunks; 

                    this.mediaRecorder.addEventListener('dataavailable', event => {
                        if (event.data && event.data.size > 0) {
                            chunks.push(event.data);
                        }
                    });
                    this.mediaRecorder.addEventListener('start', () => {
                        chunks = []; // 清空之前的录音数据
                    });
                    this.mediaRecorder.addEventListener('stop', () => {
                        this.record.blob = new Blob(chunks, { type: 'audio/webm' });
                        this.record.url = URL.createObjectURL(this.record.blob);
                        this.$refs.record.src = this.record.url;
                        this.$refs.record.play(); // 播放录音
                    });

                    this.mediaRecorder.start();
                    this.isRecording = true;
                } catch (err) {
                    console.error('录音失败：', err);
                    alert('无法获取麦克风权限');
                }
            },

            // 结束录音
            endRecord() {
                if (this.mediaRecorder && this.isRecording) {
                    this.mediaRecorder.stop();
                    this.isRecording = false;
                }
            },

            // 上传录音数据
            async uploadRecord() {
                if (!this.record.blob) return;

                const formData = new FormData();
                formData.append('file', this.record.blob, 'recording.webm');

                try {
                    const response = await fetch('/api/SaveAudio', {
                    method: 'POST',
                    body: formData
                    });
                    if (!response.ok) throw new Error(`上传失败：${response.statusText}`);
                    const result = await response.json();
                    alert('上传成功: ' + result.message);
                } catch (err) {
                    console.error(err);
                    alert('上传失败，请稍后重试');
                }
            },

            // 音频预处理
            async preprocess() {
                try {
                    let response = await axios.post("/api/preprocess")
                    if (response.status === 200) {
                        alert("音频预处理成功！");
                    } else {
                        alert("音频预处理失败！");
                    }
                } catch (error) {
                    console.error("Error during audio preprocessing:", error);
                }
            },

            // 训练集标准化
            async trainSet() {
                if (!this.name) {
                    alert("请先输入模型名！");
                    return;
                }
                try {
                    let response = await axios.post("/api/format", {
                        character: this.name,
                    }, {
                        headers: {
                            "Content-Type": "application/json",
                        }
                    })
                    if (response.status === 200) {
                        alert("训练集标准化成功！");
                    } else {
                        alert("训练集标准化失败！");
                    }
                } catch (error) {
                    console.error("Error during training set standardization:", error);
                }
            },

            // 开始声音克隆
            async startTrain() {
                if (!this.name) {
                    alert("请先输入模型名！");
                    return;
                }
                try {
                    let response = await axios.post("/api/train", {
                        character: this.name,
                    }, {
                        headers: {
                            "Content-Type": "application/json",
                        }
                    })
                    if (response.status === 200) {
                        alert("声音克隆成功！");
                    } else {
                        alert("声音克隆失败！");
                    }
                } catch (error) {
                    console.error("Error during voice cloning:", error);
                }
            }
        }
    }
</script>

<template>
    <div class="trainPanel"
        v-show="isVisible"
    >
        <div>
            <div>
                <input ref="audioUpload"type="file" style="display:none" @change="audioUpload"/>
                <button @click="this.$refs.audioUpload.click()">上传本地音频</button>
            </div>
            <div class="record-bar">
                <div class="button-bar">
                    <button @click="startRecord" :disabled="isRecording">录制声音</button>
                    <button @click="endRecord" :disabled="!isRecording">停止录音</button>
                    <button @click="uploadRecord">上传录音数据</button>
                </div>
                <audio ref="record" controls></audio>
            </div>
        </div>
        <div>
            <button @click="preprocess">音频预处理</button>
            <button @click="trainSet">训练集标准化</button>
            <button @click="startTrain">开始声音克隆</button>
            <input type="text" placeholder="请输入模型名" v-model="name" />
        </div>
    </div>
</template>

<style>
.trainPanel {
    display: flex;
    flex: 1 1 auto;
    flex-direction: column;
    height: 100%; 
    background-color: #e5dee2;
}

button {
    height: 3em;
    border-radius: 12px;
    background-color: #DCDAF5;
    border: none;
    margin: 8px 8px 0 8px;
}

button:hover {
    background-color: #D1CEE9;
    cursor: pointer;
}

.record-bar {
    width: 18em;
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin: 8px;
}

.record-bar .button-bar {
    display: flex;
    justify-content: space-around;
}

</style>