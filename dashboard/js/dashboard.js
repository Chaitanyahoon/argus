/**
 * Argus Dashboard — Live Data JS
 * Fetches real data from the Flask API at /api/*
 * Falls back gracefully to mock data if the API is unreachable.
 */

const API = 'http://localhost:5000';

// ── Colours & helpers ─────────────────────────────────────────────────────────
const COLORS = ['#6600ff','#0066ff','#00aaff','#00d4ff','#aa55ff','#ff6699','#ffaa00'];
function memberColor(i) { return COLORS[i % COLORS.length]; }
function pct(v, m) { return Math.min(100, Math.round((v / m) * 100)); }

function rankBadgeClass(n) {
  return n === 1 ? 'rank-1' : n === 2 ? 'rank-2' : n === 3 ? 'rank-3' : 'rank-n';
}
function levelBadgeClass(lv) {
  if (lv >= 80) return 'lv-legend';
  if (lv >= 50) return 'lv-high';
  if (lv >= 20) return 'lv-mid';
  return 'lv-low';
}
function trendHTML(t) {
  if (t > 0) return `<span style="color:var(--success)">↑${t}%</span>`;
  if (t < 0) return `<span style="color:var(--danger)">↓${Math.abs(t)}%</span>`;
  return `<span style="color:var(--text-muted)">—</span>`;
}

