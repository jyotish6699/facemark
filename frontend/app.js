const app = document.getElementById('app');

const demoState = {
  currentView: 'login',
  selectedClass: null,
  attendanceSession: null,
  sessionStartTime: null,
  attendanceHistory: [
    { date: '2026-08-25', className: 'CSE-A', subject: 'Operating Systems', present: 28, absent: 4, status: 'Finalized' },
    { date: '2026-08-22', className: 'CSE-A', subject: 'DBMS', present: 26, absent: 6, status: 'Finalized' },
    { date: '2026-08-18', className: 'CSE-A', subject: 'AI', present: 29, absent: 3, status: 'Finalized' }
  ],
  classes: [
    { id: 'cse-a', name: 'CSE-A', subject: 'Operating Systems', count: 32, teacher: 'Ms. Priya Nair' },
    { id: 'cse-b', name: 'CSE-B', subject: 'Data Structures', count: 34, teacher: 'Mr. Sanjay Shah' },
    { id: 'it-b', name: 'IT-B', subject: 'Computer Networks', count: 28, teacher: 'Dr. Ananya Singh' }
  ],
  students: [
    { id: 1, name: 'Rahul Verma', recognition: 'Present', finalStatus: 'Present', confidence: '98%' },
    { id: 2, name: 'Aman Shah', recognition: 'Present', finalStatus: 'Present', confidence: '96%' },
    { id: 3, name: 'Priya Nair', recognition: 'Review', finalStatus: 'Present', confidence: '67%' },
    { id: 4, name: 'Karan Mehta', recognition: 'Unknown', finalStatus: 'Review', confidence: 'N/A' },
    { id: 5, name: 'Sneha Iyer', recognition: 'Not detected', finalStatus: 'Absent', confidence: 'N/A' },
    { id: 6, name: 'Deepak Roy', recognition: 'Present', finalStatus: 'Present', confidence: '97%' },
    { id: 7, name: 'Meera Joshi', recognition: 'Present', finalStatus: 'Present', confidence: '95%' },
    { id: 8, name: 'Rohit Kumar', recognition: 'Review', finalStatus: 'Present', confidence: '64%' }
  ],
  detectResults: {
    confident: [
      { name: 'Rahul Verma', confidence: '98%' },
      { name: 'Aman Shah', confidence: '96%' },
      { name: 'Deepak Roy', confidence: '97%' },
      { name: 'Meera Joshi', confidence: '95%' }
    ],
    review: [
      { name: 'Face #12', candidate: 'Priya Nair', confidence: '67%' },
      { name: 'Face #18', candidate: 'Rohit Kumar', confidence: '64%' }
    ],
    unknown: [
      { name: 'Face #23', candidate: 'Unknown' }
    ],
    notDetected: [
      { name: 'Sneha Iyer' },
      { name: 'Student 42' }
    ]
  }
};

// ==========================================
// UTILITIES & MICRO-INTERACTIONS
// ==========================================

function navigateTo(renderFn) {
  const currentShell = document.querySelector('.app-shell');
  if (currentShell) {
    currentShell.style.opacity = '0';
    currentShell.style.transition = 'opacity 0.2s ease';
  }
  
  setTimeout(() => {
    if (window.sessionTimerInterval) {
      clearInterval(window.sessionTimerInterval);
      window.sessionTimerInterval = null;
    }
    
    renderFn();
    
    const newShell = document.querySelector('.app-shell');
    if (newShell) {
      newShell.classList.add('page-transition-enter');
    }
  }, 200);
}

