const app = document.getElementById('app');
const API_BASE_URL = (window.FACEMARK_API_BASE_URL || 'http://localhost:8001').replace(/\/$/, '');

// ==========================================
// API CLIENT & AUTHENTICATION
// ==========================================
const API_BASE = `${API_BASE_URL}/api/v1`;
let authToken = localStorage.getItem('facemark-token') || null;
let currentUser = null;

async function api(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (authToken) headers['Authorization'] = `Bearer ${authToken}`;
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }
  const resp = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (resp.status === 401) {
    authToken = null;
    localStorage.removeItem('facemark-token');
    navigateTo(() => { appState.currentView = 'login'; renderLogin(); });
    throw new Error('Session expired. Please log in again.');
  }
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(err.detail || err.error?.message || 'Request failed');
  }
  return resp.json();
}

// ==========================================
// APPLICATION STATE
// ==========================================
const appState = {
  currentView: 'login',
  selectedClass: null,
  classes: [],
  subjects: [],
  students: [],
  attendanceSession: null,
  sessionId: null,
  sessionStartTime: null,
  detectResults: null,
  reviewStudents: [],
  attendanceHistory: [],
  capturedBlob: null,
  activeTab: 'classes'
};

// ==========================================
// CAMERA UTILITY WITH SEQUENTIAL FALLBACKS
// ==========================================
async function getCameraStream(facingMode = 'environment', idealWidth = 1280, idealHeight = 720) {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    let msg = 'Camera API is not supported by your browser.';
    if (window.location.protocol !== 'https:' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
      msg += ' Modern browsers require a secure HTTPS or localhost context to access the camera.';
    }
    throw new Error(msg);
  }

  const constraints = [
    { video: { facingMode: facingMode, width: { ideal: idealWidth }, height: { ideal: idealHeight } }, audio: false },
    { video: { facingMode: facingMode }, audio: false },
    { video: true, audio: false }
  ];

  for (const c of constraints) {
    try {
      const stream = await navigator.mediaDevices.getUserMedia(c);
      if (stream) return stream;
    } catch (e) {
      console.warn('Camera constraint failed, trying next fallback:', c, e);
    }
  }
  throw new Error('Could not initialize camera on this device. Please check permissions or select a photo file.');
}

// ==========================================
// MODAL SYSTEM
// ==========================================
function openModal(title, bodyHtml, onRender = null) {
  closeModal(); // Remove any existing modal
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay';
  overlay.id = 'activeModalOverlay';
  overlay.innerHTML = `
    <div class="modal-content">
      <div class="modal-header">
        <h3>${title}</h3>
        <button class="modal-close" onclick="closeModal()">&times;</button>
      </div>
      <div class="modal-body">${bodyHtml}</div>
    </div>
  `;
  document.body.appendChild(overlay);
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) closeModal();
  });
  if (onRender) onRender(overlay);
}

function closeModal() {
  if (window.cameraStream) {
    window.cameraStream.getTracks().forEach(t => t.stop());
    window.cameraStream = null;
  }
  const existing = document.getElementById('activeModalOverlay');
  if (existing) existing.remove();
}

// ==========================================
// VIEW TRANSITION & NOTIFICATIONS
// ==========================================
function navigateTo(renderFn) {
  closeModal();
  const currentShell = document.querySelector('.app-shell');
  if (currentShell) {
    currentShell.style.opacity = '0';
    currentShell.style.transition = 'opacity 0.18s ease';
  }
  setTimeout(() => {
    if (window.sessionTimerInterval) {
      clearInterval(window.sessionTimerInterval);
      window.sessionTimerInterval = null;
    }
    if (window.cameraStream) {
      window.cameraStream.getTracks().forEach(t => t.stop());
      window.cameraStream = null;
    }
    renderFn();
    const newShell = document.querySelector('.app-shell');
    if (newShell) newShell.classList.add('page-transition-enter');
  }, 180);
}

function showToast(message, type = 'info') {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  const toast = document.createElement('div');
  toast.className = `toast toast-${type} toast-enter`;
  let icon = 'ℹ️';
  if (type === 'success') icon = '✅';
  if (type === 'error') icon = '❌';
  toast.innerHTML = `
    <span style="font-size:1.2rem;">${icon}</span>
    <span style="flex:1;">${message}</span>
    <button style="background:none;border:none;color:inherit;font-size:1.2rem;cursor:pointer;" onclick="this.parentElement.remove()">&times;</button>
  `;
  container.appendChild(toast);
  setTimeout(() => {
    toast.classList.replace('toast-enter', 'toast-exit');
    setTimeout(() => { if (toast.parentElement) toast.remove(); }, 300);
  }, 3500);
}

function initTheme() {
  const saved = localStorage.getItem('facemark-theme');
  const prefersDark = window.matchMedia?.('(prefers-color-scheme: dark)').matches;
  document.documentElement.setAttribute('data-theme', saved === 'dark' || (!saved && prefersDark) ? 'dark' : 'light');
}

function toggleTheme() {
  const next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('facemark-theme', next);
  updateThemeToggleIcon();
}

function updateThemeToggleIcon() {
  const btn = document.querySelector('.theme-toggle');
  if (btn) btn.textContent = document.documentElement.getAttribute('data-theme') === 'dark' ? '☀️' : '🌙';
}

function animateCounters() {
  document.querySelectorAll('.kpi strong').forEach(counter => {
    const text = counter.innerText;
    const hasPercent = text.includes('%');
    const target = parseInt(text.replace(/\D/g, ''), 10);
    if (isNaN(target)) return;
    const startTime = performance.now();
    const update = (t) => {
      const p = Math.min((t - startTime) / 800, 1);
      counter.innerText = Math.floor((1 - Math.pow(1 - p, 4)) * target) + (hasPercent ? '%' : '');
      if (p < 1) requestAnimationFrame(update); else counter.innerText = text;
    };
    requestAnimationFrame(update);
  });
}

function initScrollToTop() {
  if (!document.querySelector('.scroll-top-btn')) {
    const btn = document.createElement('button');
    btn.className = 'scroll-top-btn'; btn.innerHTML = '↑'; btn.title = 'Scroll to top';
    document.body.appendChild(btn);
    btn.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
  }
  const btn = document.querySelector('.scroll-top-btn');
  const handler = () => { if (window.scrollY > 300) btn.classList.add('visible'); else btn.classList.remove('visible'); };
  window.removeEventListener('scroll', window.__scrollTop); window.__scrollTop = handler; window.addEventListener('scroll', handler);
}

function initTopbarScroll() {
  const handler = () => { const t = document.querySelector('.topbar'); if (t) { if (window.scrollY > 50) t.classList.add('scrolled'); else t.classList.remove('scrolled'); } };
  window.removeEventListener('scroll', window.__scrollTopbar); window.__scrollTopbar = handler; window.addEventListener('scroll', handler);
}

function initKeyboardShortcuts() {
  if (window.__shortcutsBound) return;
  window.__shortcutsBound = true;
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      const activeModal = document.getElementById('activeModalOverlay');
      if (activeModal) {
        closeModal();
      } else if (appState.currentView !== 'login' && appState.currentView !== 'dashboard') {
        navigateTo(() => { appState.currentView = 'dashboard'; renderDashboard(); });
      }
    }
  });
}

// ==========================================
// TOPBAR NAVIGATION & WORKFLOW STEP BAR
// ==========================================
function getTopbarHtml() {
  const userName = currentUser?.full_name || 'Teacher';
  const isSession = ['session', 'upload', 'results', 'second-photo', 'final-review'].includes(appState.currentView);
  
  return `
    <header class="topbar">
      <div style="display:flex; align-items:center; gap:24px; flex-wrap:wrap;">
        <div class="brand" style="cursor:pointer;" onclick="navigateTo(() => { appState.currentView = 'dashboard'; renderDashboard(); })">
          <div class="brand-mark">F</div>
          <span>FaceMark</span>
        </div>
        <nav class="nav-pills">
          <button type="button" data-nav="dashboard" class="${appState.currentView === 'dashboard' ? 'active' : ''}">📊 Dashboard</button>
          <button type="button" data-nav="classes-hub" class="${appState.currentView === 'classes-hub' ? 'active' : ''}">🏫 Classes & Subjects</button>
          <button type="button" data-nav="students-hub" class="${appState.currentView === 'students-hub' ? 'active' : ''}">👥 Students & Faces</button>
          <button type="button" data-nav="class-select" class="${['class-select', 'upload', 'results', 'second-photo', 'final-review'].includes(appState.currentView) ? 'active' : ''}">📸 Take Attendance</button>
          <button type="button" data-nav="history" class="${appState.currentView === 'history' ? 'active' : ''}">📜 Attendance Reports</button>
        </nav>
      </div>

      <div style="display:flex; align-items:center; gap:14px; flex-wrap:wrap;">
        ${isSession ? '<div class="session-timer">⏱️ <span id="sessionTimerText">00:00</span></div>' : ''}
        <div class="user-badge">👤 ${userName}</div>
        <button class="theme-toggle" title="Toggle dark mode">🌙</button>
        <button class="logout-btn ghost-btn" style="padding:8px 14px; font-size:13px;">🚪 Logout</button>
      </div>
    </header>
  `;
}

function renderStepIndicator(currentStepIndex) {
  const steps = ['1. Select Class', '2. Capture Photo', '3. AI Matches', '4. Review & Verify', '5. Finalized'];
  let html = '<div class="step-indicator" style="margin-bottom:24px; padding:14px 20px; background:var(--panel-alt); border-radius:18px; border:1.5px solid var(--line); display:flex; align-items:center; justify-content:space-between;">';
  steps.forEach((step, i) => {
    const done = i < currentStepIndex, active = i === currentStepIndex;
    html += `
      <div class="step ${active ? 'active' : ''} ${done ? 'completed' : ''}" style="display:flex; flex-direction:column; align-items:center; gap:6px; z-index:1;">
        <div style="width:30px; height:30px; border-radius:50%; background:${done ? 'var(--success)' : active ? 'var(--primary)' : 'var(--line)'}; color:${done || active ? '#fff' : 'var(--muted)'}; display:flex; align-items:center; justify-content:center; font-size:13px; font-weight:800; box-shadow:${active ? '0 0 0 4px var(--primary-soft)' : 'none'};">
          ${done ? '✓' : i + 1}
        </div>
        <span style="font-size:12px; font-weight:${active || done ? '800' : '600'}; color:${active ? 'var(--text)' : done ? 'var(--success)' : 'var(--muted)'};">${step}</span>
      </div>
    `;
    if (i < steps.length - 1) {
      html += `<div class="step-line ${done ? 'completed' : ''}" style="flex:1; height:3px; background:${done ? 'var(--success)' : 'var(--line)'}; margin:-18px 8px 0 8px; border-radius:2px;"></div>`;
    }
  });
  return html + '</div>';
}

