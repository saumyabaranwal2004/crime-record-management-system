/* ============================================================
   NEXUS CRMS — script.js
   Requires: app.js (Auth, Cases, Alerts, Analytics, apiRequest)
============================================================ */
'use strict';
console.log("executing script.js");
console.log("executing script.js");
const CRIME_TYPES = [
  'Theft','Robbery','Assault','Fraud',
  'Cybercrime','Murder','Kidnapping','Vandalism','Drug Offense',
];

let currentUser    = null;
let selectedRole   = 'citizen';
let yearChart      = null, typeChart = null, monthlyChart = null;
let leafletMap     = null;
let manageFilter   = null;   // null = all, 'Pending Review' = incoming

const qs  = sel => document.querySelector(sel);
const qsa = sel => document.querySelectorAll(sel);
const show = el => { if (el) el.style.display = ''; };
const hide = el => { if (el) el.style.display = 'none'; };

function esc(str) {
  if (str == null) return '';
  return String(str)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}

function toast(msg, type = 'info') {
  const t = qs('#toast');
  const icons = {
    success: '<i class="fa-solid fa-circle-check"  style="color:var(--accent-green)"></i>',
    error:   '<i class="fa-solid fa-circle-xmark"  style="color:var(--accent-red)"></i>',
    info:    '<i class="fa-solid fa-circle-info"   style="color:var(--accent-blue)"></i>',
  };
  t.innerHTML = `${icons[type] || icons.info} ${esc(msg)}`;
  t.className = `toast show ${type}`;
  setTimeout(() => t.classList.remove('show'), 3500);
}

function statusBadge(s) {
  const map = { 'Open':'status-open', 'Under Investigation':'status-investigation', 'Closed':'status-closed','Pending':'status-pending', };
  return `<span class="status-badge ${map[s] || 'status-open'}">${esc(s)}</span>`;
}

function formatDate(str) {
  if (!str) return '—';
  return new Date(str).toLocaleDateString('en-IN', { day:'2-digit', month:'short', year:'numeric' });
}

function showTableLoading(tbodyId, colSpan = 8) {
  const tb = qs('#' + tbodyId);
  if (tb) tb.innerHTML = `<tr><td colspan="${colSpan}" style="text-align:center;padding:32px;color:var(--text-dim)">
    <i class="fa-solid fa-spinner fa-spin" style="font-size:20px;margin-bottom:8px;display:block"></i>Loading records…</td></tr>`;
}

function upgradeCrimeTypeField() {
  const select = document.getElementById('mType');
  if (!select || select.tagName !== 'SELECT') return;
  const dl = document.createElement('datalist');
  dl.id = 'crimeTypeOptions';
  CRIME_TYPES.forEach(t => { const o = document.createElement('option'); o.value = t; dl.appendChild(o); });
  const input = document.createElement('input');
  input.type = 'text'; input.id = 'mType';
  input.setAttribute('list', 'crimeTypeOptions');
  input.placeholder = 'Select or type crime type';
  input.autocomplete = 'off'; input.className = select.className;
  select.replaceWith(input);
  input.insertAdjacentElement('afterend', dl);
}

function fixSearchFilter() {
  const sel = qs('#filterType');
  if (!sel) return;
  sel.innerHTML = `<option value="">All Statuses</option>
    <option value="Open">Open</option>
    <option value="Under Investigation">Under Investigation</option>
    <option value="Closed">Closed</option>`;
}

/* ── Page routing ─────────────────────────────────────────── */
function capitalize(s) { return s.charAt(0).toUpperCase() + s.slice(1); }

function showPage(id) {
  qsa('.page').forEach(p => p.classList.remove('active'));
  const pg = qs(`#page${capitalize(id)}`);
  if (pg) pg.classList.add('active');
  qsa('.nav-link').forEach(l => l.classList.toggle('active', l.dataset.page === id));

  if (id === 'search')    initSearch();
  if (id === 'dashboard') initDashboard();
  if (id === 'alerts')    renderAlerts('all');

  if (id === 'myreports') {
    if (!currentUser || currentUser.role !== 'citizen') { showPage('login'); return; }
    renderMyReports();
  }

  if (id === 'manage') {
    if (!currentUser || currentUser.role !== 'officer') {
      toast('Officer login required.', 'error'); showPage('login'); return;
    }
    renderManageTable();
  }

  window.scrollTo(0, 0);
}

document.addEventListener('click', function(e) {
  const el = e.target.closest('[data-page]');
  if (!el) return;
  e.preventDefault();
  if (el.dataset.page) showPage(el.dataset.page);
});

