<script>
    
    import ModelButton from "./TrainPanelButton.vue";

    export default {
        data() {
            return {
                audio : {
                    resource: new Audio(),
                    isPlaying: false,
                    audioUrl: "",
                }
            }
        },

        methods: {
            onSelectModel(event) {
                let clickedElement = event.target;

                if (clickedElement.tagName.toLowerCase() === "button") {
                    let index = clickedElement.getAttribute("data-index");
                    this.$emit("model-select", Number(index));
                }

                if (clickedElement.tagName.toLowerCase() === "img") {
                    if (!this.audio.isPlaying) {
                        this.audio.resource.src = this.list[this.model].audioUrl;
                        this.audio.resource.play();
                        this.audio.isPlaying = true;
                    } else {
                        this.audio.resource.pause();
                        this.audio.isPlaying = false;
                    }
                } 
            }
        },

        components: {
            ModelButton
        },

        props: {
            isVisible: {
                type: Boolean,
                required: true
            },
            list: {
                type: Array,
                required: true
            },
            model: {
                type: Number,
                required: true
            }
        }
    }
</script>

<template>
    <div class="model-panel" v-show="isVisible">
        <div class="model-select"
            @click="onSelectModel"
        >
            <template v-for="(item, index) in list">
                <ModelButton 
                    :info="item"
                    :data-index="index"
                ></ModelButton>
            </template>
        </div>
        <div class="model-train">

        </div>        
    </div>
</template>

<style>
.model-panel {
    margin: 16px;
	display: flex;
    flex: 1 1 auto;
	flex-direction: column;
}

.model-select {
    display: flex;
    flex-direction: row;
    height: 70%;
    background-color: #fffefb;
}

.model-train {
    height: 30%;
    background-color: #f0f0f0;
    margin-top: 8px;
}

</style>