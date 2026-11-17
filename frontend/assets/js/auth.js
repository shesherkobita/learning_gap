const form = document.querySelector('#auth-form');
const tabs = [...document.querySelectorAll('.tab')];
const message = document.querySelector('#form-message');
const pw = document.querySelector('#password');
const roleField = document.querySelector('#role-field');
let mode = 'login';

const $ = s => document.querySelector(s);

function toggle(id, on) {
    $(id).classList.toggle('hidden', !on);
}

function setMode(next) {
    mode = next;
    tabs.forEach(t => t.classList.toggle('active', t.dataset.mode === mode));

    const reg = mode === 'register';
    $('#form-eyebrow').textContent = reg ? 'GET STARTED' : 'WELCOME BACK';
    $('#form-title').textContent = reg ? 'Create your account.' : 'Good to see you.';
    $('#form-subtitle').textContent = reg ? 'Choose your learning space and start today.' : 'Sign in to continue your learning journey.';
    $('#submit-button span').textContent = reg ? 'Create account' : 'Sign in';

    toggle('#role-field', reg);
    toggle('#name-field', reg);
    toggle('#confirm-field', reg);
    toggle('#remember-row', !reg);
    toggle('#forgot-link', !reg);

    $('#password').autocomplete = reg ? 'new-password' : 'current-password';
    $('#password').placeholder = reg ? 'Create a password' : 'Enter your password';
    message.textContent = '';
    refreshRole();
}

async function loadTeachers() {
    const select = $('#teacher-id');
    const hint = $('#teacher-hint');

    if (select.dataset.loaded) return;
    select.innerHTML = '<option value="">Loading teachers…</option>';
    hint.textContent = '';

    try {
        const res = await fetch('/api/auth/teachers', { credentials: 'same-origin' });
        if (!res.ok) throw Error('Could not load teachers');

        const data = await res.json();
        select.innerHTML = '<option value="">Select a teacher</option>';

        for (const teacher of data.teachers) {
            const option = document.createElement('option');
            option.value = teacher.teacher_id;
            option.textContent = teacher.department ? `${teacher.name} · ${teacher.department}` : teacher.name;
            select.append(option);
        }

        select.dataset.loaded = 'true';
        if (!data.teachers.length) {
            hint.textContent = 'No teacher accounts are available yet. Ask a teacher to create an account first.';
            select.disabled = true;
        } else {
            select.disabled = false;
        }
    } catch {
        select.innerHTML = '<option value="">Unable to load teachers</option>';
        hint.textContent = 'Please refresh and try again.';
    }
}

function refreshRole() {
    const role = $('input[name=role]:checked')?.value || 'student';
    const reg = mode === 'register';

    toggle('#class-field', reg && role === 'student');
    toggle('#teacher-field', reg && role === 'student');
    toggle('#department-field', reg && role === 'teacher');

    if (reg && role === 'student') loadTeachers();
}

// Event Listeners
tabs.forEach(t => t.addEventListener('click', () => setMode(t.dataset.mode)));
document.querySelectorAll('input[name=role]').forEach(x => x.addEventListener('change', refreshRole));

$('.show-password').addEventListener('click', e => {
    const visible = pw.type === 'text';
    pw.type = visible ? 'password' : 'text';
    e.currentTarget.textContent = visible ? 'Show' : 'Hide';
    e.currentTarget.setAttribute('aria-label', visible ? 'Show password' : 'Hide password');
});

pw.addEventListener('input', () => {
    const box = $('#strength');
    const p = pw.value;
    box.classList.toggle('hidden', mode !== 'register');

    let level = (p.length >= 8 ? 1 : 0) +
        (/[A-Z]/.test(p) && /[a-z]/.test(p) ? 1 : 0) +
        (/[0-9]/.test(p) ? 1 : 0) +
        (/[^A-Za-z0-9]/.test(p) ? 1 : 0);

    box.dataset.level = level;
});

$('#forgot-link').addEventListener('click', e => {
    e.preventDefault();
    message.textContent = 'Password reset is not part of this first milestone. Please contact your administrator.';
});

form.addEventListener('submit', async e => {
    e.preventDefault();
    message.textContent = '';

    const email = $('#email').value.trim();
    const password = pw.value;

    if (!email || !$('#email').checkValidity()) {
        message.textContent = 'Enter a valid email address.';
        return;
    }

    if (mode === 'register') {
        if ($('#full-name').value.trim().length < 2) {
            message.textContent = 'Enter your full name.';
            return;
        }
        if (password.length < 8) {
            message.textContent = 'Choose a password with at least 8 characters.';
            return;
        }
        if (password !== $('#confirm-password').value) {
            message.textContent = 'Your passwords do not match.';
            return;
        }

        const role = $('input[name=role]:checked').value;
        if (role === 'student' && !$('#class-name').value.trim()) {
            message.textContent = 'Enter your class or grade.';
            return;
        }
        if (role === 'student' && !$('#teacher-id').value) {
            message.textContent = 'Choose your teacher.';
            return;
        }
        if (role === 'teacher' && !$('#department').value.trim()) {
            message.textContent = 'Enter your department.';
            return;
        }
    }

    const button = $('#submit-button');
    button.disabled = true;
    button.querySelector('span').textContent = mode === 'login' ? 'Signing in…' : 'Creating account…';

    try {
        let url = '/api/auth/login';
        let body = { email, password, remember_me: $('#remember-me').checked };

        if (mode === 'register') {
            const role = $('input[name=role]:checked').value;
            url = `/api/auth/register/${role}`;
            body = {
                email,
                password,
                full_name: $('#full-name').value.trim(),
                ...(role === 'student'
                    ? { class_name: $('#class-name').value.trim(), teacher_id: Number($('#teacher-id').value) }
                    : { department: $('#department').value.trim() })
            };
        }

        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify(body)
        });

        const data = await res.json();
        if (!res.ok) throw Error(data.detail || 'Something went wrong. Please try again.');

        location.href = data.redirect;
    } catch (err) {
        message.textContent = err.message;
    } finally {
        button.disabled = false;
        button.querySelector('span').textContent = mode === 'login' ? 'Sign in' : 'Create account';
    }
});

// Initial Session Check
fetch('/api/auth/me', { credentials: 'same-origin' })
    .then(async r => {
        if (r.ok) {
            const d = await r.json();
            location.replace(`/${d.account.role}/dashboard`);
        }
    })
    .catch(() => { });