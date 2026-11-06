import json
p = "page.html"
s = open(p, encoding="utf-8").read()
def rep(a, b, c=1):
    global s
    assert s.count(a) == c, (s.count(a), a[:90])
    s = s.replace(a, b)

rep('''  function euText(p, lang) {
    const words = (p[lang] || []).map(t => t.hz).join(" ").replace(/ ([,.!?])/g, "$1");
    const end = (String(p.en || "").trim().match(/[?!.]$/) || ["."])[0];
    return words + end;
  }''', '''  function euText(p, lang) {
    const words = (p[lang] || []).map(t => t.hz).join(" ").replace(/ ([,.!?])/g, "$1");
    if (/[?!.]$/.test(words)) return words;
    const end = (String(p.en || "").trim().match(/[?!.]$/) || ["."])[0];
    return words + end;
  }

  const NATIVE = { tsn: "台山話", yue: "廣東話", en: "English", cmn: "普通话", es: "Español", fr: "Français", de: "Deutsch" };

  function fullText(p, lang) {
    if (lang === "en") return p.en;
    if (isEU(lang)) return euText(p, lang);
    const hz = (p[lang] || []).map(t => t.hz).join("").replace(/[（(][^）)]*[）)]/g, "");
    if (!hz) return "";
    const q = /\\?\\s*$/.test(p.en || "");
    return /[。？！]$/.test(hz) ? hz : hz + (q ? "？" : /!\\s*$/.test(p.en || "") ? "！" : "。");
  }

  function sayFull(p, lang) {
    if (lang === "tsn") return sayTsn((p.tsn || []).map(t => t.rom).join(" "));
    sayVoice(lang === "en" ? p.en : isEU(lang) ? euText(p, lang) : (p[lang] || []).map(t => t.hz).join(""), lang);
  }

  function showBig(p, lang) {
    let d = $("showme");
    if (!d) {
      d = document.createElement("dialog");
      d.id = "showme";
      d.className = "showme";
      d.innerHTML = `<div class="sm-in"><div class="sm-lang"></div><div class="sm-text"></div><div class="sm-rom"></div><div class="sm-btns"><button class="btn sm-play" type="button"></button><button class="btn quiet sm-close" type="button"></button></div></div>`;
      document.body.appendChild(d);
      d.querySelector(".sm-close").addEventListener("click", () => d.close());
      d.addEventListener("click", e => { if (e.target === d) d.close(); });
    }
    d.querySelector(".sm-lang").textContent = NATIVE[lang];
    const tx = d.querySelector(".sm-text");
    tx.textContent = fullText(p, lang);
    tx.className = "sm-text " + (lang === "cmn" ? "hz-cmn" : (lang === "yue" || lang === "tsn") ? "hz-yue" : "");
    const rom = (lang === "yue" || lang === "tsn" || lang === "cmn") ? romText(lang, (p[lang] || []).map(t => t.rom).filter(Boolean).join(" ")) : "";
    d.querySelector(".sm-rom").textContent = rom;
    d.querySelector(".sm-play").innerHTML = `${speaker}${tr("listen")}`;
    d.querySelector(".sm-play").onclick = () => sayFull(p, lang);
    d.querySelector(".sm-close").textContent = tr("g_close");
    d.showModal();
  }''')

rep('''    wrap.appendChild(el("p", "hint", tr("hint")));
    box.appendChild(wrap);
''', '''    wrap.appendChild(el("p", "hint", tr("hint")));
    box.appendChild(wrap);

    const full = el("div", "full");
    full.appendChild(el("div", "label", tr("full_title")));
    ["tsn", "yue", "en", "cmn", "es", "fr", "de"].forEach(lang => {
      const text = fullText(p, lang);
      if (!text) return;
      const row = el("div", "full-row");
      row.dataset.lang = lang;
      if (lang !== "en") row.hidden = !show[lang];
      const cls = lang === "cmn" ? "hz-cmn" : (lang === "yue" || lang === "tsn") ? "hz-yue" : "";
      row.appendChild(el("span", "fr-lang", esc(NATIVE[lang])));
      row.appendChild(el("span", "fr-text " + cls, esc(text)));
      const btns = el("span", "fr-btns");
      const pl = el("button", "lp", speaker);
      pl.type = "button";
      pl.setAttribute("aria-label", tr("listen_in", { lang: NAMES[lang] }));
      pl.addEventListener("click", e => { e.stopPropagation(); sayFull(p, lang); });
      const big = el("button", "lp alt", `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`);
      big.type = "button";
      big.setAttribute("aria-label", tr("show_big"));
      big.addEventListener("click", e => { e.stopPropagation(); showBig(p, lang); });
      btns.appendChild(pl);
      btns.appendChild(big);
      row.appendChild(btns);
      full.appendChild(row);
    });
    box.appendChild(full);
''')

