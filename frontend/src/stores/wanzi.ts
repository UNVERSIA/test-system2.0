import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '../api'

export type WanziStage = 'orb' | 'pet' | 'chat'
export type WanziMessage = { role: 'user' | 'assistant'; content: string; timestamp: string }
const POSITION_KEY = 'wanzi-position-vue'
const STAGE_KEY = 'wanzi-stage-vue'
const MESSAGES_KEY = 'wanzi-messages-vue'
function readJson<T>(key: string, fallback: T): T { try { return JSON.parse(localStorage.getItem(key) || '') as T } catch { return fallback } }

export const useWanziStore = defineStore('wanzi', () => {
  const stage = ref<WanziStage>(readJson(STAGE_KEY, 'orb'))
  const position = ref<{ x: number; y: number } | null>(readJson(POSITION_KEY, null))
  const messages = ref<WanziMessage[]>(readJson(MESSAGES_KEY, []))
  const sending = ref(false)
  const error = ref('')
  const modelUrl = '/assets/models/wanzi_web.glb'
  const greeting = '你好呀，我是烷仔！有什么污水处理问题都可以问我。'
  const hasMessages = computed(() => messages.value.length > 0)
  function persist() { localStorage.setItem(STAGE_KEY, JSON.stringify(stage.value)); localStorage.setItem(MESSAGES_KEY, JSON.stringify(messages.value)); if (position.value) localStorage.setItem(POSITION_KEY, JSON.stringify(position.value)) }
  function setStage(next: WanziStage) { stage.value = next; error.value = ''; persist() }
  function setPosition(next: { x: number; y: number }) { position.value = next; persist() }
  function addMessage(role: WanziMessage['role'], content: string) { messages.value.push({ role, content, timestamp: new Date().toISOString() }); persist() }
  function openPet() { setStage('pet') }
  function openChat() { setStage('chat') }
  function closeChat() { setStage('pet') }
  function restoreOrb() { setStage('orb') }
  async function sendMessage(text: string) {
    const clean = text.trim(); if (!clean || sending.value) return
    error.value = ''; addMessage('user', clean); sending.value = true
    try {
      const response = await api.post('/chat', { message: clean })
      const data = response.data as { response?: string; error?: string }
      if (data.error === 'coze_configuration') addMessage('assistant', '智能体服务尚未配置，请在本地环境变量中配置')
      else if (data.response) addMessage('assistant', data.response)
      else addMessage('assistant', '连接智能体时出现问题，请稍后重试。')
    } catch { addMessage('assistant', '连接智能体时出现问题，请确认 FastAPI 服务已启动后重试。') }
    finally { sending.value = false; persist() }
  }
  async function clearHistory() {
    try { await api.delete('/chat/history') } catch { /* Local history must remain clear even if the backend is unavailable. */ }
    messages.value = []; error.value = ''; persist()
  }
  return { stage, position, messages, sending, error, modelUrl, greeting, hasMessages, setPosition, setStage, openPet, openChat, closeChat, restoreOrb, sendMessage, clearHistory }
})