/* ── Citizen My Reports ───────────────────────────────────── */
async function renderMyReports() {
  const grid = qs('#myReportsGrid');
  grid.innerHTML = '<p style="padding:20px;color:var(--text-dim);">Loading your reports...</p>';
  try {
    const records = await Cases.list({ reporter: 'me' });
    if (!records.length) {
      grid.innerHTML = `<div style="padding:40px;text-align:center;color:var(--text-dim);grid-column:1/-1;">
        <i class="fa-solid fa-folder-open" style="font-size:32px;margin-bottom:12px;display:block"></i>
        You haven't reported any incidents yet.</div>`;
      return;
    }
    grid.innerHTML = records.map(r => `
      <div class="tracker-card">
        <div class="t-head">
          <span class="t-id">${esc(r.id)}</span>
          <span class="t-date">${formatDate(r.date)}</span>
        </div>
        <div><strong>Type:</strong> ${esc(r.type)} &nbsp;|&nbsp; <strong>Location:</strong> ${esc(r.location)}</div>
        <div>${statusBadge(r.status)}</div>
        <div class="t-officer">
          <i class="fa-solid fa-badge-sheriff"></i>
          <div>
            <div style="font-size:10px;color:var(--text-dim);text-transform:uppercase;">Investigating Officer</div>
            <strong>${esc(r.assigned_to || '—')}</strong>
          </div>
        </div>
      </div>`).join('');
  } catch (e) {
    grid.innerHTML = '<p style="color:var(--accent-red)">Failed to load your reports.</p>';
  }
}

/* ── Hamburger ────────────────────────────────────────────── */
qs('#hamburger').addEventListener('click', () => qs('#navLinks').classList.toggle('open'));

