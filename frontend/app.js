const app = document.getElementById('app');
const API_BASE_URL = 'http://localhost:8001';

const demoState = {
  currentView: 'login',
  selectedClass: null,
  attendanceSession: null,
  attendanceHistory: [],
  classes: [],
  students: [],
  detectResults: { confident: [], review: [], unknown: [], notDetected: [] },
  teacher: null,
  token: null,
  sessionId: null,
  subjectMap: []
};

async function apiFetch(path, options = {}) {
  const requestHeaders = { ...(options.headers || {}) };

  if (!(options.body instanceof FormData) && !requestHeaders['Content-Type']) {
    requestHeaders['Content-Type'] = 'application/json';
  }

  if (!requestHeaders.Authorization && demoState.token) {
    requestHeaders.Authorization = `Bearer ${demoState.token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: requestHeaders,
  });

  if (!response.ok) {
    const errorObj = await response.json().catch(() => ({}));
    throw new Error(errorObj.detail || `Request failed: ${response.status}`);
  }

  return response;
}

async function loadDashboard() {
  if (!demoState.teacher) return;

  try {
    const response = await apiFetch(`/api/dashboard/teacher/${demoState.teacher.teacher_id}`);
    const data = await response.json();
    demoState.teacher = data.teacher || demoState.teacher;

    demoState.classes = (data.subjects || []).map((subject) => ({
      id: subject.subject_id,
      name: data.section.section_name,
      subject: subject.subject_name,
      count: 32,
      teacher: data.teacher.name,
      subject_id: subject.subject_id,
      section_id: data.section.section_id,
    }));

    demoState.attendanceHistory = (data.recent_sessions || []).map((session) => ({
      date: session.session_date,
      className: data.section.section_name,
      subject: session.subject_name || session.subject_id,
      present: session.present_count || data.stats.present || 0,
      absent: session.total_students ? Math.max(session.total_students - (session.present_count || 0), 0) : 0,
      status: session.status,
    }));

    if (!demoState.selectedClass && demoState.classes.length) {
      demoState.selectedClass = demoState.classes[0];
    }
  } catch (error) {
    console.error('Dashboard load failed', error);
  }
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

    document.getElementById('startSessionBtn').addEventListener('click', async () => {
    try {
      await startSessionForSelectedClass();
    } catch (error) {
      alert(error.message || 'Unable to start the attendance session.');
    }
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

    document.getElementById('mockProcessBtn').addEventListener('click', async () => {
    const processingBox = document.getElementById('processingBox');
    processingBox.classList.remove('hidden');

    try {
      const response = await apiFetch(`/api/attendance/sessions/${demoState.sessionId}/recognize`);
      const data = await response.json();
      demoState.detectResults = buildRecognitionResults(data);
      demoState.currentView = 'results';
      renderResults();
    } catch (error) {
      processingBox.classList.add('hidden');
      alert(error.message || 'Recognition failed. Please try again.');
    }
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

    document.getElementById('processSecondPhotoBtn').addEventListener('click', async () => {
    try {
      const response = await apiFetch(`/api/attendance/sessions/${demoState.sessionId}/resolve`);
      const data = await response.json();
      demoState.students = mapSessionStudents(data);
      demoState.currentView = 'final-review';
      renderFinalReview();
    } catch (error) {
      alert(error.message || 'Unable to merge the second photo results.');
    }
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

    document.getElementById('finalizeBtn').addEventListener('click', async () => {
    try {
      const decisions = {};
      demoState.students.forEach((student) => {
        if (student.studentId) {
          decisions[student.studentId] = (student.finalStatus || 'present').toLowerCase();
        }
      });

      const response = await apiFetch(`/api/attendance/sessions/${demoState.sessionId}/finalize`, {
        method: 'POST',
        body: JSON.stringify({
          teacher_id: demoState.teacher.teacher_id,
          decisions,
        }),
      });
      const data = await response.json();

      if (data.status === 'finalized') {
        await loadDashboard();
        demoState.currentView = 'history';
        renderHistory();
        return;
      }

      throw new Error(data.detail || 'Could not finalize attendance.');
    } catch (error) {
      alert(error.message || 'Attendance could not be finalized.');
    }
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
