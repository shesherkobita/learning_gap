const $ = (s) => document.querySelector(s); const $$ = (s) => [...document.querySelectorAll(s)];

const esc = (s) =>
    String(s ?? '').replace(/[&<>"']/g, (c) => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;',
    }[c]));

const toast = (message) => {
    const el = $('#toast');
    if (!el) return;
    el.textContent = message;
    el.classList.add('show');
    setTimeout(() => el.classList.remove('show'), 2600);
};

const json = async (response) => {
    let data;
    try {
        data = await response.json();
    } catch {
        throw Error('The server did not return a valid response');
    }
    if (response.status === 401) {
        location.href = '/';
        throw Error('Please sign in again');
    }
    if (!response.ok) throw Error(data.detail || 'The request failed');
    return data;
};

async function api(url, options = {}) {
    return json(
        await fetch(url, {
            credentials: 'same-origin',
            ...options,
            headers: {
                ...(options.body ? { 'Content-Type': 'application/json' } : {}),
                ...(options.headers || {}),
            },
        })
    );
}

async function profile() {
    const d = await api('/api/auth/me');
    $('#side-name') && ($('#side-name').textContent = d.account.name);
    $('#avatar') && ($('#avatar').textContent = d.account.name[0].toUpperCase());
    $('#top-avatar') && ($('#top-avatar').textContent = d.account.name[0].toUpperCase());
    return d.account;
}

$$('[data-logout]').forEach((b) => b.addEventListener('click', async () => { try { await api('/api/auth/logout', { method: 'POST' }); } finally { location.href = '/'; } })); $$
    ('[data-close]').forEach((b) =>
        b.addEventListener('click', () => $('#' + b.dataset.close)?.close())
    );

function dateLabel(value) {
    return value
        ? new Date(value).toLocaleString(undefined, {
            month: 'short',
            day: 'numeric',
            hour: 'numeric',
            minute: '2-digit',
        })
        : 'No due date';
}

function dateShort(value) {
    return value
        ? new Date(value).toLocaleDateString(undefined, {
            month: 'short',
            day: 'numeric',
            year: 'numeric',
        })
        : '—';
}

async function loadTeacherDashboard() {
    const who = await profile();
    const d = await api('/api/teacher/dashboard');

    $('#teacher-greeting').textContent = who.name.split(' ')[0];
    $('#teacher-department').textContent = d.department || 'Teacher overview';
    $('#teacher-date').textContent = new Intl.DateTimeFormat(undefined, {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
    }).format(new Date());

    $('#t-active-classes').textContent = d.stats.active_classes;
    $('#t-students').textContent = d.stats.students;
    $('#t-pending').textContent = d.stats.pending_gradings;
    $('#t-at-risk').textContent = d.at_risk.length;

    $('#teacher-risk-list').innerHTML = d.at_risk.length
        ? d.at_risk
            .map(
                (s) =>
                    `<div class="teacher-list-row"><span class="risk-avatar">!</span><div class="teacher-list-copy"><b>${esc(s.name)}</b><small>${esc(s.class)} · ${s.scored_attempts} scored attempts</small></div><strong class="risk-score">${Number(s.average_score).toFixed(0)}%</strong></div>`
            )
            .join('')
        : '<div class="empty-note">No students are currently below the at-risk threshold.</div>';

    $('#teacher-deadlines').innerHTML = d.deadlines.length
        ? d.deadlines
            .map(
                (a) =>
                    `<div class="teacher-list-row"><span class="deadline-icon">◷</span><div class="teacher-list-copy"><b>${esc(a.title)}</b><small>${esc(a.class_title)} · ${esc(a.kind)}</small></div><time>${dateLabel(a.due_at)}</time></div>`
            )
            .join('')
        : '<div class="empty-note">No upcoming published assessments.</div>';

    $('#teacher-student-rows').innerHTML = d.students.length
        ? d.students
            .map(
                (s) =>
                    `<tr><td>${esc(s.name)}</td><td>${esc(s.class_name)}</td><td>${s.assessments}</td><td>${s.assessments ? `${Math.round(s.average)}%` : '—'}</td></tr>`
            )
            .join('')
        : '<tr><td colspan="4" class="empty-cell">No students are linked to your teacher account yet.</td></tr>';
}

