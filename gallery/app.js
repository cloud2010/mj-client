const state = { before: 0, pageSize: 20, loading: false, done: false, total: 0, grandTotal: 0 };
const $ = (id) => document.getElementById(id);

function toast(text) {
  const el = document.createElement('div');
  el.className = 'toast-item';
  el.textContent = text;
  $('toast').appendChild(el);
  setTimeout(() => el.remove(), 2200);
}

function fmtTime(ts) {
  if (!ts) return '';
  const d = new Date(ts * 1000);
  const p = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`;
}

function statusBadge(msg) {
  const s = msg.status || '';
  const cls = s === 'SUCCESS' ? 'ok' : (s === 'FAILURE' || s === 'CANCEL' ? 'err' : 'warn');
  const label = { SUCCESS: '完成', FAILURE: '失败', CANCEL: '已取消', IN_PROGRESS: '生成中', NOT_START: '排队中', SUBMITTED: '已提交' }[s] || s;
  return `<span class="badge ${cls}">${label}</span>`;
}

/** 取出可展示/可下载的图片列表：四宫格优先用 image_urls，单图消息用 image_url。 */
function pickImages(msg) {
  const arr = (msg.image_urls || []).filter(Boolean);
  if (arr.length) {
    return arr.map((it) => ({ thumb: it.thumbnail || it.url, full: it.url }));
  }
  const full = msg.image_url || msg.cdn_image_url || '';
  if (full) return [{ thumb: msg.thumbnail_image_url || full, full }];
  return [];
}

/** 拼合图（四宫格那张大图）的 URL；单图消息返回空，避免重复下载。 */
function mergedImage(msg) {
  if ((msg.image_urls || []).length > 1) {
    return msg.image_url || msg.cdn_image_url || '';
  }
  return '';
}

function download(full, name) {
  const a = document.createElement('a');
  a.href = '/dl?url=' + encodeURIComponent(full) + '&name=' + encodeURIComponent(name);
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  toast('开始下载 ' + name);
}

function fileBase(msg) {
  return 'mj_' + msg.id;
}

function extOf(url) {
  const m = /\.([a-zA-Z0-9]+)(?:\?|$)/.exec(url || '');
  return m ? '.' + m[1].toLowerCase() : '.png';
}

function card(msg) {
  const imgs = pickImages(msg);
  const el = document.createElement('article');
  el.className = 'card';

  const tiles = document.createElement('div');
  tiles.className = 'tiles ' + (imgs.length > 1 ? 'four' : 'one');
  imgs.forEach((img, i) => {
    const tile = document.createElement('div');
    tile.className = 'tile';
    tile.title = '点击下载原图';
    const name = `${fileBase(msg)}_${i + 1}${extOf(img.full)}`;
    tile.innerHTML =
      (imgs.length > 1 ? `<span class="idx">${i + 1}</span>` : '') +
      `<img loading="lazy" src="${img.thumb}" alt="image ${i + 1}">` +
      `<span class="hover"><span class="acts">` +
      `<button type="button" class="pill" data-act="dl">下载 PNG</button>` +
      `<button type="button" class="pill" data-act="pv">预览</button>` +
      `</span></span>`;
    tile.addEventListener('click', () => download(img.full, name));
    tile.querySelector('[data-act="dl"]').addEventListener('click', (e) => {
      e.stopPropagation();
      download(img.full, name);
    });
    tile.querySelector('[data-act="pv"]').addEventListener('click', (e) => {
      e.stopPropagation();
      openPreview(msg, imgs, i);
    });
    tiles.appendChild(tile);
  });

  const meta = document.createElement('div');
  meta.className = 'meta';
  const merged = mergedImage(msg);
  const type = msg.type === 'NIJI_JOURNEY' ? 'niji' : 'Midjourney';
  const action = msg.action ? ` · ${msg.action}` : '';
  const task = msg.task || {};
  const prompt = (task.prompt_en || task.prompt || msg.message_content || '').replace(/\*\*/g, '').trim();

  meta.innerHTML =
    `<div class="badges">
       ${statusBadge(msg)}
       <span class="badge type">${type}</span>
       <span class="badge">#${msg.id}</span>
       ${task.progress && msg.status !== 'SUCCESS' ? `<span class="badge warn">${task.progress}</span>` : ''}
       ${imgs.length > 1 ? `<span class="badge">${imgs.length} 张</span>` : ''}
       <span style="font-size:11px;color:var(--muted)">${action}</span>
     </div>
     <p class="prompt" title="点击展开/收起">${prompt ? escapeHtml(prompt) : '（无提示词）'}</p>
     <div class="foot">
       <span class="time">${fmtTime(msg.finish_time || msg.submit_time)}</span>
       ${merged ? `<button class="mini" data-merged="1">下载合图</button>` : ''}
       ${imgs.length > 1 ? `<button class="mini" data-all="1">下载全部 ${imgs.length} 张</button>` : ''}
       <button class="mini" data-copy="1">复制提示词</button>
       <button class="mini danger" data-del="1">删除</button>
     </div>`;

  meta.querySelector('.prompt').addEventListener('click', (e) => e.currentTarget.classList.toggle('open'));
  const allBtn = meta.querySelector('[data-all]');
  if (allBtn) {
    allBtn.addEventListener('click', () => {
      imgs.forEach((img, i) => {
        setTimeout(() => download(img.full, `${fileBase(msg)}_${i + 1}${extOf(img.full)}`), i * 350);
      });
    });
  }
  const mergedBtn = meta.querySelector('[data-merged]');
  if (mergedBtn) {
    mergedBtn.addEventListener('click', () => {
      download(merged, `${fileBase(msg)}_merged${extOf(merged)}`);
    });
  }
  meta.querySelector('[data-del]').addEventListener('click', async () => {
    if (!confirm(`确定删除消息 #${msg.id} 吗？该消息及其图片将从服务端移除，且不可恢复。`)) return;
    el.classList.add('deleting');
    try {
      const res = await fetch(`/api/msg/${msg.id}`, { method: 'DELETE' });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.error || ('HTTP ' + res.status));
      el.remove();
      state.total = Math.max(0, state.total - 1);
      $('count').textContent = `已加载 ${state.total} 条${state.grandTotal ? ' / 共 ' + Math.max(0, state.grandTotal - 1) : ''}`;
      state.grandTotal = state.grandTotal ? Math.max(0, state.grandTotal - 1) : 0;
      toast(`已删除 #${msg.id}`);
    } catch (err) {
      el.classList.remove('deleting');
      toast('删除失败：' + err.message);
    }
  });
  meta.querySelector('[data-copy]').addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(prompt);
      toast('提示词已复制');
    } catch { toast('复制失败，请手动选择文本'); }
  });

  el.append(tiles, meta);
  return el;
}

