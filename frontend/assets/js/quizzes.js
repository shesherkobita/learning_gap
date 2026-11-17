const $ = s => document.querySelector(s);

const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
}[c]));

let bank = [];
let topics = [];
let activeQuestions = [];

function toast(msg) {
    const x = $('#toast');
    x.textContent = msg;
    x.classList.add('show');
    setTimeout(() => x.classList.remove('show'), 2600);
}

async function load() {
    const auth = await fetch('/api/auth/me', { credentials: 'same-origin' });
    if (auth.status === 401) {
        location.replace('/');
        return;
    }

    const profile = await auth.json();
    $('#side-name').textContent = profile.account.name;
    $('#avatar').textContent = profile.account.name[0].toUpperCase();
    $('#top-avatar').textContent = profile.account.name[0].toUpperCase();

    try {
        const r = await fetch('/api/student/quizzes/questions', { credentials: 'same-origin' });
        const d = await r.json();
        if (!r.ok) throw Error(d.detail || 'Could not load practice questions');

        bank = d.questions;
        topics = d.topics;

        $('#quiz-topic').innerHTML = '<option value="">All available topics</option>' +
            topics.map(t => `<option value="${t.topic_id}">${esc(t.topic_name)}${t.accuracy !== null ? ` · ${t.accuracy}%` : ''}</option>`).join('');

        if (!bank.length) {
            $('#quiz-start').innerHTML = '<h2>No practice questions are available yet</h2><p>Questions will appear when assessment material is added.</p>';
        }
    } catch (e) {
        toast(e.message);
    }
}

function beginQuiz() {
    const topicValue = $('#quiz-topic').value;
    let available = topicValue ? bank.filter(q => q.topic_id === Number(topicValue)) : bank.slice();

    available = available.sort(() => Math.random() - .5).slice(0, Math.min(5, available.length));

    if (!available.length) {
        toast('There are no questions for that topic yet.');
        return;
    }

    activeQuestions = available;
    $('#quiz-start').classList.add('hidden');
    $('#quiz-results').classList.add('hidden');
    $('#quiz-active').classList.remove('hidden');
    $('#quiz-count').textContent = `${activeQuestions.length} questions`;
    $('#quiz-heading').textContent = topicValue
        ? topics.find(t => t.topic_id === Number(topicValue))?.topic_name + ' practice'
        : 'Mixed-topic practice';

    $('#quiz-question-list').innerHTML = activeQuestions.map((q, i) => `
    <article class="quiz-question">
      <div class="question-number">QUESTION ${String(i + 1).padStart(2, '0')} <span>${esc(q.topic_name)}</span></div>
      <h3>${esc(q.question_text)}</h3>
      ${q.options.length ? `
        <div class="answer-choice-list">
          ${q.options.slice().sort(() => Math.random() - .5).map((option, j) => `
            <label class="answer-choice" for="choice-${q.question_id}-${j}">
              <input id="choice-${q.question_id}-${j}" type="radio" name="question-${q.question_id}" value="${esc(option)}">
              <span>${esc(option)}</span>
            </label>
          `).join('')}
        </div>
      ` : `
        <label for="answer-${q.question_id}">Your answer</label>
        <input id="answer-${q.question_id}" class="quiz-answer-input" autocomplete="off" placeholder="Write your answer">
      `}
    </article>
  `).join('');

    window.scrollTo({ top: 0, behavior: 'smooth' });
}

async function submitQuiz() {
    const answers = activeQuestions.map(q => {
        const selected = document.querySelector(`[name="question-${q.question_id}"]:checked`);
        const typed = $(`#answer-${q.question_id}`);
        return {
            question_id: q.question_id,
            answer: selected?.value || typed?.value.trim() || ''
        };
    });

    const missing = answers.find(a => !a.answer);
    if (missing) {
        toast('Answer each question before checking your quiz.');
        return;
    }

    const topicValue = $('#quiz-topic').value;
    const payload = {
        topic_id: topicValue ? Number(topicValue) : null,
        answers
    };

    const btn = $('#submit-quiz');
    btn.disabled = true;

    try {
        const r = await fetch('/api/student/quizzes/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify(payload)
        });
        const d = await r.json();
        if (!r.ok) throw Error(d.detail || 'Could not submit quiz');

        showResults(d);
    } catch (e) {
        toast(e.message);
    } finally {
        btn.disabled = false;
    }
}

function showResults(d) {
    $('#quiz-active').classList.add('hidden');
    $('#quiz-results').classList.remove('hidden');
    $('#result-score').textContent = `${Math.round(d.score)}%`;
    $('#result-heading').textContent = d.score >= 80 ? 'Great progress!' : d.score >= 50 ? 'Good effort—keep practicing.' : 'A useful first step.';
    $('#result-summary').textContent = `You answered ${d.correct_count} of ${d.question_count} correctly. Your saved results update your Learning Gaps and Learning Plan.`;

    $('#result-answers').innerHTML = d.answers.map(a => `
    <article class="result-answer ${a.is_correct ? 'answer-correct' : 'answer-incorrect'}">
      <div class="result-answer-head">
        <span>${a.is_correct ? '✓' : '↺'} &nbsp; ${a.is_correct ? 'Correct' : 'Review this answer'}</span>
        <small>${esc(a.topic_name)}</small>
      </div>
      <h3>${esc(a.question_text)}</h3>
      <p><b>Your answer:</b> ${esc(a.your_answer)}</p>
      ${a.is_correct ? '' : `<p><b>Correct answer:</b> ${esc(a.correct_answer)}</p><div class="answer-explanation">${esc(a.explanation)}</div>`}
    </article>
  `).join('');

    window.scrollTo({ top: 0, behavior: 'smooth' });
}

$('#start-quiz').addEventListener('click', beginQuiz);
$('#submit-quiz').addEventListener('click', submitQuiz);

$('#cancel-quiz').addEventListener('click', () => {
    $('#quiz-active').classList.add('hidden');
    $('#quiz-start').classList.remove('hidden');
});

$('#try-again').addEventListener('click', () => {
    $('#quiz-results').classList.add('hidden');
    $('#quiz-start').classList.remove('hidden');
    window.scrollTo({ top: 0, behavior: 'smooth' });
});

document.querySelectorAll('[data-logout]').forEach(b =>
    b.addEventListener('click', async () => {
        await fetch('/api/auth/logout', { method: 'POST', credentials: 'same-origin' });
        location.href = '/';
    })
);

load();