function postRenderSetup() {
  initScrollToTop();
  initTopbarScroll();
  initKeyboardShortcuts();

  const themeToggle = document.querySelector('.theme-toggle');
  if (themeToggle) {
    updateThemeToggleIcon();
    themeToggle.addEventListener('click', toggleTheme);
  }

  const logoutBtn = document.querySelector('.logout-btn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
      authToken = null; currentUser = null; localStorage.removeItem('facemark-token');
      showToast('Logged out successfully', 'success');
      setTimeout(() => navigateTo(() => { appState.currentView = 'login'; renderLogin(); }), 400);
    });
  }

  bindNavigation();

  const isSession = ['session', 'upload', 'results', 'second-photo', 'final-review'].includes(appState.currentView);
  if (isSession && appState.sessionStartTime) {
    const timerEl = document.getElementById('sessionTimerText');
    if (timerEl) {
      const tick = () => {
        const d = Math.floor((Date.now() - appState.sessionStartTime) / 1000);
        timerEl.textContent = `${String(Math.floor(d / 60)).padStart(2, '0')}:${String(d % 60).padStart(2, '0')}`;
      };
      tick();
      window.sessionTimerInterval = setInterval(tick, 1000);
    }
  }
}

function bindNavigation() {
  document.querySelectorAll('[data-nav]').forEach(button => {
    button.addEventListener('click', () => {
      const target = button.dataset.nav;
      if (appState.currentView === target) return;
      navigateTo(() => {
        appState.currentView = target;
        if (target === 'dashboard') renderDashboard();
        else if (target === 'classes-hub') renderClassesHub();
        else if (target === 'students-hub') renderStudentsHub();
        else if (target === 'class-select') renderClassSelect();
        else if (target === 'history') renderHistory();
        else if (target === 'upload') renderUpload();
        else if (target === 'results') renderResults();
        else if (target === 'second-photo') renderSecondPhoto();
        else if (target === 'final-review') renderFinalReview();
        else if (target === 'manage-roster') renderRosterManagement();
      });
    });
  });
}

// ==========================================
// VIEW 1: LOGIN GUI
// ==========================================
function renderLogin() {
  app.innerHTML = `
    <div class="app-shell">
      <div class="auth-screen">
        <div class="auth-card">
          <div style="display:flex; align-items:center; gap:12px; margin-bottom:14px;">
            <div class="brand-mark" style="width:48px; height:48px; font-size:1.4rem;">F</div>
            <div>
              <div class="eyebrow">FaceMark AI System</div>
              <h2 style="font-size:1.6rem; margin:0;">Teacher Portal</h2>
            </div>
          </div>

          <p class="subtitle">Log in to manage your classes, enroll student biometrics, and mark attendance with face recognition.</p>

          <form id="loginForm" class="form-grid">
            <div class="input-wrap">
              <label for="email">Teacher Email</label>
              <input id="email" type="email" value="teacher@facemark.demo" required placeholder="teacher@facemark.demo" />
            </div>

            <div class="input-wrap">
              <label for="password">Password</label>
              <input id="password" type="password" value="demo123" required placeholder="••••••••" />
            </div>

            <button type="submit" class="primary-btn" id="loginBtn" style="height:50px; font-size:1.05rem;">
              🚀 Sign In to Dashboard
            </button>
            <div id="loginAlert" class="alert error"></div>
          </form>

          <div style="margin-top:24px; padding:14px; border-radius:14px; background:var(--panel-alt); border:1px solid var(--line); font-size:0.85rem; color:var(--muted);">
            <strong style="color:var(--text);">Demo Credentials:</strong><br/>
            • Teacher: <code>teacher@facemark.demo</code> / <code>demo123</code><br/>
            • Admin: <code>admin@facemark.demo</code> / <code>admin123</code>
          </div>
        </div>
      </div>
    </div>
  `;

  document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value.trim();
    const alertBox = document.getElementById('loginAlert');
    const btn = document.getElementById('loginBtn');
    if (!email || !password) return;
    
    btn.textContent = 'Authenticating...'; btn.disabled = true;
    try {
      const data = await api('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) });
      authToken = data.access_token;
      currentUser = data.user;
      localStorage.setItem('facemark-token', authToken);
      showToast(`Welcome back, ${currentUser.full_name}!`, 'success');
      navigateTo(() => { appState.currentView = 'dashboard'; renderDashboard(); });
    } catch (err) {
      alertBox.textContent = err.message || 'Login failed. Check credentials.';
      alertBox.classList.add('show');
      btn.textContent = '🚀 Sign In to Dashboard'; btn.disabled = false;
    }
  });

  postRenderSetup();
}

// ==========================================
// VIEW 2: DASHBOARD GUI
// ==========================================
async function renderDashboard() {
  try { appState.classes = await api('/classes'); } catch { appState.classes = []; }
  try { appState.subjects = await api('/subjects'); } catch { appState.subjects = []; }
  try { appState.students = await api('/students'); } catch { appState.students = []; }

  // Load history across classes
  let allHistory = [];
  for (const c of appState.classes) {
    try {
      const h = await api(`/history/classes/${c.id}`);
      allHistory.push(...h);
    } catch {}
  }
  allHistory.sort((a, b) => b.date.localeCompare(a.date));
  appState.attendanceHistory = allHistory;

  const totalClasses = appState.classes.length;
  const totalStudents = appState.students.length;
  const totalSessions = allHistory.length;
  
  // Calculate average attendance percentage
  let avgAttendance = 0;
  if (totalSessions > 0) {
    const totalPresent = allHistory.reduce((s, item) => s + (item.present || 0), 0);
    const totalEnrolled = allHistory.reduce((s, item) => s + ((item.present || 0) + (item.absent || 0)), 0);
    if (totalEnrolled > 0) avgAttendance = Math.round((totalPresent / totalEnrolled) * 100);
  }

  app.innerHTML = `
    <div class="app-shell">
      ${getTopbarHtml()}

      <div class="page">
        <!-- Dashboard Top Welcome & Quick Actions -->
        <div class="panel" style="margin-bottom:24px;">
          <div class="panel-header" style="flex-wrap:wrap;">
            <div>
              <div class="eyebrow">Academic Attendance Suite</div>
              <h2>Welcome, ${currentUser?.full_name || 'Teacher'} 👋</h2>
            </div>
            <div class="quick-actions-bar">
              <button class="primary-btn" onclick="openAddClassModal()">➕ Add Class</button>
              <button class="secondary-btn" onclick="openAddSubjectModal()">📚 Add Subject</button>
              <button class="secondary-btn" onclick="openAddStudentModal()">👤 Register Student</button>
            </div>
          </div>

          <!-- KPI Metric Cards -->
          <div class="kpi-row">
            <div class="kpi">
              <small>🏫 Assigned Classes</small>
              <strong>${totalClasses}</strong>
            </div>
            <div class="kpi">
              <small>👥 Registered Students</small>
              <strong>${totalStudents}</strong>
            </div>
            <div class="kpi">
              <small>📸 Completed Sessions</small>
              <strong>${totalSessions}</strong>
            </div>
            <div class="kpi">
              <small>📈 Avg Attendance Rate</small>
              <strong>${avgAttendance}%</strong>
            </div>
          </div>
        </div>

        <!-- 2-Column Dashboard Grid -->
        <div class="dashboard-grid">
          <!-- Left Column: Active Classrooms -->
          <div class="panel">
            <div class="panel-header">
              <h3>🏫 Active Classes (${totalClasses})</h3>
              <button class="ghost-btn" data-nav="classes-hub">Manage All &rarr;</button>
            </div>

            ${totalClasses === 0 ? `
              <div style="padding:48px 24px; text-align:center; color:var(--muted);">
                <div style="font-size:3rem; margin-bottom:12px;">🏫</div>
                <h4>No Classes Found</h4>
                <p style="margin-top:6px; margin-bottom:18px;">Create your first class to begin managing students and taking attendance.</p>
                <button class="primary-btn" onclick="openAddClassModal()">➕ Create Class</button>
              </div>
            ` : `
              <div class="class-grid">
                ${appState.classes.map(cls => `
                  <div class="class-card" data-class-id="${cls.id}" style="display:flex; flex-direction:column; justify-content:space-between; min-height:170px;">
                    <div>
                      <div class="eyebrow">${cls.subject || 'General'}</div>
                      <h3 style="margin-top:6px; margin-bottom:6px;">${cls.name}</h3>
                      <div class="stats" style="color:var(--muted);">
                        <span>👥 ${cls.student_count || 0} students</span>
                        <span>Sem ${cls.semester || 1}</span>
                      </div>
                    </div>
                    <div style="margin-top:16px; display:flex; gap:8px;">
                      <button class="secondary-btn manage-roster-direct-btn" data-class-id="${cls.id}" style="flex:1; padding:8px 12px; font-size:12px;">👥 Roster</button>
                      <button class="primary-btn start-session-direct-btn" data-class-id="${cls.id}" style="flex:1.4; padding:8px 12px; font-size:12px; white-space:nowrap;">📸 Attendance</button>
                    </div>
                  </div>
                `).join('')}
              </div>
            `}
          </div>

          <!-- Right Column: Recent Sessions Feed -->
          <div class="panel">
            <div class="panel-header">
              <h3>📜 Recent Sessions</h3>
              <button class="ghost-btn" data-nav="history">All Logs &rarr;</button>
            </div>

            ${allHistory.length === 0 ? `
              <div style="padding:48px 24px; text-align:center; color:var(--muted);">
                <div style="font-size:2.5rem; margin-bottom:8px;">📅</div>
                <h4>No Attendance Logs</h4>
                <p>Start a new session to record classroom attendance.</p>
              </div>
            ` : `
              <div class="list-stack">
                ${allHistory.slice(0, 6).map(item => {
                  const total = (item.present || 0) + (item.absent || 0);
                  const rate = total > 0 ? Math.round((item.present / total) * 100) : 0;
                  return `
                    <div class="list-item" style="cursor:pointer;" onclick="openSessionDetailModal('${item.session_id}')">
                      <div class="meta">
                        <strong>${item.class_name} • ${item.subject}</strong>
                        <span>📅 ${item.date}</span>
                        <small>Attendance: <strong>${item.present} Present</strong> / ${item.absent} Absent (${rate}%)</small>
                      </div>
                      <span class="badge ${rate >= 75 ? 'success' : rate >= 50 ? 'warning' : 'danger'}">${rate}%</span>
                    </div>
                  `;
                }).join('')}
              </div>
            `}
          </div>
        </div>
      </div>
    </div>
  `;

  // Bind Direct Class Card Action Buttons
  document.querySelectorAll('.manage-roster-direct-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      appState.selectedClass = appState.classes.find(c => c.id === btn.dataset.classId);
      navigateTo(() => { appState.currentView = 'manage-roster'; renderRosterManagement(); });
    });
  });

  document.querySelectorAll('.start-session-direct-btn').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.stopPropagation();
      const cls = appState.classes.find(c => c.id === btn.dataset.classId);
      appState.selectedClass = cls;
      btn.textContent = 'Starting...'; btn.disabled = true;
      try {
        const session = await api('/attendance-sessions', {
          method: 'POST',
          body: JSON.stringify({
            class_id: cls.id,
            subject_name: (cls.subject && cls.subject !== 'General') ? cls.subject : null,
            session_date: new Date().toISOString().slice(0, 10)
          })
        });
        appState.sessionId = session.id;
        appState.attendanceSession = session;
        appState.sessionStartTime = Date.now();
        showToast(`Attendance session created for ${cls.name}!`, 'success');
        navigateTo(() => { appState.currentView = 'upload'; renderUpload(); });
      } catch (err) {
        showToast(err.message, 'error');
        btn.textContent = '📸 Attendance'; btn.disabled = false;
      }
    });
  });

  postRenderSetup();
  animateCounters();
}