function escapeHtml(s) {
  return s.replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
}

async function loadMore(reset = false) {
  if (state.loading) return;
  if (reset) {
    state.before = 0; state.done = false; state.total = 0;
    $('grid').innerHTML = '';
  }
  if (state.done) return;
  state.loading = true;
  $('spinner').style.display = 'block';
  $('emptyText').textContent = '加载中…';
  $('empty').style.display = $('grid').children.length ? 'none' : 'block';
  $('more').style.display = 'none';
  try {
    const res = await fetch(`/api/list?page_size=${state.pageSize}&before=${state.before}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || ('HTTP ' + res.status));
    const list = (data.list || []).filter((m) => pickImages(m).length);
    const frag = document.createDocumentFragment();
    list.forEach((m) => frag.appendChild(card(m)));
    $('grid').appendChild(frag);
    state.total += list.length;
    const pg = data.pagination || {};
    if (reset) state.grandTotal = pg.total || 0;
    $('count').textContent = `已加载 ${state.total} 条${pg.total ? ' / 共 ' + pg.total : ''}`;
    if (!data.list || data.list.length < state.pageSize) {
      state.done = true;
    } else {
      const times = data.list.map((m) => m.submit_time).filter(Boolean);
      state.before = times.length ? Math.min(...times) : state.before;
      if (!times.length) state.done = true;
    }
    $('banner').classList.remove('show');
  } catch (err) {
    const b = $('banner');
    b.textContent = '加载失败：' + err.message + '（确认 server.py 正在运行且 Auth Code 有效）';
    b.classList.add('show');
  } finally {
    state.loading = false;
    $('spinner').style.display = 'none';
    const has = $('grid').children.length > 0;
    $('empty').style.display = has ? 'none' : 'block';
    $('emptyText').textContent = has ? '' : '暂无图片';
    $('more').style.display = state.done || !has ? 'none' : 'block';
    $('more').textContent = '加载更多';
    $('more').disabled = false;
  }
}

/* ---------------- 进行中的任务（实时进度） ---------------- */
const ACTIVE_STATUS = new Set(['NOT_START', 'SUBMITTED', 'IN_PROGRESS']);
const DONE_STATUS = new Set(['SUCCESS', 'FAILURE', 'CANCEL']);
const tasks = { watching: new Set(), seen: new Map(), busy: false, timer: null };

function statusLabel(s) {
  return { SUCCESS: '完成', FAILURE: '失败', CANCEL: '已取消', IN_PROGRESS: '生成中',
           NOT_START: '排队中', SUBMITTED: '已提交' }[s] || s || '未知';
}
function statusCls(s) {
  return s === 'SUCCESS' ? 'ok' : (s === 'FAILURE' || s === 'CANCEL' ? 'err' : 'warn');
}
/** 上游 progress 可能是 "37%" / 37 / null，统一成 0-100 的数字或 null */
function pctOf(v) {
  const m = /(-?\d+(?:\.\d+)?)/.exec(String(v == null ? '' : v));
  if (!m) return null;
  return Math.max(0, Math.min(100, parseFloat(m[1])));
}
function duration(sec) {
  sec = Math.max(0, Math.floor(sec || 0));
  if (sec < 60) return sec + ' 秒';
  const m = Math.floor(sec / 60);
  if (m < 60) return `${m} 分 ${sec % 60} 秒`;
  return `${Math.floor(m / 60)} 时 ${m % 60} 分`;
}

function taskCard(t, now) {
  const pct = pctOf(t.progress);
  const known = pct !== null && pct > 0;
  const prompt = (t.prompt || '').trim();
  return `<article class="task-card">
    <div class="task-top">
      <span class="badge ${statusCls(t.status)}">${statusLabel(t.status)}</span>
      <span class="badge type">${t.type === 'NIJI_JOURNEY' ? 'niji' : 'MJ'}</span>
      ${t.speed ? `<span class="badge">${escapeHtml(String(t.speed))}</span>` : ''}
      <span class="tid">#${t.id}</span>
    </div>
    <p class="task-prompt" title="${escapeHtml(prompt)}">${escapeHtml(prompt || '（无提示词）')}</p>
    <div class="task-bar"><i class="${known ? '' : 'indet'}"${known ? ` style="width:${pct}%"` : ''}></i></div>
    <div class="task-foot">
      <span>进度 <b>${known ? pct + '%' : '等待中'}</b></span>
      <span>已用时 <b>${duration(now - (t.start_time || t.submit_time || 0))}</b></span>
      ${t.fail_reason ? `<span class="err-text">${escapeHtml(t.fail_reason)}</span>` : ''}
    </div>
  </article>`;
}

function renderTasks(list, now) {
  const wrap = $('tasksWrap');
  if (!list.length) {
    wrap.style.display = 'none';
    $('tasks').innerHTML = '';
    return;
  }
  wrap.style.display = 'block';
  $('tasksCount').textContent = String(list.length);
  $('tasks').innerHTML = list.map((t) => taskCard(t, now)).join('');
}

async function pollTasks() {
  if (tasks.busy || document.hidden) return;
  tasks.busy = true;
  try {
    const ids = [...tasks.watching].join(',');
    const res = await fetch('/api/tasks' + (ids ? '?ids=' + encodeURIComponent(ids) : ''));
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || ('HTTP ' + res.status));
    const now = data.server_time || Math.floor(Date.now() / 1000);
    const all = data.tasks || [];
    const finished = [];
    all.forEach((t) => {
      const id = String(t.id);
      const prev = tasks.seen.get(id);
      tasks.seen.set(id, t.status);
      if (DONE_STATUS.has(t.status)) {
        if (tasks.watching.delete(id) && prev && prev !== t.status) finished.push(t);
      } else if (ACTIVE_STATUS.has(t.status)) {
        tasks.watching.add(id);
      }
    });
    const alive = new Set(all.map((t) => String(t.id)));
    [...tasks.seen.keys()].forEach((k) => { if (!alive.has(k)) tasks.seen.delete(k); });

    const list = all.filter((t) => !DONE_STATUS.has(t.status));
    renderTasks(list, now);
    $('tasksHint').textContent = list.length ? '每 4 秒自动刷新 · 站点并发上限 2' : '暂无进行中的任务';
    if (finished.length) {
      finished.forEach((t) => toast(
        `任务 #${t.id} ${statusLabel(t.status)}${t.status === 'FAILURE' && t.fail_reason ? '：' + t.fail_reason : ''}`));
      loadMore(true);
    }
  } catch (err) {
    $('tasksHint').textContent = '进度刷新失败：' + err.message;
  } finally {
    tasks.busy = false;
  }
}

