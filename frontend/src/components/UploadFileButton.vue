<script>
    import axios from "axios";

    export default {
        data() {
            return {
                file : {
                    "name": String,
                    "type": String,
                    "size": Number,
                    "url": String,
                    "content" : null,
                },

            }
        },
        methods: {
            triggerUpload() {
                this.$refs.fileinput.click();
            },

            handleFile(event) {
                this.uploadFile(event.target.files[0]);
            },

            async uploadFile(file) {
                this.file.name = file.name;
                this.file.size = file.size;
                if (file.type === "application/vnd.openxmlformats-officedocument.wordprocessingml.document") {
                    this.file.type = "docx";
                }
                else if (file.type === "application/vnd.openxmlformats-officedocument.presentationml.presentation") {
                    this.file.type = "pptx";
                    this.file["file"] = new File([file], file.name, {type:"application/vnd.openxmlformats-officedocument.presentationml.presentation"})
                }
                this.file.url = URL.createObjectURL(file); 

                let formData = new FormData();
                formData.append("file", file);

                try {
                    const response = await axios.post("/api/upload", formData);
                    this.file.content = response.data;
                    

                    // 传递文件给父组件,父组件监听get-file事件
                    this.$emit("get-file", this.file);
                    alert("上传文件成功");
                }
                catch (error) {
                    console.error('上传文件错误:', {
                        status: error.response?.status,
                        message: error.response?.data?.error || error.message,
                        data: error.response?.data
                    });
                    alert('文件上传失败: ' + (error.response?.data?.error || error.message));
                }
            },
        },

        props: {
            
        }
    }
</script>

<template>
    <div class="upload-container">
        <input 
            type="file" 
            style="display:none" 
            ref="fileinput" 
            @change="handleFile"
        />
        
        <button class="upload-button"
        @click="triggerUpload"
        >上传文件</button>

    </div>
</template>

<style>
.upload-container {
    display: flex;
}

.upload-button {
    flex: 1 1 auto;
    height: 3em;
    border-radius: 12px;
    background-color: #DCDAF5;
    border: none;
    margin: 8px 8px 0 8px;
}

.upload-button:hover {
    background-color: #D1CEE9;
}

</style>