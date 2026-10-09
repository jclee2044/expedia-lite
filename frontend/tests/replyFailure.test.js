import assert from 'node:assert/strict'
import test from 'node:test'
import { applyReplyFailure } from '../src/chat/replyFailure.js'

test('missing-date validation becomes a readable clarification for both new and restored replies', () => {
  for (const reply of [{ content: '', state: 'streaming' }, { content: '' }]) {
    const message = 'Which dated night would you like to check?'
    assert.equal(applyReplyFailure(reply, { code: 'missing_context', message }), 'More information is needed.')
    assert.equal(reply.state, 'clarification')
    assert.equal(reply.content, message)
  }
})

test('provider and interrupted-stream errors preserve received text and remain failures', () => {
  for (const message of ['Gemini timed out. Try again.', 'The chat reply was interrupted. Try again.']) {
    const reply = { content: 'Previously received text', state: 'streaming' }
    assert.equal(applyReplyFailure(reply, { code: 'retryable', message }), 'Hotel reply failed.')
    assert.equal(reply.state, 'error')
    assert.equal(reply.content, 'Previously received text')
  }
})