/** 有任务在跑就 4 秒一次；空闲时降到 20 秒，少打扰上游 */
function scheduleTasks() {
  clearTimeout(tasks.timer);
  const busy = $('tasksWrap').style.display !== 'none' || tasks.watching.size > 0;
  tasks.timer = setTimeout(async () => { await pollTasks(); scheduleTasks(); }, busy ? 4000 : 20000);
}

/* ---------------- 图片预览 ---------------- */
const pv = { msg: null, list: [], idx: 0 };

function openPreview(msg, imgs, idx) {
  pv.msg = msg; pv.list = imgs; pv.idx = idx;
  renderPreview();
  $('pvMask').classList.add('show');
  document.body.style.overflow = 'hidden';
}
function closePreview() {
  $('pvMask').classList.remove('show');
  document.body.style.overflow = '';
}
function stepPreview(d) {
  if (pv.list.length < 2) return;
  pv.idx = (pv.idx + d + pv.list.length) % pv.list.length;
  renderPreview();
}
function renderPreview() {
  const img = pv.list[pv.idx];
  const stage = $('pvStage');
  stage.classList.add('loading');
  const loader = new Image();
  loader.onload = () => { $('pvImg').src = img.full; stage.classList.remove('loading'); };
  loader.onerror = () => { $('pvImg').src = img.thumb; stage.classList.remove('loading'); toast('原图加载失败，已显示缩略图'); };
  loader.src = img.full;
  const multiple = pv.list.length > 1;
  $('pvInfo').textContent = `#${pv.msg.id}${multiple ? ` · 第 ${pv.idx + 1} / ${pv.list.length} 张` : ''}`;
  $('pvPrev').disabled = !multiple;
  $('pvNext').disabled = !multiple;
}
$('pvClose').addEventListener('click', closePreview);
$('pvMask').addEventListener('click', (e) => { if (e.target === $('pvMask')) closePreview(); });
$('pvPrev').addEventListener('click', () => stepPreview(-1));
$('pvNext').addEventListener('click', () => stepPreview(1));
$('pvDl').addEventListener('click', () => {
  const img = pv.list[pv.idx];
  download(img.full, `${fileBase(pv.msg)}_${pv.idx + 1}${extOf(img.full)}`);
});
$('pvOpen').addEventListener('click', () => {
  window.open(pv.list[pv.idx].full, '_blank', 'noopener');
});
document.addEventListener('keydown', (e) => {
  if (!$('pvMask').classList.contains('show')) return;
  if (e.key === 'Escape') closePreview();
  else if (e.key === 'ArrowLeft') stepPreview(-1);
  else if (e.key === 'ArrowRight') stepPreview(1);
});

