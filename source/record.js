  /* recordings: capture family and friends talking, keep it on the phone, and work through it slowly later */

  const Rec = (() => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    const SR_LANG = { tsn: "zh-HK", yue: "zh-HK", cmn: "zh-CN", es: "es-MX", fr: "fr-FR", de: "de-DE", en: "en-US", mix: "zh-HK" };
    const HOME_LANG = { tsn: "yue", yue: "yue", cmn: "zh", es: "es", fr: "fr", de: "de", en: "en", mix: "" };
    const REC_LANGS = ["tsn", "yue", "cmn", "es", "fr", "de", "en", "mix"];

    const DB = (() => {
      let p;
      const open = () => p || (p = new Promise((res, rej) => {
        const r = indexedDB.open("polygrok-rec", 1);
        r.onupgradeneeded = () => r.result.createObjectStore("recs", { keyPath: "id" });
        r.onsuccess = () => res(r.result);
        r.onerror = () => rej(r.error);
      }));
      const run = (mode, fn) => open().then(db => new Promise((res, rej) => {
        const t = db.transaction("recs", mode);
        const q = fn(t.objectStore("recs"));
        t.oncomplete = () => res(q && "result" in q ? q.result : undefined);
        t.onerror = () => rej(t.error);
      }));
      return {
        all: () => run("readonly", s => s.getAll()),
        get: id => run("readonly", s => s.get(id)),
        put: r => run("readwrite", s => s.put(r)),
        del: id => run("readwrite", s => s.delete(id)),
      };
    })();

    let dlg = null;
    let view = { name: "list" };
    let live = null;
    let player = null;

    const langName = l => l === "mix" ? tr("r_mixed") : NAMES[l];
    const fmt = s => { s = Math.max(0, Math.round(s)); return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`; };
    const blobOf = r => new Blob([r.buf], { type: r.type || "audio/mp4" });
    const homeUrl = () => (store.get("polygrok-home") || "").replace(/\/+$/, "");

    function pickMime() {
      if (!window.MediaRecorder || !MediaRecorder.isTypeSupported) return "";
      return ["audio/mp4", "audio/webm;codecs=opus", "audio/webm"].find(t => MediaRecorder.isTypeSupported(t)) || "";
    }


    /* rough offline gloss for Chinese transcripts, from the words in this guide */

    let ZH = null;

    function zhMap() {
      if (ZH) return ZH;
      const cnt = new Map();
      PHRASES.forEach(p => ["yue", "cmn", "tsn"].forEach(l => (p[l] || []).forEach(t => {
        if (!t.hz || (t.refs || []).length !== 1) return;
        const g = (p.gloss[t.refs[0]] || "").replace(/\([^)]*\)/g, "").trim().toLowerCase();
        if (!g) return;
        const m = cnt.get(t.hz) || new Map();
        m.set(g, (m.get(g) || 0) + 1);
        cnt.set(t.hz, m);
      })));
      ZH = new Map();
      cnt.forEach((m, hz) => ZH.set(hz, [...m.entries()].sort((a, b) => b[1] - a[1])[0][0]));
      return ZH;
    }

    function gloss(text) {
      const m = zhMap();
      const out = [];
      const cs = [...text];
      let i = 0;
      while (i < cs.length) {
        let hit = null;
        for (let n = Math.min(5, cs.length - i); n > 0; n--) {
          const w = cs.slice(i, i + n).join("");
          if (m.has(w)) { hit = [w, m.get(w)]; break; }
        }
        if (hit) { out.push(`<span class="gl"><b>${esc(hit[0])}</b><small>${esc(hit[1])}</small></span>`); i += [...hit[0]].length; }
        else { out.push(`<span class="gl"><b>${esc(cs[i])}</b><small>&nbsp;</small></span>`); i++; }
      }
      return out.join("");
    }

    const isZh = s => /[㐀-鿿]/.test(s);


    /* dialog shell */

    function open() {
      if (!dlg) {
        dlg = document.createElement("dialog");
        dlg.id = "rec";
        dlg.className = "practice rec";
        document.body.appendChild(dlg);
        dlg.addEventListener("close", () => { stopPlayer(); if (live) stopRec(true); });
      }
      if (!live) view = { name: "list" };
      paint();
      if (!dlg.open) dlg.showModal();
      try { navigator.storage && navigator.storage.persist && navigator.storage.persist(); } catch (e) {}
    }

    function shell(title) {
      dlg.innerHTML = `<div class="pr-top"><span class="pr-title">${icon("mic")}${esc(title)}</span><button class="btn quiet" type="button" data-x>${esc(tr("g_close"))}</button></div>`;
      dlg.querySelector("[data-x]").addEventListener("click", () => dlg.close());
      const body = el("div", "pr-body");
      dlg.appendChild(body);
      return body;
    }

    function paint() {
      if (view.name === "live") return paintLive();
      if (view.name === "detail") return paintDetail(view.id);
      return paintList();
    }


    /* list + start */

    async function paintList() {
      const body = shell(tr("r_title"));
      body.appendChild(el("p", "pr-lead", esc(tr("r_lead"))));

      const form = el("div", "rec-form");
      const who = document.createElement("input");
      who.className = "rec-in";
      who.placeholder = tr("r_who_ph");
      who.value = store.get("polygrok-rec-who") || "";
      const lang = document.createElement("select");
      lang.className = "rec-in";
      REC_LANGS.forEach(l => lang.appendChild(new Option(langName(l), l)));
      lang.value = store.get("polygrok-rec-lang") || "yue";
      const wl = el("label", "rec-l", `<span>${esc(tr("r_who"))}</span>`);
      wl.appendChild(who);
      const ll = el("label", "rec-l", `<span>${esc(tr("r_lang"))}</span>`);
      ll.appendChild(lang);
      form.append(wl, ll);

      let liveBox = null;
      if (SR) {
        liveBox = document.createElement("input");
        liveBox.type = "checkbox";
        liveBox.checked = store.get("polygrok-rec-live") === "1";
        const lab = el("label", "rec-check", "");
        lab.appendChild(liveBox);
        lab.appendChild(el("span", "", esc(tr("r_live"))));
        form.appendChild(lab);
      }
      const note = el("p", "pr-hint", "");
      const paintNote = () => { note.textContent = lang.value === "tsn" ? tr("r_tsn_note") : tr("r_consent"); };
      paintNote();
      lang.addEventListener("change", paintNote);
      form.appendChild(note);

      const go = el("button", "btn pr-big rec-go", `${icon("mic")}<span><b>${esc(tr("r_start"))}</b></span>`);
      go.type = "button";
      go.addEventListener("click", () => {
        store.set("polygrok-rec-who", who.value.trim());
        store.set("polygrok-rec-lang", lang.value);
        if (liveBox) store.set("polygrok-rec-live", liveBox.checked ? "1" : "");
        startRec({ who: who.value.trim(), lang: lang.value, captions: !!(liveBox && liveBox.checked) });
      });
      form.appendChild(go);
      body.appendChild(form);

      const ul = el("ul", "rec-list");
      body.appendChild(ul);
      let recs = [];
      try { recs = (await DB.all()).sort((a, b) => b.at - a.at); } catch (e) {}
      if (!recs.length) ul.appendChild(el("li", "pr-hint", esc(tr("r_none"))));
      recs.forEach(r => {
        const li = el("li", "");
        const b = el("button", "rec-row", `<span><b>${esc(r.who || tr("r_title"))}</b><small>${esc(new Date(r.at).toLocaleString([], { dateStyle: "medium", timeStyle: "short" }))} · ${esc(langName(r.lang))}</small></span><span class="rec-meta">${fmt(r.dur)}${r.marks.length ? ` · ${esc(tr("r_marks", { n: r.marks.length }))}` : ""}</span>`);
        b.type = "button";
        b.addEventListener("click", () => { view = { name: "detail", id: r.id }; paint(); });
        li.appendChild(b);
        ul.appendChild(li);
      });

      body.appendChild(homeSettings());
      body.appendChild(el("p", "pr-hint", esc(tr("r_store"))));
    }

    function homeSettings() {
      const box = el("details", "rec-home");
      box.appendChild(el("summary", "", esc(tr("r_home_set"))));
      const row = el("div", "rec-home-row");
      const inp = document.createElement("input");
      inp.className = "rec-in";
      inp.type = "url";
      inp.placeholder = tr("r_home_ph");
      inp.value = store.get("polygrok-home") || "";
      inp.addEventListener("change", () => store.set("polygrok-home", inp.value.trim()));
      const test = el("button", "pbtn", esc(tr("r_home_test")));
      test.type = "button";
      const msg = el("p", "pr-hint", "");
      test.addEventListener("click", async () => {
        store.set("polygrok-home", inp.value.trim());
        msg.textContent = "…";
        try {
          const r = await fetch(homeUrl() + "/health", { cache: "no-store" });
          const j = await r.json();
          msg.textContent = `${tr("r_home_ok")}: ${j.model || ""} ${j.device || ""}`;
        } catch (e) { msg.textContent = tr("r_home_fail"); }
      });
      row.append(inp, test);
      box.append(row, msg);
      return box;
    }


    /* recording */

    async function startRec(opts) {
      let stream;
      try {
        stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: true } });
      } catch (e) {
        alertIn(tr("r_mic_fail"));
        return;
      }
      const mime = pickMime();
      const mr = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined);
      const chunks = [];
      mr.ondataavailable = e => { if (e.data && e.data.size) chunks.push(e.data); };
      live = { ...opts, stream, mr, chunks, t0: performance.now(), marks: [], lines: [], interim: "", ac: null, raf: 0, sr: null, restarts: 0 };
      mr.start(1000);

      try {
        const AC = window.AudioContext || window.webkitAudioContext;
        const ac = new AC();
        const an = ac.createAnalyser();
        an.fftSize = 512;
        ac.createMediaStreamSource(stream).connect(an);
        live.ac = ac;
        live.an = an;
      } catch (e) {}

      if (opts.captions && SR) startCaptions();
      view = { name: "live" };
      paint();
    }

    const elapsed = () => live ? (performance.now() - live.t0) / 1000 : 0;

    function startCaptions() {
      try {
        const sr = new SR();
        sr.lang = SR_LANG[live.lang] || "zh-HK";
        sr.continuous = true;
        sr.interimResults = true;
        sr.onresult = e => {
          let interim = "";
          for (let i = e.resultIndex; i < e.results.length; i++) {
            const r = e.results[i];
            if (r.isFinal) live.lines.push({ t: Math.max(0, elapsed() - 2), text: r[0].transcript.trim(), src: "live" });
            else interim += r[0].transcript;
          }
          live.interim = interim;
          paintCaptions();
        };
        sr.onerror = e => { if (e.error === "not-allowed" || e.error === "service-not-allowed" || e.error === "network") { live.srDead = true; const n = $("rec-cap-note"); if (n) n.textContent = tr("r_live_fail"); } };
        sr.onend = () => { if (live && !live.stopping && !live.srDead && live.restarts++ < 40) { try { sr.start(); } catch (e) {} } };
        sr.start();
        live.sr = sr;
      } catch (e) { live.srDead = true; }
    }

    function paintCaptions() {
      const box = $("rec-caps");
      if (!box || !live) return;
      const last = live.lines.slice(-4).map(l => `<p>${esc(l.text)}</p>`).join("");
      box.innerHTML = last + (live.interim ? `<p class="interim">${esc(live.interim)}</p>` : "");
    }

    function paintLive() {
      const body = shell(tr("r_rec"));
      const top = el("div", "rec-live");
      top.innerHTML = `<span class="rec-dot" aria-hidden="true"></span><b id="rec-time">0:00</b><canvas id="rec-meter" width="240" height="36" aria-hidden="true"></canvas>`;
      body.appendChild(top);
      body.appendChild(el("p", "pr-hint", esc(`${live.who ? live.who + " · " : ""}${langName(live.lang)}`)));
      const acts = el("div", "rec-acts");
      const mark = el("button", "btn pr-big", `${icon("bookmark")}<span><b>${esc(tr("r_mark"))}</b><small id="rec-mk">${esc(tr("r_marks", { n: live.marks.length }))}</small></span>`);
      mark.type = "button";
      mark.addEventListener("click", () => {
        live.marks.push({ t: Math.max(0, elapsed() - 3), said: "", mean: "" });
        $("rec-mk").textContent = tr("r_marks", { n: live.marks.length });
        try { navigator.vibrate && navigator.vibrate(20); } catch (e) {}
      });
      const stop = el("button", "btn quiet pr-big rec-stop", `<span class="sq" aria-hidden="true"></span><span><b>${esc(tr("r_stop"))}</b></span>`);
      stop.type = "button";
      stop.addEventListener("click", () => stopRec(false));
      acts.append(mark, stop);
      body.appendChild(acts);
      if (live.sr || live.captions) {
        const n = el("p", "pr-hint", live.srDead ? esc(tr("r_live_fail")) : "");
        n.id = "rec-cap-note";
        body.appendChild(n);
        const caps = el("div", "rec-caps");
        caps.id = "rec-caps";
        body.appendChild(caps);
        paintCaptions();
      }
      tick();
    }

    function tick() {
      if (!live) return;
      const t = $("rec-time");
      if (t) t.textContent = fmt(elapsed());
      const c = $("rec-meter");
      if (c && live.an) {
        const g = c.getContext("2d");
        const d = new Uint8Array(live.an.fftSize);
        live.an.getByteTimeDomainData(d);
        let peak = 0;
        for (const v of d) peak = Math.max(peak, Math.abs(v - 128));
        live.hist = (live.hist || []).concat(peak / 128).slice(-60);
        const ink = getComputedStyle(c).color;
        g.clearRect(0, 0, c.width, c.height);
        g.fillStyle = ink;
        live.hist.forEach((v, i) => { const h = Math.max(2, v * c.height); g.fillRect(i * 4, (c.height - h) / 2, 2, h); });
      }
      live.raf = requestAnimationFrame(tick);
    }

    function stopRec(discard) {
      if (!live) return;
      const L = live;
      L.stopping = true;
      cancelAnimationFrame(L.raf);
      try { L.sr && L.sr.stop(); } catch (e) {}
      const dur = elapsed();
      L.mr.onstop = async () => {
        L.stream.getTracks().forEach(t => t.stop());
        try { L.ac && L.ac.close(); } catch (e) {}
        live = null;
        if (discard || !L.chunks.length) { view = { name: "list" }; if (dlg.open) paint(); return; }
        const type = L.chunks[0].type || L.mr.mimeType || "audio/mp4";
        const buf = await new Blob(L.chunks, { type }).arrayBuffer();
        const r = { id: "r" + Date.now().toString(36), at: Date.now(), who: L.who, lang: L.lang, dur, type, buf, marks: L.marks, lines: L.lines };
        try { await DB.put(r); } catch (e) { alertIn(tr("r_mic_fail")); }
        view = { name: "detail", id: r.id };
        if (dlg.open) paint();
      };
      try { L.mr.stop(); } catch (e) { L.mr.onstop(); }
    }

    function alertIn(msg) {
      const b = dlg && dlg.querySelector(".pr-body");
      if (b) b.prepend(el("p", "rec-alert", esc(msg)));
    }


    /* playback and study */

    function stopPlayer() {
      if (!player) return;
      try { player.a.pause(); URL.revokeObjectURL(player.url); } catch (e) {}
      cancelAnimationFrame(player.raf);
      player = null;
    }

    async function paintDetail(id) {
      stopPlayer();
      const r = await DB.get(id);
      if (!r) { view = { name: "list" }; return paint(); }
      const body = shell(r.who || tr("r_title"));
      const back = el("button", "link", `← ${esc(tr("r_back"))}`);
      back.type = "button";
      back.addEventListener("click", () => { stopPlayer(); view = { name: "list" }; paint(); });
      body.appendChild(back);
      body.appendChild(el("p", "pr-hint", esc(`${new Date(r.at).toLocaleString([], { dateStyle: "medium", timeStyle: "short" })} · ${langName(r.lang)} · ${fmt(r.dur)}`)));

      const url = URL.createObjectURL(blobOf(r));
      const a = new Audio(url);
      a.preload = "auto";
      player = { a, url, loop: null, raf: 0 };
      const save = () => DB.put(r).catch(() => {});

      const pl = el("div", "rec-player");
      const playB = el("button", "btn rec-play", "");
      playB.type = "button";
      const paintPlay = () => { playB.innerHTML = a.paused ? `${speaker}<span>${esc(tr("p_play"))}</span>` : `<span class="sq" aria-hidden="true"></span><span>${esc(tr("r_stop"))}</span>`; };
      paintPlay();
      playB.addEventListener("click", () => { a.paused ? a.play().catch(() => {}) : a.pause(); });
      a.addEventListener("play", paintPlay);
      a.addEventListener("pause", paintPlay);
      const back5 = el("button", "pbtn", "−5s");
      back5.type = "button";
      back5.addEventListener("click", () => { a.currentTime = Math.max(0, a.currentTime - 5); });
      const seek = document.createElement("input");
      seek.type = "range";
      seek.min = 0;
      seek.step = 0.1;
      seek.max = r.dur || 1;
      seek.value = 0;
      seek.className = "rec-seek";
      seek.addEventListener("input", () => { a.currentTime = +seek.value; });
      const tm = el("span", "rec-tm", `0:00 / ${fmt(r.dur)}`);
      const speeds = el("div", "rec-speeds");
      [0.5, 0.75, 1].forEach(s => {
        const b = el("button", "chip", `${s}×`);
        b.type = "button";
        b.setAttribute("aria-pressed", s === 1 ? "true" : "false");
        b.addEventListener("click", () => { a.playbackRate = s; speeds.querySelectorAll(".chip").forEach(x => x.setAttribute("aria-pressed", x === b ? "true" : "false")); });
        speeds.appendChild(b);
      });
      const addMark = el("button", "pbtn", `${icon("bookmark")}${esc(tr("r_mark"))}`);
      addMark.type = "button";
      addMark.addEventListener("click", () => { r.marks.push({ t: a.currentTime, said: "", mean: "" }); r.marks.sort((x, y) => x.t - y.t); save(); paintMarks(); });
      pl.append(playB, back5, seek, tm, speeds, addMark);
      body.appendChild(pl);

      const frame = () => {
        if (!player) return;
        seek.value = a.currentTime;
        tm.textContent = `${fmt(a.currentTime)} / ${fmt(r.dur)}`;
        if (player.loop && a.currentTime >= player.loop[1]) a.currentTime = player.loop[0];
        if (player.stopAt && a.currentTime >= player.stopAt) { a.pause(); player.stopAt = 0; }
        player.raf = requestAnimationFrame(frame);
      };
      frame();

      const span = (m, i) => [Math.max(0, m.t - 1), Math.min(r.dur || m.t + 6, r.marks[i + 1] ? Math.min(r.marks[i + 1].t, m.t + 12) : m.t + 6)];

      const marksBox = el("div", "rec-marks");
      body.appendChild(marksBox);

      function paintMarks() {
        marksBox.innerHTML = "";
        if (!r.marks.length) return;
        marksBox.appendChild(el("div", "label", esc(tr("r_marks", { n: r.marks.length }))));
        r.marks.forEach((m, i) => {
          const card = el("div", "rec-mark");
          const head = el("div", "rec-mark-head");
          const go = el("button", "pbtn", `${speaker}${fmt(m.t)}`);
          go.type = "button";
          go.addEventListener("click", () => { const [s0, s1] = span(m, i); player.loop = null; player.stopAt = s1; a.currentTime = s0; a.play().catch(() => {}); });
          const lp = el("button", "pbtn", `${esc(tr("r_loop"))}`);
          lp.type = "button";
          const paintLp = () => lp.classList.toggle("on", !!(player.loop && player.loop.i === i));
          lp.addEventListener("click", () => {
            if (player.loop && player.loop.i === i) { player.loop = null; a.pause(); }
            else { const s = span(m, i); player.loop = [s[0], s[1]]; player.loop.i = i; player.stopAt = 0; a.currentTime = s[0]; a.play().catch(() => {}); }
            marksBox.querySelectorAll(".rec-mark").forEach((x, k) => x.querySelector(".lp").classList.toggle("on", !!(player.loop && player.loop.i === k)));
          });
          lp.classList.add("lp");
          paintLp();
          const del = el("button", "link", "×");
          del.type = "button";
          del.setAttribute("aria-label", tr("r_delete"));
          del.addEventListener("click", () => { r.marks.splice(i, 1); player.loop = null; save(); paintMarks(); });
          head.append(go, lp, del);
          card.appendChild(head);
          const f = (key, ph, prop) => {
            const l = el("label", "my-hook-l", `<span>${esc(tr(key))}</span>`);
            const t = document.createElement("textarea");
            t.className = "my-hook";
            t.rows = 1;
            t.placeholder = tr(ph);
            t.value = m[prop] || "";
            t.addEventListener("input", () => { m[prop] = t.value; save(); paintClip(); });
            l.appendChild(t);
            return l;
          };
          card.append(f("r_said", "r_said_ph", "said"), f("r_mean", "r_mean_ph", "mean"));
          const g = el("div", "rec-gloss", "");
          card.appendChild(g);
          const clip = el("button", "pbtn", "");
          clip.type = "button";
          const key = () => `clip:${r.id}:${Math.round(m.t * 10)}`;
          function paintClip() {
            const on = Book.isSaved(key());
            clip.innerHTML = `${icon(on ? "check" : "bookmark")}${esc(tr(on ? "r_clip_saved" : "r_clip_save"))}`;
            clip.classList.toggle("on", on);
            g.innerHTML = m.said && isZh(m.said) ? gloss(m.said) : "";
            if (on) Book.saveClip(key(), clipData(r, m, i), true);
          }
          clip.addEventListener("click", () => { Book.saveClip(key(), clipData(r, m, i)); paintClip(); });
          paintClip();
          card.appendChild(clip);
          marksBox.appendChild(card);
        });
      }

      function clipData(r, m, i) {
        const [t0, t1] = span(m, i);
        return { rec: r.id, t0, t1, said: m.said, mean: m.mean, lang: r.lang, who: r.who };
      }

      paintMarks();

      const linesBox = el("div", "rec-lines");
      body.appendChild(linesBox);
      function paintLines() {
        linesBox.innerHTML = "";
        if (!r.lines.length) return;
        linesBox.appendChild(el("div", "label", esc(tr("r_lines"))));
        if (r.lines.some(l => isZh(l.text))) linesBox.appendChild(el("p", "pr-hint", esc(tr("r_gloss_note"))));
        r.lines.forEach(l => {
          const row = el("div", "rec-line");
          const t = el("button", "pbtn", fmt(l.t));
          t.type = "button";
          t.addEventListener("click", () => { player.loop = null; player.stopAt = 0; a.currentTime = Math.max(0, l.t - 0.5); a.play().catch(() => {}); });
          const tx = el("div", "rec-line-tx", `<p>${isZh(l.text) ? esc(l.text) : esc(l.text)}</p>${isZh(l.text) ? `<div class="rec-gloss">${gloss(l.text)}</div>` : ""}${l.en ? `<p class="pr-hint">${esc(l.en)}</p>` : ""}`);
          const mk = el("button", "link", `+ ${esc(tr("r_mark"))}`);
          mk.type = "button";
          mk.addEventListener("click", () => { r.marks.push({ t: l.t, said: l.text, mean: l.en || "" }); r.marks.sort((x, y) => x.t - y.t); save(); paintMarks(); });
          tx.appendChild(mk);
          row.append(t, tx);
          linesBox.appendChild(row);
        });
      }
      paintLines();

      const tools = el("div", "pr-tools rec-tools");
      if (homeUrl()) {
        const hb = el("button", "pbtn", `${icon("house")}${esc(tr("r_home"))}`);
        hb.type = "button";
        const hm = el("p", "pr-hint", "");
        hb.addEventListener("click", async () => {
          hb.disabled = true;
          hm.textContent = tr("r_home_busy");
          try {
            const fd = new FormData();
            const ext = (r.type || "").includes("webm") ? "webm" : "m4a";
            fd.append("file", blobOf(r), `${r.id}.${ext}`);
            fd.append("language", HOME_LANG[r.lang] || "");
            fd.append("translate", "1");
            const res = await fetch(homeUrl() + "/transcribe", { method: "POST", body: fd });
            if (!res.ok) throw new Error(res.status);
            const j = await res.json();
            r.lines = r.lines.filter(l => l.src !== "home").concat((j.segments || []).map(s => ({ t: s.start, text: s.text.trim(), en: s.en || "", src: "home" }))).sort((x, y) => x.t - y.t);
            await DB.put(r);
            hm.textContent = "";
            paintLines();
          } catch (e) { hm.textContent = tr("r_home_fail"); }
          hb.disabled = false;
        });
        tools.append(hb);
        body.appendChild(tools);
        body.appendChild(hm);
      }

      const tools2 = el("div", "pr-tools");
      const sh = el("button", "pbtn", `${icon("copy")}${esc(tr("r_share"))}`);
      sh.type = "button";
      sh.addEventListener("click", async () => {
        const ext = (r.type || "").includes("webm") ? "webm" : "m4a";
        const name = `${(r.who || "recording").replace(/[^\w\- ]+/g, "")} ${new Date(r.at).toISOString().slice(0, 10)}.${ext}`;
        const file = new File([blobOf(r)], name, { type: r.type });
        try {
          if (navigator.canShare && navigator.canShare({ files: [file] })) { await navigator.share({ files: [file], title: name }); return; }
        } catch (e) { if (e && e.name === "AbortError") return; }
        const link = document.createElement("a");
        link.href = url;
        link.download = name;
        document.body.appendChild(link);
        link.click();
        link.remove();
      });
      const del = el("button", "pbtn", esc(tr("r_delete")));
      del.type = "button";
      let armed = false;
      del.addEventListener("click", async () => {
        if (!armed) { armed = true; del.textContent = tr("r_delete_sure"); setTimeout(() => { armed = false; del.textContent = tr("r_delete"); }, 3000); return; }
        stopPlayer();
        await DB.del(r.id).catch(() => {});
        view = { name: "list" };
        paint();
      });
      tools2.append(sh, del);
      body.appendChild(tools2);
    }

    async function playClip(c) {
      const r = await DB.get(c.rec).catch(() => null);
      if (!r) return false;
      if (Rec._clip) { try { Rec._clip.pause(); URL.revokeObjectURL(Rec._clip.src); } catch (e) {} }
      const a = new Audio(URL.createObjectURL(blobOf(r)));
      Rec._clip = a;
      a.addEventListener("loadedmetadata", () => { a.currentTime = c.t0; a.play().catch(() => {}); }, { once: true });
      a.addEventListener("timeupdate", () => { if (a.currentTime >= c.t1) a.pause(); });
      a.load();
      return true;
    }

    return { open, playClip, gloss };
  })();
