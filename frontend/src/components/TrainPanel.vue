<script>
    import axios from 'axios';

    export default {

        data() {
            return {
                audio: {
                    file: null,
                    name: null,
                }
            }
        },

        props: {
            isVisible: Boolean,
        },

        methods: {
            // 声音上传
            async audioUpload(event) {
                let file = event.target.files[0];
                if (file) {
                    this.audio.name = file.name;
                    let formData = new FormData();
                    formData.append("file", file);
                    // const response = await axios.post("/api/SaveAudio", formData, {
                    //     headers: {
                    //         "Content-Type": "multipart/form-data",
                    //     }
                    // })
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
                <button @click="this.$refs.audioUpload.click()">上传音频</button>
            </div>
            <button @click="startRecord">录制声音</button>
        </div>
        <div>
            <button>音频预处理</button>
            <button>训练集标准化</button>
            <button>开始声音克隆</button>
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

</style>