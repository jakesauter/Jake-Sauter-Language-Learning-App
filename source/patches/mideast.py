import json
p = "page.html"
s = open(p, encoding="utf-8").read()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (s.count(a), a[:90])
    s = s.replace(a, b)

rep('''  const LANES = ["tsn", "yue", "en", "cmn", "es", "fr", "de"];
  const NAMES = { tsn: "Taishanese", yue: "Cantonese", en: "English", cmn: "Mandarin", es: "Spanish", fr: "French", de: "German" };
  const EU = new Set(["es", "fr", "de"]);''', '''  const VARIANT_OF = { fa_w: "fa", arz: "apc", ar: "apc" };
  const LANES = ["tsn", "yue", "en", "cmn", "es", "pt", "fr", "de", "fa", "apc", "he", "tr"];
  const LEARN_LANGS = LANES.filter(l => l !== "en");
  const FULL_LANGS = LANES.flatMap(l => [l, ...Object.keys(VARIANT_OF).filter(v => VARIANT_OF[v] === l)]);
  const NAMES = { tsn: "Taishanese", yue: "Cantonese", en: "English", cmn: "Mandarin", es: "Spanish", pt: "Portuguese", fr: "French", de: "German", fa: "Persian", apc: "Arabic", he: "Hebrew", tr: "Turkish", fa_w: "Persian (written)", arz: "Egyptian Arabic", ar: "Arabic (MSA)" };
  const EU = new Set(["es", "pt", "fr", "de", "fa", "apc", "he", "tr"]);
  const ME = new Set(["fa", "apc", "he", "tr"]);
  const RTL = new Set(["fa", "apc", "he", "fa_w", "arz", "ar"]);
  const VARIANT = VARIANT_OF;
  const parentLang = l => VARIANT[l] || l;
  const HTML_LANG = { fa: "fa", fa_w: "fa", apc: "ar", arz: "ar", ar: "ar", he: "he", tr: "tr" };

  function easyMe(lang, rom) {
    let r = String(rom || "");
    if (lang === "tr") {
      return r.toLowerCase().replace(/ç/g, "ch").replace(/ş/g, "sh").replace(/c/g, "j").replace(/ğ/g, "").replace(/ı/g, "uh").replace(/â/g, "a").replace(/î/g, "ee").replace(/û/g, "oo");
    }
    return r.replace(/ā/g, "aa").replace(/ī/g, "ee").replace(/ū/g, "oo").replace(/ē/g, "eh").replace(/ō/g, "oh")
      .replace(/ḥ/g, "h").replace(/ṣ/g, "s").replace(/ḍ/g, "d").replace(/ṭ/g, "t").replace(/ẓ/g, "z").replace(/ʿ/g, "'").replace(/ʾ/g, "'").replace(/ʔ/g, "'");
  }

  function meRom(lang, rom, hz) {
    if (lang === "tr") return `<span class="rom easy">${esc(easyMe("tr", hz))}</span>`;
    if (!rom) return "";
    return `<span class="rom std">${esc(rom)}</span><span class="rom easy">${esc(easyMe(lang, rom))}</span>`;
  }

  function romLine(p, lang) {
    if (VARIANT[lang]) return (p[lang] && p[lang].r) || "";
    if (lang === "tr") return easyMe("tr", fullText(p, "tr"));
    if (ME.has(lang)) return (p[lang] || []).map(t => t.rom).filter(Boolean).join(" ");
    return "";
  }''')

rep('''    const end = (String(p.en || "").trim().match(/[?!.]$/) || ["."])[0];
    return words + end;''', '''    let end = (String(p.en || "").trim().match(/[?!.]$/) || ["."])[0];
    if (lang === "fa" || lang === "apc") end = end.replace("?", "؟");
    return words + end;''')