/* ── Role selector ────────────────────────────────────────── */
qsa('.role-btn').forEach(btn => {
  btn.addEventListener('click', e => {
    e.stopPropagation();
    qsa('.role-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    selectedRole = btn.dataset.role;
    updateAccessPreview(selectedRole);
  });
});

function updateAccessPreview(role) {
  const badge = qs('#accessBadge');
  const list  = qs('#accessList');
  if (!badge || !list) return;
  if (role === 'officer') {
    badge.textContent = 'OFFICER';
    badge.style.color = 'var(--accent-red)';
    badge.style.textShadow = 'var(--red-glow)';
    list.innerHTML = `
      <li><i class="fa-solid fa-check"></i> Search case records</li>
      <li><i class="fa-solid fa-check"></i> View case details</li>
      <li><i class="fa-solid fa-check"></i> Report incidents</li>
      <li><i class="fa-solid fa-check"></i> Add / Edit records</li>
      <li><i class="fa-solid fa-check"></i> Delete records</li>
      <li><i class="fa-solid fa-check"></i> Full Officer dashboard</li>`;
  } else {
    badge.textContent = 'CITIZEN';
    badge.style.color = 'var(--accent-cyan)';
    badge.style.textShadow = 'var(--cyan-glow)';
    list.innerHTML = `
      <li><i class="fa-solid fa-check"></i> Search case records</li>
      <li><i class="fa-solid fa-check"></i> View case details</li>
      <li><i class="fa-solid fa-check"></i> Report incidents</li>
      <li class="locked"><i class="fa-solid fa-lock"></i> Add / Edit records</li>
      <li class="locked"><i class="fa-solid fa-lock"></i> Delete records</li>
      <li class="locked"><i class="fa-solid fa-lock"></i> Officer dashboard</li>`;
  }
}

/* ── Login ────────────────────────────────────────────────── */
qs('#loginBtn').addEventListener('click', doLogin);
qs('#loginUser').addEventListener('keydown', e => { if (e.key === 'Enter') doLogin(); });
qs('#loginPass').addEventListener('keydown', e => { if (e.key === 'Enter') doLogin(); });

async function doLogin() {
  const user  = qs('#loginUser').value.trim();
  const pass  = qs('#loginPass').value.trim();
  const errEl = qs('#loginError');
  errEl.textContent = '';
  if (!user || !pass) { errEl.textContent = 'Please fill in all fields.'; return; }

  const btn = qs('#loginBtn');
  btn.disabled = true; btn.textContent = 'Authenticating…';

  try {
    const ok = await Auth.login(user, pass);
    if (!ok) throw new Error('bad_credentials');
    await fetchCurrentUser();
    updateNavForUser();
    updateAlertBadge();
    toast(`Welcome back, ${currentUser.username}! (${currentUser.role === 'officer' ? 'Officer' : 'Citizen'})`, 'success');
    qs('#loginUser').value = '';
    qs('#loginPass').value = '';
    showPage(currentUser.role === 'officer' ? 'manage' : 'search');
  } catch (e) {
    currentUser = null;
    errEl.textContent = 'Invalid username or password.';
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="fa-solid fa-fingerprint"></i> Authenticate';
  }
}

async function fetchCurrentUser() {
  const res = await fetch('http://127.0.0.1:8000/api/me/', { credentials: 'include' });
  if (!res.ok) throw new Error('me_failed');
  const ud = await res.json();
  currentUser = {
    username: ud.username,
    email:    ud.email || '',
    role:     ud.role,           // 'officer' | 'admin' | 'citizen'
    is_staff: ud.is_staff,
  };
}

function updateNavForUser() {
  const signupBtn = qs('#navSignupBtn');
  if (currentUser) {
    hide(qs('#navLoginBtn'));
    if (signupBtn) hide(signupBtn);
    show(qs('#navLogoutBtn'));
    show(qs('#userPill'));

    const pillName = qs('#userPillName');
    const pillRole = qs('#userPillRole');
    if (pillName) pillName.textContent = currentUser.username;
    if (pillRole) {
      const isOfficer = currentUser.role === 'officer' || currentUser.role === 'admin';
      pillRole.textContent       = isOfficer ? 'OFFICER' : 'CITIZEN';
      pillRole.style.background  = isOfficer ? 'rgba(232,51,74,0.18)'  : 'rgba(34,211,238,0.15)';
      pillRole.style.color       = isOfficer ? 'var(--accent-red)'     : 'var(--accent-cyan)';
      pillRole.style.border      = isOfficer ? '1px solid rgba(232,51,74,0.35)' : '1px solid rgba(34,211,238,0.35)';
    }
    if (currentUser.role === 'officer' || currentUser.role === 'admin') {
      show(qs('#navManage')); hide(qs('#navMyReports'));
    } else {
      show(qs('#navMyReports')); hide(qs('#navManage'));
    }
  } else {
    show(qs('#navLoginBtn'));
    if (signupBtn) show(signupBtn);
    hide(qs('#navLogoutBtn'));
    hide(qs('#userPill'));
    hide(qs('#navManage'));
    if (qs('#navMyReports')) hide(qs('#navMyReports'));
  }
}

/* ── Logout ───────────────────────────────────────────────── */
qs('#navLogoutBtn').addEventListener('click', async () => {
  await Auth.logout();
  currentUser = null;
  updateNavForUser();

  qs('#loginSection').classList.remove('hidden');
  qs('#registerForm').classList.add('hidden');
  qs('#loginUser').value        = '';
  qs('#loginPass').value        = '';
  qs('#loginError').textContent = '';
  qs('#regUser').value          = '';
  qs('#regEmail').value         = '';
  qs('#regPass').value          = '';
  qs('#regPass2').value         = '';
  qs('#registerError').textContent = '';

  toast('Logged out successfully.', 'info');
  showPage('landing');
});

/* ── Sign Up ──────────────────────────────────────────────── */
const showRegister = qs('#showRegister');
if (showRegister) {
  showRegister.addEventListener('click', e => {
    e.preventDefault();
    qs('#loginSection').classList.add('hidden');
    qs('#registerForm').classList.remove('hidden');
    qs('#loginUser').value = ''; qs('#loginPass').value = ''; qs('#loginError').textContent = '';
    qs('#regUser').value = ''; qs('#regEmail').value = ''; qs('#regPass').value = ''; qs('#regPass2').value = ''; qs('#registerError').textContent = '';
  });
}

const regBtn = qs('#regBtn');
if (regBtn) regBtn.addEventListener('click', doRegister);
['regUser','regPass','regPass2','regEmail'].forEach(id => {
  const el = qs('#' + id);
  if (el) el.addEventListener('keydown', e => { if (e.key === 'Enter') doRegister(); });
});

async function doRegister() {
  const username  = qs('#regUser').value.trim();
  const password  = qs('#regPass').value;
  const password2 = qs('#regPass2').value;
  const email     = qs('#regEmail').value.trim();
  const errEl     = qs('#registerError');
  errEl.textContent = '';

  if (!username || !password || !password2) { errEl.textContent = 'All fields except email are required.'; return; }
  if (password.length < 6)  { errEl.textContent = 'Password must be at least 6 characters.'; return; }
  if (password !== password2) { errEl.textContent = 'Passwords do not match.'; return; }

  const btn = qs('#regBtn');
  btn.disabled = true; btn.textContent = 'Creating account…';

  try {
    // Register (always citizen — backend enforces this)
    await Auth.register(username, password, password2, email);
    // Auto-login immediately after
    const ok = await Auth.login(username, password);
    if (!ok) throw new Error('auto_login_failed');
    await fetchCurrentUser();
    updateNavForUser();
    updateAlertBadge();

    qs('#registerForm').classList.add('hidden');
    qs('#regUser').value = ''; qs('#regEmail').value = ''; qs('#regPass').value = ''; qs('#regPass2').value = '';

    toast('Account created successfully!', 'success');
    showPage(currentUser.role === 'officer' ? 'manage' : 'search');
  } catch (err) {
    if (err.fieldErrors) {
      errEl.textContent = Object.entries(err.fieldErrors)
        .map(([f, e]) => `${f}: ${Array.isArray(e) ? e.join(', ') : e}`)
        .join(' | ');
    } else {
      errEl.textContent = 'Registration failed. Please try again.';
    }
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="fa-solid fa-user-plus"></i> Create Account';
  }
}

const backToLoginBtn = qs('#backToLoginBtn');
if (backToLoginBtn) {
  backToLoginBtn.addEventListener('click', () => {
    qs('#loginSection').classList.remove('hidden');
    qs('#registerForm').classList.add('hidden');
    qs('#regUser').value = ''; qs('#regEmail').value = ''; qs('#regPass').value = ''; qs('#regPass2').value = ''; qs('#registerError').textContent = '';
  });
}

/* ── Search page ──────────────────────────────────────────── */
async function initSearch() {
  showTableLoading('casesTableBody', 8);
  try {
    const records = await Cases.list();
    renderSearchTable(records);
  } catch (e) {
    console.error(e);
    toast('Failed to load cases — is the Django server running on port 8000?', 'error');
  }
  const btn = qs('#reportCaseBtn');
  if (btn) btn.style.display = currentUser ? '' : 'none';
}

qs('#searchBtn').addEventListener('click', doSearch);
qs('#clearBtn').addEventListener('click', async () => {
  qsa('#filterID,#filterVictim,#filterSuspect,#filterArea').forEach(i => i.value = '');
  qs('#filterType').value = '';
  showTableLoading('casesTableBody', 8);
  renderSearchTable(await Cases.list());
});

['filterID','filterVictim','filterSuspect','filterArea','filterType'].forEach(id => {
  const el = qs('#' + id);
  if (el) el.addEventListener('keydown', e => { if (e.key === 'Enter') doSearch(); });
});

async function doSearch() {
  showTableLoading('casesTableBody', 8);
  try {
    const status = qs('#filterType').value || undefined;
    const search = (qs('#filterVictim').value || qs('#filterSuspect').value || qs('#filterArea').value) || undefined;
    renderSearchTable(await Cases.list({ search, status }));
  } catch (e) { console.error(e); toast('Search failed', 'error'); }
}

function renderSearchTable(records) {
  const tbody     = qs('#casesTableBody');
  const noRes     = qs('#noResults');
  const count     = qs('#resultCount');
  const isOfficer = currentUser && (currentUser.role === 'officer' || currentUser.role === 'admin');

  count.textContent = records.length;
  if (!records.length) { tbody.innerHTML = ''; show(noRes); return; }
  hide(noRes);

  tbody.innerHTML = records.map(r => `
    <tr>
      <td><span class="case-id">${esc(r.id)}</span></td>
      <td>${formatDate(r.date)}</td>
      <td><span class="crime-tag">${esc(r.type)}</span></td>
      <td>${esc(r.victim)}</td>
      <td>${esc(r.suspect)}</td>
      <td><i class="fa-solid fa-location-dot" style="color:var(--text-dim);margin-right:4px"></i>${esc(r.location)}</td>
      <td>${statusBadge(r.status)}</td>
      <td class="action-btns">
        <button class="btn-icon btn-view" data-id="${r.id}" data-action="view" title="View"><i class="fa-solid fa-eye"></i></button>
        ${isOfficer ? `
        <button class="btn-icon btn-edit" data-id="${r.id}" data-action="edit" title="Edit"><i class="fa-solid fa-pen"></i></button>
        <button class="btn-icon btn-delete" data-id="${r.id}" data-action="delete" title="Delete"><i class="fa-solid fa-trash"></i></button>` : ''}
      </td>
    </tr>`).join('');

  tbody.querySelectorAll('[data-action="view"]').forEach(b => b.addEventListener('click', () => openViewModal(b.dataset.id)));
  tbody.querySelectorAll('[data-action="edit"]').forEach(b => b.addEventListener('click', () => openCaseModal(b.dataset.id)));
  tbody.querySelectorAll('[data-action="delete"]').forEach(b => b.addEventListener('click', () => confirmDelete(b.dataset.id, b.dataset.id)));
}

qs('#reportCaseBtn').addEventListener('click', () => {
  if (!currentUser) { toast('Please login to report a case.', 'error'); showPage('login'); return; }
  openCaseModal(null);
});

/* ── Alerts page ──────────────────────────────────────────── */
async function renderAlerts(filter = 'all') {
  const grid    = qs('#alertsGrid');
  const loading = qs('#alertsLoading');
  grid.innerHTML = '';
  if (loading) show(loading);

  try {
    const alerts = await Alerts.list();
    if (loading) hide(loading);

    const badge = qs('#alertBadge');
    if (badge) badge.textContent = alerts.length;

    const filtered = filter === 'all' ? alerts : alerts.filter(a => a.severity === filter);

    if (!filtered.length) {
      grid.innerHTML = `<div style="padding:40px;text-align:center;color:var(--text-dim)">
        <i class="fa-solid fa-bell-slash" style="font-size:32px;margin-bottom:12px;display:block"></i>
        No ${filter === 'all' ? '' : filter + ' '}alerts at this time.</div>`;
      return;
    }

    const icons  = { critical:'fa-circle-exclamation', warning:'fa-triangle-exclamation', info:'fa-circle-info' };
    const labels = { critical:'CRITICAL', warning:'WARNING', info:'INFO' };

    grid.innerHTML = filtered.map(a => `
      <div class="alert-card ${esc(a.severity)}">
        <div class="alert-top">
          <span class="alert-severity">
            <i class="fa-solid ${icons[a.severity] || 'fa-bell'}"></i> ${labels[a.severity] || a.severity.toUpperCase()}
          </span>
          <span class="alert-time"><i class="fa-regular fa-clock"></i> ${formatDate(a.created_at)}</span>
        </div>
        <div class="alert-title">${esc(a.title)}</div>
        <div class="alert-desc">${esc(a.description)}</div>
        <div class="alert-footer">
          <span><i class="fa-solid fa-tag"></i> ${esc(a.alert_type)}</span>
          ${a.location_label ? `<span><i class="fa-solid fa-location-dot"></i> ${esc(a.location_label)}</span>` : ''}
        </div>
      </div>`).join('');
  } catch (e) {
    if (loading) hide(loading);
    console.error('Alerts error:', e);
    grid.innerHTML = `<div style="padding:40px;text-align:center;color:var(--accent-red)">
      <i class="fa-solid fa-circle-xmark" style="font-size:32px;margin-bottom:12px;display:block"></i>
      Failed to load alerts.<br><small style="color:var(--text-dim)">Ensure Django is running on port 8000.</small></div>`;
  }
}

document.addEventListener('click', e => {
  const tab = e.target.closest('.atab');
  if (!tab) return;
  qsa('.atab').forEach(t => t.classList.remove('active'));
  tab.classList.add('active');
  renderAlerts(tab.dataset.filter);
});

async function updateAlertBadge() {
  try {
    const alerts = await Alerts.list();
    const badge = qs('#alertBadge');
    if (badge) badge.textContent = Array.isArray(alerts) ? alerts.length : 0;
  } catch (_) {}
}

/* ── Dashboard ────────────────────────────────────────────── */
Chart.defaults.color       = '#7a90b0';
Chart.defaults.borderColor = '#1e2a40';

async function initDashboard() {
  try {
    const data = await Analytics.summary();
    qs('#kpiOpen').textContent   = data.status_counts.open;
    qs('#kpiClosed').textContent = data.status_counts.closed;
    qs('#kpiInv').textContent    = data.status_counts.investigation;
    qs('#kpiTotal').textContent  = data.total_cases;
    if (typeChart) { typeChart.destroy(); typeChart = null; }
    buildTypeChart(data.by_crime_type);
    const badge = qs('#alertBadge');
    if (badge && data.active_alerts != null) badge.textContent = data.active_alerts;
  } catch (e) {
    console.error('Analytics summary:', e);
    toast('Failed to load analytics — check Django server.', 'error');
  }
  await buildYearChart();
  await buildMonthlyChart();
  buildIndiaMap();
  await buildHeatmap();
}

async function buildYearChart() {
  if (yearChart) { yearChart.destroy(); yearChart = null; }
  const ctx = qs('#yearChart'); if (!ctx) return;
  ctx.style.opacity = '0.3';
  try {
    const { years, series } = await Analytics.yearly();
    ctx.style.opacity = '1';
    const PALETTE = ['#3b82f6','#f0c040','#22d3ee','#e8334a','#f5732a','#22c55e','#a855f7','#ec4899','#14b8a6'];
    yearChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: years.map(String),
        datasets: series.map((s, i) => ({
          label: s.crime_type,
          data: s.data,
          backgroundColor: PALETTE[i % PALETTE.length],
          borderColor: PALETTE[i % PALETTE.length],
          borderWidth: 1,
        })),
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { position:'bottom', labels:{ boxWidth:12, padding:16, font:{ family:'Exo 2', size:11 } } } },
        scales: { x:{ grid:{ color:'rgba(255,255,255,0.04)' } }, y:{ grid:{ color:'rgba(255,255,255,0.04)' }, beginAtZero:true } },
      },
    });
  } catch (e) { ctx.style.opacity = '1'; console.error('Year chart:', e); }
}

