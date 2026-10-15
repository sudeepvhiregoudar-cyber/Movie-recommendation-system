(() => {
  const $ = (s, el = document) => el.querySelector(s);
  const LIMIT = 12;
  const GENRES = ['Action', 'Adventure', 'Animation', 'Comedy', 'Crime', 'Drama', 'Family', 'Fantasy', 'Horror', 'Mystery', 'Romance', 'Science Fiction', 'Thriller'];
  const state = { token: localStorage.getItem('token'), user: null, ratings: new Map(), genre: '', q: '', skip: 0, authMode: 'login' };

  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const list = s => (s || '').split('|').filter(Boolean);
  const year = m => (m.release_date || '').slice(0, 4);
  const hue = s => [...s].reduce((a, c) => (a * 31 + c.charCodeAt(0)) % 360, 7);
  const skeleton = n => '<div class="sk"></div>'.repeat(n);

  let toastTimer;
  function toast(msg, bad) {
    const t = $('#toast');
    t.textContent = msg;
    t.className = 'show' + (bad ? ' bad' : '');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => (t.className = ''), 2800);
  }

  async function api(path, { method = 'GET', body } = {}) {
    const headers = {};
    if (body) headers['Content-Type'] = 'application/json';
    if (state.token) headers.Authorization = 'Bearer ' + state.token;
    const res = await fetch(path, { method, headers, body: body ? JSON.stringify(body) : undefined });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      if (res.status === 401 && state.token) logout(true);
      const d = data.detail;
      throw new Error(typeof d === 'string' ? d : d && d[0] ? `${d[0].loc.slice(-1)[0]}: ${d[0].msg}` : 'Request failed');
    }
    return data;
  }

  /* ---------- rendering ---------- */
  function card(m, match) {
    const mine = state.ratings.get(m.id);
    return `<article class="card" data-id="${m.id}" tabindex="0" role="button" aria-label="${esc(m.title)}">
      <div class="poster" style="--h:${hue(list(m.genres)[0] || m.title)}">
        <span class="badge">★ ${Number(m.vote_average).toFixed(1)}</span>
        ${match != null ? `<span class="match">${Math.round(match * 100)}% match</span>` : ''}
        <span class="pt">${esc(m.title)}</span>
        ${mine ? `<span class="mine">You ${mine.rating}★</span>` : ''}
      </div>
      <div class="meta"><h3>${esc(m.title)}</h3><p>${esc(year(m))} · ${esc(list(m.genres).slice(0, 2).join(', '))}</p></div></article>`;
  }
  const fill = (sel, results, showMatch) => { $(sel).innerHTML = results.map(x => card(x.movie, showMatch ? x.score : null)).join('') || '<p class="empty">Nothing to show yet.</p>'; };

  function renderNav() {
    $('#auth').innerHTML = state.user
      ? `<span class="user">Hi, ${esc(state.user.username)}</span><button class="ghost" id="logoutBtn">Log out</button>`
      : `<button class="ghost" data-open="login">Log in</button><button class="primary" data-open="register">Sign up</button>`;
  }

  function renderChips() {
    $('#chips').innerHTML = ['All', ...GENRES].map(g => `<button class="chip ${(g === 'All' ? '' : g) === state.genre ? 'on' : ''}" data-genre="${g === 'All' ? '' : g}">${g}</button>`).join('');
    $('#chips').hidden = !!state.q;
  }

  /* ---------- data loading ---------- */
  async function loadHome() {
    $('#trending').innerHTML = $('#popular').innerHTML = skeleton(6);
    try {
      const [t, p] = await Promise.all([api('/api/recommendations/trending?n=6'), api('/api/recommendations/popular?n=6')]);
      fill('#trending', t.results);
      fill('#popular', p.results);
    } catch (e) { toast(e.message, true); }
  }

  async function loadRecs() {
    const sec = $('#sec-recs');
    sec.hidden = !state.user || !!state.q;
    if (sec.hidden) return;
    $('#recs').innerHTML = skeleton(6);
    try {
      const r = await api(`/api/recommendations/user/${state.user.id}?n=6`);
      const hybrid = r.strategy === 'hybrid';
      $('#recs-sub').textContent = hybrid ? 'Hybrid picks: collaborative filtering combined with content similarity' : 'Rate a few movies to personalise this list. Showing popular titles for now.';
      fill('#recs', r.results, hybrid);
    } catch (e) { $('#recs').innerHTML = `<p class="empty">${esc(e.message)}</p>`; }
  }

  async function loadBrowse(reset = true) {
    if (reset) { state.skip = 0; $('#grid').innerHTML = skeleton(LIMIT); }
    const url = state.q
      ? `/api/movies/search?q=${encodeURIComponent(state.q)}&skip=${state.skip}&limit=${LIMIT}`
      : `/api/movies?skip=${state.skip}&limit=${LIMIT}${state.genre ? '&genre=' + encodeURIComponent(state.genre) : ''}`;
    try {
      const d = await api(url);
      const html = d.items.map(m => card(m)).join('');
      $('#grid').innerHTML = reset ? html || '<p class="empty">No movies found.</p>' : $('#grid').innerHTML + html;
      state.skip += d.items.length;
      $('#count').textContent = `${d.total} movie${d.total === 1 ? '' : 's'}`;
      $('#more').hidden = state.skip >= d.total;
    } catch (e) { toast(e.message, true); }
  }

  async function loadUser() {
    if (!state.token) return;
    try {
      state.user = await api('/api/users/profile');
      const rs = await api('/api/users/ratings');
      state.ratings = new Map(rs.map(r => [r.movie_id, { id: r.id, rating: r.rating }]));
    } catch { state.user = null; }
    renderNav();
    loadRecs();
    loadBrowse(true);
  }

  function logout(expired) {
    state.token = null; state.user = null; state.ratings = new Map();
    localStorage.removeItem('token');
    renderNav(); loadRecs(); loadBrowse(true);
    toast(expired === true ? 'Session expired, please log in again' : 'Logged out');
  }

  /* ---------- search & filters ---------- */
  function applySearch(q) {
    state.q = q; state.genre = '';
    document.querySelectorAll('.home-only, #hero, #sec-recs').forEach(el => { el.hidden = !!q || (el.id === 'sec-recs' && !state.user); });
    $('#browseTitle').textContent = q ? `Results for “${q}”` : 'Browse all movies';
    renderChips(); loadBrowse(true);
  }

  /* ---------- movie detail & rating ---------- */
  const starsHTML = id => { const cur = state.ratings.get(id)?.rating || 0; return [1, 2, 3, 4, 5].map(n => `<button class="star ${n <= cur ? 'on' : ''}" data-v="${n}" aria-label="Rate ${n} out of 5">★</button>`).join(''); };

  function detailHTML(m, similar) {
    const mine = state.ratings.get(m.id);
    return `<div class="detail" data-id="${m.id}">
      <div class="poster" style="--h:${hue(list(m.genres)[0] || m.title)}"><span class="pt">${esc(m.title)}</span></div>
      <div>
        <h2>${esc(m.title)}</h2>
        <p class="facts">${esc(year(m))} · ★ ${Number(m.vote_average).toFixed(1)} (${Number(m.vote_count).toLocaleString()} votes)${m.director ? ' · Directed by ' + esc(m.director) : ''}</p>
        <div class="tags">${list(m.genres).map(g => `<span class="tag">${esc(g)}</span>`).join('')}</div>
        <p>${esc(m.overview)}</p>
        ${m.cast_names ? `<p><span class="label">Cast</span>${esc(list(m.cast_names).join(', '))}</p>` : ''}
        ${m.keywords ? `<span class="label">Keywords</span><div class="tags">${list(m.keywords).map(k => `<span class="tag">${esc(k)}</span>`).join('')}</div>` : ''}
        <span class="label">${state.user ? (mine ? 'Your rating' : 'Rate this movie') : 'Log in to rate this movie'}</span>
        <div class="stars" id="stars">${starsHTML(m.id)}</div>
      </div>
      <div class="similar"><h3>Similar movies</h3><div class="grid">${similar.map(x => card(x.movie, x.score)).join('') || '<p class="empty">No similar movies found.</p>'}</div></div>
    </div>`;
  }

  async function openMovie(id) {
    const dlg = $('#movieModal');
    $('#movieBody').innerHTML = '<div class="loading" style="padding:40px">Loading…</div>';
    if (!dlg.open) dlg.showModal();
    try {
      const [m, sim] = await Promise.all([api('/api/movies/' + id), api(`/api/recommendations/movie/${id}?n=6`)]);
      $('#movieBody').innerHTML = detailHTML(m, sim.results);
      dlg.scrollTo(0, 0);
    } catch (e) { $('#movieBody').innerHTML = `<p class="empty" style="padding:40px">${esc(e.message)}</p>`; }
  }

  async function rate(id, value) {
    if (!state.user) { $('#movieModal').close(); openAuth('login'); toast('Please log in to rate movies', true); return; }
    try {
      const ex = state.ratings.get(id);
      const r = ex
        ? await api('/api/ratings/' + ex.id, { method: 'PUT', body: { rating: value } })
        : await api('/api/ratings', { method: 'POST', body: { movie_id: id, rating: value } });
      state.ratings.set(id, { id: r.id, rating: r.rating });
      $('#stars').innerHTML = starsHTML(id);
      toast(`Saved: ${value} out of 5`);
      loadRecs();
    } catch (e) { toast(e.message, true); }
  }

  /* ---------- auth dialog ---------- */
  function setMode(mode) {
    state.authMode = mode;
    document.querySelectorAll('.tab').forEach(t => t.classList.toggle('on', t.dataset.mode === mode));
    $('#emailRow').hidden = mode !== 'register';
    $('#emailRow input').required = mode === 'register';
    $('#authSubmit').textContent = mode === 'login' ? 'Log in' : 'Create account';
    $('#authErr').textContent = '';
  }
  function openAuth(mode) { setMode(mode); $('#authModal').showModal(); }

  $('#authForm').addEventListener('submit', async e => {
    e.preventDefault();
    const f = new FormData(e.target);
    const btn = $('#authSubmit'); btn.disabled = true;
    try {
      if (state.authMode === 'register') await api('/api/auth/register', { method: 'POST', body: { username: f.get('username'), email: f.get('email'), password: f.get('password') } });
      const t = await api('/api/auth/login', { method: 'POST', body: { username: f.get('username'), password: f.get('password') } });
      state.token = t.access_token; localStorage.setItem('token', t.access_token);
      $('#authModal').close(); e.target.reset();
      await loadUser();
      toast(state.user ? `Welcome, ${state.user.username}` : 'Logged in');
    } catch (err) { $('#authErr').textContent = err.message; }
    btn.disabled = false;
  });

  /* ---------- events ---------- */
  document.addEventListener('click', e => {
    const t = e.target;
    if (t.closest('[data-close]')) return t.closest('dialog').close();
    if (t === $('#movieModal') || t === $('#authModal')) return t.close();
    const open = t.closest('[data-open]'); if (open) return openAuth(open.dataset.open);
    if (t.closest('#logoutBtn')) return logout();
    const tab = t.closest('.tab'); if (tab) return setMode(tab.dataset.mode);
    const chip = t.closest('.chip'); if (chip) { state.genre = chip.dataset.genre; renderChips(); return loadBrowse(true); }
    const star = t.closest('.star'); if (star) return rate(Number($('.detail').dataset.id), Number(star.dataset.v));
    const c = t.closest('.card'); if (c) return openMovie(c.dataset.id);
  });
  document.addEventListener('keydown', e => { if (e.key === 'Enter' && e.target.classList?.contains('card')) openMovie(e.target.dataset.id); });
  $('#more').addEventListener('click', () => loadBrowse(false));
  $('#searchForm').addEventListener('submit', e => { e.preventDefault(); applySearch($('#searchInput').value.trim()); });
  $('#searchInput').addEventListener('input', e => { if (!e.target.value && state.q) applySearch(''); });
  $('#themeBtn').addEventListener('click', () => {
    const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = next; localStorage.theme = next;
  });

  /* ---------- init ---------- */
  renderNav(); renderChips(); loadHome(); loadBrowse(true); loadUser();
})();
