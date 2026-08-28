const app = document.getElementById('app');

const demoState = {
  currentView: 'login',
  selectedClass: null,
  attendanceSession: null,
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

function render() {
  const activeClass = demoState.selectedClass || demoState.classes[0];

  if (demoState.currentView === 'login') {
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
        demoState.currentView = 'dashboard';
        render();
      } else {
        alertBox.textContent = 'Login failed. Please use valid teacher credentials.';
        alertBox.classList.add('show');
      }
    });

    return;
  }

  app.innerHTML = `
    <div class="app-shell">
      <header class="topbar">
        <div class="brand">
          <div class="brand-mark">F</div>
          <span>FaceMark</span>
        </div>
        <div class="user-badge">Teacher • Priya Nair</div>
      </header>

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
              <button class="secondary-btn" data-nav="class-select">Select class</button>
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
              ${demoState.attendanceHistory.map((item) => `
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

  bindDashboardEvents();
}

function bindDashboardEvents() {
  document.querySelectorAll('[data-class-id]').forEach((card) => {
    card.addEventListener('click', () => {
      const id = card.dataset.classId;
      demoState.selectedClass = demoState.classes.find((cls) => cls.id === id) || demoState.classes[0];
      demoState.currentView = 'class-select';
      renderClassSelect();
    });
  });

  document.querySelectorAll('[data-nav]').forEach((button) => {
    button.addEventListener('click', () => {
      const target = button.dataset.nav;
      if (target === 'dashboard') {
        demoState.currentView = 'dashboard';
        render();
      }
      if (target === 'class-select') {
        demoState.currentView = 'class-select';
        renderClassSelect();
      }
      if (target === 'history') {
        demoState.currentView = 'history';
        renderHistory();
      }
    });
  });
}

function renderClassSelect() {
  const cls = demoState.selectedClass || demoState.classes[0];
  app.innerHTML = `
    <div class="app-shell">
      <header class="topbar">
        <div class="brand">
          <div class="brand-mark">F</div>
          <span>FaceMark</span>
        </div>
        <div class="user-badge">Teacher • Priya Nair</div>
      </header>

      <div class="page">
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
      demoState.selectedClass = demoState.classes.find((clsCandidate) => clsCandidate.id === id) || demoState.classes[0];
      renderClassSelect();
    });
  });

  document.getElementById('startSessionBtn').addEventListener('click', () => {
    demoState.currentView = 'session';
    demoState.attendanceSession = {
      className: cls.name,
      subject: cls.subject,
      date: new Date().toISOString().slice(0, 10),
      status: 'Open'
    };
    renderSession();
  });

  document.querySelectorAll('[data-nav]').forEach((button) => {
    button.addEventListener('click', () => {
      const target = button.dataset.nav;
      if (target === 'dashboard') {
        demoState.currentView = 'dashboard';
        render();
      }
    });
  });
}

function renderSession() {
  const session = demoState.attendanceSession || { className: 'CSE-A', subject: 'Operating Systems', date: '2026-08-29' };
  app.innerHTML = `
    <div class="app-shell">
      <header class="topbar">
        <div class="brand">
          <div class="brand-mark">F</div>
          <span>FaceMark</span>
        </div>
        <div class="user-badge">Session active</div>
      </header>

      <div class="page">
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
    demoState.currentView = 'upload';
    renderUpload();
  });

  document.querySelectorAll('[data-nav]').forEach((button) => {
    button.addEventListener('click', () => {
      const target = button.dataset.nav;
      if (target === 'dashboard') {
        demoState.currentView = 'dashboard';
        render();
      }
    });
  });
}

function renderUpload() {
  app.innerHTML = `
    <div class="app-shell">
      <header class="topbar">
        <div class="brand">
          <div class="brand-mark">F</div>
          <span>FaceMark</span>
        </div>
        <div class="user-badge">Photo upload</div>
      </header>

      <div class="page">
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

          <label class="upload-zone" for="photoInput">
            <div class="upload-icon">📷</div>
            <strong>Choose classroom photo</strong>
            <span>PNG, JPG, or JPEG • Max 10MB</span>
            <input id="photoInput" type="file" accept="image/png,image/jpeg" />
            <button type="button" class="primary-btn">Select image</button>
          </label>

          <div class="processing-box hidden" id="processingBox">
            <strong>Processing image</strong>
            <div class="progress-line"><span></span></div>
            <p style="margin-top: 12px; color: var(--muted);">Detecting faces and matching with class roster…</p>
          </div>

          <div class="action-row">
            <button class="secondary-btn" id="mockProcessBtn">Run demo recognition</button>
            <button class="ghost-btn" data-nav="dashboard">Cancel</button>
          </div>
        </div>
      </div>
    </div>
  `;

  document.getElementById('mockProcessBtn').addEventListener('click', () => {
    const processingBox = document.getElementById('processingBox');
    processingBox.classList.remove('hidden');
    setTimeout(() => {
      demoState.currentView = 'results';
      renderResults();
    }, 1300);
  });

  document.querySelectorAll('[data-nav]').forEach((button) => {
    button.addEventListener('click', () => {
      demoState.currentView = button.dataset.nav === 'dashboard' ? 'dashboard' : 'upload';
      if (demoState.currentView === 'dashboard') render();
      else renderUpload();
    });
  });
}