function buildTypeChart(byType) {
  if (typeChart) { typeChart.destroy(); typeChart = null; }
  const labels = (byType || []).map(x => x.crime_type);
  const data   = (byType || []).map(x => x.count);
  const colors = ['#e8334a','#3b82f6','#22d3ee','#f0c040','#22c55e','#f5732a','#a855f7','#ec4899','#14b8a6'];
  const ctx = qs('#typeChart'); if (!ctx) return;
  typeChart = new Chart(ctx, {
    type: 'doughnut',
    data: { labels, datasets:[{ data, backgroundColor:colors.slice(0, labels.length), borderColor:'#101624', borderWidth:2 }] },
    options: { responsive:true, maintainAspectRatio:false, plugins:{ legend:{ position:'bottom', labels:{ boxWidth:10, padding:12, font:{ family:'Exo 2', size:11 } } } } },
  });
}

async function buildMonthlyChart() {
  if (monthlyChart) { monthlyChart.destroy(); monthlyChart = null; }
  const ctx = qs('#monthlyChart'); if (!ctx) return;
  ctx.style.opacity = '0.3';
  try {
    const { labels, data } = await Analytics.monthly(new Date().getFullYear());
    ctx.style.opacity = '1';
    monthlyChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets:[{ label:'Cases Filed', data,
          backgroundColor: data.map(v => v>=140?'rgba(232,51,74,0.8)':v>=120?'rgba(245,115,42,0.8)':'rgba(59,130,246,0.7)'),
          borderRadius:4, borderSkipped:false }],
      },
      options: {
        responsive:true, maintainAspectRatio:false,
        plugins:{ legend:{ display:false } },
        scales:{ x:{ grid:{ color:'rgba(255,255,255,0.04)' } }, y:{ grid:{ color:'rgba(255,255,255,0.04)' }, beginAtZero:true } },
      },
    });
  } catch (e) { ctx.style.opacity = '1'; console.error('Monthly chart:', e); }
}

