<script>
    export default {
        data() {
            return {
        
            }
        },
        methods: {
            handleClick(event) {
                if (this.isDocx) {
                    this.$emit("play-stream", "docx", Number(event.target.getAttribute("id")));
                }

                if (this.isPptx) {
                    this.$emit("play-stream", "pptx", Number(event.target.getAttribute("id")));
                }   
            },
            
            onChange(event) {
                this.$emit("checked", {
                    index: event.target.value,
                    checked: event.target.checked,
                });
            }
            
        },

        watch: {
            
        },

        computed: {
            isDocx() {
                return this.file.type === "docx";
            },
            
            isPptx() {
                return  this.file.type === "pptx";
            },
        },

        props: {
            isVisible: {
                type: Boolean,
                required: true
            },
            file: Object,
            uploaded: Boolean,
        },
    }
</script>

<template> 
    <div class="preview-panel" v-show="isVisible">
        <div v-if="this.uploaded">
            <div class="control-bar">
                <div>文件预览界面，请勾选文本作为待转换内容。点击🔈试听当前模型文字转语音效果</div>
            </div>
        </div>
        <div v-else>请先上传文件</div>
        <div class="preview-docx"
            v-show="isDocx"
        >
            <div class="text-line"
                v-for="(item, index) in file.content"
            >
                <input type="checkbox" class="checkbox" :value="index" @change="onChange" 
                />
                <span class="paragraph" 
                    :class="'paragraph-' + index"
                >{{ item }}<button class="play" :id="index" @click="handleClick">🔈</button></span>
                
            </div>
        </div>

        <div class="preview-pptx"
            v-show="isPptx"
        >
            <div class="page"
                v-for="(item, index) in file.content">
                <input type="checkbox" class="checkbox"
                />
                <div>
                    <span class="index"
                    >第{{ index + 1 }}页
                    <button class="play" :id="index" @click="handleClick">🔈</button>
                    </span>
                    <div class="content">
                        <span
                            v-for="line in item"
                        >{{ line }}</span>
                    </div>
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
    margin-bottom: 8px;
}

.preview-panel::-webkit-scrollbar {
    width: 8px; 
}

.preview-docx {
    display: flex;
    flex: 1 1 auto;
    flex-direction: column;
    overflow-y: auto;

    background-color: #fffefb;
}

.control-bar {
    display: flex;
    padding: 8px;
    gap: 16px;
    background-color: #f5f5f5;
    border-bottom: 1px solid #e8e8e8;
}

.select-all {
    display: flex;
    align-items: center;
    cursor: pointer;
}

.select-all input {
    margin-right: 8px;
}

.preview-docx .text-line {
    display: flex;
    flex-direction: row;
    margin-top: 1em;
    line-height: 1.5;
    align-items: flex-start;
}

.checkbox {
    margin-top: 5px;
    flex-shrink: 0;
}

.preview-docx .paragraph {
    display:block;
    padding: 0 16px;
    padding-left: 0px;
}

.preview-pptx {
    display: flex;
    flex-direction: column;
    overflow-y: scroll;
    background-color: #fffefb;
}

.preview-pptx .page {
    display: flex;
    align-items: flex-start;
    flex-direction: row;
    margin-top: 1em;
    margin-left: 2em;
}

.page .content {
    display: flex;
    flex-direction: column;
}
</style>