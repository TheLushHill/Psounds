<script>
    export default {
        props: {
            isVisible: {
                type: Boolean,
                required: true
            },
            textList: {
                type: Array,
                required: true
            }
        },
        computed: {

        }
    }
</script>

<template> 
    <div class="preview-panel" v-show="isVisible">
        <div class="preview">
            <div v-for="(item, index) in textList">
                <span class="paragraph" :class="'paragraph-' + index">{{ item }}</span>
            </div>
        </div>
        <div class="convert">
        </div>
    </div>
</template>

<style>
.preview-panel {
    margin: 16px;
    display: flex;
    flex: 1 1 auto;
    flex-direction: column;
}

.preview-panel::-webkit-scrollbar {
    width: 8px; 
}

.preview {
    display: flex;
    flex: 1 1 auto;
    flex-direction: column;
    overflow-y: auto;
    max-height: 75%;
    background-color: #fffefb;
}

.convert {
    max-height: 25%;
    height: 25%;
    margin-top: 8px;
    background-color: #fffefb;
}
</style>