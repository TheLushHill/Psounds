<script>
    export default {
        data() {
            return {

            }
        },

        computed: {
            isDocx() {
                return this.file.type === "docx";
            },
            
            isPptx() {
                return  this.file.type === "pptx";
            }
        },

        props: {
            isVisible: {
                type: Boolean,
                required: true
            },
            file: Object,
        },
    }
</script>

<template> 
    <div class="preview-panel" v-show="isVisible">
        <div class="preview-docx"
            v-show="isDocx"
        >
            <div class="text-line"
                v-for="(item, index) in file.content"
            >
                <span class="paragraph" 
                    :class="'paragraph-' + index"
                >{{ item }}</span>
            </div>
        </div>

        <div class="preview-pptx"
            v-show="isPptx"
        >
            <div class="page"
                v-for="(item, index) in file.content"
            >
                <span class="index"
                >第{{ index + 1 }}页</span>
                <div class="content">
                    <span
                        v-for="line in item"
                    >{{ line }}</span>
                </div>
            </div>

        </div>
    </div>
</template>

<style>
.preview-panel {
    display: flex;
    flex: 1 1 auto;
    flex-direction: column;
    height: 100%;
}

.preview-panel::-webkit-scrollbar {
    width: 8px; 
}

.preview-docx {
    display: flex;
    flex: 1 1 auto;
    flex-direction: column;
    overflow-y: auto;
    max-height: 75%;
    background-color: #fffefb;
}

.preview-docx .text-line {
    margin-top: 1em;
    line-height: 1.5;
}

.preview-docx .paragraph {
    display:block;
    text-indent: 2em;
    padding: 0 16px;
}

.preview-pptx {
    display: flex;
    flex-direction: column;
    max-height: 75%;
    overflow-y: scroll;
    background-color: #fffefb;
}

.preview-pptx .page {
    margin-top: 1em;
    margin-left: 2em;
}

.page .content {
    display: flex;
    flex-direction: column;
}
</style>