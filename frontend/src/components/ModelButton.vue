<script>
    export default {

        props: {
            info: {
                type: Object,
                required: true
            }
        }
    }
</script>

<template>
    <button class="modelButton">
        <div>
            <img :src="info.iconUrl"/>
            <span>{{ info.name }}</span>
        </div>
    </button>
</template>

<style>
.modelButton {
    display: flex;
    flex-direction: row;
    align-items: center;
    justify-content: center;
    min-width: 8em;
    min-height: 4em;
    max-height: 5em;
    margin: 8px;
    border: 1px solid #000000;
    border-radius: 8px;
    background-color: #ffffff;
}

.modelButton:hover {
    background-color: #d4eaf7;
}

.modelButton div {
    gap: 8px;
    display: flex;
    flex-direction: row;
    align-items: center;
    justify-content: center;
    border:1px solid #000000;
    border-radius: 8px;
}

.modelButton img {
    width: 2.5em;
    height: 2.5em;
    border: 1px solid #000000;
    border-radius: 8px;
    object-fit: cover;
}

.modelButton img:hover {
    background-color: #529cc7;
}

.modelButton span {
    font-size: 16px;
}

</style>