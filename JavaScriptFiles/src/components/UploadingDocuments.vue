<script setup>
import { ref, inject } from 'vue'
import { NCard, NForm, NFormItem, NInput, NButton } from 'naive-ui'
import { FORM_CTX_KEY } from '@/components/formCtx'
import { extractPdfText } from './pdfText.js'

const form = inject(FORM_CTX_KEY)
if (!form) throw new Error('Missing form ctx')

const errors = ref({ name:'', role:'', company:'', country:'', file:'', jobSpec:'' })
const isThinking = ref(false)

function clearErrors(){ for (const k in errors.value) errors.value[k] = '' }

function validate(){
  clearErrors()
  let ok = true
  if (!form.value.name){ errors.value.name = 'Required'; ok = false }
  if (!form.value.role){ errors.value.role = 'Required'; ok = false }
  if (!form.value.company){ errors.value.company = 'Required'; ok = false }
  if (!form.value.country){ errors.value.country = 'Required'; ok = false }
  if (!form.value.file){ errors.value.file = 'Please upload your CV'; ok = false }
  return ok
}

async function handleFileUpload(e){
  const input = e.target
  if (!input.files?.length) return
  const file = input.files[0]
  if (file.size > 5 * 1024 * 1024){ alert('File exceeds 5MB limit'); return }

  form.value.file = file
  form.value.fileName = file.name
  form.value.parsedText = ''   // 清空旧文本

  try{
    isThinking.value = true
    let text
    if (file.type === 'application/pdf'){
      text = await parsePDF(file)
    } else if (file.type.startsWith('text/')){
      text = await readTextFile(file)
    } else {
      alert('Unsupported file type. Please upload a text or PDF file.')
      return
    }
    form.value.parsedText = String(text).trim()  
    console.log('Parsed file content:', form.value.parsedText.slice(0, 1000))
  }catch(err){
    console.error('File parsing failed:', err)
    alert('File parsing failed. Please upload a valid file.')
  }finally{
    isThinking.value = false
  }
}

async function parsePDF(file){
  const buf = await file.arrayBuffer()
  return await extractPdfText(buf)
}

function readTextFile(file){
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result)
    reader.onerror = reject
    reader.readAsText(file, 'utf-8')
  })
}

function onSubmit(){
  if (!validate()) return
  console.log('Submitted form:', {
    ...form.value,
    parsedTextPreview: form.value.parsedText.slice(0, 1000),
  })
}
</script>

<template>
  <n-card>
    <h1 style="font-size: 32px; font-weight: 800; margin: 0 0 8px;">
      Welcome to Job Interview Prep Agent!
    </h1>

    <n-form :model="form" label-placement="top" @submit.prevent="onSubmit">
      <n-form-item label="What is your name?">
        <n-input v-model:value="form.name" placeholder="e.g. Jayden" />
        <p v-if="errors.name" class="err">{{ errors.name }}</p>
      </n-form-item>

      <n-form-item label="Which role have you applied to?">
        <n-input v-model:value="form.role" placeholder="e.g. SWE" />
        <p v-if="errors.role" class="err">{{ errors.role }}</p>
      </n-form-item>

      <n-form-item label="Which company have you applied to?">
        <n-input v-model:value="form.company" placeholder="e.g. Google" />
        <p v-if="errors.company" class="err">{{ errors.company }}</p>
      </n-form-item>

      <n-form-item label="What country have you applied to?">
        <n-input v-model:value="form.country" placeholder="e.g. UK" />
        <p v-if="errors.country" class="err">{{ errors.country }}</p>
      </n-form-item>

      <n-form-item label="Input the job spec">
        <n-input v-model:value="form.jobSpec" placeholder="e.g. SWE" />
        <p v-if="errors.jobSpec" class="err">{{ errors.jobSpec }}</p>
      </n-form-item>

      <n-form-item label="Upload your CV / resume">
        <input type="file" accept=".pdf,.txt,.doc,.docx" @change="handleFileUpload" />
        <div v-if="form.fileName" style="margin-top: 6px; font-size: 12px;">
          Selected: {{ form.fileName }}
        </div>
        <p v-if="errors.file" class="err">{{ errors.file }}</p>
      </n-form-item>

      <n-button type="primary" attr-type="submit" block size="large" :loading="isThinking">
        Submit
      </n-button>
    </n-form>

    <!-- 预览直接用 form.parsedText -->
    <pre v-if="form.parsedText" class="preview">
{{ form.parsedText.slice(0, 500) }}{{ form.parsedText.length > 500 ? '... (truncated)' : '' }}
    </pre>
  </n-card>
</template>

<style scoped>
.err { color: #d03050; margin: 6px 0 0; font-size: 12px; }
.preview { margin-top: 16px; font-size: 12px; background: #f7f7f7; padding: 12px; white-space: pre-wrap; border-radius: 8px; }
</style>
