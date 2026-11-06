  /* my phrasebook: sentences you save, and ones you already know */

  const Book = (() => {
    const KEY = "polygrok-book";
    let data = store.get(KEY) || {};
    let tab = "saved";

    const save = () => store.set(KEY, data);
    const rec = en => data[en] || (data[en] = {});
    const tidy = en => { if (data[en] && !data[en].s && !data[en].k) delete data[en]; };

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

    const find = en => PHRASES.find(p => p.en === en) || (data[en] && data[en].p);

    function list(which) {
      return Object.entries(data)
        .filter(([, r]) => which === "known" ? r.k : r.s)
        .sort((a, b) => (which === "known" ? b[1].k - a[1].k : b[1].s - a[1].s))
        .map(([en]) => find(en))
        .filter(Boolean);
    }

    function asText(ps) {
      const langs = LANES.filter(l => l !== "en" && show[l]);
      return ps.map(p => [p.en, ...langs.map(l => { const t = fullText(p, l); return t ? `${NAMES[l]}: ${t}` : ""; }).filter(Boolean)].join("\n")).join("\n\n");
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
      const paint = () => {
        const s = isSaved(p.en), k = isKnown(p.en);
        sv.innerHTML = `${icon("bookmark")}${esc(tr(s ? "bk_saved" : "b_save"))}`;
        sv.classList.toggle("on", s);
        kn.innerHTML = `${icon("check")}${esc(tr(k ? "b_known" : "b_know"))}`;
        kn.classList.toggle("on", k);
      };
      paint();
      sv.addEventListener("click", e => { e.stopPropagation(); toggleSave(p); paint(); Practice.updateCta(); });
      kn.addEventListener("click", e => { e.stopPropagation(); toggleKnown(p); paint(); Practice.updateCta(); });
      wrap.append(sv, kn);
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
        if (tab === "saved") {
          const pr = el("button", "pbtn", `${icon("brain")}${esc(tr("b_practice"))}`);
          pr.type = "button";
          pr.addEventListener("click", () => { d.close(); Practice.open(); });
          tools.appendChild(pr);
        }
        body.appendChild(tools);
        const ul = el("ul", "list");
        ps.forEach(p => ul.appendChild(rowItem(p)));
        body.appendChild(ul);
      }
      d.appendChild(body);
      d.querySelector("[data-x]").addEventListener("click", () => d.close());
    }

    return { isSaved, isKnown, count, toggleSave, toggleKnown, controls, open, updateBtn };
  })();
