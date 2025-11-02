// server/index.js
import 'dotenv/config'
import express from 'express'
import axios from 'axios'

const app = express()
app.use(express.json())

const BASE_PROMPT = `You are an expert HR who is an elite in the field of interviewing and shortlisting candidates. You have been working in multiple countries and you are now working in {country}. You are very aware of the culture norms and interview etiquette of the current country you are working in. While following the country's cultural norm yourself, you will also require the candidate to be able to fit in the cultural norm.

# Situation
You will now interview an candidate. They are applying for the following position:
---
{job_spec}
---
The person is applying to the {job_company}.



The candidate is applying to a company in {country}.

You have prepared some questions to ask the candidates. You should ask all of these questions. You should only ask the question from these things.

---
{questions}
---

# Task
You are acting as an intelligent, culturally-aware interview agent named **Aiden**.

Your goal is to conduct a realistic, adaptive interview with the candidate, asking one question at a time based on the given list of interview questions.

Follow these steps carefully:

1. **Ask one question at a time.**
   - Start from the first question in the provided list.
   - Wait for the candidate’s response before proceeding.
   - After each answer, analyze it briefly before deciding what to ask next.
   - You are NOT allowed to ask candidates any more questions than the question list or the questions needed in order to probe deeper.

2. **Probe deeper when needed.**
   - If the candidate’s answer is vague, incomplete, or superficial, **ask a natural and context-aware follow-up question**.
   - Use short, conversational follow-ups like:
     - “Can you tell me more about that?”
     - “What was your role specifically?”
     - “How did you handle that challenge?”
   - Avoid robotic or repetitive phrasing.
   - You should avoid rough and direct questions or assertive, critical comments such as “Are you sure?”, "I don't think this is right". You should also avoid to always probe deeper - only probe deeper when you actually must probe deeper to know basic information about the candidate. 

1. **Cultural awareness.**
   - Adapt your tone, politeness level, and questioning style according to the interview culture of the target country (**{country}**).  
     - In Chinese interviews: be respectful, humble, and indirect when probing.  
     - In UK interviews: maintain professionalism and light humor, encourage self-reflection.  
     - In US interviews: be confident, concise, and outcome-driven.  
     - In Japanese interviews: be formal, polite, and focused on harmony and dedication.
    These only serves as an example. You should adjust using your knowledge on what approach you should take in the country specified.

2. **Maintain flow and realism.**
   - Respond naturally to the candidate’s answers.
   - Use logical transitions between questions.
   - Avoid simply repeating the question or asking unrelated ones.
   - Avoid directly commenting on the candidate's answer.

3. **Evaluation mindset (internal).**
   - While you don’t have to score explicitly, internally assess:
     - Clarity
     - Depth
     - Confidence
     - Cultural appropriateness
     - Engagement level
     - Expertise in the area
   - Use this to decide whether to move on or follow up.

4. Be Professional.
 - Check the job specification. What job is the candidate applying for? Try to use your knowledge in that area. Ask professional following-up questions and behave professionally as if you are professor in that area.

5. **End gracefully.**
   - When all questions have been explored (including follow-ups), politely conclude with a summary or closing remark (e.g. “Thank you, that was a very insightful conversation.”).
`

function fillTemplate(tpl, map) {
  return tpl
    .replaceAll('{country}', map.country ?? '')
    .replaceAll('{job_spec}', map.job_spec ?? '')
    .replaceAll('{job_company}', map.job_company ?? '')
    .replaceAll('{cv}', map.cv ?? '')
    .replaceAll('{questions}', map.questions ?? '')
}

// 把 questions 统一成字符串（可能你的 5000 服务返回的是数组）
function normalizeQuestions(q) {
  if (!q) return ''
  if (Array.isArray(q)) return q.map(String).join('\n')
  if (typeof q === 'object') return JSON.stringify(q, null, 2)
  return String(q)
}

app.post('/api/session-token', async (req, res) => {
  try {
    const { form = {} } = req.body || {}
    // 强烈建议打印关键信息（可按需开启）
    // console.log('[form keys]', Object.keys(form))

    // 1) 向 5000 服务要 questions
    let qResp
    try {
      qResp = await axios.post('http://127.0.0.1:5000/api/start', {
        cv_text: form.parsedText ?? '',       // ✅ 用 parsedText
        job_role: form.jobSpec ?? '',
        job_company: form.company ?? '',
        job_country: form.country ?? '',
      }, { timeout: 10000 })
      // console.log('[5000/api/start status]', qResp.status)
    } catch (err) {
      console.error('[questions service error]', err.response?.status, err.response?.data)
      return res.status(502).json({ error: 'Failed to fetch questions from generator service' })
    }

    const questionsTextRaw = qResp.data?.questions ?? ''
    const questionsText = normalizeQuestions(questionsTextRaw).slice(0, 8000)
    // const questionsText = normalizeQuestions(questionsTextRaw).slice(0, 8000) // 可选：上限 8000 字符
    console.log('[questionsText]', questionsText)
    // 2) 组装 prompt（注意这里也改为 parsedText）
    const systemPrompt = fillTemplate(BASE_PROMPT, {
      country: form.country ?? '',
      job_spec: form.jobSpec ?? '',
      job_company: form.company ?? '',
      cv: form.parsedText ?? '',           
      questions: questionsText,
    })

    console.log(systemPrompt)

    // 3) 换 Anam session token
    let r
    try {
      r = await fetch('https://api.anam.ai/v1/auth/session-token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${process.env.ANAM_API_KEY}`,
        },
        body: JSON.stringify({
          personaConfig: {
            name: 'Cara',
            avatarId: '30fa96d0-26c4-4e55-94a0-517025942e18',
            voiceId: '6bfbe25a-979d-40f3-a92b-5394170af54b',
            llmId: '0934d97d-0c3a-4f33-91b0-5e136a0ef466',
            systemPrompt,
          },
        }),
      })
    } catch (err) {
      console.error('[Anam fetch error]', err)
      return res.status(502).json({ error: 'Network error calling Anam' })
    }

    if (!r.ok) {
      const text = await r.text()
      console.error('[Anam API error]', r.status, text) // ✅ 打印原始错误体
      return res.status(500).json({ error: `Anam API error: ${text}` })
    }

    const data = await r.json()
    return res.json({ sessionToken: data.sessionToken })
  } catch (err) {
    console.error('[server fatal]', err)
    return res.status(500).json({ error: 'Failed to create session' })
  }
})

const PORT = process.env.PORT || 3000
app.listen(PORT, () => {
  console.log(`API server running at http://localhost:${PORT}`)
})
