<script>
    export default {

        props: {
            isVisible: Boolean,
        }
    }
</script>

<template>
    <div class="trainPanel"
        v-show="isVisible"
    >
        文本转换
    </div>
</template>

<style>
.trainPanel {
    display: flex;
    flex: 1 1 auto;
    flex-direction: column;
    height: 100%; 
    background-color: #fff;
}

</style>