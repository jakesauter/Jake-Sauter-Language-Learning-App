  /* Google Translate, through the Polylang server (a Cloudflare Worker holds the key) */

  const GT_PROXY = "";

  const GT = (() => {
    const CODES = { yue: "yue", cmn: "zh-CN", es: "es", pt: "pt", fr: "fr", de: "de", fa: "fa", apc: "ar", he: "he", tr: "tr" };
    const cacheKey = (text, l) => "polygrok-gt-" + l + "-" + text.trim().toLowerCase();

    let PY = null;

    function pySounds() {
      if (PY) return PY;
      const cnt = new Map();
      PHRASES.forEach(p => (p.cmn || []).forEach(t => {
        const cs = [...(t.hz || "")];
        const ss = String(t.rom || "").trim().split(/\s+/);
        if (cs.length !== ss.length) return;
        cs.forEach((c, i) => { const k = c + "|" + ss[i]; cnt.set(k, (cnt.get(k) || 0) + 1); });
      }));
      PY = new Map();
      const best = new Map();
      cnt.forEach((n, k) => { const [c, s] = k.split("|"); if (!best.has(c) || n > best.get(c)) { best.set(c, n); PY.set(c, s); } });
      PINYIN_RAW.split(",").forEach(x => { const c = [...x][0]; if (c && !PY.has(c)) PY.set(c, x.slice(c.length)); });
      return PY;
    }

    function romFor(l, text) {
      if (l === "yue") { const m = zhSounds(); return romText("yue", [...text].map(c => m.get(c)).filter(Boolean).join(" ")); }
      if (l === "cmn") { const m = pySounds(); return romText("cmn", [...text].map(c => m.get(c)).filter(Boolean).join(" ")); }
      return "";
    }

    async function translate(text, l) {
      const ck = cacheKey(text, l);
      const hit = store.get(ck);
      if (hit && hit !== "null") return hit;
      const r = await fetch(GT_PROXY.replace(/\/+$/, "") + "/translate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ q: text, target: CODES[l] }),
      });
      let j = {};
      try { j = await r.json(); } catch (e) {}
      if (!r.ok) {
        const err = new Error(j.error || String(r.status));
        err.quota = j.error === "daily-limit";
        throw err;
      }
      const out = j.text;
      store.set(ck, out);
      return out;
    }

    function section(text) {
      if (!GT_PROXY || !text) return null;
      const langs = LEARN_LANGS.filter(l => CODES[l] && show[l]);
      if (!langs.length) return null;
      const box = el("section", "full gt");
      box.appendChild(el("div", "label", esc(tr("gt_h"))));
      const note = el("p", "pr-hint", "");
      langs.forEach(l => {
        const row = el("div", "full-row");
        row.dataset.lang = l;
        row.appendChild(el("span", "fr-lang", esc(NAMES[l])));
        const tx = el("span", "fr-text " + (l === "cmn" ? "hz-cmn" : l === "yue" ? "hz-yue" : ""), "…");
        if (RTL.has(l)) { tx.dir = "rtl"; tx.lang = HTML_LANG[l]; }
        row.appendChild(tx);
        const play = el("button", "lp", speaker);
        play.type = "button";
        play.setAttribute("aria-label", NAMES[l]);
        play.disabled = true;
        row.appendChild(play);
        box.appendChild(row);
        translate(text, l).then(out => {
          const rom = romFor(l, out);
          tx.innerHTML = esc(out) + (rom ? `<span class="fr-rom" dir="ltr">${esc(rom)}</span>` : "");
          play.disabled = false;
          play.addEventListener("click", () => sayVoice(out, l));
        }).catch(e => {
          row.remove();
          note.textContent = e.quota ? tr("gt_quota") : tr("gt_fail", { msg: e.message });
        });
      });
      box.appendChild(note);
      return box;
    }

    return { section, on: () => !!GT_PROXY };
  })();
