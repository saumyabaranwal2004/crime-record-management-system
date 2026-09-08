/**
 * app.js — NEXUS CRMS API client
 * Drop alongside index.html and script.js.
 */

const API_BASE = 'http://127.0.0.1:8000/api';

/* ── CSRF helper ─────────────────────────────────────────────── */
function getCookie(name) {
  if (!document.cookie) return null;
  const match = document.cookie
    .split(';')
    .map(c => c.trim())
    .find(c => c.startsWith(name + '='));
  return match ? decodeURIComponent(match.slice(name.length + 1)) : null;
}

/* ── Auth ────────────────────────────────────────────────────── */
const Auth = {
  isLoggedIn: () => !!sessionStorage.getItem('crms_role'),

  async login(username, password) {
    const res = await fetch(`${API_BASE}/login/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) return false;
    const data = await res.json();
    // Cache role/username in sessionStorage so UI can read them without
    // an extra /api/me/ round-trip on every page load.
    sessionStorage.setItem('crms_role',     data.role     ?? '');
    sessionStorage.setItem('crms_username', data.username ?? '');
    return true;
  },

  /**
   * POST /api/register/
   * Creates a citizen account.
   * Throws { fieldErrors, message } on 400.
   */
  async register(username, password, password2, email = '') {
    const res = await fetch(`${API_BASE}/register/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ username, password, password2, email }),
    });
    const data = await res.json();
    if (!res.ok) throw { fieldErrors: data, message: 'Registration failed.' };
    return data;
  },

  async logout() {
    await fetch(`${API_BASE}/logout/`, {
      method: 'POST',
      headers: { 'X-CSRFToken': getCookie('csrftoken') ?? '' },
      credentials: 'include',
    }).catch(() => {});
    sessionStorage.removeItem('crms_role');
    sessionStorage.removeItem('crms_username');
  },

  role:     () => sessionStorage.getItem('crms_role')     ?? '',
  username: () => sessionStorage.getItem('crms_username') ?? '',
  isOfficer: () => ['officer', 'admin'].includes(Auth.role()),
};

/* ── Generic request helper ──────────────────────────────────── */
async function apiRequest(path, method = 'GET', body = null) {
  const headers = { 'Content-Type': 'application/json' };

  const csrf = getCookie('csrftoken');
  if (csrf && ['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
    headers['X-CSRFToken'] = csrf;
  }

  const config = { method, headers, credentials: 'include' };
  if (body !== null) config.body = JSON.stringify(body);

  const res = await fetch(`${API_BASE}${path}`, config);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw Object.assign(new Error(`API ${method} ${path} [${res.status}]`), { detail: err });
  }
  return res.status === 204 ? null : res.json();
}

/* ── Cases ───────────────────────────────────────────────────── */
const Cases = {
  async list({ status, search, reporter } = {}) {
    const p = new URLSearchParams();
    if (status)   p.append('status',   status);
    if (search)   p.append('search',   search);
    if (reporter) p.append('reporter', reporter);
    return apiRequest(`/cases/${p.toString() ? '?' + p : ''}`);
  },
  async get(id)          { return apiRequest(`/cases/${id}/`); },
  async create(caseData) { return apiRequest('/cases/', 'POST', caseData); },
  async update(id, data) { return apiRequest(`/cases/${id}/`, 'PATCH', data); },
  async delete(id)       { return apiRequest(`/cases/${id}/`, 'DELETE'); },
  async takeCase(id)     { return apiRequest(`/cases/${id}/take_case/`, 'POST'); },
};

/* ── Evidence ────────────────────────────────────────────────── */
const Evidence = {
  async listForCase(caseId) { return apiRequest(`/evidence/?case=${caseId}`); },
  async add(d)              { return apiRequest('/evidence/', 'POST', d); },
  async delete(id)          { return apiRequest(`/evidence/${id}/`, 'DELETE'); },
};

/* ── Alerts ──────────────────────────────────────────────────── */
const Alerts = {
  async list(severity = null) {
    return apiRequest(`/alerts/${severity && severity !== 'all' ? '?severity=' + severity : ''}`);
  },
};

/* ── Analytics ───────────────────────────────────────────────── */
const Analytics = {
  async summary()            { return apiRequest('/analytics/summary/'); },
  async yearly()             { return apiRequest('/analytics/yearly/'); },
  async monthly(year = new Date().getFullYear()) {
    return apiRequest(`/analytics/monthly/?year=${year}`);
  },
  async heatmap()            { return apiRequest('/analytics/heatmap/'); },
};