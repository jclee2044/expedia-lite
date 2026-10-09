// Preserve actual failure text; clarification requests are not interrupted replies.
export function applyReplyFailure(reply, error) {
  const clarification = error.code === 'missing_context'
  reply.state = clarification ? 'clarification' : 'error'
  if (clarification) reply.content = error.message
  return clarification ? 'More information is needed.' : 'Hotel reply failed.'
}
