  /* practice: spaced retrieval, saying it aloud, listening, shadowing and tone training, all stored on this device */

  const Practice = (() => {
    const DAY = 86400000;
    const LANGS_P = ["yue", "tsn", "cmn", "es", "fr", "de"];
    const ZH = new Set(["yue", "tsn", "cmn"]);

    const load = (k, d) => { try { const v = JSON.parse(store.get(k) || "null"); return v ?? d; } catch (e) { return d; } };
    const save = (k, v) => store.set(k, JSON.stringify(v));

    let srs = load("polygrok-srs", {});
    let deck = load("polygrok-deck", []);
    let days = load("polygrok-days", { last: "", streak: 0, total: 0 });
    let newDay = load("polygrok-newday", { date: "", n: {} });
    let plang = store.get("polygrok-plang") || "yue";
    let newPer = Number(store.get("polygrok-newper") || 8);

    const today = () => new Date().toISOString().slice(0, 10);
    const st = (lang, en) => (srs[lang] || {})[en];
    const setSt = (lang, en, v) => { (srs[lang] = srs[lang] || {})[en] = v; save("polygrok-srs", srs); };
    const has = (p, lang) => p[lang] && p[lang].length;

    function inDeck(en) { return deck.includes(en); }
    function toggleDeck(en) {
      deck = inDeck(en) ? deck.filter(x => x !== en) : [en, ...deck];
      save("polygrok-deck", deck);
      return inDeck(en);
    }

    function counts(lang = plang) {
      const now = Date.now();
      let due = 0, learned = 0;
      PHRASES.forEach(p => { const s = st(lang, p.en); if (s) { learned++; if (s.due <= now) due++; } });
      if (newDay.date !== today()) newDay = { date: today(), n: {} };
      const newLeft = Math.max(0, newPer - (newDay.n[lang] || 0));
      return { due, learned, newLeft };
    }

    function queue(lang, size = 20) {
      const now = Date.now();
      const due = PHRASES.filter(p => has(p, lang) && st(lang, p.en) && st(lang, p.en).due <= now).sort((a, b) => st(lang, a.en).due - st(lang, b.en).due);
      const { newLeft } = counts(lang);
      const fresh = [];
      const seen = new Set();
      [...deck.map(en => PHRASES.find(p => p.en === en)).filter(Boolean), ...PHRASES].forEach(p => {
        if (fresh.length >= newLeft || seen.has(p.en) || !has(p, lang) || st(lang, p.en) || Book.isKnown(p.en)) return;
        seen.add(p.en);
        fresh.push(p);
      });
      const q = [];
      let i = 0, j = 0;
      while (q.length < size && (i < due.length || j < fresh.length)) {
        if (i < due.length) q.push({ p: due[i++], isNew: false });
        if (q.length % 3 === 0 && j < fresh.length) q.push({ p: fresh[j++], isNew: true });
        if (i >= due.length && j < fresh.length) q.push({ p: fresh[j++], isNew: true });
      }
      for (let k = q.length - 1; k > 0; k--) {
        if (Math.random() < 0.35) { const m = Math.floor(Math.random() * (k + 1)); [q[k], q[m]] = [q[m], q[k]]; }
      }
      return q.slice(0, size);
    }

    function schedule(lang, en, grade) {
      const s = st(lang, en) || { i: 0, e: 2.5, n: 0, l: 0, due: 0 };
      const now = Date.now();
      if (grade === 0) { s.l++; s.n = 0; s.i = 0; s.e = Math.max(1.3, s.e - 0.2); s.due = now + 60000; }
      else {
        if (grade === 1) { s.i = s.n === 0 ? 1 : Math.max(1, Math.round(s.i * 1.2)); s.e = Math.max(1.3, s.e - 0.15); }
        if (grade === 2) s.i = s.n === 0 ? 1 : s.n === 1 ? 3 : Math.round(s.i * s.e);
        if (grade === 3) { s.i = s.n === 0 ? 3 : Math.round(Math.max(s.i, 1) * s.e * 1.3); s.e += 0.15; }
        s.n++;
        s.due = now + s.i * DAY * (0.95 + Math.random() * 0.1);
      }
      setSt(lang, en, s);
    }

    function preview(lang, en, grade) {
      const s = st(lang, en) || { i: 0, e: 2.5, n: 0 };
      if (grade === 0) return "1m";
      let i;
      if (grade === 1) i = s.n === 0 ? 1 : Math.max(1, Math.round(s.i * 1.2));
      if (grade === 2) i = s.n === 0 ? 1 : s.n === 1 ? 3 : Math.round(s.i * s.e);
      if (grade === 3) i = s.n === 0 ? 3 : Math.round(Math.max(s.i, 1) * s.e * 1.3);
      return i >= 30 ? Math.round(i / 30) + "mo" : i + "d";
    }

    function markDay() {
      const t = today();
      if (days.last === t) return;
      const y = new Date(Date.now() - DAY).toISOString().slice(0, 10);
      days.streak = days.last === y ? days.streak + 1 : 1;
      days.last = t;
      days.total = (days.total || 0) + 1;
      save("polygrok-days", days);
    }

    /* ---------- dialog ---------- */

    let D, body, session = null;

    function ensure() {
      if (D) return;
      D = document.createElement("dialog");
      D.className = "practice";
      D.id = "practice";
      D.innerHTML = `<div class="pr-top"><span class="pr-title">${icon("brain")}<span id="pr-title"></span></span><button class="btn quiet" id="pr-close" type="button"></button></div><div class="pr-body" id="pr-body"></div>`;
      document.body.appendChild(D);
      body = D.querySelector("#pr-body");
      D.querySelector("#pr-close").addEventListener("click", () => { D.close(); Tones.stop(); Voice.stop(); updateCta(); });
      D.addEventListener("cancel", () => updateCta());
    }

    function open() {
      ensure();
      D.querySelector("#pr-title").textContent = tr("p_title");
      D.querySelector("#pr-close").textContent = tr("g_close");
      home();
      D.showModal();
    }

    function home() {
      session = null;
      const c = counts();
      body.innerHTML = "";
      const langs = el("div", "pr-langs");
      LANGS_P.forEach(l => {
        const b = el("button", "lang-chip", `<span class="tick" aria-hidden="true"></span>${esc(NAMES[l])}`);
        b.type = "button";
        b.setAttribute("aria-pressed", l === plang ? "true" : "false");
        b.addEventListener("click", () => { plang = l; store.set("polygrok-plang", l); home(); });
        langs.appendChild(b);
      });
      body.appendChild(el("p", "pr-lead", esc(tr("p_lead", { lang: NAMES[plang] }))));
      body.appendChild(langs);

      const stats = el("div", "pr-stats");
      [[c.due, tr("p_due")], [c.newLeft, tr("p_new")], [c.learned, tr("p_learned")], [days.streak || 0, tr("p_streak")]].forEach(([n, l]) => {
        stats.appendChild(el("div", "pr-stat", `<b>${n}</b><span>${esc(l)}</span>`));
      });
      body.appendChild(stats);

      const acts = el("div", "pr-acts");
      const go = el("button", "btn pr-big", `${icon("cards")}<span><b>${esc(tr("p_start"))}</b><small>${esc(tr("p_start_d"))}</small></span>`);
      go.type = "button";
      go.addEventListener("click", () => startSession("mix"));
      acts.appendChild(go);
      const li = el("button", "btn quiet pr-big", `${icon("ear")}<span><b>${esc(tr("p_listen"))}</b><small>${esc(tr("p_listen_d"))}</small></span>`);
      li.type = "button";
      li.addEventListener("click", () => startSession("listen"));
      acts.appendChild(li);
      if (ZH.has(plang)) {
        const to = el("button", "btn quiet pr-big", `${icon("tones")}<span><b>${esc(tr("p_tones"))}</b><small>${esc(tr("p_tones_d"))}</small></span>`);
        to.type = "button";
        to.addEventListener("click", () => toneTrainer());
        acts.appendChild(to);
      }
      body.appendChild(acts);

      const opt = el("div", "pr-opt");
      opt.innerHTML = `<label for="pr-newper">${esc(tr("p_newper"))} <select id="pr-newper">${[3, 5, 8, 12, 20].map(n => `<option value="${n}"${n === newPer ? " selected" : ""}>${n}</option>`).join("")}</select></label>`;
      opt.querySelector("select").addEventListener("change", e => { newPer = Number(e.target.value); store.set("polygrok-newper", String(newPer)); home(); });
      const why = el("button", "link", esc(tr("p_why")));
      why.type = "button";
      why.addEventListener("click", () => { D.close(); openLearn(); });
      opt.appendChild(why);
      body.appendChild(opt);
    }

    function startSession(mode) {
      let q = queue(plang, mode === "listen" ? 12 : 15);
      if (mode === "listen") {
        const seen = PHRASES.filter(p => has(p, plang) && st(plang, p.en));
        const pool = seen.length >= 4 ? seen : PHRASES.filter(p => has(p, plang)).slice(0, 40);
        q = pool.sort(() => Math.random() - 0.5).slice(0, 10).map(p => ({ p, isNew: false, listen: true }));
      } else {
        q.forEach(x => { if (!x.isNew && Math.random() < 0.34) x.listen = true; });
      }
      if (!q.length) { body.innerHTML = ""; body.appendChild(el("p", "pr-lead", esc(tr("p_nothing")))); const b = el("button", "btn", esc(tr("p_back"))); b.addEventListener("click", home); body.appendChild(b); return; }
      session = { q, i: 0, right: 0, done: 0, again: [] };
      markDay();
      next();
    }

    function header(item) {
      const p = item.p;
      const h = el("div", "pr-head");
      h.innerHTML = `<span class="pr-count">${session.i + 1} / ${session.q.length}</span><span class="pr-cat">${catIcon(p.cat)}${esc(catName(p.cat))}</span>${item.isNew ? `<span class="pr-new">${esc(tr("p_newtag"))}</span>` : ""}`;
      return h;
    }

    function next() {
      if (session.i >= session.q.length) return finish();
      const item = session.q[session.i];
      if (item.listen) listenItem(item); else recallItem(item);
    }

    function answerBlock(p, lang) {
      const a = el("div", "pr-answer");
      const cls = lang === "cmn" ? "hz-cmn" : ZH.has(lang) ? "hz-yue" : "";
      a.appendChild(el("div", "pr-target " + cls, esc(fullText(p, lang))));
      if (ZH.has(lang)) {
        const rom = (p[lang] || []).map(t => t.rom).filter(Boolean).join(" ");
        a.appendChild(el("div", "pr-rom", `<span class="std">${romAs("std", () => romHtml(lang, rom))}</span><span class="easy">${esc(romAs("easy", () => romText(lang, rom)))}</span>`));
      }
      const hooks = [];
      (p[lang] || []).forEach(t => hooksFor(t.hz).slice(0, 1).forEach(h => hooks.push([t.hz, h])));
      if (!ZH.has(lang)) (p.gloss || []).forEach(g => { const k = g.toLowerCase().replace(/[^a-z ]/g, "").trim(); if (EU_HOOKS[k]) hooks.push([g, ["bridge", EU_HOOKS[k]]]); });
      if (hooks.length) {
        const hk = el("div", "pr-hooks");
        hooks.slice(0, 3).forEach(([w, h]) => hk.appendChild(el("p", "", `${hookIcon(h[0])}<span><b class="${ZH.has(lang) ? cls : ""}">${esc(w)}</b> ${esc(h[1])}</span>`)));
        a.appendChild(hk);
      }
      const tools = el("div", "pr-tools");
      const pl = el("button", "pbtn", `${speaker}${esc(tr("listen"))}`);
      pl.type = "button";
      pl.addEventListener("click", () => sayFull(p, lang));
      const sh = el("button", "pbtn", `${icon("mic")}${esc(tr("p_shadow"))}`);
      sh.type = "button";
      sh.addEventListener("click", () => shadow(p, lang, sh));
      tools.appendChild(pl);
      tools.appendChild(sh);
      a.appendChild(tools);
      return a;
    }

    function recallItem(item) {
      const p = item.p;
      body.innerHTML = "";
      body.appendChild(header(item));
      body.appendChild(el("div", "pr-prompt", esc(p.en)));
      body.appendChild(el("p", "pr-hint", esc(tr("p_say", { lang: NAMES[plang] }))));
      const show = el("button", "btn pr-show", esc(tr("p_reveal")));
      show.type = "button";
      body.appendChild(show);
      show.addEventListener("click", () => {
        show.remove();
        body.appendChild(answerBlock(p, plang));
        sayFull(p, plang);
        const rate = el("div", "pr-rate");
        [[0, "p_again"], [1, "p_hard"], [2, "p_good"], [3, "p_easy"]].forEach(([g, k]) => {
          const b = el("button", "btn " + (g === 2 ? "" : "quiet"), `<b>${esc(tr(k))}</b><small>${preview(plang, p.en, g)}</small>`);
          b.type = "button";
          b.addEventListener("click", () => grade(item, g));
          rate.appendChild(b);
        });
        body.appendChild(el("p", "pr-hint", esc(tr("p_rate"))));
        body.appendChild(rate);
      });
    }

    function grade(item, g) {
      if (item.isNew) { newDay.n[plang] = (newDay.n[plang] || 0) + 1; save("polygrok-newday", newDay); }
      schedule(plang, item.p.en, g);
      session.done++;
      if (g > 0) session.right++;
      if (g === 0 && session.again.filter(x => x === item.p.en).length < 2) { session.again.push(item.p.en); session.q.push({ p: item.p, isNew: false }); }
      session.i++;
      next();
    }

    function listenItem(item) {
      const p = item.p;
      body.innerHTML = "";
      body.appendChild(header(item));
      body.appendChild(el("p", "pr-hint", esc(tr("p_listen_q", { lang: NAMES[plang] }))));
      const again = el("button", "btn pr-show", `${speaker}${esc(tr("p_play"))}`);
      again.type = "button";
      again.addEventListener("click", () => sayFull(p, plang));
      body.appendChild(again);
      setTimeout(() => sayFull(p, plang), 250);
      const pool = PHRASES.filter(x => x.en !== p.en && has(x, plang));
      const same = pool.filter(x => x.cat === p.cat).sort(() => Math.random() - 0.5).slice(0, 2);
      const other = pool.filter(x => !same.includes(x)).sort(() => Math.random() - 0.5).slice(0, 3 - same.length);
      const opts = [p, ...same, ...other].sort(() => Math.random() - 0.5);
      const box = el("div", "pr-opts");
      opts.forEach(o => {
        const b = el("button", "btn quiet pr-opt", esc(o.en));
        b.type = "button";
        b.addEventListener("click", () => {
          const ok = o === p;
          box.querySelectorAll("button").forEach(x => { x.disabled = true; });
          b.classList.add(ok ? "right" : "wrong");
          [...box.children][opts.indexOf(p)].classList.add("right");
          if (!item.isNew) schedule(plang, p.en, ok ? 2 : 0);
          session.done++;
          if (ok) session.right++;
          body.appendChild(el("p", "pr-verdict", esc(tr(ok ? "p_right" : "p_wrong"))));
          body.appendChild(answerBlock(p, plang));
          const nx = el("button", "btn pr-show", esc(tr("p_next")));
          nx.type = "button";
          nx.addEventListener("click", () => { session.i++; next(); });
          body.appendChild(nx);
        });
        box.appendChild(b);
      });
      body.appendChild(box);
    }

    function shadow(p, lang, btn) {
      const len = ZH.has(lang) ? [...fullText(p, lang)].length * 0.33 : fullText(p, lang).split(" ").length * 0.42;
      const gap = Math.max(1800, (len + 1.4) * 1000);
      const keep = settings.rate;
      let k = 0;
      btn.disabled = true;
      const steps = [0.75, 1, 1];
      const run = () => {
        if (k >= steps.length) { settings.rate = keep; btn.disabled = false; btn.innerHTML = `${icon("mic")}${esc(tr("p_shadow"))}`; return; }
        settings.rate = steps[k];
        sayFull(p, lang);
        btn.innerHTML = `${icon("mic")}${esc(tr("p_your_turn", { n: k + 1 }))}`;
        k++;
        setTimeout(run, gap / steps[k - 1] + len * 1000);
      };
      run();
    }

    function finish() {
      body.innerHTML = "";
      const pct = session.done ? Math.round(100 * session.right / session.done) : 0;
      body.appendChild(el("div", "pr-done", `${icon("sparkle")}<b>${esc(tr("p_done", { n: session.done }))}</b><span>${esc(tr("p_done_pct", { p: pct }))}</span>`));
      body.appendChild(el("p", "pr-hint", esc(tr("p_sleep"))));
      const c = counts();
      body.appendChild(el("p", "pr-hint", esc(tr("p_after", { d: c.due, s: days.streak || 1 }))));
      const b = el("button", "btn", esc(tr("p_back")));
      b.type = "button";
      b.addEventListener("click", home);
      body.appendChild(b);
      updateCta();
    }

    /* tone trainer: hear one syllable, pick its pitch shape (high-variability phonetic training) */

    function toneTrainer() {
      const lang = plang;
      const pool = [];
      PHRASES.forEach(p => (p[lang] || []).forEach(t => {
        const hz = [...(t.hz || "")].filter(c => /[㐀-鿿]/.test(c));
        const rs = String(t.rom || "").split(" ").filter(Boolean);
        if (hz.length === 1 && rs.length === 1) pool.push({ hz: hz[0], rom: rs[0] });
      }));
      const uniq = [...new Map(pool.map(x => [x.hz + x.rom, x])).values()];
      if (uniq.length < 6) return;
      const tone = r => {
        if (lang === "cmn") { const m = r.normalize("NFD").match(/[̄́̌̀]/); return m ? { "̄": "1", "́": "2", "̌": "3", "̀": "4" }[m[0]] : "5"; }
        const x = splitSyl(lang, r);
        return x.num;
      };
      const SETS = { yue: ["1", "2", "3", "4", "5", "6"], cmn: ["1", "2", "3", "4"], tsn: ["55", "33", "22", "32", "21"] };
      const LV = { yue: n => YUE_TONE[n], cmn: n => ({ 1: [5, 5], 2: [3, 5], 3: [2, 1, 4], 4: [5, 1] })[n], tsn: n => [...n].map(Number) };
      const items = uniq.filter(x => SETS[lang].includes(tone(x.rom))).sort(() => Math.random() - 0.5).slice(0, 12);
      let i = 0, right = 0;
      markDay();
      const play = it => lang === "tsn" ? sayTsn(it.rom) : sayVoice(it.hz, lang);
      const round = () => {
        body.innerHTML = "";
        if (i >= items.length) {
          body.appendChild(el("div", "pr-done", `${icon("tones")}<b>${right} / ${items.length}</b><span>${esc(tr("p_tone_done"))}</span>`));
          const b = el("button", "btn", esc(tr("p_back")));
          b.addEventListener("click", home);
          body.appendChild(b);
          return;
        }
        const it = items[i];
        const ans = tone(it.rom);
        body.appendChild(el("div", "pr-head", `<span class="pr-count">${i + 1} / ${items.length}</span>`));
        body.appendChild(el("p", "pr-hint", esc(tr("p_tone_q"))));
        const pb = el("button", "btn pr-show", `${speaker}${esc(tr("p_play"))}`);
        pb.addEventListener("click", () => play(it));
        body.appendChild(pb);
        setTimeout(() => play(it), 250);
        const grid = el("div", "pr-tones");
        SETS[lang].forEach(n => {
          const b = el("button", "btn quiet pr-tone", `${contourSvg(LV[lang](n), "big")}<b>${n}</b>`);
          b.addEventListener("click", () => {
            grid.querySelectorAll("button").forEach(x => { x.disabled = true; });
            const ok = n === ans;
            if (ok) right++;
            b.classList.add(ok ? "right" : "wrong");
            [...grid.children][SETS[lang].indexOf(ans)].classList.add("right");
            const cls = lang === "cmn" ? "hz-cmn" : "hz-yue";
            body.appendChild(el("p", "pr-verdict", `${esc(tr(ok ? "p_right" : "p_wrong"))} <span class="${cls} pr-char">${esc(it.hz)}</span> ${romAs("std", () => romHtml(lang, it.rom))}`));
            const nx = el("button", "btn pr-show", esc(tr("p_next")));
            nx.addEventListener("click", () => { i++; round(); });
            body.appendChild(nx);
          });
          grid.appendChild(b);
        });
        body.appendChild(grid);
      };
      round();
    }

    /* call-to-action on the main page */

    function updateCta() {
      const b = $("practice-btn");
      if (!b) return;
      const c = counts();
      b.innerHTML = `${icon("brain")}<span><b>${esc(tr("p_title"))}</b><small>${esc(tr("p_cta", { d: c.due, n: c.newLeft, s: days.streak || 0 }))}</small></span>`;
    }

    return { open, updateCta, inDeck, toggleDeck };
  })();


  /* research-backed guide to learning with Polygrok */

  let learnTab = "why";

  function openLearn(which) {
    let d = $("learn");
    if (!d) {
      d = document.createElement("dialog");
      d.id = "learn";
      d.className = "guide learn";
      document.body.appendChild(d);
    }
    if (which) learnTab = which;
    const tabs = [["why", "l_tab_why", "brain"], ["day", "l_tab_day", "sun"], ["rules", "l_tab_rules", "parts"], ["read", "l_tab_read", "book"]];
    const seg = `<div class="lp-tabs" role="tablist">${tabs.map(([k, l, ic]) => `<button type="button" class="chip" role="tab" data-tab="${k}" aria-pressed="${learnTab === k}">${icon(ic)}${esc(tr(l))}</button>`).join("")}</div>`;
    let body = "";
    if (learnTab === "why") {
      const P = LEARN_POINTS.map(x => `<section class="lp-item">${icon(x[0])}<div><h3>${esc(x[1])}</h3><p>${x[2]}</p><p class="lp-how"><b>${esc(tr("l_inapp"))}</b> ${x[3]}</p></div></section>`).join("");
      const S = LEARN_SOURCES.map(([t, u]) => `<li><a href="${u}" target="_blank" rel="noopener">${esc(t)}</a></li>`).join("");
      body = `<p>${esc(tr("l_lead"))}</p>${P}<section><h3>${esc(tr("g_src_h"))}</h3><ul class="lp-src">${S}</ul></section>`;
    } else if (learnTab === "day") {
      body = `<p>${esc(tr("l_day_lead"))}</p><ol class="lp-day">${DAY_PLAN.map(([ic, h, what, why]) => `<li>${icon(ic)}<div><h3>${esc(h)}</h3><p><b>${esc(what)}</b></p><p class="lp-how">${esc(why)}</p></div></li>`).join("")}</ol>`;
    } else if (learnTab === "rules") {
      body = RULES.map(r => `<section class="lp-rule"><h3>${icon(r.ico)}${esc(r.h)}</h3><p class="lp-how">${esc(r.intro)}</p><ul>${r.items.map(x => `<li>${x}</li>`).join("")}</ul></section>`).join("") + `<p class="lp-how">${esc(tr("l_rules_tip"))}</p>`;
    } else {
      body = `<p>${esc(tr("l_read_lead"))}</p>` + READING.map(([h, xs]) => `<section><h3>${esc(h)}</h3><ul class="lp-src">${xs.map(([t, u]) => `<li><a href="${u}" target="_blank" rel="noopener">${esc(t)}</a></li>`).join("")}</ul></section>`).join("");
    }
    d.innerHTML = `<div class="guide-in"><div class="guide-head"><h2>${esc(tr("l_title"))}</h2><button class="btn quiet" type="button" id="learn-close">${esc(tr("g_close"))}</button></div>${seg}${body}</div>`;
    d.querySelector("#learn-close").addEventListener("click", () => d.close());
    d.querySelectorAll("[data-tab]").forEach(b => b.addEventListener("click", () => { learnTab = b.dataset.tab; openLearn(); d.scrollTop = 0; }));
    if (!d.open) d.showModal();
  }

  const LEARN_POINTS = [
    ["brain", "Pull it out of memory, don't just reread", "Trying to recall an answer strengthens memory far more than looking at it again. In one well-known study, students who kept testing themselves on foreign words remembered about 80% a week later; students who only restudied remembered about 35%.", "Practice shows the English first and asks you to come up with the sentence before you see it."],
    ["calendar", "Space it out", "Reviews spread over days beat the same amount of study crammed into one sitting, and the best gap grows as you get better. Forgetting a little between reviews is part of what makes memories last.", "Each card comes back after 1 day, then 3, then about a week, then longer. Tap Again and it returns in a minute."],
    ["mic", "Say it out loud", "Words you produce aloud are remembered better than words you read silently: the production effect. Speaking also trains the mouth and ear together.", "Every practice card asks you to say the sentence aloud first. Shadow plays it slow, then at normal speed, with pauses for you to repeat."],
    ["bubbles", "Use what you already know", "Adults learn new words faster when they hook them onto known sounds: the keyword method roughly doubled recall in classic studies. Your 下雨 xià yǔ to lluvia link is exactly this.", "Memory hooks link Chinese sounds to English, Spanish, French and German, and show cognates across the European languages. Write your own hook in any word card: hooks you make yourself stick best."],
    ["book", "Pair words with pictures", "Information stored as both words and images has two routes back into memory (dual coding). Many Chinese characters began as pictures, and those stories make them easier to recall.", "Character stories (好 = woman + child, 休 = person resting on a tree) and a picture for every topic."],
    ["cards", "Mix it up", "Mixing topics and skills (interleaving) feels harder than doing one block at a time, but it leads to better long-term learning. That kind of helpful struggle is called a desirable difficulty.", "Sessions shuffle topics and switch between saying, listening and choosing."],
    ["ear", "Train your ear on many examples", "Adults can learn to hear tones they didn't grow up with. Training works best with lots of different words and quick feedback, and the gains carry over to new words.", "The tone trainer plays single syllables from across the guide. You pick the pitch shape and see right away if you were right."],
    ["chat", "Learn whole chunks", "Fluent speech is built from ready-made phrases, not words assembled one at a time. Learning sentences you'll actually say gives you useful chunks and their grammar for free.", "Cards are real family sentences. The word rows show how each chunk is built, and the full sentence shows how it's said."],
    ["heart", "Make it personal and emotional", "We remember what relates to ourselves and what we care about (the self-reference effect), and a bit of fun or emotion helps too.", "Add the sentences you really need to your practice deck, and use the Joking Around section on your family."],
    ["sparkle", "Sleep on it", "Sleep helps new words settle into long-term memory and connect with the words you already know. In one study, new words learned in the evening were integrated after a night's sleep; words learned in the morning weren't, until after sleep.", "A short session in the evening, then a quick review the next day, is ideal."],
  ];

  const LEARN_SOURCES = [
    ["Karpicke & Roediger (2008), The critical importance of retrieval for learning, Science", "https://www.brucehayes.org/Teaching/papers/2008_Roediger_Karpicke_Science.pdf"],
    ["Cepeda et al. (2006), Distributed practice in verbal recall tasks, Psychological Bulletin", "https://pubmed.ncbi.nlm.nih.gov/16719566/"],
    ["Raugh & Atkinson, the keyword method for foreign-language vocabulary", "https://suppescorpus.stanford.edu/sites/g/files/sbiybj32751/files/media/file/imsss_224.pdf"],
    ["Ozubko & MacLeod (2010), The production effect in memory", "https://uwaterloo.ca/memory-attention-cognition-lab/sites/default/files/uploads/files/jeplmc10-2.pdf"],
    ["Bjork & Bjork, Desirable difficulties (Association for Psychological Science)", "https://www.psychologicalscience.org/observer/desirable-difficulties"],
    ["Paivio, dual-coding theory", "https://en.wikipedia.org/wiki/Dual-coding_theory"],
    ["Dumay & Gaskell (2007), Sleep and the integration of new spoken words, Psychological Science", "https://kar.kent.ac.uk/14941"],
    ["Giannakopoulou et al. (2017), High or low? Comparing high- and low-variability phonetic training, PeerJ", "https://peerj.com/articles/3209"],
  ];
