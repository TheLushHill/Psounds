<script>
    export default {

        methods: {
            handleFileSelect(event) {
                let target = event.target;

                if (target.tagName === "BUTTON") {
                    let index = Number(target.getAttribute("file-id"));
                    this.$emit("file-select", index);
                }
            }
        },

        props: {
            fileList: Array,
        }
    }
</script>

<template>
    <div class="file-list"
        @click="handleFileSelect"
    >
        <button
            v-for="(file, index) in fileList"
            class="file-item"
            :file-id="index"
        >{{ file.name }}</button>      
    </div>
</template>

<style>
.file-list {
    display: flex;
    flex: 1 1 auto;
    flex-direction: column;
    width: 100%;
    padding-top: 8px;
    
}

.file-list button {
    margin: 0px 8px;
    padding: 8px;
    border-radius: 8px;
    background-color: #d4eaf7;
    cursor: pointer;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    border: none;
}

.file-list button:hover {
    background-color: #b3d9f0;
}

.file-list button:first-child {
    background-color: #87ceeb;  
    border-left: 4px solid #4682b4;  
    font-weight: bold; 
}
</style>