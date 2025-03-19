<script>

    import UploadFileButton from "./UploadFileButton.vue"

    export default {
        data() {
            return {
                preview: null,
                testlist: [],
            }
        },

        methods : {
            textchange(data) {
                this.testlist = data;
            },

            closePreview() {
                this.testlist = [];
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
                @file-response="textchange"
                @previewclose="closePreview"
            ></UploadFileButton>
        </div>
        <div id="container">
            <div id="filepreview">
                <div v-for="(item, index) in testlist">
                    <span class="parag" :id="'parag' + index">{{ item }}</span>
                </div>
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

#filepreview {
    margin: 16px;
	display: flex;
    flex: 1 1 auto;
	flex-direction: column;
    background-color: #fffefb;
}
</style>