rep('''    document.querySelectorAll(".say-line, .hear-row").forEach(r => { r.hidden = !show[r.dataset.lang]; });''',
    '''    document.querySelectorAll(".say-line, .hear-row, .full-row").forEach(r => { if (r.dataset.lang !== "en") r.hidden = !show[r.dataset.lang]; });''')

rep('''      es: [/^es[-_]MX/i, /^es[-_](US|419)/i, /^es/i],''', '''      en: [/^en[-_]US/i, /^en/i],
      es: [/^es[-_]MX/i, /^es[-_](US|419)/i, /^es/i],''')

rep('''  .wi-w { font-size: 1.35rem; font-weight: 600; }''', '''  .wi-w { font-size: 1.35rem; font-weight: 600; }

  .full { display: grid; gap: 2px; }
  .full .label { margin-bottom: var(--s-1); }
  .full-row { display: grid; grid-template-columns: 5.2em minmax(0, 1fr) auto; gap: var(--s-2); align-items: center; padding: 8px 0; border-top: 1px solid var(--line); }
  .full-row:first-of-type { border-top: 0; }
  .fr-lang { font-size: var(--t-xs); font-weight: 700; color: var(--muted); }
  .fr-text { font-size: 1.15rem; line-height: 1.4; overflow-wrap: anywhere; }
  .fr-text.hz-yue, .fr-text.hz-cmn { font-size: 1.35rem; }
  .fr-btns { display: flex; gap: 6px; }
  .fr-btns .lp { width: 34px; height: 34px; }
  .fr-btns .lp.alt { height: 34px; border-radius: 50%; }

  dialog.showme {
    width: min(720px, calc(100vw - 20px));
    max-height: calc(100vh - 32px);
    border: 1px solid var(--ink);
    border-radius: 18px;
    padding: 0;
    color: var(--ink);
    background: var(--paper);
  }

  dialog.showme::backdrop { background: rgba(17, 17, 17, 0.55); }
  .sm-in { display: grid; gap: var(--s-4); padding: var(--s-5) var(--s-4); }
  .sm-lang { font-size: var(--t-sm); font-weight: 700; color: var(--muted); letter-spacing: 0.04em; }
  .sm-text { font-size: clamp(2rem, 9vw, 3.6rem); line-height: 1.25; font-weight: 600; overflow-wrap: anywhere; }
  .sm-rom { font-size: var(--t-md); color: var(--muted); }
  .sm-rom:empty { display: none; }
  .sm-btns { display: flex; gap: var(--s-2); }
  .sm-play { display: inline-flex; align-items: center; gap: 6px; }
  .sm-play svg { width: 16px; height: 16px; }''')

T = {"en": ("Full sentence", "Show it big"), "es": ("Frase completa", "Mostrar en grande"), "fr": ("Phrase complète", "Afficher en grand"), "de": ("Ganzer Satz", "Groß anzeigen"), "yue": ("成句", "放大顯示"), "cmn": ("整句", "放大显示")}
anchors = {"en": '_name: "English", _lang: "en",', "es": '_name: "Español", _lang: "es",', "fr": '_name: "Français", _lang: "fr",', "de": '_name: "Deutsch", _lang: "de",', "yue": '_name: "廣東話", _lang: "zh-HK",', "cmn": '_name: "普通话", _lang: "zh-CN",'}
for k, (a, b) in T.items():
    rep(anchors[k], anchors[k] + f" full_title: {json.dumps(a, ensure_ascii=False)}, show_big: {json.dumps(b, ensure_ascii=False)},")
open(p, "w", encoding="utf-8").write(s)
print("ok")
