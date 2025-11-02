<script setup>
import { ref, provide } from 'vue'
import UploadingDocuments from './components/UploadingDocuments.vue'
import AnamDialogue from './components/AnamDialogue.vue'
import { FORM_CTX_KEY } from '@/components/formCtx'

const form = ref({
  name: '',
  role: '',
  company: '',
  country: '',
  file: null,
  fileName: '',
  jobSpec: '',
  parsedText: ''   
})


provide(FORM_CTX_KEY, form)
</script>

<template>
  <div class="container">
    <UploadingDocuments />
    <AnamDialogue />
  </div>
</template>

<style scoped>


</style>
