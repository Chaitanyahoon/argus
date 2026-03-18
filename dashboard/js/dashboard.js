/**
 * Argus Dashboard — Shared JS
 * Populates mock data across Overview, Leaderboard, and AutoMod pages.
 */

// ── Mock Data ─────────────────────────────────────────────────────────────────

const COLORS = ['#6600ff','#0066ff','#00aaff','#00d4ff','#aa55ff','#ff6699','#ffaa00'];

const MEMBERS = [
  { name: 'Nova',    disc: '#8821', lv: 62, xp: 41200, xpMax: 45000, msgs: 2841, voice: '14.2h', trend: +8  },
  { name: 'Cipher',  disc: '#3301', lv: 55, xp: 38100, xpMax: 42000, msgs: 2210, voice: '11.8h', trend: +3  },
  { name: 'Lyra',    disc: '#1192', lv: 48, xp: 32700, xpMax: 36000, msgs: 1950, voice: '9.4h',  trend: -2  },
  { name: 'Helix',   disc: '#5540', lv: 41, xp: 28900, xpMax: 32000, msgs: 1720, voice: '8.1h',  trend: +5  },
  { name: 'Zara',    disc: '#9912', lv: 36, xp: 25200, xpMax: 28000, msgs: 1480, voice: '7.6h',  trend: +1  },
  { name: 'Orion',   disc: '#2204', lv: 31, xp: 22100, xpMax: 25000, msgs: 1320, voice: '6.9h',  trend: -1  },
  { name: 'Kira',    disc: '#7731', lv: 28, xp: 19800, xpMax: 22000, msgs: 1200, voice: '5.8h',  trend: +4  },
  { name: 'Vertex',  disc: '#0041', lv: 24, xp: 17200, xpMax: 19500, msgs: 1040, voice: '4.7h',  trend: +0  },
  { name: 'Axon',    disc: '#6623', lv: 21, xp: 14900, xpMax: 17000, msgs:  920, voice: '4.1h',  trend: -3  },
  { name: 'Echo',    disc: '#3390', lv: 18, xp: 12400, xpMax: 15000, msgs:  810, voice: '3.5h',  trend: +2  },
  { name: 'Delta',   disc: '#8801', lv: 15, xp: 10100, xpMax: 13000, msgs:  700, voice: '2.9h',  trend: -1  },
  { name: 'Flare',   disc: '#1123', lv: 12, xp:  8300, xpMax: 10500, msgs:  590, voice: '2.2h',  trend: +6  },
];

const ACTIVITY = [
  { color: 'green',  icon: '✅', text: '<span class="user-mention">@Nova</span> joined the server',                    time: '1m ago'  },
  { color: 'blue',   icon: '⭐', text: '<span class="user-mention">@Ether</span> reached <strong>Level 87!</strong>',  time: '3m ago'  },
  { color: 'orange', icon: '🎵', text: '<span class="user-mention">@Void</span> queued <em>Bohemian Rhapsody</em>',    time: '5m ago'  },
  { color: 'red',    icon: '🛡️', text: 'AutoMod deleted a message from <span class="user-mention">@Shadow</span>',    time: '7m ago'  },
  { color: 'green',  icon: '🔊', text: '<span class="user-mention">@Pulse</span> joined <strong>#Gaming Lounge</strong>', time: '9m ago' },
  { color: 'blue',   icon: '⭐', text: '<span class="user-mention">@Lyra</span> reached <strong>Level 48!</strong>',   time: '12m ago' },
  { color: 'orange', icon: '🎵', text: '<span class="user-mention">@Nova</span> queued <em>Blinding Lights</em>',      time: '14m ago' },
  { color: 'green',  icon: '✅', text: '<span class="user-mention">@Cipher</span> joined the server',                  time: '18m ago' },
];

const AI_ACTIONS = [
  { bar:'del',  ts:'Today 22:49', action:'del',  user:'@Shadow#4812', reason:'Detected hate speech targeting user group',        conf: {label:'HIGH', cls:'high', val:'94%'} },
  { bar:'warn', ts:'Today 22:41', action:'warn', user:'@Ghost#2291',  reason:'Mild profanity, borderline offensive language',     conf: {label:'MED',  cls:'med',  val:'71%'} },
  { bar:'del',  ts:'Today 22:33', action:'del',  user:'@Vrex#0019',   reason:'Spam: 8 identical messages in 10 seconds',         conf: {label:'HIGH', cls:'high', val:'98%'} },
  { bar:'warn', ts:'Today 22:11', action:'warn', user:'@Blaze#5530',  reason:'Potential scam link detected in message',           conf: {label:'MED',  cls:'med',  val:'68%'} },
  { bar:'ok',   ts:'Today 21:58', action:null,   user:'@Nova#8821',   reason:'Message scanned — clean, no violations found',      conf: {label:'LOW',  cls:'low',  val:'12%'} },
  { bar:'del',  ts:'Today 21:40', action:'del',  user:'@Toxin#1121',  reason:'Severe harassment with threatening language',       conf: {label:'HIGH', cls:'high', val:'99%'} },
  { bar:'warn', ts:'Today 21:22', action:'warn', user:'@Anon#6609',   reason:'Off-topic advertising, promotional spam detected',  conf: {label:'MED',  cls:'med',  val:'75%'} },
  { bar:'ok',   ts:'Today 20:55', action:null,   user:'@Lyra#1192',   reason:'Message scanned — clean, no violations found',      conf: {label:'LOW',  cls:'low',  val:'8%'}  },
];