async function buildHeatmap() {
  const grid = qs('#heatmapGrid'); if (!grid) return;
  grid.innerHTML = `<p style="color:var(--text-dim);padding:12px"><i class="fa-solid fa-spinner fa-spin"></i> Loading…</p>`;
  try {
    const areas = await Analytics.heatmap();
    if (!areas.length) { grid.innerHTML = `<p style="color:var(--text-dim);padding:12px">No location data yet.</p>`; return; }
    grid.innerHTML = areas.map(a => `
      <div class="heat-cell heat-${esc(a.level)}">
        <div class="cell-name">${esc(a.name)}</div>
        <div class="cell-count">${a.count}</div>
        <div class="cell-label">incidents</div>
      </div>`).join('');
  } catch (e) { console.error('Heatmap:', e); grid.innerHTML = `<p style="color:var(--accent-red);padding:12px">Failed to load heatmap.</p>`; }
}

function buildIndiaMap() {
  const container = document.getElementById('indiaMap'); if (!container) return;
  if (leafletMap) { leafletMap.remove(); leafletMap = null; }
  leafletMap = L.map('indiaMap').setView([22.9734,78.6569], 5);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{ attribution:'© OpenStreetMap' }).addTo(leafletMap);
  const zones = [
    { name:'Delhi',     coords:[28.7041,77.1025], level:'critical', incidents:220 },
    { name:'Mumbai',    coords:[19.0760,72.8777], level:'critical', incidents:198 },
    { name:'Bengaluru', coords:[12.9716,77.5946], level:'high',     incidents:563 },
    { name:'Hyderabad', coords:[17.3850,78.4867], level:'high',     incidents:147 },
    { name:'Chennai',   coords:[13.0827,80.2707], level:'medium',   incidents:89  },
  ];
  const cmap = { critical:'#e8334a', high:'#f5732a', medium:'#f0c040', low:'#22c55e' };
  zones.forEach(z => L.circle(z.coords,{ color:cmap[z.level], fillColor:cmap[z.level], fillOpacity:0.45, radius:40000 })
    .addTo(leafletMap).bindPopup(`<b>${esc(z.name)}</b><br>Level: <b>${z.level}</b><br>Incidents: ${z.incidents}`));
}

