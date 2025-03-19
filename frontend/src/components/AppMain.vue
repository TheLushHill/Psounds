<script>

    import UploadFileButton from "./UploadFileButton.vue"

    export default {
        data() {
            return {
                previewPanel: true,
                presetPanel: false,
                testlist: [],
            }
        },

        methods : {
            textChange(data) {
                this.testlist = data;
            },

            closePreview() {
                this.testlist = [];
            },

            handleSwitchPreset() {
                if (!this.presetPanel) {
                    this.previewPanel = false;
                    this.presetPanel = true;
                }
            },

            updatePanel() {
                if (!this.previewPanel) {
                    this.presetPanel = false;
                    this.previewPanel = true;
                }
            }
        },

        computed : {
 
        },

        components: {
            UploadFileButton,
        }
    }
</script>

<template>
    <div id="main">
        <div id="list">
            <UploadFileButton 
                :previewPanel="previewPanel"
                @file-response="textChange"
                @previewclose="closePreview"
                @updatePanel="updatePanel"
            ></UploadFileButton>

            <span id="showReset">预设显示</span>

            <button id="switchPreset"
                @click="handleSwitchPreset"
            
            >切换预设</button>
        </div>
        <div id="container">
            <div id="previewPanel" v-show="previewPanel">
                <div v-for="(item, index) in testlist">
                    <span class="parag" :id="'parag' + index">{{ item }}</span>
                </div>
            </div>

            <div id="presetPanel" v-show="presetPanel">
                
            </div>
        </div>
    </div>
</template>

<style>
#main {
    height: 86%;
    margin: 0px 16px 16px 16px;

    display: flex;
}

#list {
    width: 16.7%;
    margin-right: 16px;

    display: flex;
    flex-direction: column;

    background-color: #cccbc8;
}

#container {
    flex:1 1 auto;
    display: flex;

    background-color: #cccbc8;
}

#previewPanel {
    margin: 16px;
	display: flex;
    flex: 1 1 auto;
	flex-direction: column;
    background-color: #fffefb;
}

#showReset {
    display: flex;
    justify-content: center;
    align-items: center;

    margin: 8px;
    height: 3em;
    border-radius: 12px;
    background-color: #d4eaf7;

}

#switchPreset {
    margin: 8px;
    height: 3em;
    border-radius: 12px;
    background-color: #d4eaf7;
}

#switchPreset:hover {
    background-color: #b3d9f0;
}
</style>