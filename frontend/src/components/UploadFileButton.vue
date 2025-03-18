<template>
    <div>
        <input type="file" style="display:none" ref="fileinput" @change="handleFile"/>
        <button @click="triggerUpload">上传文件</button>
    </div>
</template>

<script>
    import axios from "axios";

    export default {
        data() {
            return {
                 file: null,
                 fileUrl: null,
            }
        },
        methods: {
            triggerUpload() {
                this.$refs.fileinput.click();
            },
            handleFile(event) {
                this.file = event.target.files[0];
                this.fileUrl = URL.createObjectURL(this.file);

                this.uploadFile(this.file);
            },

            async uploadFile(file) {
                const formData = new FormData().append("file", file);
                
                try {
                    const response = await axios.post("/api/upload", formData, {
                        headers:{
                            "Content-Type" : "multipart/form-data"
                        }
                    });
                    console.log(response);
                }
                catch (error) {
                    console.log(error);
                }
            }
        }
    }
</script>

