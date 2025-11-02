<script setup>
import { ref, onBeforeUnmount, inject } from 'vue'
import { createClient } from '@anam-ai/js-sdk'
import axios from 'axios'
import { FORM_CTX_KEY } from '@/components/formCtx'
import { AnamEvent } from '@anam-ai/js-sdk'

const starting = ref(false)
const canStop = ref(false)
let anamClient = null
let sessionId = null
let finalReview = ref('')

const form = inject(FORM_CTX_KEY)
if (!form) throw new Error('Missing formCtx provide. Make sure ancestor provides it.')

async function startChat() {
  try {
    starting.value = true

    const payload = {
      form: {
        ...form.value,
      }
    }
    const resp = await axios.post('/api/session-token', payload)
    const { sessionToken, sessionId: flaskSessionId } = resp.data
    sessionId = flaskSessionId
    console.log('Flask sessionId:', sessionId)

    anamClient = createClient(sessionToken)
    await anamClient.streamToVideoElement('persona-video')
    bindAnamListeners()

    const videoEl = document.getElementById('persona-video')
    if (videoEl) {
      videoEl.muted = false
      videoEl.volume = 1.0
      try { await videoEl.play() } catch (err) { console.warn('play() 被阻止：', err) }
    }

    canStop.value = true
    console.log('Chat started (unmuted).')
  } catch (e) {
    console.error('Failed to start chat:', e)
  } finally {
    starting.value = false
  }
}

const chatHistory = ref([])
function updateChatHistory(messages){
  chatHistory.value = messages
}


function bindAnamListeners() {
  anamClient.addListener(AnamEvent.MESSAGE_HISTORY_UPDATED, (messages) => {
    console.log('Conversation updated:', messages)
    chatHistory.value = messages
  })
}

async function stopChat() {
  if (anamClient) {
    anamClient.stopStreaming?.()

    // 将对话记录整理为文本
    const transcript = chatHistory.value
      .map((m) => `${m.role}: ${m.content}`)
      .join('\n')

    // 如果有 sessionId，就向 Flask /api/finish 汇总
    if (sessionId && transcript) {
      try {
        console.log('📤 Sending transcript to Flask /api/finish ...')
        const finishResp = await axios.post('http://127.0.0.1:5000/api/finish', {
          session_id: sessionId,
          transcript,
        })
        console.log('✅ Final review from Flask:', finishResp.data.final_review)
        finalReview.value = finishResp.data.final_review || '(No review text)'
      } catch (err) {
        console.error('❌ Failed to finish interview:', err.response?.data || err)
      }
    }

    anamClient = null
  }
}



onBeforeUnmount(() => stopChat())
</script>

<template>
  <div style="text-align:center; padding:20px;">
    <h1>Chat with Cara</h1>
    <video id="persona-video" autoplay muted playsinline style="max-width:100%; border-radius:8px;"></video>
    <div style="margin-top:20px;">
      <button :disabled="starting || canStop" @click="startChat">
        {{ starting ? 'Starting…' : 'Start Chat' }}
      </button>
      <button :disabled="!canStop" @click="stopChat">Stop Chat</button>
    </div>
    <div style="margin-top:20px;">
      <p>Final Review: {{ finalReview }}</p>
    </div>
  </div>
</template>

<style scoped>
button { padding: 8px 14px; border-radius: 8px; border: none; cursor: pointer; margin: 0 6px; }
button:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
