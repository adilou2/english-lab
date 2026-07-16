// API Base URL
const API_BASE = '/api';

console.log('main.js loaded successfully');

// ── DATA FUNCTIONS (Now using Flask backend instead of localStorage) ──
async function getData(endpoint) {
  try {
    console.log(`Fetching ${API_BASE}${endpoint}`);
    const res = await fetch(`${API_BASE}${endpoint}`);
    const data = await res.json();
    console.log(`Response from ${endpoint}:`, data);
    return data;
  } catch (e) {
    console.error('Error fetching data:', e);
    return null;
  }
}

async function postData(endpoint, data) {
  try {
    console.log(`Posting to ${API_BASE}${endpoint}`, data);
    const res = await fetch(`${API_BASE}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    const responseData = await res.json();
    console.log(`Response from ${endpoint}:`, responseData);
    return responseData;
  } catch (e) {
    console.error('Error posting data:', e);
    return null;
  }
}

async function deleteData(endpoint, data) {
  try {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return await res.json();
  } catch (e) {
    console.error('Error deleting data:', e);
    return null;
  }
}

// ── NAVIGATION ──
function switchPanel(id) {
  // Navigation is now handled by Flask routes, but we keep this for dynamic updates
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.querySelectorAll('.bnav-item').forEach(n => n.classList.remove('active'));
  document.getElementById(id + '-panel').classList.add('active');
  document.getElementById('nav-' + id).classList.add('active');
  document.getElementById('bnav-' + id).classList.add('active');
  if (id === 'flash') renderFlashcard();
  if (id === 'vocab') renderSavedWords();
  updateBadge();
}

async function updateBadge() {
  const cards = await getData('/flashcards');
  const b = document.getElementById('flash-badge');
  if (cards && cards.length > 0) {
    b.textContent = cards.length;
    b.style.display = 'inline';
  } else {
    b.style.display = 'none';
  }
}

// Initialize badge on page load
document.addEventListener('DOMContentLoaded', () => {
  updateBadge();
  if (document.getElementById('vocab-panel')) {
    renderSavedWords();
  }
  if (document.getElementById('flash-panel')) {
    restoreFlashcardState();
    renderFlashcard();
  }
  if (document.getElementById('chat-messages')) {
    loadChatHistory();
  }
});

// ── CONVERSATION ──
let recognition = null;
let isRecording = false;
const chatHistory = [];

async function loadChatHistory() {
  try {
    const messages = await getData('/chat/history');
    const wrap = document.getElementById('chat-messages');
    if (messages && messages.length && wrap) {
      wrap.innerHTML = '';
      chatHistory.length = 0;
      messages.forEach(m => {
        chatHistory.push({ role: m.role, content: m.content });
        appendMsg(m.content, m.role);
      });
    }
  } catch (e) {
    console.log('Failed to load chat history:', e);
  }
}

(function initSpeech() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) return;
  recognition = new SR();
  recognition.lang = 'en-US';
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.onresult = e => {
    document.getElementById('chat-input').value = e.results[0][0].transcript;
    stopRecording();
    sendMessage();
  };
  recognition.onend = stopRecording;
  recognition.onerror = stopRecording;
})();

function toggleMic() {
  if (!recognition) {
    alert('Speech recognition not supported in this browser.');
    return;
  }
  isRecording ? stopRecording() : startRecording();
}

function startRecording() {
  isRecording = true;
  recognition.start();
  const btn = document.getElementById('mic-btn');
  btn.classList.add('recording');
  btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#dc2626" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="1" y1="1" x2="23" y2="23"/><path d="M9 9v3a3 3 0 0 0 5.12 2.12M15 9.34V4a3 3 0 0 0-5.94-.6"/><path d="M17 16.95A7 7 0 0 1 5 12v-2m14 0v2a7 7 0 0 1-.11 1.23"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>`;
}

function stopRecording() {
  isRecording = false;
  try { recognition && recognition.stop(); } catch (e) {}
  const btn = document.getElementById('mic-btn');
  btn.classList.remove('recording');
  btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>`;
}

function handleChatKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

async function sendMessage() {
  const inp = document.getElementById('chat-input');
  const text = inp.value.trim();
  if (!text) return;
  inp.value = '';
  appendMsg(text, 'user');
  chatHistory.push({ role: 'user', content: text });
  document.getElementById('ai-typing').style.display = 'block';
  
  try {
    const response = await postData('/chat', { message: text, history: chatHistory });
    document.getElementById('ai-typing').style.display = 'none';
    
    if (response) {
      chatHistory.push({ role: 'assistant', content: response.reply });
      appendMsg(response.reply, 'ai', response.errors);
      speak(response.reply);
      
      if (response.errors && response.errors.length) {
        await saveErrorsToFlashcards(response.errors);
        updateBadge();
      }
    }
  } catch (err) {
    document.getElementById('ai-typing').style.display = 'none';
    appendMsg('Sorry, something went wrong. Please try again.', 'ai');
  }
}

function appendMsg(text, role, errors) {
  const wrap = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = 'msg ' + role;
  div.textContent = text;
  if (errors && errors.length) {
    const note = document.createElement('div');
    note.className = 'error-note';
    note.textContent = errors.length + ' grammar note' + (errors.length > 1 ? 's' : '') + ' saved to flashcards.';
    div.appendChild(note);
  }
  wrap.appendChild(div);
  wrap.scrollTop = wrap.scrollHeight;
}

function speak(text) {
  const synth = window.speechSynthesis;
  if (!synth) return;
  synth.cancel();
  const utt = new SpeechSynthesisUtterance(text);
  utt.lang = 'en-US';
  utt.rate = 0.95;
  utt.pitch = 1;
  const v = synth.getVoices().find(v => v.lang.startsWith('en') && v.localService);
  if (v) utt.voice = v;
  const st = document.getElementById('tts-status');
  st.textContent = 'Speaking…';
  utt.onend = () => st.textContent = '';
  synth.speak(utt);
}

async function saveErrorsToFlashcards(errors) {
  for (const e of errors) {
    await postData('/flashcards', {
      id: Date.now() + Math.random(),
      type: 'grammar',
      front: e.original,
      back: e.correction,
      explanation: e.explanation,
      source: 'conversation'
    });
  }
}

// ── GRAMMAR ──
async function checkGrammar() {
  const text = document.getElementById('gram-text').value.trim();
  if (!text) {
    alert('Please enter some text first.');
    return;
  }
  const btn = document.getElementById('gram-btn');
  const loading = document.getElementById('gram-loading');
  btn.disabled = true;
  loading.style.display = 'inline';
  document.getElementById('gram-result').style.display = 'none';
  document.getElementById('gram-errors').innerHTML = '';
  
  try {
    const response = await postData('/grammar', { text: text });
    const result = document.getElementById('gram-result');
    result.style.display = 'block';
    
    if (response) {
      result.innerHTML = response.annotated.replace(/<mark data-i='(\d+)'>(.*?)<\/mark>/g, (_, i, w) => {
        const e = response.errors[+i];
        return `<span class="highlight" data-tip="${e ? e.correction : ''}">${w}</span>`;
      });
      
      const errWrap = document.getElementById('gram-errors');
      if (response.errors.length === 0) {
        errWrap.innerHTML = '<div class="error-card" style="color:#16a34a">No grammar errors found. Great writing!</div>';
      } else {
        response.errors.forEach(e => {
          errWrap.innerHTML += `<div class="error-card"><div class="orig">${e.original}</div><div class="fixed">${e.correction}</div><div class="why">${e.explanation}</div></div>`;
        });
      }
    }
  } catch (e) {
    document.getElementById('gram-errors').innerHTML = '<div class="error-card" style="color:#dc2626">Error connecting. Please try again.</div>';
  }
  
  btn.disabled = false;
  loading.style.display = 'none';
}

// ── VOCABULARY ──
let currentVocabWord = null;

async function lookupWord() {
  const word = document.getElementById('word-input').value.trim();
  if (!word) return;
  const btn = document.getElementById('vocab-btn');
  btn.disabled = true;
  btn.textContent = 'Looking up…';
  document.getElementById('vocab-result').style.display = 'none';
  
  try {
    const response = await postData('/vocabulary', { word: word });
    currentVocabWord = response;
    const r = document.getElementById('vocab-result');
    r.style.display = 'block';
    r.className = 'vocab-result';
    
    if (response) {
      r.innerHTML = `<div class="vocab-word">${response.word}</div>
<div class="vocab-pos">${response.pos}</div>
<div class="vocab-def">${response.definition}</div>
<div class="vocab-examples">${response.examples.map(ex => `<div class="vocab-ex">${ex}</div>`).join('')}</div>
<button class="save-word-btn" id="save-btn" onclick="saveWord()">
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>
  Save to library
</button>`;
    }
  } catch (e) {
    const r = document.getElementById('vocab-result');
    r.style.display = 'block';
    r.innerHTML = '<div style="color:#dc2626;font-size:14px">Error looking up word. Try again.</div>';
  }
  
  btn.disabled = false;
  btn.textContent = 'Look up';
}

async function saveWord() {
  if (!currentVocabWord) return;
  
  // Save vocabulary word
  await postData('/vocabulary', {
    word: currentVocabWord.word,
    pos: currentVocabWord.pos,
    definition: currentVocabWord.definition,
    examples: currentVocabWord.examples
  });
  
  // Save as flashcard
  await postData('/flashcards', {
    id: Date.now() + Math.random(),
    type: 'vocab',
    front: 'Define: ' + currentVocabWord.word,
    back: currentVocabWord.definition,
    explanation: currentVocabWord.examples.join(' | '),
    source: 'vocabulary'
  });
  
  updateBadge();
  const btn = document.getElementById('save-btn');
  btn.className = 'save-word-btn saved';
  btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg> Saved!`;
  renderSavedWords();
}

async function renderSavedWords() {
  const words = await getData('/vocabulary');
  const list = document.getElementById('saved-words-list');
  const label = document.getElementById('saved-words-label');
  list.innerHTML = '';
  
  if (!words || !words.length) {
    label.style.display = 'none';
    return;
  }
  
  label.style.display = 'block';
  words.forEach((w, i) => {
    const item = document.createElement('div');
    item.className = 'saved-word-item';
    item.innerHTML = `<div><strong>${w.word}</strong> <span style="color:#aaa;font-size:12px">(${w.pos})</span><br><span>${w.definition.substring(0, 70)}${w.definition.length > 70 ? '…' : ''}</span></div>
<button class="del-btn" onclick="deleteWord(${w.id})"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>`;
    list.appendChild(item);
  });
}

async function deleteWord(id) {
  await deleteData('/vocabulary', { id: id });
  renderSavedWords();
}

// ── FLASHCARDS ──
let cards = [];
let cardIdx = 0;
let cardFlipped = false;
let dailyDone = 0;

// Preserve flashcard state when navigating
function preserveFlashcardState() {
  if (!document.getElementById('flash-panel')) return;
  sessionStorage.setItem('flashcardIdx', cardIdx);
  sessionStorage.setItem('flashcardFlipped', cardFlipped);
}

function restoreFlashcardState() {
  const idx = sessionStorage.getItem('flashcardIdx');
  const flipped = sessionStorage.getItem('flashcardFlipped');
  if (idx !== null) cardIdx = parseInt(idx, 10) || 0;
  if (flipped !== null) cardFlipped = flipped === 'true';
}

window.addEventListener('beforeunload', preserveFlashcardState);

async function renderFlashcard() {
  cards = await getData('/flashcards') || [];
  const area = document.getElementById('card-area');
  const grade = document.getElementById('grade-btns');
  const counter = document.getElementById('card-counter');
  
  // Get progress
  const progress = await getData('/progress');
  if (progress) {
    dailyDone = progress.daily_done;
  }
  
  updateProgress();
  
  if (!cards || !cards.length) {
    area.innerHTML = `<div class="empty-flash"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#ccc" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/><path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/></svg><p>No flashcards yet. Have a conversation or save vocabulary words to fill your deck!</p></div>`;
    grade.style.display = 'none';
    counter.textContent = '';
    return;
  }
  
  if (cardIdx >= cards.length) cardIdx = 0;
  const card = cards[cardIdx];
  area.innerHTML = `<div class="card-stack"><div class="flashcard" id="flashcard" onclick="flipCard()">
    <div class="card-front"><p style="text-align:left;word-break:break-word">${card.front}</p><div class="card-hint">Tap to reveal</div></div>
    <div class="card-back"><div class="correction">${card.back}</div><p>${card.explanation || ''}</p></div>
  </div></div>`;
  const fc = document.getElementById('flashcard');
  if (fc) fc.classList.toggle('flipped', cardFlipped);
  grade.style.display = 'flex';
  counter.textContent = `Card ${cardIdx + 1} of ${cards.length}`;
}

function flipCard() {
  cardFlipped = !cardFlipped;
  const fc = document.getElementById('flashcard');
  if (fc) fc.classList.toggle('flipped', cardFlipped);
  preserveFlashcardState();
}

async function gradeCard(grade) {
  cards = await getData('/flashcards') || [];
  
  if (grade === 'easy') {
    // Delete card and increment progress
    if (cards[cardIdx]) {
      await deleteData('/flashcards', { id: cards[cardIdx].id });
    }
    dailyDone++;
    await postData('/progress', { daily_done: dailyDone });
    if (cardIdx >= cards.length) cardIdx = 0;
  } else if (grade === 'hard') {
    // Move to end of deck
    const c = cards.splice(cardIdx, 1)[0];
    cards.push(c);
    // Update backend
    await deleteData('/flashcards', { id: c.id });
    await postData('/flashcards', c);
    if (cardIdx >= cards.length) cardIdx = 0;
  } else {
    // Again - just move to next
    cardIdx = (cardIdx + 1) % Math.max(1, cards.length);
  }
  
  updateBadge();
  cardFlipped = false;
  preserveFlashcardState();
  renderFlashcard();
}

function updateProgress() {
  const pct = Math.min(100, Math.round(dailyDone / 10 * 100));
  document.getElementById('prog-fill').style.width = pct + '%';
  document.getElementById('prog-text').textContent = Math.min(dailyDone, 10) + ' / 10';
}

// ── EXPORT ──
function exportData() {
  window.location.href = '/api/export';
}
