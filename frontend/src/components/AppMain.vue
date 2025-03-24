<script>
    import PreviewPanel from "./PreviewPanel.vue"
    import TrainPanel from "./TrainPanel.vue"
    import TrainPanelButton from "./TrainPanelButton.vue"
    import UploadFileButton from "./UploadFileButton.vue"
    import modelConfig from "../config/model.json";
    import FileList from "./FileList.vue";

    import { moveToHead } from "../utils/utils.js"

    export default {
        data() {
            return {
                state: {
                    previewPanel: true,
                    trainPanel: false,
                },

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
                        this.state.previewPanel = true;
                }
            },

            // 处理文件选择，将选中的文件放到fileLIs中的第一个位置
            handleFileSelect(index) {
                if (index === 0) {
                    this.state.previewPanel = true;
                }
                else {
                    moveToHead(this.fileList, index);
                    this.state.previewPanel = true;
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
        }
    }
</script>

<template>
    <div class="main">
        <div class="side-list">
            <UploadFileButton 
                @get-file="handleFileUploaded"
            ></UploadFileButton>
    
            <TrainPanelButton></TrainPanelButton>
            
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