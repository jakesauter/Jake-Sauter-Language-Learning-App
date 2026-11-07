p = "page.html"
s = open(p, encoding="utf-8").read()
def rep(a, b, c=1):
    global s
    assert s.count(a) == c, (s.count(a), a[:90])
    s = s.replace(a, b)

hooks = open("hooks.js", encoding="utf-8").read()
icons = open("icons.js", encoding="utf-8").read()
practice = open("practice.js", encoding="utf-8").read()
import json
roots = "  const JYUT_RAW = " + json.dumps(open("jyut.txt", encoding="utf-8").read(), ensure_ascii=False) + ";\n\n" + "  const JYUT_MEAN = " + json.dumps(open("zhmean.txt", encoding="utf-8").read(), ensure_ascii=False) + ";\n\n" + open("roots.js", encoding="utf-8").read()
book = open("book.js", encoding="utf-8").read()

rep('''  const LANES = ["tsn", "yue", "en", "cmn", "es", "fr", "de"];''', icons + "\n\n" + hooks + "\n\n" + roots + '''

  const LANES = ["tsn", "yue", "en", "cmn", "es", "fr", "de"];''')
rep("  /* search + translate */", practice + "\n\n" + book + "\n\n  /* search + translate */")

rep('''    <p class="sub" id="sub"></p>''', '''    <p class="sub" id="sub"></p>
    <div class="learn-bar">
      <button class="practice-cta" id="practice-btn" type="button"></button>
      <button class="book-cta" id="book-btn" type="button"></button>
      <button class="learn-link" id="learn-btn" type="button"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2.1h5c0-.9.4-1.6 1-2.1A6 6 0 0 0 12 3z" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg><span data-i18n="learn_btn">How to learn with Polylang</span></button>
    </div>
    <button class="now-tip" id="now-tip" type="button"></button>''')

rep('''      const b = el("button", "", `<span>${esc(catName(c))}</span><span class="n">${n}</span>`);''',
    '''      const b = el("button", "", `<span class="toc-name">${catIcon(c)}${esc(catName(c))}</span><span class="n">${n}</span>`);''')
rep('''      head.innerHTML = `<h3>${esc(catName(c))}<span class="n">${group.length}</span></h3>`;''',
    '''      head.innerHTML = `<h3>${catIcon(c)}${esc(catName(c))}<span class="n">${group.length}</span></h3>`;''')

rep('''    box.appendChild(full);
''', '''    box.appendChild(full);

    const lr = el("div", "learn-row");
    lr.appendChild(Book.controls(p));
    if (!p.guess) {
      const add = el("button", "pbtn add-practice", "");
      add.type = "button";
      const paint = () => { const on = Practice.inDeck(p.en); add.innerHTML = `${icon(on ? "star" : "cards")}${esc(tr(on ? "p_added" : "p_add"))}`; add.classList.toggle("on", on); };
      paint();
      add.addEventListener("click", e => { e.stopPropagation(); Practice.toggleDeck(p.en); paint(); Practice.updateCta(); });
      lr.appendChild(add);
    }
    const seenH = new Set();
    const hk = [];
    ["tsn", "yue", "cmn"].forEach(l => (p[l] || []).forEach(t => hooksFor(t.hz).slice(0, 1).forEach(h => { const k = t.hz + h[1]; if (!seenH.has(k)) { seenH.add(k); hk.push([l, t.hz, h]); } })));
    (p.gloss || []).forEach(g => { const k = g.toLowerCase().replace(/[^a-z ]/g, "").trim(); if (EU_HOOKS[k] && !seenH.has(k)) { seenH.add(k); hk.push(["en", g, ["bridge", EU_HOOKS[k]]]); } });
    if (hk.length) {
      const hb = el("div", "hooks");
      hb.appendChild(el("div", "label", esc(tr("hooks_h"))));
      hk.slice(0, 5).forEach(([l, w, h]) => hb.appendChild(el("p", "", `${hookIcon(h[0])}<span><b class="${l === "cmn" ? "hz-cmn" : l === "en" ? "" : "hz-yue"}">${zhRuby(esc(w))}</b> ${noteHtml(h[1])}</span>`)));
      lr.appendChild(hb);
    }
    if (lr.children.length) box.appendChild(lr);
''')

