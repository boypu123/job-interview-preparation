<script setup>
import { ref, onBeforeUnmount, inject } from 'vue'
import { createClient } from '@anam-ai/js-sdk'
import axios from 'axios'
import { FORM_CTX_KEY } from '@/components/formCtx'

const starting = ref(false)
const canStop = ref(false)
let anamClient = null

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
    const { sessionToken } = resp.data

    anamClient = createClient(sessionToken)
    await anamClient.streamToVideoElement('persona-video')

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

anamClient.addListener(AnamEvent.MESSAGE_HISTORY_UPDATED, (messages) => {
  console.log('Conversation updated:', messages);
  updateChatHistory(messages);
});

function stopChat() {
  if (anamClient) {
    anamClient.stopStreaming?.()
    anamClient = null
  }
  const v = document.getElementById('persona-video')
  if (v) v.srcObject = null
  canStop.value = false
  
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
  </div>
</template>

<style scoped>
button { padding: 8px 14px; border-radius: 8px; border: none; cursor: pointer; margin: 0 6px; }
button:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
