const role = document.body.dataset.role;

const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
}[c]));

const fmtDate = s => new Date(s + 'T00:00:00').toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
});

const toast = t => {
    const x = document.querySelector('#toast');
    x.textContent = t;
    x.classList.add('show');
    setTimeout(() => x.classList.remove('show'), 2600);
};

document.querySelector('#today-date').textContent = new Intl.DateTimeFormat(undefined, {
    weekday: 'short',
    month: 'short',
    day: 'numeric'
}).format(new Date());

document.querySelectorAll('[data-logout]').forEach(b =>
    b.addEventListener('click', async () => {
        await fetch('/api/auth/logout', { method: 'POST', credentials: 'same-origin' });
        location.href = '/';
    })
);

async function load() {
    try {
        const res = await fetch(`/api/${role}/dashboard`, { credentials: 'same-origin' });
        if (res.status === 401) {
            location.replace('/');
            return;
        }
        if (!res.ok) throw Error('Could not load dashboard information');

        const d = await res.json();
        const name = d.account.name;

        document.querySelector('#greeting-name').textContent = name.split(' ')[0];
        document.querySelector('#side-name').textContent = name;
        document.querySelector('#avatar').textContent = name[0].toUpperCase();
        document.querySelector('#top-avatar').textContent = name[0].toUpperCase();

        if (role === 'student') {
            document.querySelector('#side-subtitle').textContent = d.class_name || 'Learner';
            document.querySelector('#welcome-subtitle').textContent = d.class_name
                ? `${d.class_name} · A little progress each day adds up.`
                : 'A little progress each day adds up.';

            document.querySelector('#stat-assessments').textContent = d.stats.assessments;
            document.querySelector('#stat-average').textContent = d.stats.assessments ? `${Math.round(d.stats.average_score)}%` : '—';
            document.querySelector('#stat-topics').textContent = d.stats.topics_practiced;

            document.querySelector('#assessment-list').innerHTML = d.recent_assessments.length
                ? d.recent_assessments.map(a => `
            <div class="assessment-row">
              <span class="assessment-symbol">▤</span>
              <div class="assessment-info">
                <b>${esc(a.type)} assessment</b>
                <small>${fmtDate(a.date)}</small>
              </div>
              <span class="assessment-score">${a.score == null ? '—' : Math.round(a.score) + '%'}</span>
            </div>
          `).join('')
                : '<div class="empty-cell">No assessments yet. Your results will appear here after your first assessment.</div>';

            document.querySelector('#topic-list').innerHTML = d.topic_performance.length
                ? d.topic_performance.map(t => `
            <div class="topic-row">
              <div class="topic-meta">
                <span>${esc(t.topic_name)}</span>
                <span>${Math.round(t.accuracy || 0)}%</span>
              </div>
              <div class="bar">
                <i style="width:${Math.max(0, Math.min(100, t.accuracy || 0))}%"></i>
              </div>
            </div>
          `).join('')
                : '<div class="empty-cell">Topic insights appear after your answers are recorded.</div>';

        } else {
            document.querySelector('#side-subtitle').textContent = d.department || 'Educator';
            document.querySelector('#welcome-subtitle').textContent = d.department
                ? `${d.department} · See how your learners are progressing.`
                : 'See how your learners are progressing.';

            document.querySelector('#stat-students').textContent = d.stats.students;
            document.querySelector('#stat-assessments').textContent = d.stats.assessments;
            document.querySelector('#stat-average').textContent = d.stats.assessments ? `${Math.round(d.stats.average_score)}%` : '—';
            document.querySelector('#stat-department').textContent = d.department || '—';
            document.querySelector('#roster-count').textContent = `${d.students.length} ${d.students.length === 1 ? 'student' : 'students'}`;

            document.querySelector('#student-rows').innerHTML = d.students.length
                ? d.students.map(s => `
            <tr>
              <td>
                <div class="student-cell">
                  <span class="avatar">${esc(s.name[0].toUpperCase())}</span>
                  ${esc(s.name)}
                  <span></span>
                </div>
              </td>
              <td>${esc(s.class_name)}</td>
              <td>${s.assessments}</td>
              <td>${s.assessments ? `<span class="score-chip">${Math.round(s.average)}%</span>` : '—'}</td>
            </tr>
          `).join('')
                : '<tr><td colspan="4" class="empty-cell">Your linked students will appear here.</td></tr>';
        }
    } catch (e) {
        toast(e.message);
    }
}

load();