let teacherClasses = [];
let managedCourseId = null;

async function loadClasses() {
    await profile();
    const d = await api('/api/teacher/classes');
    teacherClasses = d.classes;

    const root = $('#teacher-class-grid');
    root.innerHTML = teacherClasses.length
        ? teacherClasses
            .map(
                (c) =>
                    `<article class="teacher-class-card"><div class="teacher-class-art"><span>▦</span><span class="class-status ${c.is_published ? 'published' : 'draft'}">${c.is_published ? 'Published' : 'Draft'}</span></div><div class="teacher-class-card-body"><span class="course-dept">${esc(c.department)} · ${esc(c.target_class)}</span><h3>${esc(c.title)}</h3><p>${esc(c.description)}</p><div class="class-card-meta"><span>${c.student_count} students</span><span>${c.material_count} materials</span><span>${c.announcement_count} notices</span></div><div class="course-card-actions"><button class="button outline edit-class" data-id="${c.course_id}">Edit class</button><button class="button primary manage-class" data-id="${c.course_id}">Manage content</button></div><button class="publish-toggle" data-id="${c.course_id}">${c.is_published ? 'Unpublish class' : 'Publish class'}</button></div></article>`
            )
            .join('')
        : '<div class="empty-course"><span>▦</span><h3>No classes yet</h3><p>Create a class to add a syllabus, materials, announcements, and assessments.</p></div>';

    root
        .querySelectorAll('.edit-class')
        .forEach((b) => b.addEventListener('click', () => editClass(Number(b.dataset.id))));
    root
        .querySelectorAll('.manage-class')
        .forEach((b) => b.addEventListener('click', () => manageClass(Number(b.dataset.id))));
    root.querySelectorAll('.publish-toggle').forEach((b) =>
        b.addEventListener('click', async () => {
            try {
                await api(`/api/teacher/classes/${b.dataset.id}/publish`, { method: 'PATCH' });
                await loadClasses();
                toast('Class visibility updated');
            } catch (e) {
                toast(e.message);
            }
        })
    );
}

function editClass(id) {
    const form = $('#class-form');
    form.reset();
    const item = teacherClasses.find((c) => c.course_id === id);
    $('#class-dialog-title').textContent = item ? 'Edit class' : 'Create a class';
    form.elements.course_id.value = item?.course_id || '';
    if (item) {
        for (const key of ['title', 'description', 'department', 'target_class', 'syllabus']) {
            form.elements[key].value = item[key] || '';
        }
    }
    $('#class-dialog').showModal();
}

$('#new-class')?.addEventListener('click', () => editClass(null));

$('#class-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const f = e.currentTarget;
    const payload = Object.fromEntries(new FormData(f));
    const id = payload.course_id;
    delete payload.course_id;
    const msg = $('#class-message');
    msg.textContent = '';

    try {
        await api(id ? `/api/teacher/classes/${id}` : '/api/teacher/classes', {
            method: id ? 'PUT' : 'POST',
            body: JSON.stringify(payload),
        });
        $('#class-dialog').close();
        await loadClasses();
        toast(id ? 'Class updated' : 'Class created as a draft');
    } catch (err) {
        msg.textContent = err.message;
    }
});

async function manageClass(id) {
    managedCourseId = id;
    const c = teacherClasses.find((x) => x.course_id === id);
    $('#manage-class-title').textContent = c?.title || 'Class workspace';
    $('#class-content-dialog').showModal();
    await loadClassContent('materials');
}

