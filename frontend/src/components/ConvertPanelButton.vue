<script>
    export default {

    }
</script>

<template>
    <button class="train-button"
        @click="$emit('update-panel')"
    >
        转换
    </button>
</template>

<style>
.train-button {
    margin: 0 8px;
    height: 3em;
    border-radius: 12px;
    background-color: #DCDAF5;
    border: none;
}

.train-button:hover {
    background-color: #D1CEE9;
}

</style>