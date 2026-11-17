const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

let catalog = { enrolled: [], available: [], requests: [], class_name: '' };
let activeTab = 'enrolled';

function toast(msg) {
    const el = $('#toast');
    el.textContent = msg;
    el.classList.add('show');
    setTimeout(() => el.classList.remove('show'), 2600);
}

function setTab(tab) {
    activeTab = tab;
    document.querySelectorAll('.course-tab').forEach(b => b.classList.toggle('active', b.dataset.tab === tab));
    ['enrolled', 'available', 'requests'].forEach(k => $('#' + k + '-section').classList.toggle('hidden', k !== tab));
    $('#department-filter').classList.toggle('hidden', tab === 'requests');
    $('#teacher-filter').classList.toggle('hidden', tab === 'requests');
    render();
}

document.querySelectorAll('.course-tab').forEach(b => b.addEventListener('click', () => setTab(b.dataset.tab)));

function courseCard(c, enrolled) {
    return `<article class="course-card">
    <div class="course-card-art ${enrolled ? 'art-enrolled' : ''}">
      <span class="course-mark">${enrolled ? '✦' : '◈'}</span>
      <span class="course-dept">${esc(c.department)}</span>
    </div>
    <div class="course-card-body">
      <div class="course-card-meta">
        <span>${esc(c.target_class || 'All classes')}</span>
        ${enrolled ? `<span class="progress-label">${c.progress || 0}% complete</span>` : ''}
      </div>
      <h3>${esc(c.title)}</h3>
      <p class="course-description">${esc(c.description)}</p>
      <div class="course-teacher">
        <span class="teacher-avatar">${esc((c.teacher_name || '?')[0].toUpperCase())}</span>
        <span><b>${esc(c.teacher_name)}</b><small>${enrolled ? 'Your teacher' : `${c.enrolled_count} enrolled`}</small></span>
      </div>
      <div class="course-card-actions">
        <button class="button outline details-button" data-id="${c.course_id}" data-kind="${enrolled ? 'enrolled' : 'available'}">
          ${enrolled ? 'Continue learning' : 'View details'}
        </button>
        ${enrolled ? '' : `<button class="button primary enroll-button" data-id="${c.course_id}">Enroll <span>→</span></button>`}
      </div>
    </div>
  </article>`;
}

function render() {
    const q = $('#course-search').value.trim().toLowerCase();
    const dept = $('#department-filter').value;
    const teacher = $('#teacher-filter').value;
    const items = catalog[activeTab] || [];

    const filtered = items.filter(c =>
        (!q || [c.title, c.description, c.teacher_name, c.department].some(x => String(x || '').toLowerCase().includes(q))) &&
        (!dept || c.department === dept) &&
        (!teacher || c.teacher_name === teacher)
    );

    if (activeTab === 'requests') {
        const list = $('#request-list');
        list.innerHTML = filtered.length ? filtered.map(r => `
      <article class="request-item">
        <div class="request-symbol">⌑</div>
        <div class="request-main">
          <h3>${esc(r.title)}</h3>
          <p>${esc(r.department)} · ${esc(r.target_class)}</p>
          <small>${esc(r.description)}</small>
          <time>${new Date(r.created_at).toLocaleDateString()}</time>
        </div>
        <span class="status-pill status-${esc(r.status)}">${esc(r.status)}</span>
      </article>
    `).join('') : `
      <div class="empty-course">
        <span>✳</span>
        <h3>No course requests yet</h3>
        <p>Ask for a course you’d like your teachers to offer.</p>
        <button class="button primary request-inline">Request a course</button>
      </div>
    `;
        list.querySelector('.request-inline')?.addEventListener('click', () => $('#request-dialog').showModal());
        return;
    }

    const grid = $(`#${activeTab}-grid`);
    grid.innerHTML = filtered.length ? filtered.map(c => courseCard(c, activeTab === 'enrolled')).join('') : `
    <div class="empty-course">
      <span>${activeTab === 'enrolled' ? '▤' : '⌕'}</span>
      <h3>${q ? 'No matching courses' : activeTab === 'enrolled' ? 'No courses yet' : 'No courses available'}</h3>
      <p>${activeTab === 'enrolled' ? 'Explore the catalog and enroll in a course to get started.' : 'Try a different search or ask for a course you want to learn.'}</p>
      ${activeTab === 'enrolled' ? '<button class="button primary explore-inline">Explore courses</button>' : '<button class="button outline request-inline">Request a course</button>'}
    </div>
  `;

    grid.querySelector('.explore-inline')?.addEventListener('click', () => setTab('available'));
    grid.querySelector('.request-inline')?.addEventListener('click', () => $('#request-dialog').showModal());
    grid.querySelectorAll('.details-button').forEach(b => b.addEventListener('click', () => showDetails(Number(b.dataset.id), b.dataset.kind)));
    grid.querySelectorAll('.enroll-button').forEach(b => b.addEventListener('click', () => enroll(Number(b.dataset.id), b)));
}