rep('''      b.addEventListener("click", () => lang === "tsn" ? sayTsn(t.rom) : sayVoice(t.hz, lang));
      plays.appendChild(b);
    }

    box.hidden = false;''', '''      b.addEventListener("click", () => lang === "tsn" ? sayTsn(t.rom) : sayVoice(t.hz, lang));
      plays.appendChild(b);
    }

    const hk = isEU(lang) ? means.map(m => EU_HOOKS[String(m).toLowerCase()]).filter(Boolean).map(x => ["bridge", x]) : hooksFor(t.hz);
    const hb = el("div", "wi-hooks");
    hk.forEach(h => hb.appendChild(el("p", "", `${hookIcon(h[0])}<span>${noteHtml(h[1])}</span>`)));
    const key = myHookKey(lang, t.hz);
    const ta = document.createElement("textarea");
    ta.className = "my-hook";
    ta.rows = 2;
    ta.placeholder = tr("myhook_ph");
    ta.value = store.get(key) || "";
    ta.addEventListener("input", () => store.set(key, ta.value));
    ta.addEventListener("click", e => e.stopPropagation());
    const lab = el("label", "my-hook-l", `<span>${esc(tr("myhook"))}</span>`);
    lab.appendChild(ta);
    hb.appendChild(lab);
    box.appendChild(hb);

    box.hidden = false;''')

rep('''  applyUI(store.get("phrasebook-ui") || "en");''', '''  applyUI(store.get("phrasebook-ui") || "en");
  Practice.updateCta();
  Book.updateBtn();
  const paintNow = () => { const [ic, k] = nowTip(); $("now-tip").innerHTML = `${icon(ic)}<span>${esc(tr(k))}</span>`; };
  paintNow();
  $("now-tip").addEventListener("click", () => openLearn("day"));
  $("book-btn").addEventListener("click", () => Book.open());
  window.__paintNow = paintNow;
  $("practice-btn").addEventListener("click", () => Practice.open());
  $("learn-btn").addEventListener("click", () => openLearn());''')
rep('''    if (result.children.length && q) showResult(q);
  });''', '''    if (result.children.length && q) showResult(q);
    Practice.updateCta();
    Book.updateBtn();
    if (window.__paintNow) window.__paintNow();
  });''')