/* ---------------- 生成图片弹窗 ---------------- */
function openGen(preset) {
  const sel = $('genModel');
  if (preset === 'niji') sel.value = 'NIJI_JOURNEY|--niji 8.2';
  else if (preset === 'mj') sel.value = 'MID_JOURNEY|--v 8.2';
  $('genStatus').textContent = '';
  $('genMask').classList.add('show');
  setTimeout(() => $('genPrompt').focus(), 30);
}
function closeGen() { $('genMask').classList.remove('show'); }

$('genBtn').addEventListener('click', (e) => {
  e.stopPropagation();
  $('genMenu').classList.toggle('show');
});
document.addEventListener('click', () => $('genMenu').classList.remove('show'));
$('genMenu').addEventListener('click', (e) => {
  const btn = e.target.closest('button[data-preset]');
  if (!btn) return;
  openGen(btn.dataset.preset);
});
$('genClose').addEventListener('click', closeGen);
$('genMask').addEventListener('click', (e) => { if (e.target === $('genMask')) closeGen(); });
document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeGen(); });
$('genStylize').addEventListener('input', (e) => { $('genStylizeVal').textContent = e.target.value; });

$('genForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const prompt = $('genPrompt').value.trim();
  if (!prompt) { toast('请先填写提示词'); return; }
  const [botType, model] = $('genModel').value.split('|');
  const payload = {
    prompt,
    bot_type: botType,
    model,
    ar: $('genAr').value,
    speed: $('genSpeed').value,
    stylize: +$('genStylize').value,
    hd: $('genHd').value === '1',
  };
  const btn = $('genSubmit');
  btn.disabled = true;
  $('genStatus').textContent = '提交中…';
  try {
    const res = await fetch('/api/imagine', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || ('HTTP ' + res.status));
    toast(`任务已提交，消息 #${data.msg_id}`);
    if (data.msg_id) tasks.watching.add(String(data.msg_id));
    $('genPrompt').value = '';
    $('genStatus').textContent = '';
    closeGen();
    loadMore(true);
    pollTasks();
    scheduleTasks();
  } catch (err) {
    $('genStatus').textContent = '';
    toast('提交失败：' + err.message);
  } finally {
    btn.disabled = false;
  }
});

