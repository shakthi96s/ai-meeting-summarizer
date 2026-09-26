const form = document.querySelector('#upload-form');
const input = document.querySelector('#transcript');
const label = document.querySelector('#file-label');
const button = document.querySelector('#submit');
const error = document.querySelector('#error');
const results = document.querySelector('#results');
let latest;

input.addEventListener('change', () => { label.textContent = input.files[0]?.name || 'Upload a .txt transcript'; });
form.addEventListener('submit', async (event) => {
  event.preventDefault(); error.textContent = '';
  if (!input.files[0]) return;
  button.disabled = true; button.innerHTML = 'Summarizing…';
  try {
    const response = await fetch('/api/summarize', { method: 'POST', body: new FormData(form) });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Request failed');
    latest = data; render(data); results.hidden = false; results.scrollIntoView({ behavior: 'smooth' });
  } catch (err) { error.textContent = err.message; }
  finally { button.disabled = false; button.innerHTML = 'Summarize meeting <span>→</span>'; }
});
function render(data) {
  document.querySelector('#summary').textContent = data.summary;
  document.querySelector('#decisions').innerHTML = data.decisions.length ? data.decisions.map(x => `<li>${escapeHtml(x)}</li>`).join('') : '<li>No decisions recorded.</li>';
  document.querySelector('#topics').innerHTML = data.topics.map(x => `<span>${escapeHtml(x)}</span>`).join('') || '<small>No topics recorded.</small>';
  document.querySelector('#actions').innerHTML = data.action_items.length ? data.action_items.map(x => `<div class="action"><strong>${escapeHtml(x.task)}</strong><small>${escapeHtml(x.owner || 'Owner not assigned')} · ${escapeHtml(x.deadline || 'No deadline')}</small></div>`).join('') : '<p>No action items recorded.</p>';
}
function escapeHtml(value) { const div = document.createElement('div'); div.textContent = value; return div.innerHTML; }
document.querySelector('#download').addEventListener('click', () => { const blob = new Blob([JSON.stringify(latest, null, 2)], { type: 'application/json' }); const link = document.createElement('a'); link.href = URL.createObjectURL(blob); link.download = 'meeting-summary.json'; link.click(); URL.revokeObjectURL(link.href); });
