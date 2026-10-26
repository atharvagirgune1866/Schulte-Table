/* ============================================================
   Data layer: talks to the Flask backend when it exists,
   otherwise stores everything in localStorage.
   The game code only ever calls Api.* and never cares which.
   ============================================================ */
const Api = (() => {
  const BASE = (window.SCHULTE_CONFIG?.API_BASE || "").replace(/\/$/, "");
  const PENALTY = 2;
  const LS_KEY = "schulte.scores.v1";
  let online = false;

  // ---------- helpers ----------
  const clean = (n) => (String(n || "").replace(/\s+/g, " ").trim().slice(0, 20) || "Player");
  const finalScore = (s) => Math.round((s.time + PENALTY * s.mistakes) * 100) / 100;

  const readLocal = () => {
    try { return JSON.parse(localStorage.getItem(LS_KEY)) || []; } catch { return []; }
  };
  const writeLocal = (rows) => {
    try { localStorage.setItem(LS_KEY, JSON.stringify(rows.slice(-500))); } catch { /* storage full/blocked */ }
  };

  async function getJson(path, opts) {
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), 4000); // don't hang if the free host is asleep
    try {
      const r = await fetch(BASE + path, { ...opts, signal: ctrl.signal });
      if (!r.ok) throw new Error((await r.json().catch(() => ({}))).error || r.statusText);
      return await r.json();
    } finally { clearTimeout(t); }
  }

  // ---------- startup check ----------
  async function init() {
    try {
      const h = await getJson("/api/health");
      online = h && h.ok === true;
    } catch { online = false; }
    return online;
  }

  // ---------- local implementations ----------
  const local = {
    submit(p) {
      const rows = readLocal();
      const prev = rows
        .filter((r) => r.player === p.player && r.size === p.size && r.mode === p.mode)
        .map(finalScore);
      const entry = { player: p.player, size: p.size, mode: p.mode, time: p.time,
                      mistakes: p.mistakes, date: new Date().toISOString() };
      const score = finalScore(entry);
      const rank = 1 + rows.filter((r) => r.size === p.size && r.mode === p.mode && finalScore(r) < score).length;
      rows.push(entry);
      writeLocal(rows);
      return { final_score: score, rank, is_personal_best: !prev.length || score < Math.min(...prev) };
    },
    board(size, mode, limit) {
      return readLocal()
        .filter((r) => r.size === size && r.mode === mode)
        .map((r) => ({ player: r.player, time: r.time, mistakes: r.mistakes,
                       score: finalScore(r), date: r.date }))
        .sort((a, b) => a.score - b.score)
        .slice(0, limit)
        .map((r, i) => ({ ...r, rank: i + 1 }));
    },
    stats(player) {
      const mine = readLocal().filter((r) => r.player === player);
      const groups = {};
      mine.forEach((r) => { (groups[r.size + "|" + r.mode] ||= []).push(finalScore(r)); });
      const summary = Object.entries(groups).map(([k, v]) => {
        const [size, mode] = k.split("|");
        return { size: Number(size), mode, games: v.length,
                 best: Math.min(...v), avg: v.reduce((a, b) => a + b, 0) / v.length };
      });
      const recent = mine.slice(-20).map((r) => ({ size: r.size, mode: r.mode, score: finalScore(r), date: r.date }));
      return { player, summary, recent };
    },
  };

  // ---------- public API ----------
  return {
    init,
    get online() { return online; },

    async submitScore(p) {
      p = { ...p, player: clean(p.player) };
      if (online) {
        try {
          return await getJson("/api/scores", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify(p),
          });
        } catch (e) { console.warn("Backend failed, saving locally:", e); online = false; }
      }
      return local.submit(p);
    },

    async leaderboard(size, mode, limit = 10) {
      if (online) {
        try { return await getJson(`/api/leaderboard?size=${size}&mode=${mode}&limit=${limit}`); }
        catch { online = false; }
      }
      return local.board(size, mode, limit);
    },

    async stats(player) {
      player = clean(player);
      if (online) {
        try { return await getJson(`/api/stats?player=${encodeURIComponent(player)}`); }
        catch { online = false; }
      }
      return local.stats(player);
    },

    clearLocal() { localStorage.removeItem(LS_KEY); },
  };
})();