rep('''  const NATIVE = { tsn: "台山話", yue: "廣東話", en: "English", cmn: "普通话", es: "Español", fr: "Français", de: "Deutsch" };''',
    '''  const NATIVE = { tsn: "台山話", yue: "廣東話", en: "English", cmn: "普通话", es: "Español", pt: "Português (Brasil)", fr: "Français", de: "Deutsch", fa: "فارسی · spoken", fa_w: "فارسی · written", apc: "شامي · Levantine", arz: "مصري · Egyptian", ar: "فصحى · MSA", he: "עברית", tr: "Türkçe" };''')
rep('''    if (lang === "en") return p.en;
    if (isEU(lang)) return euText(p, lang);''', '''    if (lang === "en") return p.en;
    if (VARIANT[lang]) return (p[lang] && p[lang].t) || "";
    if (isEU(lang)) return euText(p, lang);''')
rep('''    if (lang === "tsn") return sayTsn((p.tsn || []).map(t => t.rom).join(" "));
    sayVoice(''', '''    if (lang === "tsn") return sayTsn((p.tsn || []).map(t => t.rom).join(" "));
    if (VARIANT[lang]) return sayVoice(fullText(p, lang), lang);
    sayVoice(''')
rep('''    tx.textContent = fullText(p, lang);
    tx.className = "sm-text " + (lang === "cmn" ? "hz-cmn" : (lang === "yue" || lang === "tsn") ? "hz-yue" : "");
    const rom = (lang === "yue" || lang === "tsn" || lang === "cmn") ? romText(lang, (p[lang] || []).map(t => t.rom).filter(Boolean).join(" ")) : "";''',
    '''    tx.textContent = fullText(p, lang);
    tx.dir = RTL.has(lang) ? "rtl" : "auto";
    tx.lang = HTML_LANG[lang] || "";
    tx.className = "sm-text " + (lang === "cmn" ? "hz-cmn" : (lang === "yue" || lang === "tsn") ? "hz-yue" : "");
    const rom = (lang === "yue" || lang === "tsn" || lang === "cmn") ? romText(lang, (p[lang] || []).map(t => t.rom).filter(Boolean).join(" ")) : romLine(p, lang);''')

rep('''      es: [/^es[-_]MX/i, /^es[-_](US|419)/i, /^es/i],
      fr: [/^fr[-_]FR/i, /^fr/i],
      de: [/^de[-_]DE/i, /^de/i],
    };''', '''      es: [/^es[-_]MX/i, /^es[-_](US|419)/i, /^es/i],
      fr: [/^fr[-_]FR/i, /^fr/i],
      de: [/^de[-_]DE/i, /^de/i],
      pt: [/^pt[-_]BR/i, /^pt/i],
      fa: [/^fa/i, /persian|farsi/i],
      fa_w: [/^fa/i, /persian|farsi/i],
      apc: [/^ar[-_](JO|LB|SY|PS)/i, /^ar/i],
      arz: [/^ar[-_]EG/i, /^ar/i],
      ar: [/^ar[-_]SA/i, /^ar[-_]001/i, /^ar/i],
      he: [/^he/i, /^iw/i],
      tr: [/^tr/i],
    };''')
rep('''        u.lang = { yue: "zh-HK", cmn: "zh-CN", es: "es-MX", fr: "fr-FR", de: "de-DE" }[lang] || "en-US";''',
    '''        u.lang = { yue: "zh-HK", cmn: "zh-CN", es: "es-MX", fr: "fr-FR", de: "de-DE", pt: "pt-BR", fa: "fa-IR", fa_w: "fa-IR", apc: "ar-JO", arz: "ar-EG", ar: "ar-SA", he: "he-IL", tr: "tr-TR" }[lang] || "en-US";''')

