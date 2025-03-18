<script>
    import AppButton from "./AppButton.vue"
    import UploadFileButton from "./UploadFileButton.vue"

    export default {
        components: {
            AppButton,
            UploadFileButton,
        }
    }
</script>

<template>
    <div id="main">
        <div id="list">
            <UploadFileButton id="uploadfile"></UploadFileButton>
            <AppButton id="b2"></AppButton>
            <AppButton id="b3"></AppButton>
            <AppButton id="b4"></AppButton>
        </div>
        <div id="container">container</div>
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
    margin: 0 16px;

    display: flex;
    flex-direction: column;

    background-color: #cccbc8;
}

#container {
    flex:1 1 auto;

    background-color: #cccbc8;
}

#uploadfile {
    
}
</style>