/* ---------------- 主题：深色 / 浅色 ---------------- */
const THEME_KEY = 'mj-theme';
const ICON_SUN = '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M19.1 4.9l-1.4 1.4M6.3 17.7l-1.4 1.4"/></svg>';
const ICON_MOON = '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.8A8.5 8.5 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>';

function applyTheme(theme, persist = true) {
  const light = theme === 'light';
  document.documentElement.dataset.theme = light ? 'light' : 'dark';
  if (persist) { try { localStorage.setItem(THEME_KEY, light ? 'light' : 'dark'); } catch (e) {} }
  $('themeIcon').innerHTML = light ? ICON_SUN : ICON_MOON;
  $('themeLabel').textContent = light ? '浅色' : '深色';
  $('themeBtn').title = light ? '当前浅色 · 点击切换深色' : '当前深色 · 点击切换浅色';
}
$('themeBtn').addEventListener('click', () => {
  applyTheme(document.documentElement.dataset.theme === 'light' ? 'dark' : 'light');
});
applyTheme(document.documentElement.dataset.theme === 'light' ? 'light' : 'dark', false);
const media = window.matchMedia && matchMedia('(prefers-color-scheme: light)');
if (media && media.addEventListener) {
  media.addEventListener('change', (e) => {
    let saved = null;
    try { saved = localStorage.getItem(THEME_KEY); } catch (err) {}
    if (!saved) applyTheme(e.matches ? 'light' : 'dark', false);
  });
}

$('refresh').addEventListener('click', () => { loadMore(true); pollTasks(); });
$('pageSize').addEventListener('change', (e) => { state.pageSize = +e.target.value; loadMore(true); });
$('more').addEventListener('click', () => loadMore());
window.addEventListener('scroll', () => {
  if (window.innerHeight + window.scrollY > document.body.offsetHeight - 400) loadMore();
});
document.addEventListener('visibilitychange', () => { if (!document.hidden) pollTasks(); });
loadMore();
pollTasks();
scheduleTasks();