// ── API fetch wrapper ─────────────────────────────────────────────────────────
async function apiFetch(path, options = {}) {
  try {
    const res = await fetch(`${API}${path}`, {
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      ...options,
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (e) {
    console.warn(`[Argus API] ${path} failed:`, e.message, '— using mock data');
    return null;
  }
}

// ── Mock fallback data ────────────────────────────────────────────────────────
const MOCK_MEMBERS = [
  { username:'Nova',   level:62, xp:41200, xp_max:45000, total_messages:2841, voice_time_seconds:51120, trend:8  },
  { username:'Cipher', level:55, xp:38100, xp_max:42000, total_messages:2210, voice_time_seconds:42480, trend:3  },
  { username:'Lyra',   level:48, xp:32700, xp_max:36000, total_messages:1950, voice_time_seconds:33840, trend:-2 },
  { username:'Helix',  level:41, xp:28900, xp_max:32000, total_messages:1720, voice_time_seconds:29160, trend:5  },
  { username:'Zara',   level:36, xp:25200, xp_max:28000, total_messages:1480, voice_time_seconds:27360, trend:1  },
  { username:'Orion',  level:31, xp:22100, xp_max:25000, total_messages:1320, voice_time_seconds:24840, trend:-1 },
  { username:'Kira',   level:28, xp:19800, xp_max:22000, total_messages:1200, voice_time_seconds:20880, trend:4  },
  { username:'Vertex', level:24, xp:17200, xp_max:19500, total_messages:1040, voice_time_seconds:16920, trend:0  },
  { username:'Axon',   level:21, xp:14900, xp_max:17000, total_messages:920,  voice_time_seconds:14760, trend:-3 },
  { username:'Echo',   level:18, xp:12400, xp_max:15000, total_messages:810,  voice_time_seconds:12600, trend:2  },
  { username:'Delta',  level:15, xp:10100, xp_max:13000, total_messages:700,  voice_time_seconds:10440, trend:-1 },
  { username:'Flare',  level:12, xp:8300,  xp_max:10500, total_messages:590,  voice_time_seconds:7920,  trend:6  },
];

const MOCK_OVERVIEW = {
  total_users: 4281, total_xp: 48200000, avg_level: 23.4,
  total_messages: 18492, voice_hours: 42.0, music_plays: 1240,
};

const MOCK_ACTIVITY = [
  { color:'green',  icon:'✅', text:'<span class="user-mention">@Nova</span> joined the server',                     time:'1m ago'  },
  { color:'blue',   icon:'⭐', text:'<span class="user-mention">@Ether</span> reached <strong>Level 87!</strong>',   time:'3m ago'  },
  { color:'orange', icon:'🎵', text:'<span class="user-mention">@Void</span> queued <em>Bohemian Rhapsody</em>',     time:'5m ago'  },
  { color:'red',    icon:'🛡️', text:'AutoMod deleted a message from <span class="user-mention">@Shadow</span>',     time:'7m ago'  },
  { color:'green',  icon:'🔊', text:'<span class="user-mention">@Pulse</span> joined <strong>#Gaming Lounge</strong>',time:'9m ago' },
  { color:'blue',   icon:'⭐', text:'<span class="user-mention">@Lyra</span> reached <strong>Level 48!</strong>',    time:'12m ago' },
  { color:'orange', icon:'🎵', text:'<span class="user-mention">@Nova</span> queued <em>Blinding Lights</em>',       time:'14m ago' },
];

const MOCK_AI_ACTIONS = [
  { bar:'del',  ts:'Today 22:49', action:'del',  user:'@Shadow#4812', reason:'Detected hate speech targeting user group',    conf:{label:'HIGH',cls:'high',val:'94%'} },
  { bar:'warn', ts:'Today 22:41', action:'warn', user:'@Ghost#2291',  reason:'Mild profanity, borderline offensive language', conf:{label:'MED', cls:'med', val:'71%'} },
  { bar:'del',  ts:'Today 22:33', action:'del',  user:'@Vrex#0019',   reason:'Spam: 8 identical messages in 10 seconds',     conf:{label:'HIGH',cls:'high',val:'98%'} },
  { bar:'warn', ts:'Today 22:11', action:'warn', user:'@Blaze#5530',  reason:'Potential scam link detected in message',       conf:{label:'MED', cls:'med', val:'68%'} },
  { bar:'ok',   ts:'Today 21:58', action:null,   user:'@Nova#8821',   reason:'Message scanned — clean, no violations found',  conf:{label:'LOW', cls:'low', val:'12%'} },
  { bar:'del',  ts:'Today 21:40', action:'del',  user:'@Toxin#1121',  reason:'Severe harassment with threatening language',   conf:{label:'HIGH',cls:'high',val:'99%'} },
];

// ── Render: Overview Stat Cards ──────────────────────────────────────────────────
async function renderOverviewStats() {
  const data = (await apiFetch('/api/overview')) || MOCK_OVERVIEW;
  const setEl = (id, val) => { const e = document.getElementById(id); if (e) e.textContent = val; };
  setEl('stat-members',  data.total_users?.toLocaleString()   || '—');
  setEl('stat-messages', data.total_messages?.toLocaleString() || '—');
  setEl('stat-voice',    data.voice_hours ? `${data.voice_hours}h` : '—');
  setEl('stat-xp',       data.total_xp ? `${(data.total_xp/1e6).toFixed(2)}M` : '—');
}

// ── Render: Mini Leaderboard (Overview page) ────────────────────────────────────
async function buildOverviewLB() {
  const el = document.getElementById('leaderboard-body');
  if (!el) return;
  const raw = await apiFetch('/api/leaderboard?limit=5');
  const members = (raw && raw.length) ? raw : MOCK_MEMBERS.slice(0, 5);
  members.forEach((m, i) => {
    const rank = i + 1;
    const xpMax = m.xp_max || m.xp * 1.1 || 10000;
    const p = pct(m.xp, xpMax);
    const clr = memberColor(i);
    el.innerHTML += `
      <tr>
        <td><span class="rank-badge ${rankBadgeClass(rank)}">${rank}</span></td>
        <td>
          <div class="flex items-center gap-8">
            <div class="avatar" style="background:${clr}20;border:1.5px solid ${clr}50;color:${clr}">${(m.username||'?')[0].toUpperCase()}</div>
            <div>
              <div class="font-bold" style="font-size:13px">${m.username || 'Unknown'}</div>
              <div class="text-muted" style="font-size:10px">Level ${m.level || 1}</div>
            </div>
          </div>
        </td>
        <td><span class="level-badge ${levelBadgeClass(m.level || 1)}">Lv.${m.level || 1}</span></td>
        <td style="min-width:130px">
          <div class="xp-bar-track" style="margin-bottom:3px"><div class="xp-bar-fill" style="width:${p}%"></div></div>
          <div class="text-xs text-muted">${(m.xp||0).toLocaleString()} XP</div>
        </td>
        <td class="text-sm">${(m.total_messages||0).toLocaleString()}</td>
        <td>${trendHTML(m.trend || 0)}</td>
      </tr>`;
  });
}

// ── Render: Activity Feed ────────────────────────────────────────────────────────
function buildFeed() {
  const el = document.getElementById('activity-feed');
  if (!el) return;
  MOCK_ACTIVITY.forEach(a => {
    el.innerHTML += `
      <div class="feed-item">
        <div class="feed-bar ${a.color}"></div>
        <div class="feed-content">
          <div class="feed-text">${a.icon} ${a.text}</div>
          <div class="feed-time">${a.time}</div>
        </div>
      </div>`;
  });
}

// ── Render: Full Leaderboard Table ───────────────────────────────────────────────
async function buildFullLB() {
  const el = document.getElementById('lb-body');
  if (!el) return;
  const raw = await apiFetch('/api/leaderboard?limit=12');
  const members = (raw && raw.length) ? raw : MOCK_MEMBERS;
  members.forEach((m, i) => {
    const rank = i + 4;
    const xpMax = m.xp_max || m.xp * 1.1 || 10000;
    const p = pct(m.xp, xpMax);
    const clr = memberColor(i);
    const voiceH = m.voice_time_seconds ? (m.voice_time_seconds / 3600).toFixed(1) + 'h' : '—';
    el.innerHTML += `
      <tr>
        <td><span class="rank-badge rank-n">${rank}</span></td>
        <td>
          <div class="flex items-center gap-8">
            <div class="avatar" style="background:${clr}20;border:1.5px solid ${clr}50;color:${clr}">${(m.username||'?')[0].toUpperCase()}</div>
            <div>
              <div class="font-bold" style="font-size:13px">${m.username || 'Unknown'}</div>
              <div class="text-muted" style="font-size:10px">#${String(m.user_id || '0000').slice(-4)}</div>
            </div>
          </div>
        </td>
        <td><span class="level-badge ${levelBadgeClass(m.level || 1)}">Lv.${m.level || 1}</span></td>
        <td style="min-width:140px">
          <div class="xp-bar-track" style="margin-bottom:3px"><div class="xp-bar-fill" style="width:${p}%"></div></div>
          <div class="text-xs text-muted">${(m.xp||0).toLocaleString()} / ${xpMax.toLocaleString()} (${p}%)</div>
        </td>
        <td class="text-sm">💬 ${(m.total_messages||0).toLocaleString()}</td>
        <td class="text-sm">🎤 ${voiceH}</td>
        <td>${trendHTML(m.trend || 0)}</td>
      </tr>`;
  });
}

// ── Render: AutoMod Action Feed ──────────────────────────────────────────────────
function buildActionFeed() {
  const el = document.getElementById('action-feed');
  if (!el) return;
  MOCK_AI_ACTIONS.forEach(a => {
    const badgeHTML = a.action === 'del'
      ? `<span class="action-badge action-del">DELETED</span>`
      : a.action === 'warn'
        ? `<span class="action-badge action-warn">WARNED</span>`
        : `<span class="action-badge" style="background:rgba(0,255,136,0.12);color:var(--success)">CLEAN</span>`;
    el.innerHTML += `
      <div class="action-entry">
        <div class="action-bar ${a.bar}"></div>
        <div class="action-body">
          <div class="action-top">
            <span class="action-ts">${a.ts}</span>
            ${badgeHTML}
            <span class="user-mention" style="font-size:12px">${a.user}</span>
            <span class="conf-badge conf-${a.conf.cls}">${a.conf.label} ${a.conf.val}</span>
          </div>
          <div class="action-reason">"${a.reason}"</div>
        </div>
      </div>`;
  });
}

// ── AutoMod save ─────────────────────────────────────────────────────────────────
async function saveAutomod(guildId) {
  const toxicity = document.getElementById('tox-toggle')?.checked ?? true;
  const spam     = document.getElementById('spam-toggle')?.checked ?? false;
  const threshold = parseFloat(document.getElementById('tox-val')?.textContent || '0.7');
  const res = await apiFetch(`/api/guilds/${guildId}/automod`, {
    method: 'POST',
    body: JSON.stringify({ toxicity_enabled: toxicity, spam_enabled: spam, threshold }),
  });
  if (res) {
    alert('✅ AutoMod settings saved!');
  } else {
    alert('⚠️ API offline — settings not saved to database.');
  }
}

// ── Tab buttons ────────────────────────────────────────────────────────────────
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    btn.closest('.filter-tabs').querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
  });
});

// ── AutoMod toggle helper ──────────────────────────────────────────────────────
function toggleSection(id, chk) {
  const el = document.getElementById(id);
  if (el) el.classList.toggle('disabled-overlay', !chk.checked);
}

// ── Bootstrap ─────────────────────────────────────────────────────────────────
(async () => {
  await renderOverviewStats();
  await buildOverviewLB();
  buildFeed();
  await buildFullLB();
  buildActionFeed();
})();