rep('''    box.innerHTML = isEU(lang)
      ? `<div class="wi-head"><span class="wi-w">${esc(t.hz)}</span><span class="wi-kind">${esc(kind)}</span></div>${parts.join("")}<div class="plays"></div>`''',
    '''    box.innerHTML = isEU(lang)
      ? `<div class="wi-head"><span class="wi-w"${RTL.has(lang) ? ` dir="rtl" lang="${HTML_LANG[lang]}"` : ""}>${esc(t.hz)}</span>${ME.has(lang) ? `<span class="wi-rom">${meRom(lang, t.rom, t.hz)}</span>` : ""}<span class="wi-kind">${esc(kind)}</span></div>${parts.join("")}<div class="plays"></div>`''')

rep('''    const rows = {}, toks = { tsn: [], yue: [], en: [], cmn: [], es: [], fr: [], de: [] };''',
    '''    const rows = {}, toks = Object.fromEntries(LANES.map(l => [l, []]));''')
rep('''        (p[lang] || []).forEach(t => {
          const refs = t.refs || [];
          const sure = t.sure !== false;
          const inner = isEU(lang)''', '''        (RTL.has(lang) ? (p[lang] || []).slice().reverse() : (p[lang] || [])).forEach(t => {
          const refs = t.refs || [];
          const sure = t.sure !== false;
          const inner = ME.has(lang)
            ? `<span class="w"${RTL.has(lang) ? ` dir="rtl" lang="${HTML_LANG[lang]}"` : ""}>${esc(t.hz)}</span>${meRom(lang, t.rom, t.hz)}`
            : isEU(lang)''')
rep('''          const b = el("button", "tok" + (refs.length ? "" : " grammar") + (isEU(lang) ? " eu" : ""),''',
    '''          const b = el("button", "tok" + (refs.length ? "" : " grammar") + (isEU(lang) ? " eu" : "") + (ME.has(lang) ? " me" : ""),''')

rep('''    ["tsn", "yue", "en", "cmn", "es", "fr", "de"].forEach(lang => {
      const text = fullText(p, lang);
      if (!text) return;
      const row = el("div", "full-row");
      row.dataset.lang = lang;
      if (lang !== "en") row.hidden = !show[lang];
      const cls = lang === "cmn" ? "hz-cmn" : (lang === "yue" || lang === "tsn") ? "hz-yue" : "";
      row.appendChild(el("span", "fr-lang", esc(NATIVE[lang])));
      row.appendChild(el("span", "fr-text " + cls, esc(text)));''', '''    FULL_LANGS.forEach(lang => {
      const text = fullText(p, lang);
      if (!text) return;
      const row = el("div", "full-row");
      row.dataset.lang = parentLang(lang);
      if (lang !== "en") row.hidden = !show[parentLang(lang)];
      const cls = lang === "cmn" ? "hz-cmn" : (lang === "yue" || lang === "tsn") ? "hz-yue" : "";
      row.appendChild(el("span", "fr-lang", esc(NATIVE[lang])));
      const ft = el("span", "fr-text " + cls, esc(text) + (romLine(p, lang) ? `<span class="fr-rom" dir="ltr">${esc(easyMe(lang, romLine(p, lang)))}</span>` : ""));
      if (RTL.has(lang)) { ft.dir = "rtl"; ft.lang = HTML_LANG[lang]; }
      row.appendChild(ft);''')

rep('''        <label for="col-de"><input type="checkbox" id="col-de" checked> <span data-i18n="de">German</span></label>''',
    '''        <label for="col-de"><input type="checkbox" id="col-de" checked> <span data-i18n="de">German</span></label>
        <label for="col-pt"><input type="checkbox" id="col-pt"> <span data-i18n="pt">Portuguese</span></label>
        <label for="col-fa"><input type="checkbox" id="col-fa"> <span data-i18n="fa">Persian</span></label>
        <label for="col-apc"><input type="checkbox" id="col-apc"> <span data-i18n="apc">Arabic</span></label>
        <label for="col-he"><input type="checkbox" id="col-he"> <span data-i18n="he">Hebrew</span></label>
        <label for="col-tr"><input type="checkbox" id="col-tr"> <span data-i18n="tr">Turkish</span></label>''')
