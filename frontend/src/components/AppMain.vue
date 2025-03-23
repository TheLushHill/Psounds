<script>
    import PreviewPanel from "./PreviewPanel.vue"
    import ModelPanel from "./ModelPanel.vue"
    import UploadFileButton from "./UploadFileButton.vue"
    import modelConfig from "../config/model.json";
    import FileList from "./FileList.vue";

    import { moveToHead } from "../utils/utils.js"

    export default {
        data() {
            return {
                state: {
                    previewPanel: true,
                    modelPanel: false,
                },

                fileList: [],

                modelList: modelConfig,
                selectedModel: 0
                // textList: [],  
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
            
            handleSwitchPreset() {
                if (!this.state.modelPanel) {
                    this.state.previewPanel = false;
                    this.state.modelPanel = true;
                }
            },
            
            updatePanel() {
                if (!this.state.previewPanel) {
                    this.state.modelPanel = false;
                    this.state.previewPanel = true;
                }
            },
            
            updateModel(index) {
                this.selectedModel = index;
            }
            
            // closePreview() {
            //     this.textList = [];    
            // },
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
            ModelPanel,
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
                <!-- :isVisible="state.previewPanel"
                @preview-close="closePreview"
                @update-panel="updatePanel" -->

            <FileList
                :fileList="fileList"
                @file-select="handleFileSelect"
            ></FileList>

            <!-- <div class="show-preset">
                <span>当前模型：</span>
                <img :src="modelList[selectedModel].iconUrl" />
                <span>{{ modelList[selectedModel].name }}</span>
            </div> -->

            <!-- <button class="switch-preset"
                @click="handleSwitchPreset"
            >切换预设</button> -->
        </div>
        <div class="content-container">
            <PreviewPanel
                :isVisible="state.previewPanel"
                :file="getFile"
            ></PreviewPanel>
                <!-- :text-list="textList"  -->
                
            <ModelPanel 
                :isVisible="state.modelPanel"
                :list="modelList"
                :model="selectedModel"
                @model-select="updateModel"
            ></ModelPanel>
        </div>
    </div>
</template>

<style>
.main {
    height: 86%;
    margin: 0px 16px 16px 16px;
    display: flex;
}

.side-list {
    width: 16.7%;
    margin-right: 16px;
    display: flex;
    flex-direction: column;
    background-color: #cccbc8;
}

.content-container {
    flex: 1 1 auto;
    display: flex;
    background-color: #cccbc8;
}

.show-preset {
    display: flex;
    justify-content: center;
    gap: 1em;
    align-items: center;
    margin: 8px;
    height: 3em;
    border-radius: 12px;
    background-color: #d4eaf7;
}

.show-preset img {
    width: 2.5em;
    height: 2.5em;
    border-radius: 8px;
    object-fit: cover;
}

.switch-preset {
    margin: 8px;
    height: 3em;
    border-radius: 12px;
    background-color: #d4eaf7;
}

.switch-preset:hover {
    background-color: #b3d9f0;
}
</style>