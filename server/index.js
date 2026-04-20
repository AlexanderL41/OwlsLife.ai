const express = require('express')
const bodyParser = require('body-parser')
const fs = require('fs')
const path = require('path')
const cors = require('cors')
const fetch = global.fetch || require('node-fetch')

const DATA_PATH = path.join(__dirname, 'faudata.json')

function loadData(){
  try{
    const raw = fs.readFileSync(DATA_PATH, 'utf8')
    const json = JSON.parse(raw)
    return Array.isArray(json) ? json : []
  }catch(e){
    return []
  }
}

function saveData(data){
  fs.writeFileSync(DATA_PATH, JSON.stringify(data, null, 2), 'utf8')
}

function normalizeEntry(entry){
  const now = new Date().toISOString()
  return {
    id: String(entry.id || Date.now()),
    title: entry.title || '',
    text: entry.text || '',
    topic: entry.topic || 'general',
    sourceType: entry.sourceType || 'official',
    sourceName: entry.sourceName || 'FAU Assistant Dataset',
    sourceUrl: entry.sourceUrl || '',
    campus: entry.campus || 'Boca Raton',
    updatedAt: entry.updatedAt || now,
    tags: Array.isArray(entry.tags) ? entry.tags : []
  }
}

let data = loadData()

const app = express()
app.use(cors())
app.use(bodyParser.json({limit:'1mb'}))

// Serve Index/index.html as the homepage and keep static assets from project root.
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, '..', 'Index', 'index.html'))
})

// Serve static assets (css/js/Index/FauOwl.svg)
app.use(express.static(path.join(__dirname, '..')))

app.get('/health', (req,res)=>{
  res.json({ok:true, items: data.length})
})

// Simple keyword-based search + context retrieval
app.post('/query', (req,res)=>{
  const question = (req.body && req.body.question) ? String(req.body.question).trim() : ''
  if(!question) return res.status(400).send('question required')

  const qwords = question.toLowerCase().split(/\W+/).filter(Boolean)
  if(qwords.length===0) return res.json({answer:'', sources:[]})

  // Score documents by counting word hits in title + text
  const scored = data.map(d=>{
    const text = ((d.title||'') + ' ' + (d.text||'')).toLowerCase()
    let score = 0
    for(const w of qwords){
      // small boost for longer words
      const re = new RegExp('\\b'+w.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+'\\b','g')
      const m = text.match(re)
      if(m) score += m.length
    }
    return {doc:d, score}
  }).filter(x=>x.score>0)

  scored.sort((a,b)=>b.score - a.score)
  const top = scored.slice(0,5)

  if(top.length===0){
    return res.json({answer: "I couldn't find relevant information in the local FAU dataset.", sources:[]})
  }

  // Build a simple answer by summarizing top hits (concatenate short excerpts)
  const sources = top.map(item=>{
    const d = item.doc
    const txt = (d.text||'')
    // find first matched word index for excerpt
    let idx = -1
    for(const w of qwords){
      const i = txt.toLowerCase().indexOf(w)
      if(i>=0){ idx = i; break }
    }
    let excerpt = txt.slice(0, 220)
    if(idx>0){
      const start = Math.max(0, idx - 60)
      excerpt = txt.slice(start, Math.min(txt.length, start + 220))
      if(start>0) excerpt = '...' + excerpt
      if(start + 220 < txt.length) excerpt = excerpt + '...'
    }
    return { id: d.id || null, title: d.title || '', excerpt: excerpt }
  })

  // naive answer: list the top source titles and short passages
  let answer = ''
  answer += 'Found relevant info in ' + sources.length + ' local sources.\n\n'
  for(const s of sources.slice(0,3)){
    answer += `- ${s.title}: ${s.excerpt.replace(/\n+/g,' ')}\n\n`
  }

  res.json({answer, sources})
})

// Ingest endpoint: accept raw { title, text } or { url }
app.post('/ingest', async (req,res)=>{
  const body = req.body || {}
  try{
    if(body.url){
      // fetch public URL and store as a new doc
      const r = await fetch(body.url)
      if(!r.ok) return res.status(400).send('failed to fetch url')
      const text = await r.text()
      const entry = normalizeEntry({
        id: String(Date.now()),
        title: body.title || body.url,
        text,
        topic: body.topic,
        sourceType: body.sourceType || 'web',
        sourceName: body.sourceName || body.url,
        sourceUrl: body.url,
        campus: body.campus,
        tags: body.tags
      })
      data.push(entry)
      saveData(data)
      return res.json({ok:true, entry})
    }

    if(body.title && body.text){
      const entry = normalizeEntry({
        id: String(Date.now()),
        title: body.title,
        text: body.text,
        topic: body.topic,
        sourceType: body.sourceType,
        sourceName: body.sourceName,
        sourceUrl: body.sourceUrl,
        campus: body.campus,
        tags: body.tags
      })
      data.push(entry)
      saveData(data)
      return res.json({ok:true, entry})
    }

    return res.status(400).send('provide url or title+text')
  }catch(err){
    console.error('ingest error', err)
    return res.status(500).send('ingest failed')
  }
})

const port = process.env.PORT || 3000
app.listen(port, ()=>{
  console.log(`FAU assistant server listening on http://localhost:${port}`)
})