// ── Helpers ───────────────────────────────────────────────────────────────────

function rankBadgeClass(n) {
  return n === 1 ? 'rank-1' : n === 2 ? 'rank-2' : n === 3 ? 'rank-3' : 'rank-n';
}

function levelBadgeClass(lv) {
  if (lv >= 80) return 'lv-legend';
  if (lv >= 50) return 'lv-high';
  if (lv >= 20) return 'lv-mid';
  return 'lv-low';
}

function pct(val, max) { return Math.round((val / max) * 100); }

function memberColor(i) { return COLORS[i % COLORS.length]; }

function trendHTML(t) {
  if (t > 0) return `<span style="color:var(--success)">↑${t}%</span>`;
  if (t < 0) return `<span style="color:var(--danger)">↓${Math.abs(t)}%</span>`;
  return `<span style="color:var(--text-muted)">—</span>`;
}

// ── Overview Leaderboard ──────────────────────────────────────────────────────

(function buildOverviewLB() {
  const el = document.getElementById('leaderboard-body');
  if (!el) return;
  MEMBERS.slice(0, 5).forEach((m, i) => {
    const rank = i + 1;
    const p = pct(m.xp, m.xpMax);
    const clr = memberColor(i);
    el.innerHTML += `
      <tr>
        <td><span class="rank-badge ${rankBadgeClass(rank)}">${rank}</span></td>
        <td>
          <div class="flex items-center gap-8">
            <div class="avatar" style="background:${clr}20;border:1.5px solid ${clr}50;color:${clr}">${m.name[0]}</div>
            <div>
              <div class="font-bold" style="font-size:13px">${m.name}</div>
              <div class="text-muted" style="font-size:10px">Joined Jan 2024</div>
            </div>
          </div>
        </td>
        <td><span class="level-badge ${levelBadgeClass(m.lv)}">Lv.${m.lv}</span></td>
        <td style="min-width:130px">
          <div class="xp-bar-track" style="margin-bottom:3px"><div class="xp-bar-fill" style="width:${p}%"></div></div>
          <div class="text-xs text-muted">${m.xp.toLocaleString()} / ${m.xpMax.toLocaleString()}</div>
        </td>
        <td class="text-sm">${m.msgs.toLocaleString()}</td>
        <td>${trendHTML(m.trend)}</td>
      </tr>`;
  });
})();

// ── Activity Feed ─────────────────────────────────────────────────────────────

(function buildFeed() {
  const el = document.getElementById('activity-feed');
  if (!el) return;
  ACTIVITY.forEach(a => {
    el.innerHTML += `
      <div class="feed-item">
        <div class="feed-bar ${a.color}"></div>
        <div class="feed-content">
          <div class="feed-text">${a.icon} ${a.text}</div>
          <div class="feed-time">${a.time}</div>
        </div>
      </div>`;
  });
})();

// ── Leaderboard Full Table ────────────────────────────────────────────────────

(function buildFullLB() {
  const el = document.getElementById('lb-body');
  if (!el) return;
  MEMBERS.forEach((m, i) => {
    const rank = i + 4; // podium is 1-3
    const p = pct(m.xp, m.xpMax);
    const clr = memberColor(i);
    el.innerHTML += `
      <tr>
        <td><span class="rank-badge rank-n">${rank}</span></td>
        <td>
          <div class="flex items-center gap-8">
            <div class="avatar" style="background:${clr}20;border:1.5px solid ${clr}50;color:${clr}">${m.name[0]}</div>
            <div>
              <div class="font-bold" style="font-size:13px">${m.name}</div>
              <div class="text-muted" style="font-size:10px">${m.disc}</div>
            </div>
          </div>
        </td>
        <td><span class="level-badge ${levelBadgeClass(m.lv)}">Lv.${m.lv}</span></td>
        <td style="min-width:140px">
          <div class="xp-bar-track" style="margin-bottom:3px"><div class="xp-bar-fill" style="width:${p}%"></div></div>
          <div class="text-xs text-muted">${m.xp.toLocaleString()} / ${m.xpMax.toLocaleString()} (${p}%)</div>
        </td>
        <td class="text-sm">💬 ${m.msgs.toLocaleString()}</td>
        <td class="text-sm">🎤 ${m.voice}</td>
        <td>${trendHTML(m.trend)}</td>
      </tr>`;
  });
})();

// ── AutoMod Action Feed ───────────────────────────────────────────────────────

(function buildActionFeed() {
  const el = document.getElementById('action-feed');
  if (!el) return;
  AI_ACTIONS.forEach(a => {
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
})();

// ── Tab buttons ───────────────────────────────────────────────────────────────
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    btn.closest('.filter-tabs').querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
  });
});