/* ── Manage (Officer only) ────────────────────────────────── */
if (qs('#btnFilterAll')) {
  qs('#btnFilterAll').addEventListener('click', () => {
    qs('#btnFilterAll').classList.add('active');
    qs('#btnFilterIncoming').classList.remove('active');
    manageFilter = null;
    renderManageTable();
  });
  qs('#btnFilterIncoming').addEventListener('click', () => {
    qs('#btnFilterIncoming').classList.add('active');
    qs('#btnFilterAll').classList.remove('active');
    manageFilter = 'Pending';
    renderManageTable();
  });
}

async function renderManageTable() {
  showTableLoading('manageTableBody', 8);
  try {
    const records = await Cases.list(manageFilter ? { status: manageFilter } : {});
    const tbody = qs('#manageTableBody');
    tbody.innerHTML = records.map(r => `
      <tr>
        <td>${esc(r.id)}</td><td>${formatDate(r.date)}</td><td>${esc(r.type)}</td>
        <td>${esc(r.victim)}</td><td>${esc(r.suspect)}</td><td>${esc(r.location)}</td>
        <td>${statusBadge(r.status)}</td>
        <td class="action-btns">
          <button class="btn-icon btn-view"   data-id="${r.id}" data-action="view"   title="View"><i class="fa-solid fa-eye"></i></button>
          <button class="btn-icon btn-edit"   data-id="${r.id}" data-action="edit"   title="Edit"><i class="fa-solid fa-pen"></i></button>
          <button class="btn-icon btn-delete" data-id="${r.id}" data-action="delete" title="Delete"><i class="fa-solid fa-trash"></i></button>
        </td>
      </tr>`).join('');
    tbody.querySelectorAll('[data-action="view"]').forEach(b => b.addEventListener('click', () => openViewModal(b.dataset.id)));
    tbody.querySelectorAll('[data-action="edit"]').forEach(b => b.addEventListener('click', () => openCaseModal(b.dataset.id)));
    tbody.querySelectorAll('[data-action="delete"]').forEach(b => b.addEventListener('click', () => confirmDelete(b.dataset.id, b.dataset.id)));
  } catch (e) {
    console.error(e);
    toast('Failed to load records', 'error');
  }
}