rep('''  .wi-w { font-size: 1.35rem; font-weight: 600; }''', '''  .wi-w { font-size: 1.35rem; font-weight: 600; }

  .zg { display: inline-flex; flex-direction: column; align-items: center; vertical-align: middle; line-height: 1.1; margin: 0 2px; }
  .zg b { font-weight: inherit; font-size: 1.1em; }
  .zg small { font-size: 0.62em; font-weight: 400; color: var(--muted); white-space: nowrap; font-style: normal; letter-spacing: 0; }
  .zg .zm { color: var(--ink-2); }
  ruby { ruby-position: over; }
  rt { font-size: 0.58em; font-weight: 400; color: var(--muted); letter-spacing: 0; font-style: normal; }
  .hooks p, .wi-hooks p, .pr-hooks p, dialog.learn p, dialog.learn li { line-height: 1.95; }
  .ico { width: 1.15em; height: 1.15em; flex: none; vertical-align: -0.2em; }
  .toc-name { display: inline-flex; align-items: center; gap: 10px; }
  .toc-name .ico { width: 20px; height: 20px; color: var(--ink-2); }
  .group-title h3 { display: flex; align-items: center; gap: 10px; }
  .group-title h3 .ico { width: 24px; height: 24px; }

  .learn-bar { display: flex; flex-wrap: wrap; align-items: center; gap: var(--s-2) var(--s-3); margin-top: var(--s-1); }

  .practice-cta {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    padding: 8px 16px 8px 12px;
    border: 1.5px solid var(--ink);
    border-radius: 14px;
    background: var(--paper);
    color: var(--ink);
    font: inherit;
    text-align: left;
    cursor: pointer;
  }

  .practice-cta .ico { width: 26px; height: 26px; }
  .practice-cta span { display: grid; line-height: 1.2; }
  .practice-cta b { font-size: var(--t-md); }
  .practice-cta small { font-size: var(--t-xs); color: var(--muted); }
  .book-cta { display: inline-flex; align-items: center; gap: 8px; padding: 10px 14px; border: 1px solid var(--line); border-radius: 14px; background: var(--paper); color: var(--ink); font: inherit; font-weight: 600; cursor: pointer; min-height: 52px; }
  .book-cta .ico { width: 20px; height: 20px; }
  .book-cta .n { color: var(--muted); font-weight: 400; font-variant-numeric: tabular-nums; }
  .now-tip { display: flex; align-items: flex-start; gap: 8px; margin-top: var(--s-2); padding: 0; background: none; border: 0; font: inherit; font-size: var(--t-sm); color: var(--ink-2); text-align: left; cursor: pointer; }
  .now-tip .ico { width: 18px; height: 18px; margin-top: 2px; }
  .book-acts { display: flex; flex-wrap: wrap; gap: 6px; }
  .book-acts .pbtn.on, .add-practice.on { border-color: var(--ink); background: var(--ink); color: var(--paper); }
  .book-acts .ico { width: 15px; height: 15px; }
  dialog.book .list { margin: 0; }
  .lp-tabs { display: flex; flex-wrap: wrap; gap: 6px; margin: var(--s-3) 0; }
  .lp-tabs .chip { display: inline-flex; align-items: center; gap: 6px; }
  .lp-tabs .ico { width: 16px; height: 16px; }
  dialog.learn .lp-day { list-style: none; margin: 0; padding: 0; display: grid; gap: var(--s-4); }
  dialog.learn .lp-day li { display: grid; grid-template-columns: 30px 1fr; gap: 12px; }
  dialog.learn .lp-day .ico { width: 26px; height: 26px; margin-top: 2px; }
  dialog.learn .lp-day h3, dialog.learn .lp-day p { margin: 0 0 4px; }
  dialog.learn .lp-rule h3 { display: flex; align-items: center; gap: 10px; }
  dialog.learn .lp-rule h3 .ico { width: 24px; height: 24px; }
  dialog.learn .lp-rule ul { margin: 0; padding-left: 1.1em; display: grid; gap: 8px; line-height: 1.5; }
  dialog.learn .lp-rule li, dialog.learn .lp-day p { font-size: 0.95rem; }
  .learn-link { display: inline-flex; align-items: center; gap: 6px; background: none; border: 0; padding: 4px 0; font: inherit; font-size: var(--t-sm); color: var(--ink-2); text-decoration: underline; text-underline-offset: 3px; cursor: pointer; }
  .learn-link svg { width: 18px; height: 18px; }

  .learn-row { display: grid; gap: var(--s-3); }
  .add-practice { justify-self: start; }
  .add-practice.on { border-color: var(--ink); }
  .add-practice .ico { width: 15px; height: 15px; }
  .hooks, .pr-hooks, .wi-hooks { display: grid; gap: 6px; }
  .hooks p, .pr-hooks p, .wi-hooks p { margin: 0; display: flex; gap: 8px; align-items: flex-start; font-size: 0.95rem; line-height: 1.45; }
  .hooks .ico, .pr-hooks .ico, .wi-hooks .ico { width: 18px; height: 18px; margin-top: 2px; color: var(--ink-2); }
  .hooks b, .pr-hooks b { margin-right: 4px; }
  .my-hook-l { display: grid; gap: 4px; font-size: var(--t-xs); font-weight: 700; color: var(--muted); }
  .my-hook { font: inherit; font-size: 0.95rem; font-weight: 400; color: var(--ink); background: var(--wash); border: 1px solid var(--line); border-radius: 8px; padding: 8px 10px; resize: vertical; }

  dialog.practice {
    width: min(640px, calc(100vw - 16px));
    height: min(860px, calc(100dvh - 24px));
    max-height: calc(100dvh - 24px);
    border: 1px solid var(--ink);
    border-radius: 18px;
    padding: 0;
    color: var(--ink);
    background: var(--paper);
  }

  dialog.practice::backdrop { background: rgba(17, 17, 17, 0.5); }
  .pr-top { position: sticky; top: 0; z-index: 2; display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; background: var(--paper); border-bottom: 1px solid var(--line); }
  .pr-title { display: inline-flex; align-items: center; gap: 8px; font-weight: 700; font-size: var(--t-lg); }
  .pr-title .ico { width: 24px; height: 24px; }
  .pr-body { display: grid; gap: var(--s-4); padding: var(--s-4); align-content: start; }
  .pr-lead { margin: 0; color: var(--ink-2); }
  .pr-langs { display: flex; flex-wrap: wrap; gap: 6px; }
  .pr-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; }
  .pr-stat { display: grid; justify-items: center; padding: 10px 4px; border: 1px solid var(--line); border-radius: 12px; text-align: center; }
  .pr-stat b { font-size: 1.5rem; line-height: 1.1; }
  .pr-stat span { font-size: 0.7rem; color: var(--muted); line-height: 1.2; }
  .pr-acts { display: grid; gap: 8px; }
  .pr-big { display: flex; align-items: center; gap: 12px; padding: 12px 14px; text-align: left; min-height: 64px; }
  .pr-big .ico { width: 28px; height: 28px; }
  .pr-big span { display: grid; gap: 2px; }
  .pr-big small { font-weight: 400; font-size: var(--t-xs); opacity: 0.8; }
  .pr-opt { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 8px; font-size: var(--t-sm); }
  .pr-opt select { font: inherit; padding: 4px 8px; border: 1px solid var(--line); border-radius: 8px; background: var(--paper); color: var(--ink); }
  .pr-head { display: flex; align-items: center; gap: 10px; font-size: var(--t-sm); color: var(--muted); }
  .pr-cat { display: inline-flex; align-items: center; gap: 6px; }
  .pr-new { margin-left: auto; font-size: var(--t-xs); font-weight: 700; border: 1px solid var(--ink); color: var(--ink); border-radius: 999px; padding: 1px 8px; }
  .pr-prompt { font-size: clamp(1.4rem, 6vw, 2rem); font-weight: 700; line-height: 1.25; }
  .pr-hint { margin: 0; color: var(--muted); font-size: var(--t-sm); }
  .pr-show { justify-self: start; display: inline-flex; align-items: center; gap: 6px; }
  .pr-show svg { width: 16px; height: 16px; }
  .pr-answer { display: grid; gap: 10px; padding: var(--s-3) var(--s-4); background: var(--wash); border-radius: 14px; }
  .pr-target { font-size: clamp(1.5rem, 7vw, 2.2rem); line-height: 1.3; font-weight: 600; overflow-wrap: anywhere; }
  .pr-rom { display: grid; gap: 2px; color: var(--ink-2); }
  .pr-rom .easy { font-style: italic; color: var(--muted); }
  .pr-rom .std .syl sup { display: inline; }
  .pr-tools { display: flex; flex-wrap: wrap; gap: 6px; }
  .pr-tools .ico { width: 14px; height: 14px; }
  .pr-rate { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; }
  .pr-rate .btn { display: grid; justify-items: center; padding: 8px 4px; min-height: 56px; }
  .pr-rate small { font-weight: 400; font-size: 0.7rem; opacity: 0.8; }
  .pr-opts { display: grid; gap: 8px; }
  .pr-opt.btn { text-align: left; font-weight: 600; padding: 12px 14px; min-height: 48px; }
  .btn.right { background: var(--ink); color: var(--paper); border-color: var(--ink); }
  .btn.wrong { text-decoration: line-through; opacity: 0.6; }
  .pr-verdict { margin: 0; font-weight: 700; display: flex; align-items: baseline; gap: 8px; flex-wrap: wrap; }
  .pr-char { font-size: 1.8rem; }
  .pr-verdict .syl sup { display: inline; }
  .pr-tones { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
  .pr-tone { display: grid; justify-items: center; gap: 2px; padding: 10px 4px; min-height: 76px; }
  .pr-tone svg { width: 40px; height: 40px; overflow: visible; }
  .pr-tone.right svg .pitch { stroke: var(--paper); }
  .pr-tone.right svg .head { fill: var(--paper); }
  .pr-done { display: grid; justify-items: center; gap: 6px; padding: var(--s-5) 0; text-align: center; }
  .pr-done .ico { width: 40px; height: 40px; }
  .pr-done b { font-size: 1.5rem; }

  dialog.learn .lp-item { display: grid; grid-template-columns: 30px 1fr; gap: 12px; align-items: start; }
  dialog.learn .lp-item .ico { width: 28px; height: 28px; margin-top: 2px; }
  dialog.learn .lp-item h3 { margin: 0 0 4px; }
  dialog.learn .lp-item p { margin: 0 0 6px; }
  dialog.learn .lp-how { color: var(--ink-2); }
  dialog.learn .lp-routine, dialog.learn .lp-src { margin: 0; padding-left: 1.2em; display: grid; gap: 6px; font-size: 0.95rem; }
  dialog.learn a { color: var(--ink); }''')
open(p, "w", encoding="utf-8").write(s)
print("ok")
