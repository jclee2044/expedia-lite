<script setup>
import { nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'

import { getChatHistory, streamChatReply } from '../api/chatStream.js'
import { applyReplyFailure } from '../chat/replyFailure.js'

const STORAGE_KEY = 'expedia-lite-chat-conversation-id'

const isOpen = ref(false)
const draft = ref('')
const messages = ref([])
const isStreaming = ref(false)
const isLoadingHistory = ref(false)
const errorMessage = ref('')
const errorCode = ref('')
const retryQuestion = ref('')
const conversationId = ref(null)
const announcement = ref('')
const launcher = ref(null)
const input = ref(null)
const log = ref(null)
const followLatest = ref(true)
const streamController = ref(null)
let nextMessageId = 0

onMounted(async () => {
  const savedId = localStorage.getItem(STORAGE_KEY)
  if (!savedId) return
  isLoadingHistory.value = true
  try {
    const history = await getChatHistory(savedId)
    if (!history) {
      localStorage.removeItem(STORAGE_KEY)
      return
    }
    conversationId.value = history.conversation_id
    messages.value = history.messages.map((message) => ({
      id: ++nextMessageId,
      role: message.role,
      content: message.content,
      state: message.role === 'assistant' ? 'complete' : undefined,
    }))
    if (history.last_error && messages.value.at(-1)?.role === 'user') {
      retryQuestion.value = messages.value.at(-1).content
      errorMessage.value = history.last_error
      errorCode.value = history.last_error_code || 'retryable'
      const reply = { id: ++nextMessageId, role: 'assistant', content: '' }
      announcement.value = applyReplyFailure(reply, { message: history.last_error, code: errorCode.value })
      messages.value.push(reply)
    }
  } catch (error) {
    errorMessage.value = error.message || 'Saved chat history could not be loaded.'
  } finally {
    isLoadingHistory.value = false
  }
})

function onLogScroll() {
  const element = log.value
  if (!element) return
  followLatest.value = element.scrollHeight - element.scrollTop - element.clientHeight < 48
}

async function scrollToLatest(force = false) {
  await nextTick()
  if (log.value && (force || followLatest.value)) {
    log.value.scrollTop = log.value.scrollHeight
  }
}

async function openChat() {
  isOpen.value = true
  await nextTick()
  input.value?.focus()
  if (followLatest.value) await scrollToLatest()
}

async function closeChat() {
  isOpen.value = false
  await nextTick()
  launcher.value?.focus()
}

function toggleChat() {
  if (isOpen.value) closeChat()
  else openChat()
}

async function sendQuestion(question) {
  if (isStreaming.value || isLoadingHistory.value) return
  const normalized = question.trim()
  if (!normalized) {
    errorMessage.value = 'Enter a question to send.'
    input.value?.focus()
    return
  }

  errorMessage.value = ''
  errorCode.value = ''
  retryQuestion.value = ''
  announcement.value = ''
  messages.value.push({ id: ++nextMessageId, role: 'user', content: normalized })
  draft.value = ''
  const reply = reactive({ id: ++nextMessageId, role: 'assistant', content: '', state: 'streaming' })
  messages.value.push(reply)
  isStreaming.value = true
  followLatest.value = true
  await scrollToLatest(true)

  const controller = new AbortController()
  streamController.value = controller
  try {
    for await (const chunk of streamChatReply({
      question: normalized,
      conversationId: conversationId.value,
      onMeta: (id) => {
        conversationId.value = id
        localStorage.setItem(STORAGE_KEY, id)
      },
      signal: controller.signal,
    })) {
      reply.content += chunk
      await scrollToLatest()
    }
    if (!controller.signal.aborted) {
      reply.state = 'complete'
      announcement.value = 'Grounded reply complete.'
    }
  } catch (error) {
    if (controller.signal.aborted) return
    errorMessage.value = error.message || 'The chat reply stopped. Try again.'
    errorCode.value = error.code || 'retryable'
    retryQuestion.value = normalized
    announcement.value = applyReplyFailure(reply, { message: errorMessage.value, code: errorCode.value })
  } finally {
    isStreaming.value = false
    streamController.value = null
    await scrollToLatest()
  }
}

function submitQuestion() {
  sendQuestion(draft.value)
}

function retryReply() {
  if (!retryQuestion.value) return
  if (errorCode.value === 'missing_context') {
    draft.value = retryQuestion.value
    input.value?.focus()
  } else sendQuestion(retryQuestion.value)
}

onBeforeUnmount(() => streamController.value?.abort())
</script>

<template>
  <div class="chat-dock">
    <Transition name="chat-panel">
      <section
        v-show="isOpen"
        id="hotel-chat-panel"
        class="chat-panel"
        aria-labelledby="hotel-chat-title"
        :inert="!isOpen"
        @keydown.esc="closeChat"
      >
        <header class="chat-panel-header">
          <div>
            <p class="chat-kicker">Saved hotel assistant · simulated data</p>
            <h2 id="hotel-chat-title">Ask Expedia Lite</h2>
          </div>
          <button type="button" class="chat-close" aria-label="Close chat" @click="closeChat">×</button>
        </header>

        <div ref="log" class="chat-log" role="log" aria-label="Chat conversation" aria-live="off" @scroll="onLogScroll">
          <p v-if="!messages.length" class="chat-empty">
            Ask which hotels are saved for a ZIP. Include dates when asking about simulated prices or availability.
          </p>
          <article
            v-for="message in messages"
            :key="message.id"
            class="chat-message"
            :class="`chat-message--${message.role}`"
          >
            <span class="chat-message-role">{{ message.role === 'user' ? 'You' : 'Assistant' }}</span>
            <p>{{ message.content || (message.state === 'error' ? 'No answer was saved.' : 'Preparing a checked reply…') }}</p>
            <span v-if="message.state === 'streaming'" class="chat-streaming-label">Checking the recommendation…</span>
            <span v-else-if="message.state === 'clarification'" class="chat-streaming-label">More information needed</span>
            <span v-else-if="message.state === 'error'" class="chat-failed-label">Reply failed</span>
          </article>
        </div>

        <p class="chat-announcement" role="status">{{ announcement }}</p>
        <div v-if="errorMessage" class="chat-error" :class="{ 'chat-error--clarification': errorCode === 'missing_context' }" :role="errorCode === 'missing_context' ? 'status' : 'alert'">
          <span>{{ errorMessage }}</span>
          <button v-if="retryQuestion" type="button" @click="retryReply">{{ errorCode === 'missing_context' ? 'Edit question' : 'Retry reply' }}</button>
        </div>

        <form class="chat-composer" @submit.prevent="submitQuestion">
          <label for="chat-question">Ask a question</label>
          <div class="chat-composer-row">
            <textarea
              id="chat-question"
              ref="input"
              v-model="draft"
              rows="2"
              maxlength="500"
              placeholder="Ask about a hotel stay…"
              :disabled="isStreaming || isLoadingHistory"
              @keydown.enter.exact.prevent="submitQuestion"
            ></textarea>
            <button type="submit" :disabled="isStreaming || isLoadingHistory || !draft.trim()">Send</button>
          </div>
          <p class="chat-help">Enter to send · Shift+Enter for a new line</p>
        </form>
      </section>
    </Transition>

    <button
      ref="launcher"
      type="button"
      class="chat-launcher"
      :aria-expanded="isOpen"
      aria-controls="hotel-chat-panel"
      @click="toggleChat"
    >
      <span class="chat-launcher-icon" aria-hidden="true">✦</span>
      {{ isOpen ? 'Hide chat' : 'Chat' }}
    </button>
  </div>
</template>
