<script>
    import PreviewPanel from "./PreviewPanel.vue"
    import ModelPanel from "./ModelPanel.vue"
    import UploadFileButton from "./UploadFileButton.vue"
    import modelConfig from "../config/model.json";

    export default {
        data() {
            return {
                state: {
                    previewPanel: true,
                    modelPanel: false,
                },
                textList: [],  
                modelList: modelConfig,
                selectedModel: 0
            }
        },

        methods : {
            textChange(data) {
                this.textList = data;  
            },

            closePreview() {
                this.textList = [];    
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

            // 选择模型按钮后更新模型
            updateModel(index) {
                this.selectedModel = index;
            }
        },

        components: {
            UploadFileButton,
            PreviewPanel,
            ModelPanel
        }
    }
</script>

<template>
    <div class="main">
        <div class="side-list">
            <UploadFileButton 
                :isVisible="state.previewPanel"
                @file-response="textChange"
                @preview-close="closePreview"
                @update-panel="updatePanel"
            ></UploadFileButton>

            <div class="show-preset">
                <span>当前模型：</span>
                <img :src="modelList[selectedModel].iconUrl" />
                <span>{{ modelList[selectedModel].name }}</span>
            </div>

            <button class="switch-preset"
                @click="handleSwitchPreset"
            >切换预设</button>
        </div>
        <div class="content-container">
            <PreviewPanel
                :isVisible="state.previewPanel"
                :text-list="textList" 
            ></PreviewPanel>

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