qs('#addCaseBtn').addEventListener('click', () => openCaseModal(null));

async function confirmDelete(id, displayId) {
  const label = displayId || `#${id}`;
  if (!confirm(`Permanently delete case ${label}?\n\nThis cannot be undone.`)) return;
  try {
    await Cases.delete(id);
    toast(`Case ${label} deleted.`, 'success');
    if (qs('#pageManage.active')) renderManageTable(); else initSearch();
  } catch (e) { console.error(e); toast('Delete failed — check permissions.', 'error'); }
}

/* ── Case modal ───────────────────────────────────────────── */
// FIX: clearModalForm and closeModal are top-level functions, NOT nested inside openCaseModal.
// In the original they were defined inside openCaseModal's body, making them unreachable
// from the modalClose / modalCancel / modalSave event listeners.

let editingID = null;

function clearModalForm() {
  ['mType','mVictim','mSuspect','mLocation','mDesc'].forEach(id => {
    const el = qs('#' + id); if (el) el.value = '';
  });
  if (qs('#mStatus')) qs('#mStatus').value = 'Open';
  if (qs('#mDate'))   qs('#mDate').value   = new Date().toISOString().slice(0, 10);
}

function closeModal() {
  qs('#caseModal').classList.remove('open');
  editingID = null;
}

async function openCaseModal(id) {
  editingID = id;
  qs('#modalError').textContent = '';
  clearModalForm();

  const isCitizen = currentUser && currentUser.role === 'citizen';
  if (qs('#mStatus')) qs('#mStatus').closest('.form-group').style.display  = isCitizen ? 'none' : '';
  if (qs('#mSuspect')) qs('#mSuspect').closest('.form-group').style.display = isCitizen ? 'none' : '';

  const saveBtn = qs('#modalSave');
  saveBtn.innerHTML = isCitizen
    ? '<i class="fa-solid fa-paper-plane"></i> Report Case'
    : '<i class="fa-solid fa-floppy-disk"></i> Save Case';

  if (id) {
    try {
      const rec = await Cases.get(id);
      if (qs('#mType'))     qs('#mType').value     = rec.type     || '';
      if (qs('#mVictim'))   qs('#mVictim').value   = rec.victim   || '';
      if (qs('#mSuspect'))  qs('#mSuspect').value  = rec.suspect  || '';
      if (qs('#mLocation')) qs('#mLocation').value = rec.location || '';
      if (qs('#mStatus'))   qs('#mStatus').value   = rec.status   || 'Open';
      if (qs('#mDate'))     qs('#mDate').value     = rec.date     || '';
      if (qs('#mDesc'))     qs('#mDesc').value     = rec.desc     || '';
    } catch (e) {
      toast('Failed to load case for editing.', 'error'); return;
    }
  }

  qs('#caseModal').classList.add('open');
}

qs('#modalClose').addEventListener('click', closeModal);
qs('#modalCancel').addEventListener('click', closeModal);
qs('#caseModal').addEventListener('click', e => { if (e.target === qs('#caseModal')) closeModal(); });