function updateFilters() {
    const all = [...catalog.enrolled, ...catalog.available];
    const departments = [...new Set(all.map(c => c.department))].sort();
    const teachers = [...new Set(all.map(c => c.teacher_name))].sort();

    const d = $('#department-filter');
    const t = $('#teacher-filter');
    const oldD = d.value;
    const oldT = t.value;

    d.innerHTML = '<option value="">All departments</option>' + departments.map(x => `<option>${esc(x)}</option>`).join('');
    t.innerHTML = '<option value="">All teachers</option>' + teachers.map(x => `<option>${esc(x)}</option>`).join('');

    d.value = oldD;
    t.value = oldT;
}

async function load() {
    try {
        const r = await fetch('/api/student/courses', { credentials: 'same-origin' });
        if (r.status === 401) {
            location.replace('/');
            return;
        }
        const data = await r.json();
        if (!r.ok) throw Error(data.detail || 'Could not load courses');

        catalog = data;
        $('#side-name').textContent = data.account.name;
        $('#avatar').textContent = data.account.name[0].toUpperCase();
        $('#top-avatar').textContent = data.account.name[0].toUpperCase();
        $('#side-subtitle').textContent = data.class_name;
        $('#course-subtitle').textContent = `Browse courses for ${data.class_name}, or continue learning.`;
        $('#request-class').value = data.class_name;
        $('#count-enrolled').textContent = data.enrolled.length;
        $('#count-available').textContent = data.available.length;
        $('#count-requests').textContent = data.requests.length;

        updateFilters();
        render();
    } catch (e) {
        toast(e.message);
    }
}

async function enroll(id, button) {
    button.disabled = true;
    try {
        const r = await fetch(`/api/student/courses/${id}/enroll`, { method: 'POST', credentials: 'same-origin' });
        const data = await r.json();
        if (!r.ok) throw Error(data.detail || 'Could not enroll');
        toast(data.message);
        await load();
        setTab('enrolled');
    } catch (e) {
        toast(e.message);
        button.disabled = false;
    }
}

function showDetails(id, kind) {
    const course = (catalog[kind] || []).find(c => c.course_id === id);
    if (!course) return;

    $('#detail-title').textContent = course.title;
    $('#detail-content').innerHTML = `
    <div class="detail-tags">
      <span>${esc(course.department)}</span>
      <span>${esc(course.target_class || 'All classes')}</span>
    </div>
    <p>${esc(course.description)}</p>
    <div class="detail-teacher">
      <span class="teacher-avatar">${esc(course.teacher_name[0].toUpperCase())}</span>
      <div>
        <b>${esc(course.teacher_name)}</b>
        <small>Course teacher</small>
      </div>
    </div>
    ${kind === 'enrolled' ? '<div class="detail-progress"><span>Course progress</span><b>0%</b><div class="bar"><i style="width:0%"></i></div></div>' : ''}
    <div class="detail-next">
      <b>Course lessons</b>
      <p>Lessons and course materials will appear here as the course content is added.</p>
    </div>
  `;
    $('#detail-dialog').showModal();
}

$('#course-search').addEventListener('input', render);
$('#department-filter').addEventListener('change', render);
$('#teacher-filter').addEventListener('change', render);
$('#request-open').addEventListener('click', () => $('#request-dialog').showModal());
document.querySelectorAll('[data-close]').forEach(b => b.addEventListener('click', () => $('#' + b.dataset.close).close()));

$('#request-form').addEventListener('submit', async e => {
    e.preventDefault();
    const form = e.currentTarget;
    const payload = Object.fromEntries(new FormData(form));
    payload.reason = payload.reason.trim() || null;

    const button = form.querySelector('button[type=submit]');
    button.disabled = true;
    $('#request-message').textContent = '';

    try {
        const r = await fetch('/api/student/course-requests', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify(payload)
        });
        const data = await r.json();
        if (!r.ok) throw Error(data.detail || 'Could not send request');

        form.reset();
        $('#request-class').value = catalog.class_name;
        $('#request-dialog').close();
        toast('Course request sent');
        await load();
        setTab('requests');
    } catch (err) {
        $('#request-message').textContent = err.message;
    } finally {
        button.disabled = false;
    }
});

document.querySelectorAll('[data-logout]').forEach(b => b.addEventListener('click', async () => {
    await fetch('/api/auth/logout', { method: 'POST', credentials: 'same-origin' });
    location.href = '/';
}));

load();