const STREAM_URL = '/api/chat/stream'

export class ChatReplyError extends Error {
  constructor(message, code = 'retryable') {
    super(message)
    this.code = code
  }
}

export async function* readChatEvents(body) {
  if (!body) throw new Error('The chat stream did not start.')
  const reader = body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let event = ''
  let data = []
  try {
    while (true) {
      const { value, done } = await reader.read()
      buffer += done ? decoder.decode() : decoder.decode(value, { stream: true })
      if (buffer.length > 65536) throw new Error('The chat stream was too large.')
      while (buffer.includes('\n')) {
        const end = buffer.indexOf('\n')
        const line = buffer.slice(0, end).replace(/\r$/, '')
        buffer = buffer.slice(end + 1)
        if (line.startsWith('event:')) event = line.slice(6).trim()
        else if (line.startsWith('data:')) data.push(line.slice(5).trimStart())
        else if (!line && data.length) {
          let payload
          try {
            payload = JSON.parse(data.join('\n'))
          } catch {
            throw new Error('The chat stream contained invalid data.')
          }
          yield { event, payload }
          event = ''
          data = []
        }
      }
      if (done) break
    }
    if (data.length) {
      try {
        yield { event, payload: JSON.parse(data.join('\n')) }
      } catch {
        throw new Error('The chat stream contained invalid data.')
      }
    }
  } finally {
    reader.releaseLock()
  }
}

export async function* streamChatReply({ question, conversationId, onMeta, signal }) {
  const response = await fetch(STREAM_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, conversation_id: conversationId || null }),
    signal,
  })
  if (!response.ok) {
    throw new Error(response.status === 422 ? 'Enter a valid question.' : 'The chat request failed.')
  }
  let completed = false
  let receivedMeta = false
  for await (const { event, payload } of readChatEvents(response.body)) {
    if (event === 'meta' && typeof payload.conversation_id === 'string') {
      receivedMeta = true
      onMeta?.(payload.conversation_id)
    } else if (event === 'delta' && typeof payload.text === 'string') yield payload.text
    else if (event === 'done') {
      completed = true
      break
    } else if (event === 'error') {
      throw new ChatReplyError(
        typeof payload.message === 'string' ? payload.message : 'Gemini could not reply.',
        payload.code === 'missing_context' ? 'missing_context' : 'retryable',
      )
    } else {
      throw new Error('The chat stream contained an unknown event.')
    }
  }
  if (!completed || !receivedMeta) throw new Error('The chat reply was interrupted. Try again.')
}

export async function getChatHistory(conversationId) {
  const response = await fetch(`/api/chat/history?conversation_id=${encodeURIComponent(conversationId)}`)
  if (response.status === 404) return null
  if (!response.ok) throw new Error('Saved chat history could not be loaded.')
  return response.json()
}
