const $ = s => document.querySelector(s);

const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
}[c]));

function showToast(msg) {
    const x = $('#toast');
    x.textContent = msg;
    x.classList.add('show');
    setTimeout(() => x.classList.remove('show'), 2500);
}

async function loadAccount() {
    const r = await fetch('/api/auth/me', { credentials: 'same-origin' });
    if (r.status === 401) {
        location.replace('/');
        return false;
    }
    const d = await r.json();
    $('#side-name').textContent = d.account.name;
    $('#avatar').textContent = d.account.name[0].toUpperCase();
    $('#top-avatar').textContent = d.account.name[0].toUpperCase();
    return true;
}

document.querySelectorAll('[data-logout]').forEach(b =>
    b.addEventListener('click', async () => {
        await fetch('/api/auth/logout', { method: 'POST', credentials: 'same-origin' });
        location.href = '/';
    })
);

async function loadGaps() {
    if (!await loadAccount()) return;
    try {
        const r = await fetch('/api/student/learning-gaps', { credentials: 'same-origin' });
        const d = await r.json();
        if (!r.ok) throw Error(d.detail || 'Could not load learning gaps');

        $('#gap-reviewed').textContent = d.topics.length;
        $('#gap-attention').textContent = d.summary.identified;
        $('#gap-critical').textContent = d.summary.critical;
        $('#gap-strong').textContent = d.summary.strong;

        const root = $('#gap-topics');
        if (!d.topics.length) {
            root.innerHTML = `
        <div class="empty-course">
          <span>◉</span>
          <h3>Your topic picture will appear here</h3>
          <p>Take a practice quiz or assessment. Your learning gaps will be calculated from your actual answers.</p>
          <a class="button primary" href="/student/quizzes">Start a practice quiz</a>
        </div>
      `;
            return;
        }

        root.innerHTML = d.topics.map(t => `
      <article class="gap-topic-card">
        <div class="gap-card-head">
          <div>
            <span class="severity severity-${t.severity.replaceAll(' ', '-')}">${esc(t.severity)}</span>
            <h3>${esc(t.topic_name)}</h3>
          </div>
          <strong>${t.accuracy}%</strong>
        </div>
        <div class="bar gap-bar">
          <i class="${t.severity === 'strong' ? 'strong-fill' : ''}" style="width:${t.accuracy}%"></i>
        </div>
        <div class="gap-statline">
          <span>${t.attempts} answers reviewed</span>
          <span>${t.incorrect} incorrect</span>
        </div>
        ${t.mistakes.length ? `
          <div class="mistake-list">
            <h4>What to review</h4>
            ${t.mistakes.map(m => `
              <div class="mistake-item">
                <span class="mistake-mark">↳</span>
                <div>
                  <b>${esc(m.pattern || 'Review this idea')}</b>
                  <p>${esc(m.pattern_description || `You answered “${m.answer}”. The correct answer is ${m.correct_answer}.`)}</p>
                  <small>Question: ${esc(m.question_text)}</small>
                </div>
              </div>
            `).join('')}
          </div>
        ` : `
          <div class="topic-strength-note">No incorrect answers recorded for this topic. Keep practicing to build confidence.</div>
        `}
        <a class="gap-practice-link" href="/student/quizzes">Practice ${esc(t.topic_name)} <span>→</span></a>
      </article>
    `).join('');
    } catch (e) {
        showToast(e.message);
    }
}

async function loadPlan() {
    if (!await loadAccount()) return;
    try {
        const r = await fetch('/api/student/learning-plan', { credentials: 'same-origin' });
        const d = await r.json();
        if (!r.ok) throw Error(d.detail || 'Could not load your plan');

        const pct = d.lesson_count ? Math.round(d.completed / d.lesson_count * 100) : 0;
        $('#plan-completed').textContent = d.completed;
        $('#plan-total').textContent = d.lesson_count;
        $('#plan-percent').textContent = `${pct}%`;
        $('#plan-bar-fill').style.width = `${pct}%`;

        const root = $('#plan-modules');
        if (!d.modules.length) {
            root.innerHTML = `
        <div class="empty-course">
          <span>✳</span>
          <h3>Your learning plan will grow from your results</h3>
          <p>Complete a quiz or assessment to identify topics for your personal plan. Strong topics won’t be added as gaps.</p>
          <a class="button primary" href="/student/quizzes">Take a practice quiz</a>
        </div>
      `;
            return;
        }

        root.innerHTML = d.modules.map((m, i) => `
      <section class="plan-module">
        <div class="plan-module-heading">
          <span class="module-number">${String(i + 1).padStart(2, '0')}</span>
          <div>
            <span class="severity severity-${m.severity.replaceAll(' ', '-')}">${esc(m.severity)} · ${m.accuracy}%</span>
            <h2>${esc(m.topic_name)}</h2>
          </div>
          <span class="module-count">${m.lessons.filter(l => l.completed).length}/${m.lessons.length} lessons</span>
        </div>
        <div class="lesson-list">
          ${m.lessons.map((l, j) => `
            <article class="lesson-card ${l.completed ? 'lesson-done' : ''}">
              <span class="lesson-step">${l.completed ? '✓' : String(j + 1).padStart(2, '0')}</span>
              <div class="lesson-card-copy">
                <h3>${esc(l.title)}</h3>
                <p>${esc(l.objective)}</p>
              </div>
              <button class="lesson-open" 
                data-id="${l.lesson_id}" 
                data-topic="${esc(m.topic_name)}" 
                data-title="${esc(l.title)}" 
                data-objective="${esc(l.objective)}" 
                data-body="${esc(l.lesson_text)}" 
                data-completed="${l.completed}">
                ${l.completed ? 'Review' : 'Start lesson'} <span>→</span>
              </button>
            </article>
          `).join('')}
        </div>
      </section>
    `).join('');

        root.querySelectorAll('.lesson-open').forEach(b => b.addEventListener('click', () => openLesson(b)));
    } catch (e) {
        showToast(e.message);
    }
}

let currentLessonId = null;
let currentLessonCompleted = false;

function openLesson(button) {
    currentLessonId = Number(button.dataset.id);
    currentLessonCompleted = button.dataset.completed === 'true';
    $('#lesson-topic').textContent = button.dataset.topic.toUpperCase();
    $('#lesson-title').textContent = button.dataset.title;
    $('#lesson-objective').textContent = button.dataset.objective;
    $('#lesson-body').textContent = button.dataset.body;
    $('#lesson-complete').classList.toggle('hidden', currentLessonCompleted);
    $('#lesson-dialog').showModal();
}

if (location.pathname.endsWith('learning-gaps')) {
    loadGaps();
} else if (location.pathname.endsWith('learning-plan')) {
    loadPlan();
}

$('#lesson-close')?.addEventListener('click', () => $('#lesson-dialog').close());

$('#lesson-complete')?.addEventListener('click', async () => {
    const b = $('#lesson-complete');
    b.disabled = true;
    try {
        const r = await fetch(`/api/student/learning-plan/lessons/${currentLessonId}/complete`, {
            method: 'POST',
            credentials: 'same-origin'
        });
        const d = await r.json();
        if (!r.ok) throw Error(d.detail || 'Could not save lesson progress');

        $('#lesson-dialog').close();
        showToast(d.message);
        await loadPlan();
    } catch (e) {
        showToast(e.message);
    } finally {
        b.disabled = false;
    }
});