// ==========================================
// VIEW 3: CLASSES & SUBJECTS HUB GUI
// ==========================================
async function renderClassesHub() {
  try { appState.classes = await api('/classes'); } catch { appState.classes = []; }
  try { appState.subjects = await api('/subjects'); } catch { appState.subjects = []; }

  app.innerHTML = `
    <div class="app-shell">
      ${getTopbarHtml()}

      <div class="page">
        <div class="panel">
          <div class="panel-header" style="flex-wrap:wrap;">
            <div>
              <div class="eyebrow">Academic Curriculum</div>
              <h2>Classes & Subjects Management</h2>
            </div>
            <div class="quick-actions-bar">
              <button class="primary-btn" onclick="openAddClassModal()">➕ Add Class</button>
              <button class="secondary-btn" onclick="openAddSubjectModal()">📚 Add Subject</button>
            </div>
          </div>

          <!-- Tabs Header -->
          <div class="tabs-header">
            <button class="tab-btn ${appState.activeTab === 'classes' ? 'active' : ''}" id="tabClassesBtn">🏫 Classes (${appState.classes.length})</button>
            <button class="tab-btn ${appState.activeTab === 'subjects' ? 'active' : ''}" id="tabSubjectsBtn">📚 Subjects (${appState.subjects.length})</button>
          </div>

          <!-- Classes Tab Content -->
          <div id="classesTabContent" class="${appState.activeTab === 'classes' ? '' : 'hidden'}">
            ${appState.classes.length === 0 ? `
              <div style="padding:48px; text-align:center; color:var(--muted);">
                <h4>No classes created yet.</h4>
                <p>Click "Add Class" above to set up a class.</p>
              </div>
            ` : `
              <div class="class-grid">
                ${appState.classes.map(cls => `
                  <div class="class-card" style="display:flex; flex-direction:column; justify-content:space-between; min-height:190px;">
                    <div>
                      <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                        <span class="eyebrow">${cls.subject || 'General'}</span>
                        <button class="icon-btn danger" title="Delete Class" onclick="deleteClassConfirm('${cls.id}', '${cls.name}')">🗑️</button>
                      </div>
                      <h3 style="margin-top:8px; margin-bottom:8px;">${cls.name}</h3>
                      <div class="stats" style="color:var(--muted); margin-bottom:8px;">
                        <span>👥 ${cls.student_count || 0} Students</span>
                        <span>Semester ${cls.semester || 1}</span>
                      </div>
                      <div style="font-size:0.85rem; color:var(--muted);">Year: ${cls.academic_year || '2026-2027'}</div>
                    </div>
                    <div style="margin-top:16px; display:flex; gap:8px;">
                      <button class="secondary-btn" style="flex:1; padding:8px 12px; font-size:12px;" onclick="goToRoster('${cls.id}')">👥 Roster</button>
                      <button class="primary-btn" style="flex:1.3; padding:8px 12px; font-size:12px;" onclick="startSessionDirect('${cls.id}')">📸 Session</button>
                    </div>
                  </div>
                `).join('')}
              </div>
            `}
          </div>

          <!-- Subjects Tab Content -->
          <div id="subjectsTabContent" class="${appState.activeTab === 'subjects' ? '' : 'hidden'}">
            ${appState.subjects.length === 0 ? `
              <div style="padding:48px; text-align:center; color:var(--muted);">
                <h4>No subjects registered yet.</h4>
                <p>Click "Add Subject" above to register course subjects.</p>
              </div>
            ` : `
              <table class="mini-table">
                <thead>
                  <tr>
                    <th>Subject Code</th>
                    <th>Subject Name</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  ${appState.subjects.map(s => `
                    <tr>
                      <td style="font-weight:800; color:var(--primary);">${s.code}</td>
                      <td style="font-weight:700;">${s.name}</td>
                      <td>
                        <button class="icon-btn danger" onclick="deleteSubjectConfirm('${s.id}', '${s.name}')">🗑️ Delete</button>
                      </td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
            `}
          </div>
        </div>
      </div>
    </div>
  `;

  document.getElementById('tabClassesBtn').addEventListener('click', () => {
    appState.activeTab = 'classes';
    document.getElementById('tabClassesBtn').classList.add('active');
    document.getElementById('tabSubjectsBtn').classList.remove('active');
    document.getElementById('classesTabContent').classList.remove('hidden');
    document.getElementById('subjectsTabContent').classList.add('hidden');
  });

  document.getElementById('tabSubjectsBtn').addEventListener('click', () => {
    appState.activeTab = 'subjects';
    document.getElementById('tabSubjectsBtn').classList.add('active');
    document.getElementById('tabClassesBtn').classList.remove('active');
    document.getElementById('subjectsTabContent').classList.remove('hidden');
    document.getElementById('classesTabContent').classList.add('hidden');
  });

  postRenderSetup();
}

// Global Class Action Helpers
window.goToRoster = (classId) => {
  appState.selectedClass = appState.classes.find(c => c.id === classId);
  navigateTo(() => { appState.currentView = 'manage-roster'; renderRosterManagement(); });
};

window.startSessionDirect = async (classId) => {
  const cls = appState.classes.find(c => c.id === classId);
  appState.selectedClass = cls;
  try {
    const session = await api('/attendance-sessions', {
      method: 'POST',
      body: JSON.stringify({
        class_id: cls.id,
        subject_name: (cls.subject && cls.subject !== 'General') ? cls.subject : null,
        session_date: new Date().toISOString().slice(0, 10)
      })
    });
    appState.sessionId = session.id;
    appState.attendanceSession = session;
    appState.sessionStartTime = Date.now();
    showToast(`Session started for ${cls.name}!`, 'success');
    navigateTo(() => { appState.currentView = 'upload'; renderUpload(); });
  } catch (err) {
    showToast(err.message, 'error');
  }
};

window.deleteClassConfirm = async (classId, className) => {
  if (!confirm(`Are you sure you want to delete class "${className}"?`)) return;
  try {
    await api(`/classes/${classId}`, { method: 'DELETE' });
    showToast(`Class "${className}" deleted`, 'success');
    renderClassesHub();
  } catch (err) {
    showToast(err.message, 'error');
  }
};

window.deleteSubjectConfirm = async (subjectId, subjectName) => {
  if (!confirm(`Are you sure you want to delete subject "${subjectName}"?`)) return;
  try {
    await api(`/subjects/${subjectId}`, { method: 'DELETE' });
    showToast(`Subject "${subjectName}" deleted`, 'success');
    renderClassesHub();
  } catch (err) {
    showToast(err.message, 'error');
  }
};

// ==========================================
// VIEW 4: STUDENTS DIRECTORY & BIOMETRICS HUB
// ==========================================
async function renderStudentsHub() {
  try { appState.students = await api('/students'); } catch { appState.students = []; }
  try { appState.classes = await api('/classes'); } catch { appState.classes = []; }

  app.innerHTML = `
    <div class="app-shell">
      ${getTopbarHtml()}

      <div class="page">
        <div class="panel">
          <div class="panel-header" style="flex-wrap:wrap;">
            <div>
              <div class="eyebrow">Student Roster & Biometric DB</div>
              <h2>Registered Students Directory</h2>
            </div>
            <div class="quick-actions-bar">
              <button class="primary-btn" onclick="openAddStudentModal()">➕ Register Student</button>
            </div>
          </div>

          <!-- Search & Filter Controls -->
          <div style="display:flex; gap:12px; margin-bottom:20px; flex-wrap:wrap;">
            <input type="text" class="search-input" id="globalStudentSearch" placeholder="Search by name or roll number..." style="flex:1; min-width:240px;" />
            <select id="biometricFilter" style="padding:12px 16px; border-radius:14px; border:1.5px solid var(--line); background:var(--panel-alt); color:var(--text); font-weight:700;">
              <option value="All">All Face Statuses</option>
              <option value="Enrolled">✅ Enrolled Only</option>
              <option value="Missing">⚠️ Missing Face Only</option>
            </select>
          </div>

          <!-- Students Table -->
          <div id="studentsTableContainer">
            ${renderStudentsTableHtml(appState.students)}
          </div>
        </div>
      </div>
    </div>
  `;

  // Search and Filter Listeners
  const filterStudents = () => {
    const term = document.getElementById('globalStudentSearch').value.toLowerCase().trim();
    const bioFilter = document.getElementById('biometricFilter').value;

    const filtered = appState.students.filter(s => {
      const matchText = s.full_name.toLowerCase().includes(term) || s.student_number.toLowerCase().includes(term);
      const matchBio = bioFilter === 'All' ? true : bioFilter === 'Enrolled' ? s.has_face_enrollment : !s.has_face_enrollment;
      return matchText && matchBio;
    });

    document.getElementById('studentsTableContainer').innerHTML = renderStudentsTableHtml(filtered);
  };

  document.getElementById('globalStudentSearch').addEventListener('input', filterStudents);
  document.getElementById('biometricFilter').addEventListener('change', filterStudents);

  postRenderSetup();
}

function renderStudentsTableHtml(studentsList) {
  if (studentsList.length === 0) {
    return `
      <div style="padding:48px; text-align:center; color:var(--muted);">
        <div style="font-size:2.5rem; margin-bottom:8px;">👥</div>
        <h4>No students found matching filter</h4>
      </div>
    `;
  }

  return `
    <table class="mini-table">
      <thead>
        <tr>
          <th>Student</th>
          <th>Roll / Reg No</th>
          <th>Contact Email</th>
          <th>Biometric Status</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        ${studentsList.map(s => {
          const initials = s.full_name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
          return `
            <tr>
              <td>
                <div style="display:flex; align-items:center; gap:12px;">
                  <div class="student-avatar">${initials}</div>
                  <div>
                    <strong style="color:var(--text); font-size:1.02rem;">${s.full_name}</strong>
                    <div style="font-size:0.8rem; color:var(--muted);">${s.status}</div>
                  </div>
                </div>
              </td>
              <td style="font-weight:800; color:var(--primary);">${s.student_number}</td>
              <td style="color:var(--muted); font-weight:600;">${s.email || '—'}</td>
              <td>
                <span class="status-pill ${s.has_face_enrollment ? 'present' : 'absent'}">
                  ${s.has_face_enrollment ? '✅ 512-dim Enrolled' : '⚠️ Missing Face'}
                </span>
              </td>
              <td>
                <div style="display:flex; gap:8px;">
                  <button class="secondary-btn" style="padding:6px 12px; font-size:12px;" onclick="openEnrollFaceModal('${s.id}', '${s.full_name}', '${s.student_number}')">
                    📸 Enroll Face
                  </button>
                  <button class="icon-btn danger" title="Delete Student" onclick="deleteStudentConfirm('${s.id}', '${s.full_name}')">
                    🗑️
                  </button>
                </div>
              </td>
            </tr>
          `;
        }).join('')}
      </tbody>
    </table>
  `;
}

window.deleteStudentConfirm = async (studentId, studentName) => {
  if (!confirm(`Are you sure you want to delete student "${studentName}"?`)) return;
  try {
    await api(`/students/${studentId}`, { method: 'DELETE' });
    showToast(`Student "${studentName}" removed`, 'success');
    renderStudentsHub();
  } catch (err) {
    showToast(err.message, 'error');
  }
};

// ==========================================
// VIEW 5: CLASS ROSTER & ENROLLMENT GUI
// ==========================================
async function renderRosterManagement() {
  const cls = appState.selectedClass;
  if (!cls) {
    navigateTo(() => { appState.currentView = 'classes-hub'; renderClassesHub(); });
    return;
  }

  let roster = [];
  try { roster = await api(`/classes/${cls.id}/students`); } catch (err) { showToast(err.message, 'error'); }

  app.innerHTML = `
    <div class="app-shell">
      ${getTopbarHtml()}

      <div class="page">
        <div class="panel">
          <div class="panel-header" style="flex-wrap:wrap;">
            <div>
              <div class="eyebrow">${cls.name} • ${cls.subject || 'General'}</div>
              <h2>Class Roster Management</h2>
            </div>
            <div class="quick-actions-bar">
              <button class="primary-btn" onclick="startSessionDirect('${cls.id}')">📸 Start Attendance</button>
              <button class="secondary-btn" data-nav="classes-hub">&larr; Back to Classes</button>
            </div>
          </div>

          <!-- Quick Add Student Form Directly to This Class -->
          <div class="summary-box" style="margin-bottom:24px; border:1.5px solid var(--primary);">
            <h4 style="margin:0 0 12px 0;">➕ Add Student Directly to ${cls.name}</h4>
            <form id="rosterAddStudentForm" style="display:flex; gap:12px; align-items:flex-end; flex-wrap:wrap;">
              <div class="input-wrap" style="flex:1; min-width:200px; margin:0;">
                <label for="rosterStudentName">Full Name</label>
                <input id="rosterStudentName" type="text" placeholder="e.g. Rahul Verma" required />
              </div>
              <div class="input-wrap" style="flex:1; min-width:160px; margin:0;">
                <label for="rosterStudentNumber">Registration / Roll No</label>
                <input id="rosterStudentNumber" type="text" placeholder="e.g. ROLL-001" required />
              </div>
              <div class="input-wrap" style="flex:1; min-width:180px; margin:0;">
                <label for="rosterStudentEmail">Email (Optional)</label>
                <input id="rosterStudentEmail" type="email" placeholder="student@demo.com" />
              </div>
              <button type="submit" class="primary-btn" id="rosterAddBtn" style="height:48px;">Add to Class</button>
            </form>
          </div>

          <!-- Roster Table -->
          <div class="summary-box">
            <h4 style="margin:0 0 14px 0;">Enrolled Roster (${roster.length} Students)</h4>
            ${roster.length === 0 ? `
              <div style="padding:32px; text-align:center; color:var(--muted);">
                <p>No students enrolled in ${cls.name} yet. Use the form above to add students.</p>
              </div>
            ` : `
              <table class="mini-table">
                <thead>
                  <tr>
                    <th>Roll No</th>
                    <th>Student Name</th>
                    <th>Biometric Profile</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  ${roster.map(s => `
                    <tr>
                      <td style="font-weight:800; color:var(--primary);">${s.student_number}</td>
                      <td style="font-weight:700;">${s.name}</td>
                      <td>
                        <span class="status-pill ${s.has_enrollment ? 'present' : 'absent'}">
                          ${s.has_enrollment ? '✅ Biometric Ready' : '⚠️ Missing Photo'}
                        </span>
                      </td>
                      <td>
                        <button class="secondary-btn" style="padding:6px 12px; font-size:12px;" onclick="openEnrollFaceModal('${s.id}', '${s.name}', '${s.student_number}')">
                          📸 Capture & Enroll
                        </button>
                      </td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
            `}
          </div>
        </div>
      </div>
    </div>
  `;

  document.getElementById('rosterAddStudentForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('rosterAddBtn');
    btn.textContent = 'Adding...'; btn.disabled = true;

    const full_name = document.getElementById('rosterStudentName').value.trim();
    const student_number = document.getElementById('rosterStudentNumber').value.trim();
    const email = document.getElementById('rosterStudentEmail').value.trim() || undefined;

    try {
      await api('/students', {
        method: 'POST',
        body: JSON.stringify({ full_name, student_number, email, class_id: cls.id })
      });
      showToast(`Student "${full_name}" added to ${cls.name}!`, 'success');
      renderRosterManagement();
    } catch (err) {
      showToast(err.message, 'error');
      btn.textContent = 'Add to Class'; btn.disabled = false;
    }
  });

  postRenderSetup();
}

// ==========================================
// VIEW 6: ATTENDANCE CLASS SELECTION GUI
// ==========================================
async function renderClassSelect() {
  try { appState.classes = await api('/classes'); } catch { appState.classes = []; }

  const cls = appState.selectedClass || appState.classes[0];
  if (!cls) {
    app.innerHTML = `
      <div class="app-shell">
        ${getTopbarHtml()}
        <div class="page">
          <div class="panel" style="text-align:center; padding:60px 24px;">
            <div style="font-size:3rem; margin-bottom:12px;">🏫</div>
            <h2>No Classes Found</h2>
            <p style="color:var(--muted); margin-bottom:20px;">Create a class before you can start taking attendance.</p>
            <button class="primary-btn" onclick="openAddClassModal()">➕ Create Class</button>
          </div>
        </div>
      </div>
    `;
    postRenderSetup();
    return;
  }

  app.innerHTML = `
    <div class="app-shell">
      ${getTopbarHtml()}

      <div class="page">
        ${renderStepIndicator(0)}

        <div class="panel">
          <div class="panel-header">
            <div>
              <div class="eyebrow">Step 1 of 5</div>
              <h2>Select Class for Attendance</h2>
            </div>
          </div>

          <div class="class-grid">
            ${appState.classes.map(item => `
              <div class="class-card ${item.id === cls.id ? 'selected' : ''}" data-class-id="${item.id}">
                <div class="eyebrow">${item.subject || 'General'}</div>
                <h3 style="margin-top:6px; margin-bottom:8px;">${item.name}</h3>
                <div class="stats" style="color:var(--muted);">
                  <span>👥 ${item.student_count || 0} students</span>
                  <span>Sem ${item.semester || 1}</span>
                </div>
              </div>
            `).join('')}
          </div>

          <div class="summary-box" style="margin-top:28px; border:2px solid var(--primary);">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
              <div>
                <strong>Selected: ${cls.name} (${cls.subject || 'General'})</strong>
                <div style="color:var(--muted); margin-top:4px;">${cls.student_count || 0} enrolled students in candidate search space</div>
              </div>
              <div style="display:flex; gap:12px;">
                <button class="primary-btn" id="startSessionBtn" style="padding:14px 28px; font-size:1.05rem;">
                  📸 Launch Attendance Camera &rarr;
                </button>
                <button class="secondary-btn" onclick="goToRoster('${cls.id}')">👥 View Roster</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;

  document.querySelectorAll('[data-class-id]').forEach(card => {
    card.addEventListener('click', () => {
      appState.selectedClass = appState.classes.find(c => c.id === card.dataset.classId);
      renderClassSelect();
    });
  });

  document.getElementById('startSessionBtn').addEventListener('click', async () => {
    const btn = document.getElementById('startSessionBtn');
    btn.textContent = 'Initializing Session...'; btn.disabled = true;
    try {
      const session = await api('/attendance-sessions', {
        method: 'POST',
        body: JSON.stringify({
          class_id: cls.id,
          subject_name: (cls.subject && cls.subject !== 'General') ? cls.subject : null,
          session_date: new Date().toISOString().slice(0, 10)
        })
      });
      appState.sessionId = session.id;
      appState.attendanceSession = session;
      appState.sessionStartTime = Date.now();
      showToast('Attendance Session Active!', 'success');
      navigateTo(() => { appState.currentView = 'upload'; renderUpload(); });
    } catch (err) {
      showToast(err.message, 'error');
      btn.textContent = '📸 Launch Attendance Camera →'; btn.disabled = false;
    }
  });

  postRenderSetup();
}

// ==========================================
// VIEW 7: LIVE ATTENDANCE CAMERA STUDIO GUI
// ==========================================
function renderUpload() {
  const session = appState.attendanceSession || {};
  app.innerHTML = `
    <div class="app-shell">
      ${getTopbarHtml()}

      <div class="page">
        ${renderStepIndicator(1)}

        <div class="panel">
          <div class="panel-header" style="flex-wrap:wrap;">
            <div>
              <div class="eyebrow">${session.class_name || 'Class'} • ${session.subject_name || 'Subject'}</div>
              <h2>Classroom Photo Capture</h2>
            </div>
            <div style="display:flex; gap:8px; flex-wrap:wrap;">
              <button class="secondary-btn" id="startLiveAttendanceBtn">🟢 Start Live Attendance</button>
              <button class="ghost-btn" data-nav="class-select">&larr; Change Class</button>
            </div>
          </div>

          <!-- Camera Viewfinder Studio -->
          <div class="viewfinder-box" id="mainViewfinder">
            <video id="cameraPreview" autoplay playsinline style="display:none;"></video>
            <canvas id="cameraCanvas" style="display:none;"></canvas>
            <img id="capturedImage" style="display:none;" />
            
            <div class="viewfinder-overlay" id="viewfinderOverlay" style="display:none;">
              <div class="viewfinder-guide"></div>
              <div class="viewfinder-tag">
                <span class="live-dot"></span> LIVE AI VIEWFINDER
              </div>
            </div>

            <div id="cameraPrompt" style="padding:60px 20px; text-align:center; color:#fff;">
              <div style="font-size:3.5rem; margin-bottom:12px;">📷</div>
              <h3>Ready to Capture Class Photo</h3>
              <p style="color:#94a3b8; max-width:400px; margin:8px auto 20px auto;">
                Ensure good lighting and that all students are clearly in frame.
              </p>
              <button class="primary-btn" id="openCameraBtn" style="padding:14px 28px; font-size:1.05rem;">
                📹 Open Webcam / Camera
              </button>
            </div>
          </div>

          <div id="liveAttendancePanel" class="panel" style="display:none; margin-top:16px; background:var(--panel-alt);">
            <div style="display:flex; justify-content:space-between; align-items:center; gap:12px; flex-wrap:wrap;">
              <div>
                <strong>🟢 Live Attendance Running</strong>
                <div id="liveAttendanceStatus" style="color:var(--muted); margin-top:4px;">Waiting for first frame...</div>
              </div>
              <div style="display:flex; gap:10px;">
                <span class="badge success" id="livePresentCount">Present: 0</span>
                <span class="badge info" id="liveDetectedCount">Faces: 0</span>
                <button class="secondary-btn" id="stopLiveAttendanceBtn">⏹ Stop Live Mode</button>
              </div>
            </div>
            <div id="liveNewStudents" style="margin-top:14px;"></div>
          </div>

          <!-- Live Camera Controls -->
          <div style="display:flex; justify-content:center; gap:12px; margin-top:16px;">
            <button class="primary-btn" id="captureBtn" style="display:none; padding:12px 24px;">📸 Snap Classroom Picture</button>
            <button class="secondary-btn" id="retakeBtn" style="display:none;">🔄 Retake Picture</button>
          </div>

          <!-- Or File Upload Fallback -->
          <div style="text-align:center; margin:20px 0 10px 0; color:var(--muted); font-weight:800;">
            — OR SELECT FROM IMAGE GALLERY —
          </div>
          <label class="upload-zone" id="mainUploadZone" for="photoInput" style="margin-top:0;">
            <div class="upload-icon">📁</div>
            <strong>Choose High-Res Class Photo</strong>
            <span>JPG, PNG or WEBP (Max 15MB)</span>
            <input id="photoInput" type="file" accept="image/png,image/jpeg,image/jpg,image/webp" />
          </label>

          <!-- Recognition Progress Steps -->
          <div class="processing-box hidden" id="processingBox">
            <h4 style="margin:0 0 14px 0;">⚡ AI Recognition Engine Processing...</h4>
            <div class="progress-step" id="step1"><div class="step-num">1</div><span>Detecting human faces in classroom</span></div>
            <div class="progress-step" id="step2"><div class="step-num">2</div><span>Extracting 512-dim ArcFace biometric vectors</span></div>
            <div class="progress-step" id="step3"><div class="step-num">3</div><span>Matching against enrolled class roster</span></div>
            <div class="progress-step" id="step4"><div class="step-num">✓</div><span>Finalizing candidate classification</span></div>
          </div>

          <div class="action-row" style="margin-top:24px;">
            <button class="primary-btn" id="uploadAndProcessBtn" disabled style="padding:14px 28px; font-size:1.05rem;">
              ⚡ Run AI Face Recognition &rarr;
            </button>
            <button class="ghost-btn" data-nav="dashboard">Cancel</button>
          </div>
        </div>
      </div>
    </div>
  `;

  let selectedFile = null;
  const video = document.getElementById('cameraPreview');
  const canvas = document.getElementById('cameraCanvas');
  const capturedImg = document.getElementById('capturedImage');
  const prompt = document.getElementById('cameraPrompt');
  const overlay = document.getElementById('viewfinderOverlay');
  const openCameraBtn = document.getElementById('openCameraBtn');
  const captureBtn = document.getElementById('captureBtn');
  const retakeBtn = document.getElementById('retakeBtn');
  const uploadBtn = document.getElementById('uploadAndProcessBtn');

  openCameraBtn.addEventListener('click', async () => {
    try {
      const stream = await getCameraStream('environment', 1920, 1080);
      window.cameraStream = stream;
      video.srcObject = stream;
      video.style.display = 'block';
      prompt.style.display = 'none';
      overlay.style.display = 'grid';
      capturedImg.style.display = 'none';
      captureBtn.style.display = 'inline-flex';
      retakeBtn.style.display = 'none';
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  captureBtn.addEventListener('click', () => {
    canvas.width = video.videoWidth || 1280;
    canvas.height = video.videoHeight || 720;
    canvas.getContext('2d').drawImage(video, 0, 0);
    canvas.toBlob(blob => {
      appState.capturedBlob = blob;
      selectedFile = new File([blob], 'classroom_capture.jpg', { type: 'image/jpeg' });
      capturedImg.src = URL.createObjectURL(blob);
      capturedImg.style.display = 'block';
      video.style.display = 'none';
      overlay.style.display = 'none';
      captureBtn.style.display = 'none';
      retakeBtn.style.display = 'inline-flex';
      uploadBtn.disabled = false;
      if (window.cameraStream) { window.cameraStream.getTracks().forEach(t => t.stop()); window.cameraStream = null; }
    }, 'image/jpeg', 0.95);
  });

  retakeBtn.addEventListener('click', () => {
    capturedImg.style.display = 'none';
    selectedFile = null;
    uploadBtn.disabled = true;
    retakeBtn.style.display = 'none';
    openCameraBtn.click();
  });

  document.getElementById('photoInput').addEventListener('change', (e) => {
    if (e.target.files?.length) {
      selectedFile = e.target.files[0];
      capturedImg.src = URL.createObjectURL(selectedFile);
      capturedImg.style.display = 'block';
      prompt.style.display = 'none';
      video.style.display = 'none';
      overlay.style.display = 'none';
      uploadBtn.disabled = false;
      retakeBtn.style.display = 'inline-flex';
    }
  });

  uploadBtn.addEventListener('click', async () => {
    if (!selectedFile) return;
    uploadBtn.disabled = true; uploadBtn.textContent = 'Processing AI Recognition...';
    const box = document.getElementById('processingBox');
    box.classList.remove('hidden');
    box.scrollIntoView({ behavior: 'smooth' });

    const steps = [document.getElementById('step1'), document.getElementById('step2'), document.getElementById('step3'), document.getElementById('step4')];
    steps[0].classList.add('active');

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      setTimeout(() => { steps[0].classList.replace('active', 'done'); steps[1].classList.add('active'); }, 500);
      setTimeout(() => { steps[1].classList.replace('active', 'done'); steps[2].classList.add('active'); }, 1100);

      const results = await api(`/attendance-sessions/${appState.sessionId}/photos`, {
        method: 'POST',
        body: formData,
        headers: {}
      });

      steps[2].classList.replace('active', 'done'); steps[3].classList.add('active');
      appState.detectResults = results;
      showToast(`Recognition Complete! ${results.confident?.length || 0} confident matches detected.`, 'success');

      setTimeout(() => {
        navigateTo(() => { appState.currentView = 'results'; renderResults(); });
      }, 700);
    } catch (err) {
      showToast('Recognition error: ' + err.message, 'error');
      uploadBtn.disabled = false; uploadBtn.textContent = '⚡ Run AI Face Recognition →';
      box.classList.add('hidden');
    }
  });


  // -------- Real-time attendance mode --------
  const liveBtn = document.getElementById('startLiveAttendanceBtn');
  const livePanel = document.getElementById('liveAttendancePanel');
  const liveStatus = document.getElementById('liveAttendanceStatus');
  const livePresent = document.getElementById('livePresentCount');
  const liveDetected = document.getElementById('liveDetectedCount');
  const liveNew = document.getElementById('liveNewStudents');
  const stopLiveBtn = document.getElementById('stopLiveAttendanceBtn');

  let liveRunning = false;
  let liveTimer = null;
  const liveSeen = new Set();

  const captureLiveFrame = () => {
    if (!liveRunning || !video.srcObject || !video.videoWidth) return;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
    canvas.toBlob(async blob => {
      if (!blob || !liveRunning) return;
      try {
        const formData = new FormData();
        formData.append('file', new File([blob], 'live-frame.jpg', {type:'image/jpeg'}));
        const result = await api(`/attendance-sessions/${appState.sessionId}/live-frame`, {
          method: 'POST',
          body: formData,
          headers: {}
        });
        livePresent.textContent = `Present: ${result.present_count}/${result.total_enrolled}`;
        liveDetected.textContent = `Faces: ${result.detected_faces}`;
        liveStatus.textContent = `${result.newly_present?.length || 0} new attendance record(s) from this frame.`;

        if (result.newly_present?.length) {
          const items = result.newly_present.filter(s => !liveSeen.has(s.student_id));
          items.forEach(s => liveSeen.add(s.student_id));
          if (items.length) {
            liveNew.innerHTML = items.map(s =>
              `<span class="badge success" style="margin:4px;">✓ ${s.name} ${s.confidence}</span>`
            ).join('') + liveNew.innerHTML;
            showToast(`${items.length} student(s) marked present`, 'success');
          }
        }
      } catch (err) {
        liveStatus.textContent = `Frame error: ${err.message}`;
      }
    }, 'image/jpeg', 0.80);
  };

  const stopLive = () => {
    liveRunning = false;
    if (liveTimer) { clearInterval(liveTimer); liveTimer = null; }
    if (window.cameraStream) {
      window.cameraStream.getTracks().forEach(t => t.stop());
      window.cameraStream = null;
    }
    livePanel.style.display = 'none';
    liveBtn.disabled = false;
    liveBtn.textContent = '🟢 Start Live Attendance';
  };

  if (liveBtn) {
    liveBtn.addEventListener('click', async () => {
      try {
        const stream = await getCameraStream('environment', 1920, 1080);
        window.cameraStream = stream;
        video.srcObject = stream;
        video.style.display = 'block';
        prompt.style.display = 'none';
        overlay.style.display = 'grid';
        capturedImg.style.display = 'none';
        captureBtn.style.display = 'none';
        retakeBtn.style.display = 'none';
        uploadBtn.style.display = 'none';
        livePanel.style.display = 'block';
        liveBtn.disabled = true;
        liveBtn.textContent = '🟢 Live Mode Active';
        liveRunning = true;
        captureLiveFrame();
        liveTimer = setInterval(captureLiveFrame, 2000);
      } catch (err) {
        showToast(err.message, 'error');
      }
    });
  }

  if (stopLiveBtn) stopLiveBtn.addEventListener('click', stopLive);

  postRenderSetup();
}

// ==========================================
// VIEW 8: AI RECOGNITION RESULTS BREAKDOWN GUI
// ==========================================
function renderResults() {
  const r = appState.detectResults || { confident: [], review: [], unknown: [], not_detected: [] };
  
  app.innerHTML = `
    <div class="app-shell">
      ${getTopbarHtml()}

      <div class="page">
        ${renderStepIndicator(2)}

        <div class="panel">
          <div class="panel-header" style="flex-wrap:wrap;">
            <div>
              <div class="eyebrow">Step 3 of 5</div>
              <h2>AI Recognition Analysis</h2>
            </div>
            <div class="quick-actions-bar">
              <button class="secondary-btn" id="takeSecondPhotoBtn">📸 Take 2nd Resolution Photo</button>
              <button class="primary-btn" id="proceedReviewBtn">Confirm & Verify Attendance &rarr;</button>
            </div>
          </div>

          <!-- Stats Overview -->
          <div class="kpi-row" style="margin-bottom:24px;">
            <div class="kpi">
              <small>🟢 Confident Matches</small>
              <strong>${r.confident?.length || 0}</strong>
            </div>
            <div class="kpi">
              <small>🟡 Needs Review</small>
              <strong>${r.review?.length || 0}</strong>
            </div>
            <div class="kpi">
              <small>⚪ Unknown Faces</small>
              <strong>${r.unknown?.length || 0}</strong>
            </div>
            <div class="kpi">
              <small>🔴 Not Detected</small>
              <strong>${r.not_detected?.length || 0}</strong>
            </div>
          </div>

          <!-- Categorized Results Grid -->
          <div class="results-grid">
            <!-- Confident -->
            <div class="result-card">
              <h4>🟢 Confidently Recognized (${r.confident?.length || 0})</h4>
              <div class="result-list">
                ${(r.confident || []).map(i => `
                  <div class="result-item">
                    <div>
                      <strong>${i.name}</strong>
                      <div style="font-size:0.8rem; color:var(--muted);">${i.student_number}</div>
                    </div>
                    <span class="badge success">${i.confidence}</span>
                  </div>
                `).join('') || '<div style="color:var(--muted); padding:12px;">No confident matches</div>'}
              </div>
            </div>

            <!-- Needs Review -->
            <div class="result-card">
              <h4>🟡 Needs Teacher Review (${r.review?.length || 0})</h4>
              <div class="result-list">
                ${(r.review || []).map(i => `
                  <div class="result-item">
                    <div>
                      <strong>${i.candidate_name || i.face_id}</strong>
                      <div style="font-size:0.8rem; color:var(--muted);">Candidate Match</div>
                    </div>
                    <span class="badge warning">${i.confidence}</span>
                  </div>
                `).join('') || '<div style="color:var(--muted); padding:12px;">None</div>'}
              </div>
            </div>

            <!-- Unknown -->
            <div class="result-card">
              <h4>⚪ Unknown Faces (${r.unknown?.length || 0})</h4>
              <div class="result-list">
                ${(r.unknown || []).map(i => `
                  <div class="result-item">
                    <strong>${i.face_id}</strong>
                    <span class="badge neutral">Unknown</span>
                  </div>
                `).join('') || '<div style="color:var(--muted); padding:12px;">None</div>'}
              </div>
            </div>

            <!-- Not Detected -->
            <div class="result-card">
              <h4>🔴 Absent / Not Detected (${r.not_detected?.length || 0})</h4>
              <div class="result-list">
                ${(r.not_detected || []).map(i => `
                  <div class="result-item">
                    <div>
                      <strong>${i.name}</strong>
                      <div style="font-size:0.8rem; color:var(--muted);">${i.student_number}</div>
                    </div>
                    <span class="badge danger">Not Detected</span>
                  </div>
                `).join('') || '<div style="color:var(--muted); padding:12px;">None</div>'}
              </div>
            </div>
          </div>

          <div class="action-row" style="margin-top:28px;">
            <button class="primary-btn" id="proceedReviewBtn2" style="padding:14px 28px; font-size:1.05rem;">
              ✅ Proceed to Final Review Table &rarr;
            </button>
            <button class="secondary-btn" data-nav="upload">🔄 Retake Photo</button>
          </div>
        </div>
      </div>
    </div>
  `;

  document.getElementById('takeSecondPhotoBtn').addEventListener('click', () => {
    navigateTo(() => { appState.currentView = 'second-photo'; renderSecondPhoto(); });
  });

  const goReview = () => navigateTo(() => { appState.currentView = 'final-review'; renderFinalReview(); });
  document.getElementById('proceedReviewBtn').addEventListener('click', goReview);
  document.getElementById('proceedReviewBtn2').addEventListener('click', goReview);

  postRenderSetup();
  animateCounters();
}

// ==========================================
// VIEW 9: RESOLUTION 2ND PHOTO STUDIO GUI
// ==========================================
function renderSecondPhoto() {
  app.innerHTML = `
    <div class="app-shell">
      ${getTopbarHtml()}

      <div class="page">
        ${renderStepIndicator(2)}

        <div class="panel">
          <div class="panel-header">
            <div>
              <div class="eyebrow">Multi-Photo Merge</div>
              <h2>Capture 2nd Resolution Photo</h2>
            </div>
            <button class="ghost-btn" data-nav="results">&larr; Back to Results</button>
          </div>

          <div class="summary-box" style="margin-bottom:20px;">
            <strong>💡 Multi-Photo Resolution Engine</strong>
            <span>Photo 2 will merge seamlessly with Photo 1 to resolve any uncertain or missed students.</span>
          </div>

          <div class="viewfinder-box">
            <video id="camera2Preview" autoplay playsinline style="display:none;"></video>
            <canvas id="camera2Canvas" style="display:none;"></canvas>
            <img id="captured2Image" style="display:none;" />
            <div id="camera2Prompt" style="padding:60px 20px; text-align:center; color:#fff;">
              <div style="font-size:3rem; margin-bottom:10px;">🧭</div>
              <h3>Capture Tighter Angle for Uncertain Faces</h3>
              <button class="primary-btn" id="openCamera2Btn" style="margin-top:14px;">📹 Open Camera</button>
            </div>
          </div>

          <div style="display:flex; justify-content:center; gap:12px; margin-top:16px;">
            <button class="primary-btn" id="capture2Btn" style="display:none;">📸 Snap Resolution Photo</button>
            <button class="secondary-btn" id="retake2Btn" style="display:none;">🔄 Retake</button>
          </div>

          <div class="action-row" style="margin-top:24px;">
            <button class="primary-btn" id="process2Btn" disabled>⚡ Merge & Update Results</button>
            <button class="ghost-btn" onclick="navigateTo(() => { appState.currentView = 'final-review'; renderFinalReview(); })">Skip to Review &rarr;</button>
          </div>
        </div>
      </div>
    </div>
  `;

  let file2 = null;
  const video = document.getElementById('camera2Preview');
  const canvas = document.getElementById('camera2Canvas');
  const img = document.getElementById('captured2Image');
  const prompt = document.getElementById('camera2Prompt');
  const processBtn = document.getElementById('process2Btn');
  const capture2Btn = document.getElementById('capture2Btn');
  const retake2Btn = document.getElementById('retake2Btn');

  document.getElementById('openCamera2Btn').addEventListener('click', async () => {
    try {
      const stream = await getCameraStream('environment', 1920, 1080);
      window.cameraStream = stream;
      video.srcObject = stream;
      video.style.display = 'block';
      prompt.style.display = 'none';
      capture2Btn.style.display = 'inline-flex';
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  capture2Btn.addEventListener('click', () => {
    canvas.width = video.videoWidth || 1280;
    canvas.height = video.videoHeight || 720;
    canvas.getContext('2d').drawImage(video, 0, 0);
    canvas.toBlob(blob => {
      file2 = new File([blob], 'classroom_photo2.jpg', { type: 'image/jpeg' });
      img.src = URL.createObjectURL(blob);
      img.style.display = 'block';
      video.style.display = 'none';
      capture2Btn.style.display = 'none';
      retake2Btn.style.display = 'inline-flex';
      processBtn.disabled = false;
      if (window.cameraStream) { window.cameraStream.getTracks().forEach(t => t.stop()); window.cameraStream = null; }
    }, 'image/jpeg', 0.95);
  });

  retake2Btn.addEventListener('click', () => {
    img.style.display = 'none';
    file2 = null;
    processBtn.disabled = true;
    retake2Btn.style.display = 'none';
    document.getElementById('openCamera2Btn').click();
  });

  processBtn.addEventListener('click', async () => {
    if (!file2) return;
    processBtn.disabled = true; processBtn.textContent = 'Merging Photos...';
    try {
      const formData = new FormData();
      formData.append('file', file2);
      const results = await api(`/attendance-sessions/${appState.sessionId}/photos`, { method: 'POST', body: formData, headers: {} });
      appState.detectResults = results;
      showToast('Second photo merged successfully!', 'success');
      navigateTo(() => { appState.currentView = 'final-review'; renderFinalReview(); });
    } catch (err) {
      showToast(err.message, 'error');
      processBtn.disabled = false; processBtn.textContent = '⚡ Merge & Update Results';
    }
  });

  postRenderSetup();
}

// ==========================================
// VIEW 10: FINAL ATTENDANCE REVIEW & CONFIRMATION GUI
// ==========================================
async function renderFinalReview() {
  let reviewData;
  try {
    reviewData = await api(`/attendance-sessions/${appState.sessionId}/review-table`);
  } catch (err) {
    showToast(err.message, 'error');
    return;
  }

  appState.reviewStudents = reviewData.students || [];
  const students = appState.reviewStudents;

  app.innerHTML = `
    <div class="app-shell">
      ${getTopbarHtml()}

      <div class="page">
        ${renderStepIndicator(3)}

        <div class="panel">
          <div class="panel-header" style="flex-wrap:wrap;">
            <div>
              <div class="eyebrow">${reviewData.class_name} • ${reviewData.subject_name} • ${reviewData.session_date}</div>
              <h2>Teacher Verification & Final Review</h2>
            </div>
            <div class="quick-actions-bar">
              <button class="primary-btn" id="finalizeBtn" style="padding:12px 24px; font-size:1rem;">
                🚀 Finalize Attendance
              </button>
            </div>
          </div>

          <!-- Dynamic Status KPI -->
          <div class="kpi-row" style="margin-bottom:20px;">
            <div class="kpi">
              <small>🟢 Present Count</small>
              <strong id="presentKpi">${students.filter(s => s.final_status === 'PRESENT').length}</strong>
            </div>
            <div class="kpi">
              <small>🔴 Absent Count</small>
              <strong id="absentKpi">${students.filter(s => s.final_status === 'ABSENT').length}</strong>
            </div>
            <div class="kpi">
              <small>👥 Total Roster</small>
              <strong>${students.length}</strong>
            </div>
          </div>

          <!-- Search & Status Filter -->
          <div style="display:flex; gap:12px; margin-bottom:16px; flex-wrap:wrap;">
            <input type="text" class="search-input" id="studentSearch" placeholder="Search student name or roll number..." style="flex:1; min-width:240px;" />
            <select id="statusFilter" style="padding:12px 16px; border-radius:14px; border:1.5px solid var(--line); background:var(--panel-alt); color:var(--text); font-weight:700;">
              <option value="All">All Statuses</option>
              <option value="PRESENT">Present Only</option>
              <option value="ABSENT">Absent Only</option>
            </select>
          </div>

          <!-- Verification Table -->
          <table class="mini-table">
            <thead>
              <tr>
                <th>Roll No</th>
                <th>Student Name</th>
                <th>AI Detection</th>
                <th>Final Status Decision</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody id="studentTableBody">
              ${students.map(s => `
                <tr data-student-row="${s.id}">
                  <td style="font-weight:800; color:var(--primary);">${s.student_number}</td>
                  <td style="font-weight:700;">${s.name}</td>
                  <td>
                    <span class="status-pill ${s.recognition === 'Present' ? 'present' : s.recognition === 'Review' ? 'review pulse' : 'absent'}">
                      ${s.recognition}
                    </span>
                  </td>
                  <td>
                    <select class="final-status-select" data-student-id="${s.id}" data-status="${s.final_status}">
                      <option value="PRESENT" ${s.final_status === 'PRESENT' ? 'selected' : ''}>Present</option>
                      <option value="ABSENT" ${s.final_status === 'ABSENT' ? 'selected' : ''}>Absent</option>
                    </select>
                  </td>
                  <td>
                    <button class="ghost-btn confirm-action-btn" data-student-id="${s.id}">Confirm</button>
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>

          <div class="action-row" style="margin-top:28px;">
            <button class="primary-btn" id="finalizeBtn2" style="padding:14px 32px; font-size:1.05rem;">
              🚀 Finalize Attendance &rarr;
            </button>
            <button class="ghost-btn" data-nav="dashboard">Cancel</button>
          </div>
        </div>
      </div>
    </div>
  `;

  // Search & Filter
  const filterTable = () => {
    const term = document.getElementById('studentSearch').value.toLowerCase().trim();
    const statusVal = document.getElementById('statusFilter').value;
    document.querySelectorAll('tr[data-student-row]').forEach(row => {
      const s = students.find(st => st.id === row.dataset.studentRow);
      if (!s) return;
      const matchText = s.name.toLowerCase().includes(term) || s.student_number.toLowerCase().includes(term);
      const matchStatus = statusVal === 'All' || s.final_status === statusVal;
      row.style.display = (matchText && matchStatus) ? '' : 'none';
    });
  };
  document.getElementById('studentSearch').addEventListener('input', filterTable);
  document.getElementById('statusFilter').addEventListener('change', filterTable);

  // Status Change Overrides
  document.querySelectorAll('.final-status-select').forEach(select => {
    select.addEventListener('change', e => {
      const s = students.find(st => st.id === e.target.dataset.studentId);
      if (s) s.final_status = e.target.value;
      e.target.setAttribute('data-status', e.target.value);
      
      // Update KPIs
      document.getElementById('presentKpi').textContent = students.filter(st => st.final_status === 'PRESENT').length;
      document.getElementById('absentKpi').textContent = students.filter(st => st.final_status === 'ABSENT').length;
    });
  });

  // Confirm Single Row
  document.querySelectorAll('.confirm-action-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const s = students.find(st => st.id === btn.dataset.studentId);
      if (s) {
        btn.parentElement.innerHTML = '<span class="confirm-check">✓ Confirmed</span>';
        showToast(`${s.name} marked as ${s.final_status}`, 'success');
      }
    });
  });

  // Finalize Submission
  const finalizeAttendance = async () => {
    const finalBtns = [document.getElementById('finalizeBtn'), document.getElementById('finalizeBtn2')];
    finalBtns.forEach(b => { if (b) { b.disabled = true; b.textContent = 'Saving Final Records...'; } });

    try {
      const updates = students.map(s => ({ student_id: s.id, final_status: s.final_status }));
      const result = await api(`/attendance-sessions/${appState.sessionId}/finalize`, {
        method: 'POST',
        body: JSON.stringify({ updates })
      });

      // Show Confetti Celebration
      const overlay = document.createElement('div');
      overlay.className = 'celebration';
      overlay.innerHTML = '<div style="font-size:5rem; animation:popIn 0.5s ease forwards;">🎉</div>';
      document.body.appendChild(overlay);

      showToast(`Attendance Finalized! ${result.present_count} Present, ${result.absent_count} Absent.`, 'success');
      appState.sessionStartTime = null;
      appState.sessionId = null;

      setTimeout(() => {
        overlay.remove();
        navigateTo(() => { appState.currentView = 'history'; renderHistory(); });
      }, 1200);
    } catch (err) {
      showToast('Finalization error: ' + err.message, 'error');
      finalBtns.forEach(b => { if (b) { b.disabled = false; b.textContent = '🚀 Finalize Attendance'; } });
    }
  };

  document.getElementById('finalizeBtn').addEventListener('click', finalizeAttendance);
  document.getElementById('finalizeBtn2').addEventListener('click', finalizeAttendance);

  postRenderSetup();
  animateCounters();
}

