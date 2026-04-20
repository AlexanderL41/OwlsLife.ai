// Frontend logic: send question to /chat and render results
const askBtn = document.getElementById('ask')
const questionEl = document.getElementById('question')
const questionCountEl = document.getElementById('question-count')
const feedbackPanelEl = document.getElementById('feedback-panel')
const feedbackToggleEl = document.getElementById('feedback-toggle')
const feedbackContentEl = document.getElementById('feedback-content')
const feedbackTitleEl = document.getElementById('feedback-title')
const feedbackTextEl = document.getElementById('feedback-text')
const sendFeedbackBtnEl = document.getElementById('send-feedback')
const feedbackStatusEl = document.getElementById('feedback-status')
const MAX_QUESTION_CHARS = 1200
const PRIMARY_API_BASE = (window.location.port === '5000') ? '' : 'http://127.0.0.1:5000'
const FALLBACK_API_BASE = (window.location.port === '5000') ? '' : `http://${window.location.hostname}:5000`

let lastQuestion = ''
let lastErrorMessage = ''

questionEl.setAttribute('maxlength', String(MAX_QUESTION_CHARS))

askBtn.addEventListener('click', sendQuestion)
if(feedbackToggleEl){
  feedbackToggleEl.addEventListener('click', toggleFeedbackPanel)
}
if(sendFeedbackBtnEl){
  sendFeedbackBtnEl.addEventListener('click', submitFeedback)
}

questionEl.addEventListener('keydown', (e)=>{
  // Enter submits. Shift+Enter inserts a newline.
  // Ctrl/Cmd+Enter also submits.
  if(e.key==='Enter' && (e.ctrlKey || e.metaKey)){
    e.preventDefault()
    sendQuestion()
    return
  }

  if(e.key==='Enter' && !e.shiftKey){
    e.preventDefault()
    sendQuestion()
  }
})

questionEl.addEventListener('input', autoResizeQuestion)
questionEl.addEventListener('input', updateQuestionCounter)

// Ensure the textarea matches its content height immediately on page load.
autoResizeQuestion()
updateQuestionCounter()

function autoResizeQuestion(){
  questionEl.style.height = 'auto'
  questionEl.style.height = `${questionEl.scrollHeight}px`
}

function updateQuestionCounter(){
  if(!questionCountEl) return
  questionCountEl.innerText = `${questionEl.value.length} / ${MAX_QUESTION_CHARS}`
}

async function sendQuestion(){
  const qEl = questionEl
  const question = qEl.value.trim()
  lastQuestion = question
  const results = document.getElementById('results')
  if(!question) return
  hideFeedbackPanel()
  results.innerText = 'Searching...'
  try{
    let res
    let endpoint = '/chat'
    try {
      res = await fetch(`${PRIMARY_API_BASE}${endpoint}`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ question })
      })

      // If Node backend is running, /chat may return 404; try /query.
      if(res.status === 404){
        endpoint = '/query'
        res = await fetch(`${PRIMARY_API_BASE}${endpoint}`, {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ question })
        })
      }
    } catch (primaryErr) {
      // Retry once with hostname-based HTTP URL.
      if(FALLBACK_API_BASE && FALLBACK_API_BASE !== PRIMARY_API_BASE){
        res = await fetch(`${FALLBACK_API_BASE}${endpoint}`, {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ question })
        })

        if(res.status === 404){
          endpoint = '/query'
          res = await fetch(`${FALLBACK_API_BASE}${endpoint}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ question })
          })
        }
      } else {
        throw primaryErr
      }
    }

    if(!res){
      throw new Error('No response from backend')
    }

    
    if(!res.ok){
      const t = await res.text()
      results.innerText = 'Error: ' + t
      lastErrorMessage = `HTTP ${res.status}: ${t}`
      showFeedbackPanel()
      return
    }
    const data = await res.json()
    // render
    const answer = data.answer || ''
    let html = ''
    html += `<h3>Answer</h3><div class="answer">${escapeHtml(answer).replace(/\n/g,'<br>')}</div>`
    results.innerHTML = html
  }catch(err){
    lastErrorMessage = String(err.message || err)
    results.innerText = `Network error: cannot reach backend at http://127.0.0.1:5000. Make sure backend app.py is running on port 5000.\n\nDetails: ${lastErrorMessage}`
    showFeedbackPanel()
  }
}

async function submitFeedback(){
  if(!feedbackTextEl || !feedbackStatusEl) return

  const feedback = feedbackTextEl.value.trim()
  if(!feedback){
    feedbackStatusEl.innerText = 'Please enter feedback before sending.'
    return
  }

  feedbackStatusEl.innerText = 'Sending feedback...'

  try{
    const payload = {
      question: lastQuestion,
      error: lastErrorMessage,
      feedback,
      client: 'web'
    }

    let res
    try{
      res = await fetch(`${PRIMARY_API_BASE}/feedback`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
      })
    }catch(primaryErr){
      if(FALLBACK_API_BASE && FALLBACK_API_BASE !== PRIMARY_API_BASE){
        res = await fetch(`${FALLBACK_API_BASE}/feedback`, {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(payload)
        })
      }else{
        throw primaryErr
      }
    }

    if(!res || !res.ok){
      const errText = res ? await res.text() : 'No response from backend'
      feedbackStatusEl.innerText = `Could not submit feedback: ${errText}`
      return
    }

    feedbackStatusEl.innerText = 'Thanks — feedback sent.'
    feedbackTextEl.value = ''
  }catch(err){
    feedbackStatusEl.innerText = `Could not submit feedback: ${err.message || err}`
  }
}

function showFeedbackPanel(){
  if(!feedbackPanelEl) return
  if(feedbackToggleEl){
    feedbackToggleEl.innerText = 'Give Feedback (issue detected)'
  }
  if(feedbackTitleEl) feedbackTitleEl.innerText = 'Something went wrong — optional feedback'
}

function hideFeedbackPanel(){
  if(!feedbackPanelEl) return
  if(feedbackToggleEl){
    feedbackToggleEl.innerText = 'Give Feedback'
  }
  if(feedbackTitleEl) feedbackTitleEl.innerText = 'Optional feedback'
  if(feedbackStatusEl) feedbackStatusEl.innerText = ''
}

function toggleFeedbackPanel(){
  if(!feedbackPanelEl || !feedbackContentEl || !feedbackToggleEl) return

  const isExpanded = feedbackPanelEl.classList.contains('expanded')
  if(isExpanded){
    feedbackPanelEl.classList.remove('expanded')
    feedbackPanelEl.classList.add('minimized')
    feedbackContentEl.classList.add('hidden')
    feedbackToggleEl.setAttribute('aria-expanded', 'false')
    feedbackToggleEl.innerText = 'Give Feedback'
  }else{
    feedbackPanelEl.classList.remove('minimized')
    feedbackPanelEl.classList.add('expanded')
    feedbackContentEl.classList.remove('hidden')
    feedbackToggleEl.setAttribute('aria-expanded', 'true')
    feedbackToggleEl.innerText = 'Minimize Feedback'
  }
}

function escapeHtml(text){
  if(!text) return ''
  return text.replace(/[&<>\"']/g, function(m){ return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[m] })
}