function triggerStaggerAnimations() {
  const elements = document.querySelectorAll('.class-card, .result-card, .kpi, .list-item, .history-item, .result-item');
  elements.forEach((el, index) => {
    el.classList.add('animate-in');
    el.style.setProperty('--delay', `${(index + 1) * 0.05}s`);
  });
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
    <span class="toast-icon">${icon}</span>
    <span class="toast-message">${message}</span>
    <button class="toast-close">&times;</button>
  `;

  container.appendChild(toast);

  const closeBtn = toast.querySelector('.toast-close');
  
  const dismiss = () => {
    toast.classList.replace('toast-enter', 'toast-exit');
    setTimeout(() => {
      if (toast.parentElement) toast.remove();
    }, 300);
  };

  closeBtn.addEventListener('click', dismiss);
  setTimeout(dismiss, 3500);
}

function initRipples() {
  const buttons = document.querySelectorAll('.primary-btn, .secondary-btn, .ghost-btn');
  buttons.forEach(btn => {
    btn.addEventListener('click', function(e) {
      const rect = this.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      
      const ripple = document.createElement('span');
      ripple.className = 'ripple-effect';
      ripple.style.left = `${x}px`;
      ripple.style.top = `${y}px`;
      
      this.appendChild(ripple);
      
      setTimeout(() => {
        ripple.remove();
      }, 600);
    });
  });
}

function showFilePreview(file, uploadZone) {
  const reader = new FileReader();
  reader.onload = (e) => {
    let previewContainer = uploadZone.querySelector('.file-preview');
    if (!previewContainer) {
      previewContainer = document.createElement('div');
      previewContainer.className = 'file-preview';
      uploadZone.appendChild(previewContainer);
    }
    previewContainer.innerHTML = `
      <img src="${e.target.result}" alt="Preview" style="max-width: 100%; max-height: 200px; border-radius: 8px; margin-top: 12px; object-fit: cover;" />
      <div style="margin-top: 8px; font-size: 0.85rem; color: var(--muted);">${file.name}</div>
    `;
    uploadZone.classList.add('has-file');
  };
  reader.readAsDataURL(file);
}

function initDragAndDrop(uploadZoneId, inputId) {
  const uploadZone = document.getElementById(uploadZoneId);
  const input = document.getElementById(inputId);
  if (!uploadZone || !input) return;

  uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadZone.classList.add('drag-over');
  });

  uploadZone.addEventListener('dragleave', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('drag-over');
  });

  uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('drag-over');
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      input.files = e.dataTransfer.files;
      showFilePreview(e.dataTransfer.files[0], uploadZone);
    }
  });

  input.addEventListener('change', (e) => {
    if (e.target.files && e.target.files.length > 0) {
      showFilePreview(e.target.files[0], uploadZone);
    }
  });
}

function initTheme() {
  const savedTheme = localStorage.getItem('facemark-theme');
  const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
    document.documentElement.setAttribute('data-theme', 'dark');
  } else {
    document.documentElement.setAttribute('data-theme', 'light');
  }
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme');
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('facemark-theme', next);
  updateThemeToggleIcon();
}

function updateThemeToggleIcon() {
  const btn = document.querySelector('.theme-toggle');
  if (btn) {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    btn.textContent = isDark ? '☀️' : '🌙';
  }
}

function animateCounters() {
  const counters = document.querySelectorAll('.kpi strong');
  counters.forEach(counter => {
    const text = counter.innerText;
    const hasPercent = text.includes('%');
    const target = parseInt(text.replace(/\\D/g, ''), 10);
    if (isNaN(target)) return;

    let start = 0;
    const duration = 800;
    const startTime = performance.now();

    const update = (currentTime) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      
      const easeOutQuart = 1 - Math.pow(1 - progress, 4);
      const current = Math.floor(easeOutQuart * target);
      
      counter.innerText = current + (hasPercent ? '%' : '');

      if (progress < 1) {
        requestAnimationFrame(update);
      } else {
        counter.innerText = text; // ensure final exact match
      }
    };
    requestAnimationFrame(update);
  });
}

function initScrollToTop() {
  if (!document.querySelector('.scroll-top-btn')) {
    const btn = document.createElement('button');
    btn.className = 'scroll-top-btn';
    btn.innerHTML = '↑';
    btn.title = 'Scroll to top';
    document.body.appendChild(btn);

    btn.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  const btn = document.querySelector('.scroll-top-btn');
  const scrollHandler = () => {
    if (window.scrollY > 300) btn.classList.add('visible');
    else btn.classList.remove('visible');
  };
  window.removeEventListener('scroll', window.__scrollHandlerTop);
  window.__scrollHandlerTop = scrollHandler;
  window.addEventListener('scroll', scrollHandler);
}

function initTopbarScroll() {
  const scrollHandler = () => {
    const topbar = document.querySelector('.topbar');
    if (topbar) {
      if (window.scrollY > 50) topbar.classList.add('scrolled');
      else topbar.classList.remove('scrolled');
    }
  };
  window.removeEventListener('scroll', window.__scrollHandlerTopbar);
  window.__scrollHandlerTopbar = scrollHandler;
  window.addEventListener('scroll', scrollHandler);
}

function initKeyboardShortcuts() {
  if (window.__shortcutsBound) return;
  window.__shortcutsBound = true;
  
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      if (demoState.currentView !== 'login' && demoState.currentView !== 'dashboard') {
        navigateTo(() => {
          demoState.currentView = 'dashboard';
          renderDashboard();
        });
      }
    } else if (e.key === 'Enter') {
      const activeEl = document.activeElement;
      if (activeEl && (activeEl.tagName === 'INPUT' || activeEl.tagName === 'TEXTAREA' || activeEl.tagName === 'SELECT')) {
        return; // Don't intercept enter inside inputs
      }
      const primaryBtn = document.querySelector('.primary-btn');
      if (primaryBtn) primaryBtn.click();
    }
  });
}

function renderStepIndicator(currentStepIndex) {
  const steps = ['Select Class', 'Setup', 'Upload', 'Results', 'Review', 'Finalize'];
  
  let html = '<div class="step-indicator" style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px; padding: 12px 16px; background: var(--panel-alt); border-radius: 14px; border: 1px solid var(--line);">';
  
  steps.forEach((step, i) => {
    const isCompleted = i < currentStepIndex;
    const isActive = i === currentStepIndex;
    const classes = `step ${isActive ? 'active' : ''} ${isCompleted ? 'completed' : ''}`;
    
    html += `
      <div class="${classes}" style="display: flex; flex-direction: column; align-items: center; gap: 6px; z-index: 1;">
        <div style="width: 28px; height: 28px; border-radius: 50%; background: ${isCompleted ? 'var(--success)' : isActive ? 'var(--primary)' : 'var(--line)'}; color: ${isCompleted || isActive ? '#ffffff' : 'var(--muted)'}; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 800; box-shadow: ${isActive ? '0 0 0 3px var(--primary-soft)' : 'none'};">
          ${isCompleted ? '✓' : i + 1}
        </div>
        <span style="font-size: 12px; color: ${isActive ? 'var(--text)' : isCompleted ? 'var(--success)' : 'var(--muted)'}; font-weight: ${isActive || isCompleted ? '700' : '600'}; letter-spacing: 0.02em;">${step}</span>
      </div>
    `;

    if (i < steps.length - 1) {
      html += `<div class="step-line ${isCompleted ? 'completed' : ''}" style="flex: 1; height: 3px; background: ${isCompleted ? 'var(--success)' : 'var(--line)'}; margin: -20px 8px 0 8px; border-radius: 2px;"></div>`;
    }
  });

  html += '</div>';
  return html;
}

function getTopbarHtml(title) {
  const isSessionActive = ['session', 'upload', 'results', 'second-photo', 'final-review'].includes(demoState.currentView);
  
  return `
    <header class="topbar">
      <div class="brand">
        <div class="brand-mark">F</div>
        <span>FaceMark</span>
      </div>
      <div style="display:flex; align-items:center; gap: 16px;">
        ${isSessionActive ? '<div class="session-timer" style="font-family: monospace; font-weight: bold; color: var(--primary);">00:00</div>' : ''}
        <div class="user-badge">${title}</div>
        <button class="theme-toggle" title="Toggle dark mode" style="background:none; border:none; cursor:pointer; font-size:1.2rem;">🌙</button>
        <button class="logout-btn ghost-btn" style="padding: 4px 8px; font-size: 12px;">Logout</button>
      </div>
    </header>
  `;
}

function postRenderSetup() {
  initRipples();
  triggerStaggerAnimations();
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
      showToast('Logged out successfully', 'success');
      setTimeout(() => {
        navigateTo(() => {
          demoState.currentView = 'login';
          renderLogin();
        });
      }, 500);
    });
  }

  const navPills = document.querySelectorAll('.nav-pills button');
  navPills.forEach(btn => {
    if (btn.dataset.nav === demoState.currentView) {
      btn.classList.add('active');
    }
  });

  const isSessionActive = ['session', 'upload', 'results', 'second-photo', 'final-review'].includes(demoState.currentView);
  if (isSessionActive && demoState.sessionStartTime) {
    const timerEl = document.querySelector('.session-timer');
    if (timerEl) {
      const updateTimer = () => {
        const diff = Math.floor((Date.now() - demoState.sessionStartTime) / 1000);
        const m = String(Math.floor(diff / 60)).padStart(2, '0');
        const s = String(diff % 60).padStart(2, '0');
        timerEl.textContent = `${m}:${s}`;
      };
      updateTimer();
      window.sessionTimerInterval = setInterval(updateTimer, 1000);
    }
  }
}

// ==========================================
// VIEWS
// ==========================================

function renderLogin() {
  app.innerHTML = `
    <div class="app-shell">
      <div class="auth-screen">
        <div class="auth-card">
          <div class="eyebrow">FaceMark</div>
          <h1>Classroom attendance, simplified.</h1>
          <p class="subtitle">Log in to review recognition, resolve uncertain faces, and finalize class attendance quickly.</p>

          <form id="loginForm" class="form-grid">
            <div class="input-wrap">
              <label for="email">Email</label>
              <input id="email" type="email" value="teacher@facemark.demo" required />
            </div>

            <div class="input-wrap">
              <label for="password">Password</label>
              <input id="password" type="password" value="demo123" required />
            </div>

            <button type="submit" class="primary-btn">Login</button>
            <div id="loginAlert" class="alert error"></div>
          </form>
          <div style="margin-top:24px; text-align:center; font-size:0.92rem; font-weight:700; color:var(--muted);">
             Press <strong>Enter</strong> to login quickly.
          </div>
        </div>
      </div>
    </div>
  `;

  const form = document.getElementById('loginForm');
  form.addEventListener('submit', (event) => {
    event.preventDefault();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value.trim();
    const alertBox = document.getElementById('loginAlert');

    if (!email || !password) {
      alertBox.textContent = 'Please enter both email and password.';
      alertBox.classList.add('show');
      return;
    }

    if (email.includes('@') && password.length >= 4) {
      showToast('Logged in successfully', 'success');
      navigateTo(() => {
        demoState.currentView = 'dashboard';
        renderDashboard();
      });
    } else {
      alertBox.textContent = 'Login failed. Please use valid teacher credentials.';
      alertBox.classList.add('show');
    }
  });
  
  postRenderSetup();
}

function renderDashboard() {
  const activeClass = demoState.selectedClass || demoState.classes[0];

  app.innerHTML = `
    <div class="app-shell">
      ${getTopbarHtml('Teacher • Priya Nair')}

      <div class="page">
        <div class="panel">
          <div class="panel-header">
            <div>
              <div class="eyebrow">Teacher Dashboard</div>
              <h2>Attendance overview</h2>
            </div>
            <div class="nav-pills">
              <button type="button" data-nav="dashboard">Dashboard</button>
              <button type="button" data-nav="history">History</button>
              <button type="button" class="primary-btn" data-nav="class-select">Start Attendance</button>
            </div>
          </div>

          <div class="kpi-row">
            <div class="kpi">
              <small>Assigned classes</small>
              <strong>3</strong>
            </div>
            <div class="kpi">
              <small>Sessions this month</small>
              <strong>12</strong>
            </div>
            <div class="kpi">
              <small>Average attendance</small>
              <strong>91%</strong>
            </div>
          </div>
        </div>

        <div class="dashboard-grid">
          <div class="panel">
            <div class="panel-header">
              <h3>Assigned classes</h3>
              <button class="secondary-btn tooltip" data-nav="class-select" data-tip="Start a new session">Select class</button>
            </div>

            <div class="class-grid">
              ${demoState.classes.map((cls) => `
                <div class="class-card ${cls.id === activeClass.id ? 'selected' : ''}" data-class-id="${cls.id}">
                  <div class="eyebrow">${cls.subject}</div>
                  <h3>${cls.name}</h3>
                  <div class="stats">
                    <span>${cls.count} students</span>
                    <span>${cls.teacher}</span>
                  </div>
                </div>
              `).join('')}
            </div>
          </div>

          <div class="panel">
            <div class="panel-header">
              <h3>Recent sessions</h3>
            </div>
            <div class="list-stack">
              ${demoState.attendanceHistory.slice(0, 5).map((item) => `
                <div class="list-item">
                  <div class="meta">
                    <strong>${item.className}</strong>
                    <span>${item.subject}</span>
                    <small>${item.date}</small>
                  </div>
                  <span class="badge success">${item.present} present</span>
                </div>
              `).join('')}
            </div>
          </div>
        </div>
      </div>
    </div>
  `;

  bindNavigation();

  document.querySelectorAll('[data-class-id]').forEach((card) => {
    card.addEventListener('click', () => {
      const id = card.dataset.classId;
      demoState.selectedClass = demoState.classes.find((cls) => cls.id === id) || demoState.classes[0];
      navigateTo(() => {
        demoState.currentView = 'class-select';
        renderClassSelect();
      });
    });
  });

  postRenderSetup();
  animateCounters();
}

function bindNavigation() {
  document.querySelectorAll('[data-nav]').forEach((button) => {
    button.addEventListener('click', () => {
      const target = button.dataset.nav;
      if (demoState.currentView === target) return;
      
      navigateTo(() => {
        demoState.currentView = target;
        if (target === 'dashboard') renderDashboard();
        else if (target === 'class-select') renderClassSelect();
        else if (target === 'history') renderHistory();
        else if (target === 'session') renderSession();
        else if (target === 'upload') renderUpload();
        else if (target === 'results') renderResults();
        else if (target === 'second-photo') renderSecondPhoto();
        else if (target === 'final-review') renderFinalReview();
      });
    });
  });
}

function renderClassSelect() {
  const cls = demoState.selectedClass || demoState.classes[0];
  app.innerHTML = `
    <div class="app-shell">
      ${getTopbarHtml('Teacher • Priya Nair')}

      <div class="page">
        ${renderStepIndicator(0)}
        <div class="panel">
          <div class="panel-header">
            <div>
              <div class="eyebrow">Class Selection</div>
              <h2>Choose a class for attendance</h2>
            </div>
            <div class="nav-pills">
              <button type="button" data-nav="dashboard">Back</button>
            </div>
          </div>

          <div class="class-grid">
            ${demoState.classes.map((item) => `
              <div class="class-card ${item.id === cls.id ? 'selected' : ''}" data-class-id="${item.id}">
                <div class="eyebrow">${item.subject}</div>
                <h3>${item.name}</h3>
                <div class="stats">
                  <span>${item.count} students</span>
                  <span>${item.teacher}</span>
                </div>
              </div>
            `).join('')}
          </div>

          <div class="summary-box" style="margin-top: 24px;">
            <strong>Selected class</strong>
            <div>${cls.name} • ${cls.subject}</div>
            <div>${cls.count} enrolled students</div>
            <div class="action-row">
              <button class="primary-btn" id="startSessionBtn">Start attendance session</button>
              <button class="ghost-btn" data-nav="dashboard">Cancel</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;

  document.querySelectorAll('[data-class-id]').forEach((card) => {
    card.addEventListener('click', () => {
      const id = card.dataset.classId;
      demoState.selectedClass = demoState.classes.find((c) => c.id === id) || demoState.classes[0];
      renderClassSelect(); // re-render without transition for fast selection
      postRenderSetup();
    });
  });

  document.getElementById('startSessionBtn').addEventListener('click', () => {
    demoState.attendanceSession = {
      className: cls.name,
      subject: cls.subject,
      date: new Date().toISOString().slice(0, 10),
      status: 'Open'
    };
    navigateTo(() => {
      demoState.currentView = 'session';
      renderSession();
    });
  });

  bindNavigation();
  postRenderSetup();
}