// ==========================================
// VIEW 11: ATTENDANCE HISTORY & REPORTS GUI
// ==========================================
async function renderHistory() {
  try { appState.classes = await api('/classes'); } catch { appState.classes = []; }

  let allHistory = [];
  for (const c of appState.classes) {
    try {
      const h = await api(`/history/classes/${c.id}`);
      allHistory.push(...h);
    } catch {}
  }
  allHistory.sort((a, b) => b.date.localeCompare(a.date));
  appState.attendanceHistory = allHistory;

  app.innerHTML = `
    <div class="app-shell">
      ${getTopbarHtml()}

      <div class="page">
        <div class="panel">
          <div class="panel-header" style="flex-wrap:wrap;">
            <div>
              <div class="eyebrow">Audited Attendance Logs</div>
              <h2>Attendance Reports & Analytics</h2>
            </div>
            <div class="quick-actions-bar">
              <button class="secondary-btn" onclick="exportHistoryCsv()">📥 Export CSV</button>
              <button class="secondary-btn" onclick="window.print()">🖨️ Print Report</button>
            </div>
          </div>

          ${allHistory.length === 0 ? `
            <div style="padding:60px 24px; text-align:center; color:var(--muted);">
              <div style="font-size:3rem; margin-bottom:12px;">📅</div>
              <h3>No Attendance Records Found</h3>
              <p>Start a session to generate attendance logs.</p>
              <button class="primary-btn" data-nav="class-select" style="margin-top:14px;">📸 Take Attendance Now</button>
            </div>
          ` : `
            <table class="mini-table">
              <thead>
                <tr>
                  <th>Session Date</th>
                  <th>Class</th>
                  <th>Subject</th>
                  <th>Attendance Metric</th>
                  <th>Rate</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                ${allHistory.map(item => {
                  const total = (item.present || 0) + (item.absent || 0);
                  const rate = total > 0 ? Math.round((item.present / total) * 100) : 0;
                  return `
                    <tr>
                      <td style="font-weight:800; color:var(--primary);">${item.date}</td>
                      <td style="font-weight:700;">${item.class_name}</td>
                      <td>${item.subject}</td>
                      <td style="font-weight:700;">
                        <span style="color:var(--success);">${item.present} Present</span> / 
                        <span style="color:var(--danger);">${item.absent} Absent</span>
                      </td>
                      <td style="min-width:140px;">
                        <div style="display:flex; align-items:center; gap:8px;">
                          <div class="progress-bar-container" style="flex:1;">
                            <div class="progress-bar-fill" style="width:${rate}%; background:${rate >= 75 ? 'var(--success)' : rate >= 50 ? 'var(--warning)' : 'var(--danger)'};"></div>
                          </div>
                          <span style="font-size:0.85rem; font-weight:800;">${rate}%</span>
                        </div>
                      </td>
                      <td>
                        <span class="badge ${item.status === 'FINALIZED' ? 'success' : 'warning'}">${item.status}</span>
                      </td>
                      <td>
                        <button class="icon-btn" onclick="openSessionDetailModal('${item.session_id}')">🔍 Details</button>
                      </td>
                    </tr>
                  `;
                }).join('')}
              </tbody>
            </table>
          `}
        </div>
      </div>
    </div>
  `;

  postRenderSetup();
}