qs('#modalSave').addEventListener('click', async () => {
  const err      = qs('#modalError');
  err.textContent = '';
  const type     = qs('#mType')     ? qs('#mType').value.trim()     : '';
  const date     = qs('#mDate')     ? qs('#mDate').value            : '';
  const victim   = qs('#mVictim')   ? qs('#mVictim').value.trim()   : '';
  const suspect  = qs('#mSuspect')  ? qs('#mSuspect').value.trim()  : 'Unknown';
  const location = qs('#mLocation') ? qs('#mLocation').value.trim() : '';
  const status   = qs('#mStatus')   ? qs('#mStatus').value          : 'Open';
  const desc     = qs('#mDesc')     ? qs('#mDesc').value.trim()     : '';

  if (!type || !victim || !location || !date) {
    err.textContent = 'Crime Type, Date, Victim, and Location are required.';
    return;
  }

  const saveBtn = qs('#modalSave');
  saveBtn.disabled = true; saveBtn.textContent = 'Saving…';

  try {
    const payload = { type, date, victim, suspect, location, status, desc };
    if (editingID) {
      await Cases.update(editingID, payload);
      toast('Case updated.', 'success');
    } else {
      await Cases.create(payload);
      toast('Case created.', 'success');
    }
    closeModal();
    if (qs('#pageManage.active')) renderManageTable(); else initSearch();
  } catch (e) {
    console.error(e);
    const d = e.detail;
    err.textContent = d && typeof d === 'object'
      ? Object.entries(d).map(([f, errs]) => `${f}: ${Array.isArray(errs) ? errs.join(', ') : errs}`).join(' | ')
      : 'Save failed. Check your input.';
  } finally {
    saveBtn.disabled = false;
    const isCitizen = currentUser && currentUser.role === 'citizen';
    saveBtn.innerHTML = isCitizen
      ? '<i class="fa-solid fa-paper-plane"></i> Report Case'
      : '<i class="fa-solid fa-floppy-disk"></i> Save Case';
  }
});

/* ── View modal ───────────────────────────────────────────── */
async function openViewModal(id) {
  qs('#viewModal').classList.add('open');
  qs('#viewModalTitle').innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Loading…`;
  qs('#viewModalBody').innerHTML  = '';
  try {
    const rec = await Cases.get(id);
    if (!rec) return;
    qs('#viewModalTitle').innerHTML = `<i class="fa-solid fa-file-lines"></i> Case — ${esc(rec.id)}`;

    const isOfficer = currentUser && (currentUser.role === 'officer' || currentUser.role === 'admin');
    const takeBtn   = (isOfficer && rec.status === 'Pending')
      ? `<button class="btn-primary" id="btnTakeCase" style="margin-top:16px;width:100%;justify-content:center;">
           <i class="fa-solid fa-clipboard-check"></i> Take Case
         </button>`
      : '';

    qs('#viewModalBody').innerHTML = `
      <div class="case-detail-grid">
        <p><strong>ID:</strong> ${esc(rec.id)}</p>
        <p><strong>Date:</strong> ${formatDate(rec.date)}</p>
        <p><strong>Type:</strong> ${esc(rec.type)}</p>
        <p><strong>Status:</strong> ${statusBadge(rec.status)}</p>
        <p><strong>Victim:</strong> ${esc(rec.victim)}</p>
        <p><strong>Suspect:</strong> ${esc(rec.suspect)}</p>
        <p><strong>Location:</strong> ${esc(rec.location)}</p>
        <p class="full-col"><strong>Description:</strong> ${esc(rec.desc) || '—'}</p>
      </div>
      ${takeBtn}`;

    if (qs('#btnTakeCase')) {
      qs('#btnTakeCase').addEventListener('click', async () => {
        const btn = qs('#btnTakeCase');
        btn.disabled = true; btn.textContent = 'Assigning...';
        try {
          await Cases.takeCase(id);
          toast('Case assigned to you!', 'success');
          qs('#viewModal').classList.remove('open');
          renderManageTable();
        } catch (e) {
          toast('Failed to take case.', 'error');
          btn.disabled = false;
        }
      });
    }
  } catch (e) {
    qs('#viewModalBody').innerHTML = `<p style="color:var(--accent-red)">Failed to load case details.</p>`;
  }
}

qs('#viewModalClose').addEventListener('click', () => qs('#viewModal').classList.remove('open'));
qs('#viewModal').addEventListener('click', e => { if (e.target === qs('#viewModal')) qs('#viewModal').classList.remove('open'); });

/* ── Landing counters ─────────────────────────────────────── */
function animateCounters() {
  qsa('[data-target]').forEach(el => {
    const target = parseInt(el.dataset.target); let start = 0;
    const step = target / 60;
    const timer = setInterval(() => {
      start = Math.min(start + step, target);
      el.textContent = Math.floor(start).toLocaleString();
      if (start >= target) clearInterval(timer);
    }, 20);
  });
}

/* ── Init ─────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  upgradeCrimeTypeField();
  fixSearchFilter();
});

(async function init() {
  updateNavForUser();
  if (Auth.isLoggedIn()) {
    try {
      await fetchCurrentUser();
      updateNavForUser();
      updateAlertBadge();
      showPage(currentUser.role === 'officer' || currentUser.role === 'admin' ? 'manage' : 'search');
    } catch {
      await Auth.logout().catch(() => {});
      currentUser = null;
      updateNavForUser();
      showPage('landing');
    }
  } else {
    showPage('landing');
    updateAlertBadge();
  }
  setTimeout(animateCounters, 400);
})();