$$('.workspace-tab').forEach((b) => b.addEventListener('click', () => {
    $$
        ('.workspace-tab').forEach((x) => x.classList.toggle('active', x === b));
    loadClassContent(b.dataset.workspace);
})
);

async function loadClassContent(mode) {
    const root = $('#class-workspace-content');
    root.innerHTML = '<div class="loading-line">Loading class content…</div>';

    try {
        const d = await api(`/api/teacher/classes/${managedCourseId}/content`);
        if (mode === 'materials') {
            root.innerHTML = `<form class="inline-create" id="material-form"><input name="title" required placeholder="Material title"><select name="material_type"><option value="link">Link</option><option value="notes">Study notes</option><option value="worksheet">Worksheet</option><option value="video">Video</option></select><input name="resource_url" type="url" required placeholder="https://…"><button class="button primary">Add material</button></form><div class="workspace-list">${d.materials.length
                ? d.materials
                    .map(
                        (m) =>
                            `<a class="workspace-record" href="${esc(m.resource_url)}" target="_blank" rel="noopener"><span>↗</span><div><b>${esc(m.title)}</b><small>${esc(m.material_type)} ·${dateShort(m.created_at)}</small></div></a>`
                    )
                    .join('')
                : '<div class="empty-note">No materials added yet.</div>'
                }</div>`;
        } else if (mode === 'announcements') {
            root.innerHTML = `<form class="inline-create announcement-create" id="announcement-form"><input name="title" required placeholder="Announcement title"><textarea name="body" required placeholder="Write a class announcement"></textarea><button class="button primary">Post announcement</button></form><div class="workspace-list">${d.announcements.length
                ? d.announcements
                    .map(
                        (a) =>
                            `<article class="workspace-record"><span>✦</span><div><b>${esc(a.title)}</b><p>${esc(a.body)}</p><small>${dateShort(a.created_at)}</small></div></article>`
                    )
                    .join('')
                : '<div class="empty-note">No announcements yet.</div>'
                }</div>`;
        } else {
            root.innerHTML = d.students.length
                ? `<div class="table-scroll"><table><thead><tr><th>STUDENT</th><th>EMAIL</th><th>CLASS</th></tr></thead><tbody>${d.students
                    .map((s) => `<tr><td>${esc(s.name)}</td><td>${esc(s.email)}</td><td>${esc(s.class)}</td></tr>`)
                    .join('')}</tbody></table></div>`
                : '<div class="empty-note">No students enrolled in this class yet.</div>';
        }

        $('#material-form')?.addEventListener('submit', (e) => saveClassContent(e, 'materials'));
        $('#announcement-form')?.addEventListener('submit', (e) => saveClassContent(e, 'announcements'));
    } catch (e) {
        root.innerHTML = `<div class="empty-note">${esc(e.message)}</div>`;
    }
}

async function saveClassContent(e, mode) {
    e.preventDefault();
    const form = e.currentTarget;
    const body = JSON.stringify(Object.fromEntries(new FormData(form)));
    try {
        await api(`/api/teacher/classes/${managedCourseId}/${mode}`, { method: 'POST', body });
        await loadClassContent(mode);
        await loadClasses();
        toast(mode === 'materials' ? 'Material added' : 'Announcement posted');
    } catch (err) {
        toast(err.message);
    }
}

let assessmentData = { assessments: [], classes: [] };

async function loadAssessments() {
    await profile();
    const d = await api('/api/teacher/assessments');
    assessmentData = d;

    $('#assessment-course').innerHTML =
        d.classes.map((c) => `<option value="${c.course_id}">${esc(c.title)}</option>`).join('') ||
        '<option value="">Create a class first</option>';

    const a = d.assessments;
    $('#a-scheduled').textContent = a.filter((x) => x.is_published).length;
    $('#a-submissions').textContent = a.reduce((n, x) => n + x.submission_count, 0);
    $('#a-pending').textContent = a.reduce((n, x) => n + x.pending_count, 0);
    $('#a-drafts').textContent = a.filter((x) => !x);
}