rep('''  ["tsn", "yue", "cmn", "es", "fr", "de"].forEach(l => {
    const box = $("col-" + l);''', '''  LEARN_LANGS.forEach(l => {
    const box = $("col-" + l);''')

rep('''  .tok .w { ''', '''  .tok.me { display: grid; justify-items: center; gap: 1px; }
  .tok.me .w { font-size: 1.15rem; }
  .tok.me .w[lang="fa"], .tok.me .w[lang="ar"], .fr-text[lang="fa"], .fr-text[lang="ar"] { font-family: "Geeza Pro", "Noto Naskh Arabic", "Segoe UI", Tahoma, sans-serif; }
  .fr-rom { display: block; font-size: 0.85rem; color: var(--muted); font-style: italic; margin-top: 2px; text-align: left; }
  .tok .w { ''')

U = {"en": ["Persian","Arabic","Hebrew","Turkish","Portuguese"], "es": ["Persa","Árabe","Hebreo","Turco","Portugués"], "fr": ["Persan","Arabe","Hébreu","Turc","Portugais"], "de": ["Persisch","Arabisch","Hebräisch","Türkisch","Portugiesisch"], "yue": ["波斯文","阿拉伯文","希伯來文","土耳其文","葡萄牙文"], "cmn": ["波斯语","阿拉伯语","希伯来语","土耳其语","葡萄牙语"]}
anchors = {"en": '_name: "English", _lang: "en",', "es": '_name: "Español", _lang: "es",', "fr": '_name: "Français", _lang: "fr",', "de": '_name: "Deutsch", _lang: "de",', "yue": '_name: "廣東話", _lang: "zh-HK",', "cmn": '_name: "普通话", _lang: "zh-CN",'}
for k, v in U.items():
    add = " ".join(f"{key}: {json.dumps(x, ensure_ascii=False)}," for key, x in zip(["fa", "apc", "he", "tr", "pt"], v))
    rep(anchors[k], anchors[k] + " " + add)

rep('''    const SR_LANG = { tsn: "zh-HK", yue: "zh-HK", cmn: "zh-CN", es: "es-MX", fr: "fr-FR", de: "de-DE", en: "en-US", mix: "zh-HK" };
    const HOME_LANG = { tsn: "yue", yue: "yue", cmn: "zh", es: "es", fr: "fr", de: "de", en: "en", mix: "" };
    const REC_LANGS = ["tsn", "yue", "cmn", "es", "fr", "de", "en", "mix"];''', '''    const SR_LANG = { tsn: "zh-HK", yue: "zh-HK", cmn: "zh-CN", es: "es-MX", pt: "pt-BR", fr: "fr-FR", de: "de-DE", fa: "fa-IR", apc: "ar-JO", he: "he-IL", tr: "tr-TR", en: "en-US", mix: "zh-HK" };
    const HOME_LANG = { tsn: "yue", yue: "yue", cmn: "zh", es: "es", pt: "pt", fr: "fr", de: "de", fa: "fa", apc: "ar", he: "he", tr: "tr", en: "en", mix: "" };
    const REC_LANGS = [...LEARN_LANGS, "en", "mix"];''')

rep('''    const LANGS_P = ["yue", "tsn", "cmn", "es", "fr", "de"];''', '''    const LANGS_P = LEARN_LANGS;''')
rep('''      a.appendChild(el("div", "pr-target " + cls, esc(fullText(p, lang))));''', '''      const tgt = el("div", "pr-target " + cls, esc(fullText(p, lang)));
      if (RTL.has(lang)) { tgt.dir = "rtl"; tgt.lang = HTML_LANG[lang]; }
      a.appendChild(tgt);
      if (ME.has(lang) && romLine(p, lang)) a.appendChild(el("div", "pr-rom", `<span class="std">${esc(lang === "tr" ? "" : romLine(p, lang))}</span><span class="easy">${esc(easyMe(lang, romLine(p, lang)))}</span>`));''')

open(p, "w", encoding="utf-8").write(s)
print("mideast ok")