function renderResults() {
  app.innerHTML = `
    <div class="app-shell">
      <header class="topbar">
        <div class="brand">
          <div class="brand-mark">F</div>
          <span>FaceMark</span>
        </div>
        <div class="user-badge">Recognition results</div>
      </header>

      <div class="page">
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
        </div>
      </div>
    </div>
  `;

  document.getElementById('takeSecondPhotoBtn').addEventListener('click', () => {
    demoState.currentView = 'second-photo';
    renderSecondPhoto();
  });

  document.querySelectorAll('[data-nav]').forEach((button) => {
    button.addEventListener('click', () => {
      if (button.dataset.nav === 'upload') {
        demoState.currentView = 'upload';
        renderUpload();
      }
    });
  });
}

function renderSecondPhoto() {
  app.innerHTML = `
    <div class="app-shell">
      <header class="topbar">
        <div class="brand">
          <div class="brand-mark">F</div>
          <span>FaceMark</span>
        </div>
        <div class="user-badge">Second photo workflow</div>
      </header>

      <div class="page">
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

          <label class="upload-zone" for="secondPhotoInput">
            <div class="upload-icon">🧭</div>
            <strong>Upload second classroom photo</strong>
            <span>Use a tighter image focusing on the uncertain faces.</span>
            <input id="secondPhotoInput" type="file" accept="image/png,image/jpeg" />
            <button type="button" class="primary-btn">Select second image</button>
          </label>

          <div class="action-row">
            <button class="primary-btn" id="processSecondPhotoBtn">Process second photo</button>
            <button class="ghost-btn" data-nav="results">Skip</button>
          </div>
        </div>
      </div>
    </div>
  `;

  document.getElementById('processSecondPhotoBtn').addEventListener('click', () => {
    demoState.currentView = 'final-review';
    renderFinalReview();
  });

  document.querySelectorAll('[data-nav]').forEach((button) => {
    button.addEventListener('click', () => {
      if (button.dataset.nav === 'results') {
        demoState.currentView = 'results';
        renderResults();
      }
    });
  });
}

function renderFinalReview() {
  app.innerHTML = `
    <div class="app-shell">
      <header class="topbar">
        <div class="brand">
          <div class="brand-mark">F</div>
          <span>FaceMark</span>
        </div>
        <div class="user-badge">Final review</div>
      </header>

      <div class="page">
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

          <table class="mini-table">
            <thead>
              <tr>
                <th>Student</th>
                <th>Recognition</th>
                <th>Final status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              ${demoState.students.map((student) => `
                <tr data-student-row="${student.id}">
                  <td>${student.name}</td>
                  <td>
                    <span class="status-pill ${student.recognition === 'Present' ? 'present' : student.recognition === 'Review' ? 'review' : student.recognition === 'Unknown' ? 'unknown' : 'absent'}">
                      ${student.recognition}
                    </span>
                  </td>
                  <td>
                    <select class="final-status-select" data-student-id="${student.id}">
                      <option value="Present" ${student.finalStatus === 'Present' ? 'selected' : ''}>Present</option>
                      <option value="Absent" ${student.finalStatus === 'Absent' ? 'selected' : ''}>Absent</option>
                      <option value="Review" ${student.finalStatus === 'Review' ? 'selected' : ''}>Review</option>
                    </select>
                  </td>
                  <td>
                    <button class="ghost-btn" data-student-id="${student.id}">Confirm</button>
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

  document.querySelectorAll('.final-status-select').forEach((select) => {
    select.addEventListener('change', (event) => {
      const id = Number(event.target.dataset.studentId);
      const student = demoState.students.find((item) => item.id === id);
      if (student) student.finalStatus = event.target.value;
    });
  });

  document.querySelectorAll('[data-student-id]').forEach((button) => {
    button.addEventListener('click', () => {
      const id = Number(button.dataset.studentId);
      const student = demoState.students.find((item) => item.id === id);
      if (student) {
        student.finalStatus = student.finalStatus || 'Present';
        alert(`${student.name} marked as ${student.finalStatus}`);
      }
    });
  });

  document.getElementById('finalizeBtn').addEventListener('click', () => {
    demoState.currentView = 'history';
    renderHistory();
  });

  document.querySelectorAll('[data-nav]').forEach((button) => {
    button.addEventListener('click', () => {
      if (button.dataset.nav === 'results') {
        demoState.currentView = 'results';
        renderResults();
      }
      if (button.dataset.nav === 'history') {
        demoState.currentView = 'history';
        renderHistory();
      }
    });
  });
}

function renderHistory() {
  app.innerHTML = `
    <div class="app-shell">
      <header class="topbar">
        <div class="brand">
          <div class="brand-mark">F</div>
          <span>FaceMark</span>
        </div>
        <div class="user-badge">Attendance history</div>
      </header>

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
                  <div style="color: var(--muted); margin-top: 4px;">${item.date}</div>
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

  document.querySelectorAll('[data-nav]').forEach((button) => {
    button.addEventListener('click', () => {
      if (button.dataset.nav === 'dashboard') {
        demoState.currentView = 'dashboard';
        render();
      }
    });
  });
}

render();
