export async function api(method, args = {}, verb = 'POST') {
  const url = '/api/method/reckon_crm.api.' + method
  const response = await fetch(verb === 'GET' ? `${url}?${new URLSearchParams(args)}` : url, {
    method: verb, credentials: 'same-origin',
    headers: verb === 'GET' ? {} : { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': window.csrf_token || '' },
    ...(verb === 'GET' ? {} : { body: JSON.stringify(args) }),
  })
  const body = await response.json().catch(() => ({}))
  if (!response.ok || body.exc || !body.message?.success) {
    let message = 'Request failed. Please refresh and try again.'
    try {
      const messages = JSON.parse(body._server_messages || '[]')
      if (messages.length) message = JSON.parse(messages[0]).message
      else if (body.exception) message = body.exception.split(':').slice(1).join(':').trim()
    } catch { /* Keep the safe fallback. */ }
    throw new Error(String(message).replace(/<[^>]*>/g, ''))
  }
  return body.message.data
}

export async function uploadVisitFile(visit, fieldname, file) {
  const form = new FormData()
  form.append('file', file)
  form.append('is_private', '1')
  form.append('doctype', 'CRM Field Visit')
  form.append('docname', visit)
  const response = await fetch('/api/method/upload_file', {
    method: 'POST', credentials: 'same-origin', body: form,
    headers: { 'X-Frappe-CSRF-Token': window.csrf_token || '' },
  })
  const body = await response.json()
  if (!response.ok || !body.message?.file_url) throw new Error('File upload failed. Check your permissions and file size.')
  return api('visits.attach_file', { name: visit, fieldname, file_url: body.message.file_url })
}
