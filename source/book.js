  /* my phrasebook: sentences you save, and ones you already know */

  const Book = (() => {
    const KEY = "polygrok-book";
    let data = (() => { try { const v = JSON.parse(store.get(KEY) || "{}"); return v && typeof v === "object" ? v : {}; } catch (e) { return {}; } })();
    let tab = "saved";

    const save = () => store.set(KEY, JSON.stringify(data));
    const rec = en => data[en] || (data[en] = {});
    const tidy = en => { if (data[en] && !data[en].s && !data[en].k && !data[en].n) delete data[en]; };
    const noteOf = key => (data[key] && data[key].n) || "";

    function noteBox(key) {
      const l = el("label", "my-hook-l anchor-note", `<span>${esc(tr("bk_anchor"))}</span>`);
      const t = document.createElement("textarea");
      t.className = "my-hook";
      t.rows = 2;
      t.placeholder = tr("bk_anchor_ph");
      t.value = noteOf(key);
      t.addEventListener("input", () => { rec(key).n = t.value.trim() ? t.value : ""; tidy(key); save(); });
      t.addEventListener("click", e => e.stopPropagation());
      l.appendChild(t);
      return l;
    }

    const isSaved = en => !!(data[en] && data[en].s);
    const isKnown = en => !!(data[en] && data[en].k);
    const count = () => Object.values(data).filter(x => x.s).length;

    function toggleSave(p) {
      const r = rec(p.en);
      r.s = r.s ? 0 : Date.now();
      if (r.s && p.guess) r.p = p;
      if (r.s && !Practice.inDeck(p.en) && !p.guess) Practice.toggleDeck(p.en);
      tidy(p.en);
      save();
      updateBtn();
    }

    function toggleKnown(p) {
      const r = rec(p.en);
      r.k = r.k ? 0 : Date.now();
      if (r.k && p.guess) r.p = p;
      tidy(p.en);
      save();
      updateBtn();
    }

    function saveClip(key, c, updateOnly) {
      if (updateOnly) { if (data[key] && data[key].s) { data[key].c = c; save(); } return; }
      if (data[key] && data[key].s) delete data[key];
      else data[key] = { s: Date.now(), c };
      save();
      updateBtn();
    }

    const find = en => PHRASES.find(p => p.en === en) || (data[en] && data[en].p);

    function list(which) {
      return Object.entries(data)
        .filter(([, r]) => which === "known" ? r.k : r.s)
        .sort((a, b) => (which === "known" ? b[1].k - a[1].k : b[1].s - a[1].s))
        .map(([en, r]) => r.c ? { clip: r.c, key: en } : find(en))
        .filter(Boolean);
    }

    function asText(ps) {
      const langs = LANES.filter(l => l !== "en" && show[l]);
      const anchor = k => noteOf(k) ? `${tr("bk_anchor")}: ${noteOf(k)}` : "";
      return ps.map(p => p.clip ? [p.clip.mean, p.clip.said, p.clip.who, anchor(p.key)].filter(Boolean).join("\n") : [p.en, ...langs.map(l => { const t = fullText(p, l); return t ? `${NAMES[l]}: ${t}` : ""; }), anchor(p.en)].filter(Boolean).join("\n")).join("\n\n");
    }

    function updateBtn() {
      const b = $("book-btn");
      if (b) b.innerHTML = `${icon("bookmark")}<span>${esc(tr("b_btn"))}</span><span class="n">${count()}</span>`;
    }

    function controls(p) {
      const wrap = el("div", "book-acts");
      const sv = el("button", "pbtn", "");
      sv.type = "button";
      const kn = el("button", "pbtn", "");
      kn.type = "button";
      const nb = noteBox(p.en);
      const paint = () => {
        const s = isSaved(p.en), k = isKnown(p.en);
        nb.hidden = !(s || k || noteOf(p.en));
        sv.innerHTML = `${icon("bookmark")}${esc(tr(s ? "bk_saved" : "b_save"))}`;
        sv.classList.toggle("on", s);
        kn.innerHTML = `${icon("check")}${esc(tr(k ? "b_known" : "b_know"))}`;
        kn.classList.toggle("on", k);
      };
      paint();
      sv.addEventListener("click", e => { e.stopPropagation(); toggleSave(p); paint(); Practice.updateCta(); });
      kn.addEventListener("click", e => { e.stopPropagation(); toggleKnown(p); paint(); Practice.updateCta(); });
      wrap.append(sv, kn, nb);
      return wrap;
    }

    function open() {
      let d = $("book");
      if (!d) {
        d = document.createElement("dialog");
        d.id = "book";
        d.className = "practice book";
        document.body.appendChild(d);
        d.addEventListener("click", e => { if (e.target === d) d.close(); });
      }
      paintDialog(d);
      if (!d.open) d.showModal();
    }

    function paintDialog(d) {
      const ps = list(tab);
      d.innerHTML = `<div class="pr-top"><span class="pr-title">${icon("bookmark")}${esc(tr("b_title"))}</span><button class="btn quiet" type="button" data-x>${esc(tr("g_close"))}</button></div>`;
      const body = el("div", "pr-body");
      body.appendChild(el("p", "pr-lead", esc(tr("b_lead"))));
      const seg = el("div", "pr-langs");
      [["saved", "b_tab_saved", count()], ["known", "b_tab_known", Object.values(data).filter(x => x.k).length]].forEach(([k, label, n]) => {
        const b = el("button", "chip" + (tab === k ? " on" : ""), `${esc(tr(label))} <span class="n">${n}</span>`);
        b.type = "button";
        b.setAttribute("aria-pressed", tab === k ? "true" : "false");
        b.addEventListener("click", () => { tab = k; paintDialog(d); });
        seg.appendChild(b);
      });
      body.appendChild(seg);
      if (!ps.length) {
        body.appendChild(el("p", "pr-hint", esc(tr(tab === "known" ? "b_empty_known" : "b_empty"))));
      } else {
        const tools = el("div", "pr-tools");
        const cp = el("button", "pbtn", `${icon("copy")}${esc(tr("b_copy"))}`);
        cp.type = "button";
        cp.addEventListener("click", () => {
          const txt = asText(ps);
          const done = () => { cp.innerHTML = `${icon("check")}${esc(tr("b_copied"))}`; };
          try { navigator.clipboard.writeText(txt).then(done, () => {}); } catch (e) {}
        });
        tools.appendChild(cp);
        const pdf = el("button", "pbtn", `${icon("book")}${esc(tr("b_pdf"))}`);
        pdf.type = "button";
        pdf.addEventListener("click", () => { d.close(); exportPdf(ps, tab); });
        tools.appendChild(pdf);
        if (tab === "saved") {
          const pr = el("button", "pbtn", `${icon("brain")}${esc(tr("b_practice"))}`);
          pr.type = "button";
          pr.addEventListener("click", () => { d.close(); Practice.open(); });
          tools.appendChild(pr);
        }
        body.appendChild(tools);
        const ul = el("ul", "list");
        ps.forEach(p => {
          const li = p.clip ? clipItem(p, d) : rowItem(p);
          li.appendChild(noteBox(p.clip ? p.key : p.en));
          ul.appendChild(li);
        });
        body.appendChild(ul);
      }
      d.appendChild(body);
      d.querySelector("[data-x]").addEventListener("click", () => d.close());
    }

    const ZH_LANGS = ["tsn", "yue", "cmn"];

    function pdfRow(p, l) {
      const text = fullText(p, l);
      if (!text) return "";
      const zh = ZH_LANGS.includes(l);
      const rom = zh ? romText(l, (p[l] || []).map(t => t.rom).filter(Boolean).join(" ")) : (romLine(p, l) ? easyMe(l, romLine(p, l)) : "");
      const words = zh ? (p[l] || []).filter(t => t.hz).map(t => {
        const g = (t.refs || []).map(r => p.gloss[r]).filter(Boolean).join(" ");
        return `<span class="pb-w"><small>${esc(romText(l, t.rom || ""))}</small><b>${esc(t.hz)}</b><small>${esc(g || "·")}</small></span>`;
      }).join("") : "";
      const dir = RTL.has(l) ? ` dir="rtl" lang="${HTML_LANG[l]}"` : "";
      return `<div class="pb-row"><div class="pb-lang">${esc(NAMES[l])}</div><div><div class="pb-text"${dir}>${esc(text)}</div>${rom ? `<div class="pb-rom">${esc(rom)}</div>` : ""}${words ? `<div class="pb-words">${words}</div>` : ""}</div></div>`;
    }

    const pdfNote = key => noteOf(key) ? `<div class="pb-note"><b>${esc(tr("bk_anchor"))}:</b> ${esc(noteOf(key))}</div>` : "";

    function pdfItem(p) {
      if (p.clip) {
        const c = p.clip;
        const zh = c.said && /[㐀-鿿]/.test(c.said);
        return `<section class="pb-item"><h2>${esc(c.mean || "…")}</h2>${c.said ? `<div class="pb-text">${esc(c.said)}</div>` : ""}${zh ? `<div class="rec-gloss">${Rec.gloss(c.said)}</div>` : ""}<div class="pb-meta">${esc(tr("r_title"))}${c.who ? " · " + esc(c.who) : ""} · ${esc(c.lang === "mix" ? tr("r_mixed") : NAMES[c.lang])}</div>${pdfNote(p.key)}</section>`;
      }
      const langs = FULL_LANGS.filter(l => l !== "en" && show[parentLang(l)]);
      return `<section class="pb-item"><h2>${esc(p.en)}</h2>${pdfNote(p.en)}${langs.map(l => pdfRow(p, l)).join("")}</section>`;
    }

    function exportPdf(ps, which) {
      let box = $("print-book");
      if (!box) {
        box = document.createElement("div");
        box.id = "print-book";
        document.body.appendChild(box);
      }
      const date = new Date().toLocaleDateString([], { dateStyle: "long" });
      box.innerHTML = `<header class="pb-head"><h1>${esc(tr("b_title"))}</h1><p>Polyling · ${esc(tr(which === "known" ? "b_tab_known" : "b_tab_saved"))} · ${ps.length} · ${esc(date)}</p></header>${ps.map(pdfItem).join("")}`;
      const title = document.title;
      document.title = `${tr("b_title")} ${new Date().toISOString().slice(0, 10)}`;
      const done = () => { document.title = title; box.innerHTML = ""; window.removeEventListener("afterprint", done); };
      window.addEventListener("afterprint", done);
      setTimeout(() => { try { window.print(); } catch (e) { done(); } }, 80);
    }

    function clipItem(p, d) {
      const c = p.clip;
      const li = el("li", "item clip-item");
      const play = el("button", "pbtn", `${speaker}<span>${esc(tr("p_play"))}</span>`);
      play.type = "button";
      play.addEventListener("click", async () => { if (!(await Rec.playClip(c))) play.disabled = true; });
      const tx = el("div", "clip-tx", `<div class="en">${esc(c.mean || "…")}</div>${c.said ? `<div class="clip-said">${esc(c.said)}</div>` : ""}${c.said && /[\u3400-\u9fff]/.test(c.said) ? `<div class="rec-gloss">${Rec.gloss(c.said)}</div>` : ""}<small>${icon("mic")} ${esc([c.who, c.lang === "mix" ? tr("r_mixed") : NAMES[c.lang]].filter(Boolean).join(" · "))}</small>`);
      const rm = el("button", "link", "×");
      rm.type = "button";
      rm.setAttribute("aria-label", tr("r_delete"));
      rm.addEventListener("click", () => { delete data[p.key]; save(); updateBtn(); paintDialog(d); });
      li.append(play, tx, rm);
      return li;
    }

    return { saveClip, isSaved, isKnown, count, toggleSave, toggleKnown, controls, open, updateBtn };
  })();
