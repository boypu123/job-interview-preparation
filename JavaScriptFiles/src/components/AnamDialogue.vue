<script setup>
import { ref, onBeforeUnmount, inject } from 'vue'
import { createClient, AnamEvent } from '@anam-ai/js-sdk'
import axios from 'axios'
import { FORM_CTX_KEY } from '@/components/formCtx'

const starting = ref(false)
const canStop = ref(false)
let anamClient = null
let sessionId = null

// 结果对象（用于结构化展示）
const finalReview = ref(null)

const form = inject(FORM_CTX_KEY)
if (!form) throw new Error('Missing formCtx provide. Make sure ancestor provides it.')

const chatHistory = ref([])

function bindAnamListeners() {
  anamClient.addListener(AnamEvent.MESSAGE_HISTORY_UPDATED, (messages) => {
    console.log('Conversation updated:', messages)
    chatHistory.value = messages
  })
}

async function startChat() {
  try {
    starting.value = true

    const payload = { form: { ...form.value } }
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
  } catch (e) {
    console.error('Failed to start chat:', e)
  } finally {
    starting.value = false
  }
}

async function stopChat() {
  if (anamClient) {
    anamClient.stopStreaming?.()

    const transcript = chatHistory.value
      .map((m) => `${m.role}: ${m.content}`)
      .join('\n')

    if (sessionId && transcript) {
      try {
        console.log('Sending transcript to Flask /api/finish ...')
        const finishResp = await axios.post('http://127.0.0.1:5000/api/finish', {
          session_id: sessionId,
          transcript,
        })
        console.log('Final review from Flask:', finishResp.data.final_review)
        // 假设后端返回的是 JSON 对象
        try {
          finalReview.value = typeof finishResp.data.final_review === 'string'
            ? JSON.parse(finishResp.data.final_review)
            : finishResp.data.final_review
        } catch {
          finalReview.value = { raw: finishResp.data.final_review }
        }
      } catch (err) {
        console.error('Failed to finish interview:', err.response?.data || err)
      }
    }

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

    <video
      id="persona-video"
      autoplay
      muted
      playsinline
      style="max-width:100%; border-radius:8px;"
    ></video>

    <div style="margin-top:20px;">
      <button :disabled="starting || canStop" @click="startChat">
        {{ starting ? 'Starting…' : 'Start Chat' }}
      </button>
      <button :disabled="!canStop" @click="stopChat">Stop Chat</button>
    </div>

    <!-- === 结果展示区 === -->
    <div v-if="finalReview" class="review-section">
      <h2>Performance Summary</h2>
      <p>{{ finalReview.performance_summary }}</p>

      <h2>Topic Ratings</h2>
      <ul>
        <li v-for="(obj, key) in finalReview.topic_ratings" :key="key">
          <strong>{{ key }}:</strong> {{ obj.Rating }}/5 — {{ obj.Reasoning }}
        </li>
      </ul>

      <h2>Strengths</h2>
      <ul>
        <li v-for="s in finalReview.strengths" :key="s">{{ s }}</li>
      </ul>

      <h2>Weaknesses</h2>
      <ul>
        <li v-for="w in finalReview.weaknesses" :key="w">{{ w }}</li>
      </ul>

      <h2>Fit Assessment</h2>
      <div v-for="(cat, name) in finalReview.fit_assessment" :key="name" class="fit-block">
        <h3>{{ name }}</h3>
        <p><strong>Score:</strong> {{ cat.Score }}</p>
        <p><strong>Reason:</strong> {{ cat.Justification }}</p>
      </div>

      <h2>Improvement Plan</h2>
      <ul>
        <li v-for="(item, idx) in finalReview.improvement_plan" :key="idx">
          <strong>{{ item['Issue'] }}</strong> → {{ item['Action Step'] }}
          <br /><em>({{ item['Timeline'] }} — {{ item['Why it matters'] }})</em>
        </li>
      </ul>

      <h2>Agentic Follow-ups</h2>
      <ul>
        <li v-for="(f, idx) in finalReview.agentic_followup" :key="idx">{{ f }}</li>
      </ul>

      <h2>Final Decision</h2>
      <p><strong>{{ finalReview.decision }}</strong></p>
    </div>

    <!-- 如果返回的是非结构化内容 -->
    <div v-else-if="typeof finalReview === 'string'">
      <h2>Raw Review Text</h2>
      <pre style="white-space:pre-wrap; text-align:left;">{{ finalReview }}</pre>
    </div>
  </div>
</template>

<style scoped>
.review-section {
  text-align: left;
  max-width: 800px;
  margin: 40px auto;
  padding: 20px;
  background: #f9fafb;
  border-radius: 12px;
  box-shadow: 0 0 10px rgba(0,0,0,0.1);
}
.review-section h2 {
  color: #1a1a1a;
  margin-top: 1.5em;
  border-bottom: 2px solid #ddd;
  padding-bottom: 4px;
}
.fit-block {
  background: #fff;
  padding: 10px 14px;
  border-radius: 8px;
  margin: 10px 0;
  border: 1px solid #eee;
}
ul {
  list-style: disc;
  padding-left: 24px;
}
button {
  padding: 8px 14px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  margin: 0 6px;
}
button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
