import assert from 'node:assert/strict'
import test from 'node:test'

import { getChatHistory, streamChatReply } from '../src/api/chatStream.js'

function responseFromPieces(pieces, status = 200) {
  return new Response(new ReadableStream({
    start(controller) {
      for (const piece of pieces) controller.enqueue(new TextEncoder().encode(piece))
      controller.close()
    },
  }), { status, headers: { 'Content-Type': 'text/event-stream' } })
}

async function withFetch(stub, action) {
  const previous = globalThis.fetch
  globalThis.fetch = stub
  try {
    return await action()
  } finally {
    globalThis.fetch = previous
  }
}

test('chat stream parses metadata and deltas and sends the conversation ID', async () => {
  const observed = []
  const conversationIds = []
  const chunks = await withFetch(async (url, options) => {
    observed.push({ url, options })
    return responseFromPieces([
      'event: meta\ndata: {"conversation_id":"fixed-id","turn_id":"turn-id"}\n\n',
      'event: delta\ndata: {"text":"Hel',
      'lo "}\n\n',
      'event: delta\ndata: {"text":"there."}\n\n',
      'event: done\ndata: {}\n\n',
    ])
  }, async () => {
    const result = []
    for await (const chunk of streamChatReply({
      question: 'Hello?', conversationId: 'prior-id',
      onMeta: (id) => conversationIds.push(id),
    })) result.push(chunk)
    return result
  })
  assert.deepEqual(chunks, ['Hello ', 'there.'])
  assert.deepEqual(conversationIds, ['fixed-id'])
  assert.equal(observed[0].url, '/api/chat/stream')
  assert.equal(observed[0].options.method, 'POST')
  assert.deepEqual(JSON.parse(observed[0].options.body), {
    question: 'Hello?', conversation_id: 'prior-id',
  })
  assert.equal('GEMINI_API_KEY' in observed[0].options, false)
})

test('chat stream reports provider error after a partial answer', async () => {
  await withFetch(async () => responseFromPieces([
    'event: meta\ndata: {"conversation_id":"fixed-id"}\n\n',
    'event: delta\ndata: {"text":"Partial"}\n\n',
    'event: error\ndata: {"message":"Gemini timed out. Try again.","code":"retryable"}\n\n',
  ]), async () => {
    const stream = streamChatReply({ question: 'Hello' })
    assert.equal((await stream.next()).value, 'Partial')
    await assert.rejects(stream.next(), /Gemini timed out/)
  })
})

test('missing context error identifies an editable question', async () => {
  await withFetch(async () => responseFromPieces([
    'event: meta\ndata: {"conversation_id":"fixed-id"}\n\n',
    'event: error\ndata: {"message":"Include a ZIP.","code":"missing_context"}\n\n',
  ]), async () => {
    const stream = streamChatReply({ question: 'Which hotels?' })
    await assert.rejects(stream.next(), (error) =>
      error.message === 'Include a ZIP.' && error.code === 'missing_context')
  })
})

test('chat stream treats a missing completion event as interrupted', async () => {
  await withFetch(async () => responseFromPieces([
    'event: meta\ndata: {"conversation_id":"fixed-id"}\n\n',
    'event: delta\ndata: {"text":"Partial"}\n\n',
  ]), async () => {
    const stream = streamChatReply({ question: 'Hello' })
    assert.equal((await stream.next()).value, 'Partial')
    await assert.rejects(stream.next(), /interrupted/)
  })
})

test('saved chat history loads by ID and handles a missing conversation', async () => {
  const observed = []
  const history = await withFetch(async (url) => {
    observed.push(url)
    return new Response(JSON.stringify({ conversation_id: 'fixed-id', messages: [] }), {
      status: 200,
    })
  }, () => getChatHistory('fixed-id'))
  assert.deepEqual(history, { conversation_id: 'fixed-id', messages: [] })
  assert.equal(observed[0], '/api/chat/history?conversation_id=fixed-id')
  assert.equal(await withFetch(async () => new Response('', { status: 404 }),
    () => getChatHistory('missing')), null)
})