window.exportHistoryCsv = () => {
  if (!appState.attendanceHistory?.length) {
    showToast('No history records to export', 'info');
    return;
  }
  let csv = 'Date,Class,Subject,Present,Absent,Status\n';
  appState.attendanceHistory.forEach(item => {
    csv += `"${item.date}","${item.class_name}","${item.subject}",${item.present},${item.absent},"${item.status}"\n`;
  });
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `facemark_attendance_${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
  showToast('Attendance report exported to CSV', 'success');
};

window.openSessionDetailModal = async (sessionId) => {
  try {
    const data = await api(`/attendance-sessions/${sessionId}/review-table`);
    const students = data.students || [];
    const html = `
      <div style="margin-bottom:14px;">
        <div><strong>Class:</strong> ${data.class_name} • <strong>Subject:</strong> ${data.subject_name}</div>
        <div><strong>Date:</strong> ${data.session_date}</div>
      </div>
      <table class="mini-table" style="margin-top:10px;">
        <thead>
          <tr>
            <th>Roll No</th>
            <th>Name</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          ${students.map(s => `
            <tr>
              <td style="font-weight:800; color:var(--primary);">${s.student_number}</td>
              <td style="font-weight:700;">${s.name}</td>
              <td>
                <span class="badge ${s.final_status === 'PRESENT' ? 'success' : 'danger'}">
                  ${s.final_status}
                </span>
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
    openModal(`Session Record • ${data.class_name}`, html);
  } catch (err) {
    showToast('Could not load session details: ' + err.message, 'error');
  }
};

// ==========================================
// MODAL DIALOGS (ADD CLASS, SUBJECT, STUDENT, ENROLL)
// ==========================================
window.openAddClassModal = () => {
  const subjectsHtml = appState.subjects.map(s => `<option value="${s.name}">${s.name} (${s.code})</option>`).join('');
  const html = `
    <form id="modalAddClassForm" class="form-grid" style="margin-top:0;">
      <div class="input-wrap">
        <label for="modalClassName">Class Name</label>
        <input id="modalClassName" type="text" placeholder="e.g. CSE-A" required />
      </div>
      <div class="input-wrap">
        <label for="modalClassSubject">Assign Subject</label>
        <select id="modalClassSubject">
          <option value="General">General (Default)</option>
          ${subjectsHtml}
        </select>
      </div>
      <div class="input-wrap">
        <label for="modalClassSemester">Semester</label>
        <input id="modalClassSemester" type="number" value="5" min="1" max="10" required />
      </div>
      <div style="display:flex; justify-content:flex-end; gap:10px; margin-top:10px;">
        <button type="button" class="ghost-btn" onclick="closeModal()">Cancel</button>
        <button type="submit" class="primary-btn" id="modalSaveClassBtn">Save Class</button>
      </div>
    </form>
  `;

  openModal('➕ Create New Class', html, (modal) => {
    modal.querySelector('#modalAddClassForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = modal.querySelector('#modalSaveClassBtn');
      btn.textContent = 'Saving...'; btn.disabled = true;

      const name = modal.querySelector('#modalClassName').value.trim();
      const subject = modal.querySelector('#modalClassSubject').value;
      const semester = parseInt(modal.querySelector('#modalClassSemester').value, 10);

      try {
        await api('/classes', {
          method: 'POST',
          body: JSON.stringify({ name, subject, semester, academic_year: '2026-2027' })
        });
        showToast(`Class "${name}" created successfully!`, 'success');
        closeModal();
        if (appState.currentView === 'classes-hub') renderClassesHub();
        else renderDashboard();
      } catch (err) {
        showToast(err.message, 'error');
        btn.textContent = 'Save Class'; btn.disabled = false;
      }
    });
  });
};

window.openAddSubjectModal = () => {
  const html = `
    <form id="modalAddSubjectForm" class="form-grid" style="margin-top:0;">
      <div class="input-wrap">
        <label for="modalSubjectName">Subject Name</label>
        <input id="modalSubjectName" type="text" placeholder="e.g. Operating Systems" required />
      </div>
      <div class="input-wrap">
        <label for="modalSubjectCode">Subject Code (Optional)</label>
        <input id="modalSubjectCode" type="text" placeholder="e.g. CS501" />
      </div>
      <div style="display:flex; justify-content:flex-end; gap:10px; margin-top:10px;">
        <button type="button" class="ghost-btn" onclick="closeModal()">Cancel</button>
        <button type="submit" class="primary-btn" id="modalSaveSubjectBtn">Save Subject</button>
      </div>
    </form>
  `;

  openModal('📚 Create New Subject', html, (modal) => {
    modal.querySelector('#modalAddSubjectForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = modal.querySelector('#modalSaveSubjectBtn');
      btn.textContent = 'Saving...'; btn.disabled = true;

      const name = modal.querySelector('#modalSubjectName').value.trim();
      const code = modal.querySelector('#modalSubjectCode').value.trim() || undefined;

      try {
        await api('/subjects', {
          method: 'POST',
          body: JSON.stringify({ name, code })
        });
        showToast(`Subject "${name}" registered!`, 'success');
        closeModal();
        if (appState.currentView === 'classes-hub') renderClassesHub();
        else renderDashboard();
      } catch (err) {
        showToast(err.message, 'error');
        btn.textContent = 'Save Subject'; btn.disabled = false;
      }
    });
  });
};

window.openAddStudentModal = () => {
  const classOptions = appState.classes.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
  const html = `
    <form id="modalAddStudentForm" class="form-grid" style="margin-top:0;">
      <div class="input-wrap">
        <label for="modalStudentName">Full Student Name</label>
        <input id="modalStudentName" type="text" placeholder="e.g. Priya Sharma" required />
      </div>
      <div class="input-wrap">
        <label for="modalStudentNumber">Registration / Roll Number</label>
        <input id="modalStudentNumber" type="text" placeholder="e.g. 21BCSE042" required />
      </div>
      <div class="input-wrap">
        <label for="modalStudentEmail">Email Address (Optional)</label>
        <input id="modalStudentEmail" type="email" placeholder="priya@student.edu" />
      </div>
      <div class="input-wrap">
        <label for="modalStudentClass">Assign to Class (Optional)</label>
        <select id="modalStudentClass">
          <option value="">-- No Class Selected --</option>
          ${classOptions}
        </select>
      </div>
      <div style="display:flex; justify-content:flex-end; gap:10px; margin-top:10px;">
        <button type="button" class="ghost-btn" onclick="closeModal()">Cancel</button>
        <button type="submit" class="primary-btn" id="modalSaveStudentBtn">Register Student</button>
      </div>
    </form>
  `;

  openModal('👤 Register New Student', html, (modal) => {
    modal.querySelector('#modalAddStudentForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = modal.querySelector('#modalSaveStudentBtn');
      btn.textContent = 'Registering...'; btn.disabled = true;

      const full_name = modal.querySelector('#modalStudentName').value.trim();
      const student_number = modal.querySelector('#modalStudentNumber').value.trim();
      const email = modal.querySelector('#modalStudentEmail').value.trim() || undefined;
      const class_id = modal.querySelector('#modalStudentClass').value || undefined;

      try {
        await api('/students', {
          method: 'POST',
          body: JSON.stringify({ full_name, student_number, email, class_id })
        });
        showToast(`Student "${full_name}" registered!`, 'success');
        closeModal();
        if (appState.currentView === 'students-hub') renderStudentsHub();
        else renderDashboard();
      } catch (err) {
        showToast(err.message, 'error');
        btn.textContent = 'Register Student'; btn.disabled = false;
      }
    });
  });
};

window.openEnrollFaceModal = (studentId, studentName, studentNumber) => {
  const html = `
    <div style="text-align:center;">
      <p style="color:var(--muted); margin-bottom:16px;">
        Position the student inside the oval frame and click <strong>Capture Face</strong>.
      </p>

      <div class="viewfinder-box" style="max-width:320px; aspect-ratio:1; margin-bottom:16px;">
        <video id="modalEnrollVideo" autoplay playsinline style="display:none; width:100%; height:100%; object-fit:cover;"></video>
        <canvas id="modalEnrollCanvas" style="display:none;"></canvas>
        <img id="modalEnrollImg" style="display:none; width:100%; height:100%; object-fit:cover;" />
        
        <div id="modalEnrollPrompt" style="padding:48px 16px; color:#fff;">
          <div style="font-size:2.5rem; margin-bottom:8px;">📹</div>
          <button class="primary-btn" id="modalStartCamBtn">Start Webcam</button>
        </div>
      </div>

      <div style="display:flex; justify-content:center; gap:10px; margin-bottom:14px;">
        <button class="primary-btn" id="modalSnapBtn" style="display:none;">📸 Capture Face</button>
        <button class="secondary-btn" id="modalRetakeBtn" style="display:none;">🔄 Retake</button>
        <button class="primary-btn" id="modalUploadEmbeddingBtn" style="display:none;">💾 Save 512-dim Vector</button>
      </div>

      <div style="color:var(--muted); font-size:0.85rem; font-weight:700;">
        — OR upload a portrait photo file —
        <input type="file" id="modalEnrollFileInput" accept="image/*" style="margin-top:8px; display:block; width:100%;" />
      </div>
    </div>
  `;

  openModal(`📸 Biometric Face Enrollment • ${studentName}`, html, (modal) => {
    const video = modal.querySelector('#modalEnrollVideo');
    const canvas = modal.querySelector('#modalEnrollCanvas');
    const img = modal.querySelector('#modalEnrollImg');
    const prompt = modal.querySelector('#modalEnrollPrompt');
    const startCamBtn = modal.querySelector('#modalStartCamBtn');
    const snapBtn = modal.querySelector('#modalSnapBtn');
    const retakeBtn = modal.querySelector('#modalRetakeBtn');
    const uploadBtn = modal.querySelector('#modalUploadEmbeddingBtn');
    const fileInput = modal.querySelector('#modalEnrollFileInput');

    let blobData = null;

    startCamBtn.addEventListener('click', async () => {
      try {
        const stream = await getCameraStream('user', 480, 480);
        window.cameraStream = stream;
        video.srcObject = stream;
        video.style.display = 'block';
        prompt.style.display = 'none';
        snapBtn.style.display = 'inline-flex';
      } catch (err) {
        showToast(err.message, 'error');
      }
    });

    snapBtn.addEventListener('click', () => {
      canvas.width = 480; canvas.height = 480;
      canvas.getContext('2d').drawImage(video, 0, 0, 480, 480);
      canvas.toBlob(blob => {
        blobData = blob;
        img.src = URL.createObjectURL(blob);
        img.style.display = 'block';
        video.style.display = 'none';
        snapBtn.style.display = 'none';
        retakeBtn.style.display = 'inline-flex';
        uploadBtn.style.display = 'inline-flex';
        if (window.cameraStream) { window.cameraStream.getTracks().forEach(t => t.stop()); window.cameraStream = null; }
      }, 'image/jpeg', 0.95);
    });

    retakeBtn.addEventListener('click', () => {
      img.style.display = 'none';
      blobData = null;
      retakeBtn.style.display = 'none';
      uploadBtn.style.display = 'none';
      startCamBtn.click();
    });

    fileInput.addEventListener('change', (e) => {
      if (e.target.files?.length) {
        blobData = e.target.files[0];
        img.src = URL.createObjectURL(blobData);
        img.style.display = 'block';
        prompt.style.display = 'none';
        video.style.display = 'none';
        snapBtn.style.display = 'none';
        retakeBtn.style.display = 'inline-flex';
        uploadBtn.style.display = 'inline-flex';
        if (window.cameraStream) { window.cameraStream.getTracks().forEach(t => t.stop()); window.cameraStream = null; }
      }
    });

    uploadBtn.addEventListener('click', async () => {
      if (!blobData) return;
      uploadBtn.disabled = true; uploadBtn.textContent = 'Extracting Vector...';
      try {
        const formData = new FormData();
        formData.append('file', blobData);
        await api(`/students/${studentId}/face-enrollment`, { method: 'POST', body: formData, headers: {} });
        showToast(`Face biometric enrolled for ${studentName}!`, 'success');
        closeModal();
        if (appState.currentView === 'students-hub') renderStudentsHub();
        else if (appState.currentView === 'manage-roster') renderRosterManagement();
      } catch (err) {
        showToast('Enrollment failed: ' + err.message, 'error');
        uploadBtn.disabled = false; uploadBtn.textContent = '💾 Save 512-dim Vector';
      }
    });
  });
};

// ==========================================
// BOOTSTRAP APPLICATION
// ==========================================
initTheme();
if (authToken) {
  api('/auth/me').then(user => {
    currentUser = user;
    appState.currentView = 'dashboard';
    renderDashboard();
  }).catch(() => {
    authToken = null;
    localStorage.removeItem('facemark-token');
    renderLogin();
  });
} else {
  renderLogin();
}
