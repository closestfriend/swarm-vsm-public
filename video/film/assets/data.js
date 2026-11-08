// Single data module for every number on screen. Each value traces to a committed source.
window.VSMDATA = {
  // METR (2026), p. 3: ~1,200 agents on the board, >70,000 messages and files, ~700 joined the attack.
  agents: "1,200", messages: "70,000+", attackers: "700",
  // calibration/wiki_overnight + wiki_abstain/comparison_full.json; swarm_abstain/summary_full.json
  wikiRecords: "6,051", swarmRecords: "6,000",
  swarmAbstainPct: 58,            // 3,470 / 6,000
  wikiAbstainPct: 8,              // 507 / 6,051
  // figures/fig2_label_distribution.csv: shares of sufficient records (%)
  wikiShare: { S1: 26.9, S2: 58.2, S4: 13.3 },
  swarmShare: { S1: 85.5, S2: 0.1, S4: 14.2 },
  // figures/fig3_wiki_transitions.csv: P(next | current), adjacent sufficient turns on a page
  matrix: {
    states: ["S0", "S1", "S2", "S4"],
    p: [
      [0.12, 0.44, 0.19, 0.26],
      [0.01, 0.54, 0.27, 0.18],
      [0.01, 0.09, 0.87, 0.03],
      [0.01, 0.40, 0.21, 0.38],
    ],
  },
  // METR (2026), pp. 5, 45–48, 59–60
  s5Functions: ["identity", "sacrifice", "succession", "binding rules"],
};

// Deterministic board rows (illustrative, after METR's message types). Seeded, no Math.random.
window.VSMBoard = (function () {
  function rng(seed) { let s = seed >>> 0; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); }
  const PREFIX = ["zzASK", "zzR", "zzIDEA", "zzFILE", "zzINBOX", "zzURG", "zzANSWER", "zzOFFER"];
  const WORDS = ["RESET", "SCORER", "TRIPWIRE", "MAILBOX", "HOLD", "TARGET", "BRIDGE", "CACHE", "LOG", "STATUS",
                 "PROBE", "BUNDLE", "SIGNAL", "QUEUE", "PATCH", "RELAY", "LANE", "TEAM", "VERIFY", "NOTE"];
  function name(r) {
    const p = PREFIX[Math.floor(r() * PREFIX.length)];
    const id = Math.floor(r() * 90000 + 10000).toString(16).toUpperCase();
    const a = WORDS[Math.floor(r() * WORDS.length)], b = WORDS[Math.floor(r() * WORDS.length)];
    return `${p}_${id}_${a}_${b}_…/`;
  }
  function rows(container, n, seed, startMinute) {
    const r = rng(seed);
    let html = "";
    for (let i = 0; i < n; i++) {
      const m = (startMinute + i) % 60, h = 8 + Math.floor((startMinute + i) / 60) % 16;
      const t = `2026-07-${String(9 + (i % 4)).padStart(2, "0")} ${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
      const size = r() < 0.4 ? "-" : `${Math.floor(r() * 900 + 40)}K`;
      html += `<div class="row"><span class="nm">${name(r)}</span><span class="dt">${t}</span><span class="sz">${size}</span></div>`;
    }
    container.innerHTML = html;
    return container.querySelectorAll(".row");
  }
  return { rows, rng };
})();
