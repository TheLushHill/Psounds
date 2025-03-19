<script>
    import axios from "axios";

    export default {
        data() {
            return {
                 file: null,
                 fileUrl: null,
                 fileName: '',
                 isUpload: false
            }
        },
        methods: {
            /**
             * trigger the file input
             */
            triggerUpload() {
                this.$refs.fileinput.click();
            },

            handleFile(event) {
                if (!this.previewPanel) {
                    this.$emit("updatePanel");
                }
                this.file = event.target.files[0]; 
                this.uploadFile(this.file);
            },

            async uploadFile(file) {
                const formData = new FormData();
                formData.append("file", file);

                
                try {
                    const response = await axios.post("/api/upload", formData);
                    this.isUpload = true;
                    this.fileName = file.name;
                    this.$emit("file-response", response.data);
                }
                catch (error) {
                    console.log(error);
                }
            },

            /**
             * close the file
             * isUpload controls the display of the file info
             * the file information will be cleared
             */
            closeFile() {
                this.isUpload = false;
                this.file = null;
                this.fileName = '';
                this.$refs.fileinput.value = '';
                this.$emit("previewclose");
            }
        },

        props: {
            previewPanel: {
                type: Boolean,
                required: true
            }
        }
    }
</script>

<template>
    <div id="upload-container">
        
        <input 
            type="file" 
            style="display:none" 
            ref="fileinput" 
            @change="handleFile"
        />
        
        <button id="upload-button"
            v-if="!isUpload"
            @click="triggerUpload"
        >
            上传文件
        </button>

        <div v-else id="file-info">
            <button id="filename"
                @click="$emit('updatePanel')"
            > {{ fileName }}</button>
            <button
                @click="closeFile"
            >
                关闭    
        </button>

        </div>
    </div>
</template>


<style>
#upload-container {
    display: flex;
}

#upload-button {
    flex:1 1 auto;
    margin: 8px;
    height: 3em;
    border-radius: 12px;
    background-color: #d4eaf7;
}

#upload-button:hover {
    background-color: #b3d9f0;
}

#file-info {
    display: flex;
    flex:1 1 auto;
    align-items: center;
    justify-content: center;

    height: 3em;
    margin: 8px;
    border-radius: 12px;
    background-color: #d4eaf7;
}

/* #file-info span {
    max-width: 9em;
    margin-right: 1em;
    padding: 8px;
    border-radius: 12px;
    background-color: #f5f4f1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
} */

#file-info button,#filename {
    max-width: 9em;
    height: 2.4em;
    border-radius: 8px;
    margin-right: 1em;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    background-color: #f0f0f0;
}

#file-info button {
    height: 2.4em;
    border-radius: 8px;
    background-color: #f0f0f0;
}

#file-info button:hover {
    background-color: #e0e0e0;
    cursor: pointer;
}
</style>