function renderSession() {
  const session = demoState.attendanceSession || { className: 'CSE-A', subject: 'Operating Systems', date: '2026-08-29' };
  
  if (!demoState.sessionStartTime) {
    demoState.sessionStartTime = Date.now();
  }

  app.innerHTML = `
    <div class="app-shell">
      ${getTopbarHtml('Session active')}

      <div class="page">
        ${renderStepIndicator(1)}
        <div class="panel">
          <div class="panel-header">
            <div>
              <div class="eyebrow">Attendance Setup</div>
              <h2>${session.className}</h2>
            </div>
            <div class="nav-pills">
              <button type="button" data-nav="dashboard">Dashboard</button>
            </div>
          </div>

          <div class="session-form">
            <div class="summary-box">
              <strong>Selected class</strong>
              <span>${session.className}</span>
              <span>Subject: ${session.subject}</span>
              <span>Date: ${session.date}</span>
              <span>Students enrolled: ${demoState.selectedClass?.count || 32}</span>
            </div>

            <div class="input-wrap">
              <label for="subjectInput">Subject</label>
              <input id="subjectInput" type="text" value="${session.subject}" />
            </div>

            <div class="input-wrap">
              <label for="dateInput">Session date</label>
              <input id="dateInput" type="date" value="${session.date}" />
            </div>

            <div class="action-row">
              <button class="primary-btn" id="continueUploadBtn">Continue to photo upload</button>
              <button class="ghost-btn" data-nav="class-select">Back</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;

  document.getElementById('continueUploadBtn').addEventListener('click', () => {
    navigateTo(() => {
      demoState.currentView = 'upload';
      renderUpload();
    });
  });

  bindNavigation();
  postRenderSetup();
}

function renderUpload() {
  app.innerHTML = `
    <div class="app-shell">
      ${getTopbarHtml('Photo upload')}

      <div class="page">
        ${renderStepIndicator(2)}
        <div class="panel">
          <div class="panel-header">
            <div>
              <div class="eyebrow">Upload classroom photo</div>
              <h2>First recognition pass</h2>
            </div>
            <div class="nav-pills">
              <button type="button" data-nav="dashboard">Dashboard</button>
            </div>
          </div>

          <div class="summary-box">
            <strong>Photo guidance</strong>
            <span>Make sure all students are visible and faces are clear.</span>
            <span>Use good lighting and avoid excessive blur.</span>
          </div>

          <label class="upload-zone" id="mainUploadZone" for="photoInput">
            <div class="upload-icon">📷</div>
            <strong>Choose classroom photo</strong>
            <span>Drag & drop or click to select • PNG, JPG • Max 10MB</span>
            <input id="photoInput" type="file" accept="image/png,image/jpeg" />
            <button type="button" class="primary-btn" style="pointer-events:none;">Select image</button>
          </label>

          <div class="processing-box hidden" id="processingBox">
            <div style="display:flex; flex-direction:column; gap:12px;">
              <div class="progress-step" id="step1">
                <div class="step-num">1</div><span>Detecting faces</span>
              </div>
              <div class="progress-step" id="step2">
                <div class="step-num">2</div><span>Generating embeddings</span>
              </div>
              <div class="progress-step" id="step3">
                <div class="step-num">3</div><span>Matching roster</span>
              </div>
              <div class="progress-step" id="step4">
                <div class="step-num">✓</div><span>Complete</span>
              </div>
            </div>
          </div>

          <div class="action-row" id="uploadActions">
            <button class="secondary-btn" id="mockProcessBtn">Run demo recognition</button>
            <button class="ghost-btn" data-nav="dashboard">Cancel</button>
          </div>
        </div>
      </div>
    </div>
  `;

  initDragAndDrop('mainUploadZone', 'photoInput');

  document.getElementById('mockProcessBtn').addEventListener('click', () => {
    const box = document.getElementById('processingBox');
    const actions = document.getElementById('uploadActions');
    const uploadZone = document.getElementById('mainUploadZone');
    
    box.classList.remove('hidden');
    actions.style.display = 'none';
    uploadZone.style.pointerEvents = 'none';
    uploadZone.style.opacity = '0.6';

    const steps = [
      document.getElementById('step1'),
      document.getElementById('step2'),
      document.getElementById('step3'),
      document.getElementById('step4')
    ];

    let delay = 0;
    steps.forEach((step, i) => {
      setTimeout(() => {
        if (i > 0) steps[i-1].classList.replace('active', 'done');
        step.classList.add('active');
        if (i === steps.length - 1) {
          setTimeout(() => {
            navigateTo(() => {
              demoState.currentView = 'results';
              renderResults();
            });
          }, 800);
        }
      }, delay);
      delay += 800;
    });
  });

  bindNavigation();
  postRenderSetup();
}

function renderResults() {
  app.innerHTML = `
    <div class="app-shell">
      ${getTopbarHtml('Recognition results')}

      <div class="page">
        ${renderStepIndicator(3)}
        <div class="panel">
          <div class="panel-header">
            <div>
              <div class="eyebrow">Attendance Review</div>
              <h2>Photo 1 results</h2>
            </div>
            <div class="nav-pills">
              <button type="button" data-nav="upload">Retake photo</button>
              <button type="button" class="primary-btn" id="takeSecondPhotoBtn">Take another photo</button>
            </div>
          </div>

          <div class="results-grid">
            <div class="result-card">
              <h4>✅ Confidently recognized</h4>
              <div class="result-list">
                ${demoState.detectResults.confident.map((item) => `
                  <div class="result-item">
                    <strong>${item.name}</strong>
                    <span class="badge success">${item.confidence}</span>
                  </div>
                `).join('')}
              </div>
            </div>

            <div class="result-card">
              <h4>⚠️ Needs review</h4>
              <div class="result-list">
                ${demoState.detectResults.review.map((item) => `
                  <div class="result-item">
                    <strong>${item.name}</strong>
                    <span class="badge warning">${item.confidence}</span>
                  </div>
                `).join('')}
              </div>
            </div>

            <div class="result-card">
              <h4>❓ Unknown</h4>
              <div class="result-list">
                ${demoState.detectResults.unknown.map((item) => `
                  <div class="result-item">
                    <strong>${item.name}</strong>
                    <span class="badge neutral">${item.candidate}</span>
                  </div>
                `).join('')}
              </div>
            </div>

            <div class="result-card">
              <h4>👤 Not detected</h4>
              <div class="result-list">
                ${demoState.detectResults.notDetected.map((item) => `
                  <div class="result-item">
                    <strong>${item.name}</strong>
                    <span class="badge info">Not detected</span>
                  </div>
                `).join('')}
              </div>
            </div>
          </div>
          
          <div class="action-row" style="margin-top:24px;">
            <button class="primary-btn" id="skipToReviewBtn">Proceed to Final Review</button>
          </div>
        </div>
      </div>
    </div>
  `;

  document.getElementById('takeSecondPhotoBtn').addEventListener('click', () => {
    navigateTo(() => {
      demoState.currentView = 'second-photo';
      renderSecondPhoto();
    });
  });

  document.getElementById('skipToReviewBtn').addEventListener('click', () => {
    navigateTo(() => {
      demoState.currentView = 'final-review';
      renderFinalReview();
    });
  });

  bindNavigation();
  postRenderSetup();
}

function renderSecondPhoto() {
  app.innerHTML = `
    <div class="app-shell">
      ${getTopbarHtml('Second photo workflow')}

      <div class="page">
        ${renderStepIndicator(4)}
        <div class="panel">
          <div class="panel-header">
            <div>
              <div class="eyebrow">Resolution photo</div>
              <h2>Resolve uncertain / unknown faces</h2>
            </div>
            <div class="nav-pills">
              <button type="button" data-nav="results">Back to results</button>
            </div>
          </div>

          <div class="summary-box">
            <strong>Use this photo to resolve only the uncertain or unknown students.</strong>
            <span>Photo 2 is merged with Photo 1; it does not replace the original result.</span>
          </div>

          <label class="upload-zone" id="secondUploadZone" for="secondPhotoInput">
            <div class="upload-icon">🧭</div>
            <strong>Upload second classroom photo</strong>
            <span>Drag & drop or click • Use a tighter image focusing on uncertain faces.</span>
            <input id="secondPhotoInput" type="file" accept="image/png,image/jpeg" />
            <button type="button" class="primary-btn" style="pointer-events:none;">Select second image</button>
          </label>

          <div class="action-row">
            <button class="primary-btn" id="processSecondPhotoBtn">Process second photo</button>
            <button class="ghost-btn" data-nav="results">Skip</button>
          </div>
        </div>
      </div>
    </div>
  `;

  initDragAndDrop('secondUploadZone', 'secondPhotoInput');

  document.getElementById('processSecondPhotoBtn').addEventListener('click', () => {
    const btn = document.getElementById('processSecondPhotoBtn');
    btn.textContent = 'Processing...';
    btn.disabled = true;
    setTimeout(() => {
      showToast('Second photo processed successfully', 'success');
      navigateTo(() => {
        demoState.currentView = 'final-review';
        renderFinalReview();
      });
    }, 1200);
  });

  bindNavigation();
  postRenderSetup();
}

function renderFinalReview() {
  app.innerHTML = `
    <div class="app-shell">
      ${getTopbarHtml('Final review')}

      <div class="page">
        ${renderStepIndicator(5)}
        <div class="panel">
          <div class="panel-header">
            <div>
              <div class="eyebrow">Teacher review</div>
              <h2>Confirm final attendance</h2>
            </div>
            <div class="nav-pills">
              <button type="button" data-nav="results">Back</button>
            </div>
          </div>
          
          <div style="display:flex; gap:16px; margin-bottom:16px;">
            <input type="text" class="search-input" id="studentSearch" placeholder="Search students..." style="flex:1;" />
            <select id="statusFilter" style="padding:10px 14px; border-radius:12px; border:1px solid var(--line); background:var(--panel-alt); color:var(--text); font-weight:700; font-size:0.9rem; cursor:pointer;">
              <option value="All">All Statuses</option>
              <option value="Present">Present</option>
              <option value="Absent">Absent</option>
              <option value="Review">Review</option>
            </select>
          </div>

          <table class="mini-table">
            <thead>
              <tr>
                <th>Student</th>
                <th>Recognition</th>
                <th>Final status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody id="studentTableBody">
              ${demoState.students.map((student) => `
                <tr data-student-row="${student.id}" class="animate-in">
                  <td>${student.name}</td>
                  <td>
                    <span class="status-pill ${student.recognition === 'Present' ? 'present' : student.recognition === 'Review' ? 'review pulse' : student.recognition === 'Unknown' ? 'unknown' : 'absent'}">
                      ${student.recognition}
                    </span>
                  </td>
                  <td>
                    <select class="final-status-select" data-student-id="${student.id}" data-status="${student.finalStatus}">
                      <option value="Present" ${student.finalStatus === 'Present' ? 'selected' : ''}>Present</option>
                      <option value="Absent" ${student.finalStatus === 'Absent' ? 'selected' : ''}>Absent</option>
                      <option value="Review" ${student.finalStatus === 'Review' ? 'selected' : ''}>Review</option>
                    </select>
                  </td>
                  <td>
                    <button class="ghost-btn confirm-action-btn" data-student-id="${student.id}">Confirm</button>
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>

          <div class="action-row">
            <button class="primary-btn" id="finalizeBtn">Finalize attendance</button>
            <button class="secondary-btn" data-nav="history">View history</button>
          </div>
        </div>
      </div>
    </div>
  `;

  const filterTable = () => {
    const term = document.getElementById('studentSearch').value.toLowerCase();
    const statusVal = document.getElementById('statusFilter').value;
    
    document.querySelectorAll('tr[data-student-row]').forEach(row => {
      const id = Number(row.dataset.studentRow);
      const student = demoState.students.find(s => s.id === id);
      if (!student) return;
      
      const matchName = student.name.toLowerCase().includes(term);
      const matchStatus = statusVal === 'All' || student.finalStatus === statusVal || student.recognition === statusVal;
      
      row.style.display = (matchName && matchStatus) ? '' : 'none';
    });
  };

  document.getElementById('studentSearch').addEventListener('input', filterTable);
  document.getElementById('statusFilter').addEventListener('change', filterTable);

  document.querySelectorAll('.final-status-select').forEach((select) => {
    select.setAttribute('data-status', select.value);
    select.addEventListener('change', (event) => {
      const id = Number(event.target.dataset.studentId);
      const student = demoState.students.find((item) => item.id === id);
      if (student) student.finalStatus = event.target.value;
      event.target.setAttribute('data-status', event.target.value);
      
      // Add subtle flash to row
      const row = event.target.closest('tr');
      row.style.backgroundColor = 'var(--primary-soft)';
      setTimeout(() => { row.style.backgroundColor = ''; }, 300);
    });
  });

  document.querySelectorAll('.confirm-action-btn').forEach((button) => {
    button.addEventListener('click', () => {
      const id = Number(button.dataset.studentId);
      const student = demoState.students.find((item) => item.id === id);
      if (student) {
        student.finalStatus = document.querySelector(`select[data-student-id="${id}"]`).value;
        
        // Inline UI swap
        const parent = button.parentElement;
        parent.innerHTML = '<span class="confirm-check" style="color: var(--success); font-weight: bold;">✓ Confirmed</span>';
        
        showToast(`${student.name} marked as ${student.finalStatus}`, 'success');
        
        const row = document.querySelector(`tr[data-student-row="${id}"]`);
        row.style.opacity = '0.6';
      }
    });
  });

  document.getElementById('finalizeBtn').addEventListener('click', () => {
    const overlay = document.createElement('div');
    overlay.className = 'celebration';
    overlay.style.position = 'fixed';
    overlay.style.inset = '0';
    overlay.style.backgroundColor = 'rgba(0,0,0,0.5)';
    overlay.style.display = 'flex';
    overlay.style.alignItems = 'center';
    overlay.style.justifyContent = 'center';
    overlay.style.zIndex = '9999';
    overlay.innerHTML = '<div style="font-size: 5rem; animation: popIn 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);">🎉</div>';
    
    // Add popIn keyframe dynamically just for this if not in CSS
    if (!document.getElementById('tempKeyframes')) {
      const style = document.createElement('style');
      style.id = 'tempKeyframes';
      style.textContent = '@keyframes popIn { 0% { transform: scale(0); opacity: 0; } 100% { transform: scale(1); opacity: 1; } }';
      document.head.appendChild(style);
    }
    
    document.body.appendChild(overlay);
    showToast('Attendance finalized successfully! 🎉', 'success');
    
    const presentCount = demoState.students.filter(s => s.finalStatus === 'Present').length;
    const absentCount = demoState.students.filter(s => s.finalStatus === 'Absent').length;
    
    demoState.attendanceHistory.unshift({
      date: new Date().toISOString().slice(0, 10),
      className: demoState.attendanceSession?.className || 'Class',
      subject: demoState.attendanceSession?.subject || 'Subject',
      present: presentCount,
      absent: absentCount,
      status: 'Finalized'
    });
    
    demoState.sessionStartTime = null;

    setTimeout(() => {
      overlay.remove();
      navigateTo(() => {
        demoState.currentView = 'history';
        renderHistory();
      });
    }, 1500);
  });

  bindNavigation();
  postRenderSetup();
}

function renderHistory() {
  app.innerHTML = `
    <div class="app-shell">
      ${getTopbarHtml('Attendance history')}

      <div class="page">
        <div class="panel">
          <div class="panel-header">
            <div>
              <div class="eyebrow">Session history</div>
              <h2>Recent attendance logs</h2>
            </div>
            <div class="nav-pills">
              <button type="button" data-nav="dashboard">Dashboard</button>
            </div>
          </div>

          <div class="history-list">
            ${demoState.attendanceHistory.map((item) => `
              <div class="history-item">
                <div>
                  <strong>${item.className} • ${item.subject}</strong>
                  <div style="color: var(--muted); margin-top: 6px; font-weight: 700; font-size: 0.92rem;">${item.date}</div>
                </div>
                <div class="action-row" style="margin-top: 0;">
                  <span class="badge success">${item.present} present</span>
                  <span class="badge danger">${item.absent} absent</span>
                  <span class="badge neutral">${item.status}</span>
                </div>
              </div>
            `).join('')}
          </div>
        </div>
      </div>
    </div>
  `;

  bindNavigation();
  postRenderSetup();
}

// Initial boot
initTheme();
renderLogin();
