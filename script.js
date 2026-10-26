/* ============================================================
   Schulte Trainer - frontend logic
   Sections:
     1. State & helpers      4. Game logic
     2. Sound & theme        5. Talking to the backend (fetch)
     3. Board rendering      6. Charts & result dialog
   ============================================================ */

// ---------------------------------------------------------------
// 1. STATE & HELPERS
// ---------------------------------------------------------------
const $ = (id) => document.getElementById(id);

const state = {
  size: 5,
  mode: "classic",      // classic | reverse | shuffle
  expected: 1,          // the number the player must tap next
  mistakes: 0,
  startTime: null,      // performance.now() of first tap
  splits: [],           // seconds at which each correct tap happened
  running: false,
  rafId: null,
  sound: true,
};

const PENALTY = 2;       // seconds added per mistake (same as backend)
const MODE_LABEL = { classic: "Classic", reverse: "Reverse", shuffle: "Shuffle" };

function total() { return state.size * state.size; }
function fmt(n) { return Number(n).toFixed(2); }

// Fisher-Yates shuffle (unbiased, unlike sort(() => Math.random()-.5))
function shuffled(n) {
  const a = Array.from({ length: n }, (_, i) => i + 1);
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

// ---------------------------------------------------------------
// 2. SOUND & THEME
// ---------------------------------------------------------------
let audioCtx = null;
function beep(freq, dur = 0.08, type = "sine") {
  if (!state.sound) return;
  try {
    audioCtx = audioCtx || new (window.AudioContext || window.webkitAudioContext)();
    const o = audioCtx.createOscillator();
    const g = audioCtx.createGain();
    o.type = type; o.frequency.value = freq;
    g.gain.value = 0.05;
    o.connect(g); g.connect(audioCtx.destination);
    o.start(); o.stop(audioCtx.currentTime + dur);
  } catch (_) { /* sound is optional */ }
}

function setTheme(t) {
  document.documentElement.dataset.theme = t;
  $("themeBtn").textContent = t === "dark" ? "☀️" : "🌙";
  localStorage.setItem("schulte.theme", t);
  drawProgressChart(); // colours changed, redraw canvas
}

// ---------------------------------------------------------------
// 3. BOARD RENDERING
// ---------------------------------------------------------------
function renderBoard() {
  const board = $("board");
  board.style.gridTemplateColumns = `repeat(${state.size}, 1fr)`;
  board.innerHTML = "";
  const nums = shuffled(total());
  for (const n of nums) {
    const b = document.createElement("button");
    b.className = "cell";
    b.textContent = n;
    b.dataset.n = n;
    b.addEventListener("pointerdown", () => onCellTap(b, n)); // pointerdown = snappier than click
    board.appendChild(b);
  }
  board.classList.toggle("dot", $("dotToggle").checked);
}

// Used by Shuffle mode: rearrange numbers without losing "done" styling
function reshuffleRemaining() {
  const board = $("board");
  board.innerHTML = "";                       // rebuild = old listeners vanish
  for (const n of shuffled(total())) {
    const b = document.createElement("button");
    b.className = "cell" + (isDone(n) ? " done" : "");
    b.textContent = n;
    b.addEventListener("pointerdown", () => onCellTap(b, n));
    board.appendChild(b);
  }
}

// "done" = already found, depending on direction
function isDone(n) {
  return state.mode === "reverse" ? n > state.expected : n < state.expected;
}

// ---------------------------------------------------------------
// 4. GAME LOGIC
// ---------------------------------------------------------------
function newGame() {
  cancelAnimationFrame(state.rafId);
  state.running = false;
  state.startTime = null;
  state.mistakes = 0;
  state.splits = [];
  state.expected = state.mode === "reverse" ? total() : 1;

  renderBoard();
  $("board").classList.add("locked");
  $("startOverlay").classList.remove("hidden");
  updateHud(0);
}

function beginPlay() {
  $("startOverlay").classList.add("hidden");
  $("board").classList.remove("locked");
}

function onCellTap(cell, n) {
  if (cell.classList.contains("done")) return;

  // Timer starts on the very first tap (like the original Python version)
  if (state.startTime === null) {
    state.startTime = performance.now();
    state.running = true;
    tick();
  }

  if (n === state.expected) {
    cell.classList.add("done");
    state.splits.push((performance.now() - state.startTime) / 1000);
    beep(520 + (state.splits.length * 8));
    state.expected += state.mode === "reverse" ? -1 : 1;

    const finished = state.mode === "reverse" ? state.expected < 1 : state.expected > total();
    if (finished) return finishGame();
    if (state.mode === "shuffle") reshuffleRemaining();
  } else {
    state.mistakes++;
    cell.classList.add("wrong");
    setTimeout(() => cell.classList.remove("wrong"), 300);
    beep(180, 0.15, "square");
  }
  updateHud();
}

// requestAnimationFrame keeps the timer smooth and pauses when tab is hidden
// (this replaces the background thread from the Python version)
function tick() {
  if (!state.running) return;
  updateHud();
  state.rafId = requestAnimationFrame(tick);
}

function elapsed() {
  return state.startTime ? (performance.now() - state.startTime) / 1000 : 0;
}

function updateHud() {
  $("timer").textContent = fmt(elapsed());
  $("mistakes").textContent = state.mistakes;
  const found = state.splits.length;
  $("target").textContent = state.running || found === 0 ? state.expected : "✓";
  const pct = Math.round((found / total()) * 100);
  $("progress").textContent = pct + "%";
  $("barFill").style.width = pct + "%";
}

async function finishGame() {
  state.running = false;
  cancelAnimationFrame(state.rafId);
  const time = elapsed();
  updateHud();
  beep(880, 0.2); setTimeout(() => beep(1175, 0.25), 150);

  const payload = {
    player: playerName(),
    size: state.size,
    mode: state.mode,
    time: Number(fmt(time)),
    mistakes: state.mistakes,
    splits: state.splits,
  };

  const res = await submitScore(payload);
  showResult(payload, res);
  loadLeaderboard();
  loadStats();
}

// ---------------------------------------------------------------
// 5. BACKEND (fetch API)
// ---------------------------------------------------------------
function playerName() {
  const n = $("nameInput").value.trim() || "Player";
  localStorage.setItem("schulte.name", n);
  return n;
}

// All data goes through Api (api.js): backend if available, else this browser.
const submitScore = (payload) => Api.submitScore(payload);

function updateModeBadge() {
  const b = $("modeBadge");
  b.textContent = Api.online ? "● Online leaderboard" : "● Local mode (scores saved in this browser)";
  b.className = "badge " + (Api.online ? "on" : "off");
}

async function loadLeaderboard() {
  $("lbLabel").textContent = `${state.size}×${state.size} · ${MODE_LABEL[state.mode]}`;
  const tbody = $("lbTable").querySelector("tbody");
  try {
    const rows = await Api.leaderboard(state.size, state.mode, 10);
    updateModeBadge();
    if (!rows.length) {
      tbody.innerHTML = `<tr><td colspan="5" class="empty">No scores yet - be the first!</td></tr>`;
      return;
    }
    const me = playerName().toLowerCase();
    tbody.innerHTML = rows.map((s) => `
      <tr class="${s.player.toLowerCase() === me ? "me" : ""}">
        <td>${["🥇","🥈","🥉"][s.rank - 1] || s.rank}</td>
        <td>${escapeHtml(s.player)}</td>
        <td>${fmt(s.time)}s</td>
        <td>${s.mistakes}</td>
        <td><b>${fmt(s.score)}</b></td>
      </tr>`).join("");
  } catch {
    tbody.innerHTML = `<tr><td colspan="5" class="empty">Could not load scores.</td></tr>`;
  }
}

let myHistory = [];
async function loadStats() {
  try {
    const d = await Api.stats(playerName());
    myHistory = d.recent.filter((g) => g.size === state.size && g.mode === state.mode);
    const row = d.summary.find((s) => s.size === state.size && s.mode === state.mode);
    $("myStats").innerHTML = row
      ? `<div>Games played: <b>${row.games}</b></div>
         <div>Personal best: <b>${fmt(row.best)}s</b></div>
         <div>Average: <b>${fmt(row.avg)}s</b></div>`
      : `<div>No games yet for this setup.</div>`;
  } catch {
    myHistory = [];
    $("myStats").textContent = "";
  }
  drawProgressChart();
}

// Never inject user text into innerHTML unescaped (prevents XSS via names)
function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

// ---------------------------------------------------------------
// 6. CHARTS & RESULT DIALOG (plain canvas, no libraries)
// ---------------------------------------------------------------
function css(name) { return getComputedStyle(document.documentElement).getPropertyValue(name).trim(); }

function drawLine(canvas, values, { label = "s" } = {}) {
  const ctx = canvas.getContext("2d");
  const W = canvas.width, H = canvas.height, pad = 26;
  ctx.clearRect(0, 0, W, H);
  ctx.font = "11px system-ui";
  if (values.length < 2) {
    ctx.fillStyle = css("--muted");
    ctx.textAlign = "center";
    ctx.fillText("Play at least 2 games to see a trend", W / 2, H / 2);
    return;
  }
  const min = Math.min(...values), max = Math.max(...values);
  const span = max - min || 1;
  const x = (i) => pad + (i * (W - pad * 2)) / (values.length - 1);
  const y = (v) => H - pad - ((v - min) / span) * (H - pad * 2);

  ctx.strokeStyle = css("--line"); ctx.lineWidth = 1;
  for (let i = 0; i < 3; i++) {
    const gy = pad + (i * (H - pad * 2)) / 2;
    ctx.beginPath(); ctx.moveTo(pad, gy); ctx.lineTo(W - pad, gy); ctx.stroke();
  }
  ctx.fillStyle = css("--muted"); ctx.textAlign = "left";
  ctx.fillText(fmt(max) + label, 2, pad + 4);
  ctx.fillText(fmt(min) + label, 2, H - pad + 4);

  ctx.strokeStyle = css("--accent"); ctx.lineWidth = 2.5; ctx.lineJoin = "round";
  ctx.beginPath();
  values.forEach((v, i) => (i ? ctx.lineTo(x(i), y(v)) : ctx.moveTo(x(i), y(v))));
  ctx.stroke();
  ctx.fillStyle = css("--accent");
  values.forEach((v, i) => { ctx.beginPath(); ctx.arc(x(i), y(v), 3.5, 0, 7); ctx.fill(); });
}

function drawProgressChart() {
  drawLine($("chart"), myHistory.map((g) => g.score));
}

// Per-number time (how long each find took) - shows where you slowed down
function drawSplits(splits) {
  const per = splits.map((t, i) => t - (splits[i - 1] || 0));
  const c = $("splitChart"), ctx = c.getContext("2d");
  const W = c.width, H = c.height, pad = 20;
  ctx.clearRect(0, 0, W, H);
  const max = Math.max(...per);
  const bw = (W - pad * 2) / per.length;
  per.forEach((v, i) => {
    const h = (v / max) * (H - pad * 2);
    ctx.fillStyle = v > max * 0.75 ? css("--bad") : css("--accent");
    ctx.fillRect(pad + i * bw + 1, H - pad - h, Math.max(bw - 2, 1), h);
  });
  ctx.fillStyle = css("--muted"); ctx.font = "11px system-ui"; ctx.textAlign = "center";
  ctx.fillText("time per number (red = slowest)", W / 2, H - 5);
}

function showResult(p, res) {
  const final = p.time + PENALTY * p.mistakes;
  $("resTime").textContent = fmt(p.time) + "s";
  $("resMist").textContent = p.mistakes;
  $("resScore").textContent = fmt(final) + "s";
  $("resRank").textContent = res ? "#" + res.rank : "-";
  $("resTitle").textContent = res?.is_personal_best ? "🏅 New personal best!" : "🎉 Finished!";

  // small insight: compare first half vs second half pace
  const per = p.splits.map((t, i) => t - (p.splits[i - 1] || 0));
  const h = Math.floor(per.length / 2);
  const a = per.slice(0, h).reduce((s, v) => s + v, 0) / h;
  const b = per.slice(h).reduce((s, v) => s + v, 0) / (per.length - h);
  const slow = per.indexOf(Math.max(...per)) + 1;
  $("resInsight").textContent =
    `Slowest find: number #${slow} (${fmt(Math.max(...per))}s). ` +
    (b < a ? "You sped up as you went - nice rhythm." : "You slowed down in the second half - try relaxing your gaze on the dot.");

  drawSplits(p.splits);
  $("resultDlg").showModal();
}

// ---------------------------------------------------------------
// EVENT WIRING
// ---------------------------------------------------------------
function wireSegment(segId, attr, onChange) {
  $(segId).addEventListener("click", (e) => {
    const btn = e.target.closest("button");
    if (!btn) return;
    [...$(segId).children].forEach((b) => b.classList.toggle("active", b === btn));
    onChange(btn.dataset[attr]);
  });
}

function refreshAll() { newGame(); loadLeaderboard(); loadStats(); }

wireSegment("sizeSeg", "size", (v) => { state.size = Number(v); refreshAll(); });
wireSegment("modeSeg", "mode", (v) => { state.mode = v; refreshAll(); });

$("startBtn").addEventListener("click", beginPlay);
$("restartBtn").addEventListener("click", newGame);
$("againBtn").addEventListener("click", () => { newGame(); beginPlay(); });
$("dotToggle").addEventListener("change", () => $("board").classList.toggle("dot", $("dotToggle").checked));
$("soundBtn").addEventListener("click", () => {
  state.sound = !state.sound;
  $("soundBtn").textContent = state.sound ? "🔊" : "🔇";
});
$("themeBtn").addEventListener("click", () =>
  setTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark"));
$("nameInput").addEventListener("change", () => { playerName(); loadLeaderboard(); loadStats(); });

// Keyboard: Enter/Space starts, R restarts
document.addEventListener("keydown", (e) => {
  if (e.target.tagName === "INPUT") return;
  if ((e.key === "Enter" || e.key === " ") && !$("startOverlay").classList.contains("hidden")) {
    e.preventDefault(); beginPlay();
  } else if (e.key.toLowerCase() === "r") newGame();
});

// ---- boot ----
$("nameInput").value = localStorage.getItem("schulte.name") || "";
setTheme(localStorage.getItem("schulte.theme") ||
  (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"));
// Check whether the Flask backend exists, then start (falls back to local mode)
Api.init().finally(() => { updateModeBadge(); refreshAll(); });
