const BACKEND_URL = "http://127.0.0.1:5000";
let currentNoteId = null;

async function loadNotes() {
  try {
    const res = await fetch(`${BACKEND_URL}/api/notes`);
    const notes = await res.json();
    const container = document.getElementById('notes-list');
    container.innerHTML = '';

    if (notes.length === 0) {
      container.innerHTML = `<p class="text-gray-400 p-6 text-center">No notes yet. Upload your first handwritten note!</p>`;
      return;
    }

    notes.forEach(note => {
      const div = document.createElement('div');
      div.className = `p-4 mb-3 mx-2 rounded-2xl cursor-pointer hover:bg-gray-800 transition ${currentNoteId === note.id ? 'bg-gray-800' : 'bg-gray-900'}`;
      div.innerHTML = `
        <div class="font-medium text-white">${note.title}</div>
        <div class="text-xs text-gray-400 mt-1">${new Date(note.created_at).toLocaleDateString()}</div>
      `;
      div.onclick = () => loadNote(note.id);
      container.appendChild(div);
    });
  } catch (err) {
    console.error(err);
  }
}

async function loadNote(id) {
  currentNoteId = id;
  const res = await fetch(`${BACKEND_URL}/api/notes/${id}`);
  const note = await res.json();

  document.getElementById('hero').classList.add('hidden');
  document.getElementById('note-view').classList.remove('hidden');

  document.getElementById('note-title').textContent = note.title;
  document.getElementById('note-date').textContent = new Date(note.created_at).toLocaleString();
  document.getElementById('note-image').src = `${BACKEND_URL}${note.image_path}`;
  document.getElementById('extracted-text').textContent = note.extracted_text;

  renderChat(note.chat_history || []);
}

function renderChat(history) {
  const container = document.getElementById('chat-messages');
  container.innerHTML = '';
  history.forEach(msg => {
    const isUser = msg.role === 'user';
    const div = document.createElement('div');
    div.className = `flex ${isUser ? 'justify-end' : 'justify-start'}`;
    div.innerHTML = `
      <div class="${isUser ? 'bg-blue-600' : 'bg-gray-800'} max-w-[85%] rounded-3xl px-5 py-3">
        ${msg.content}
      </div>
    `;
    container.appendChild(div);
  });
  container.scrollTop = container.scrollHeight;
}

async function sendChatMessage() {
  const input = document.getElementById('chat-input');
  const message = input.value.trim();
  if (!message || !currentNoteId) return;

  const container = document.getElementById('chat-messages');
  container.innerHTML += `<div class="flex justify-end"><div class="bg-blue-600 max-w-[85%] rounded-3xl px-5 py-3">${message}</div></div>`;
  container.scrollTop = container.scrollHeight;

  input.value = '';

  try {
    const res = await fetch(`${BACKEND_URL}/api/chat/${currentNoteId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    });
    const data = await res.json();

    container.innerHTML += `<div class="flex justify-start"><div class="bg-gray-800 max-w-[85%] rounded-3xl px-5 py-3">${data.reply}</div></div>`;
    container.scrollTop = container.scrollHeight;
  } catch (err) {
    console.error(err);
  }
}

function showUploadModal() {
  document.getElementById('upload-modal').classList.remove('hidden');
}

function hideUploadModal() {
  document.getElementById('upload-modal').classList.add('hidden');
}

let selectedFile = null;

function handleFileSelect(e) {
  selectedFile = e.target.files[0];
}

async function uploadFile() {
  if (!selectedFile) {
    alert("Please select an image file");
    return;
  }

  const formData = new FormData();
  formData.append('file', selectedFile);

  const btn = document.getElementById('upload-btn');
  const originalText = btn.textContent;
  btn.textContent = "Digitizing with Grok...";
  btn.disabled = true;

  try {
    const res = await fetch(`${BACKEND_URL}/api/upload`, {
      method: 'POST',
      body: formData
    });
    const note = await res.json();

    hideUploadModal();
    await loadNotes();
    loadNote(note.id);
  } catch (err) {
    alert("Upload failed. Make sure backend is running.");
    console.error(err);
  } finally {
    btn.textContent = originalText;
    btn.disabled = false;
  }
}

function backToList() {
  currentNoteId = null;
  document.getElementById('note-view').classList.add('hidden');
  document.getElementById('hero').classList.remove('hidden');
  loadNotes();
}

// Initialize
window.onload = () => {
  loadNotes();
  console.log("✅ StudyBuddy AI frontend loaded");
};