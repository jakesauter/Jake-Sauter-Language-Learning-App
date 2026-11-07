import json
p = "page.html"
s = open(p, encoding="utf-8").read()
def rep(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:90])
    s = s.replace(a, b)

rep('''  function romText(lang, rom) {''', '''  const ZH_ROM = new Set(["yue", "tsn", "cmn"]);

  function romBoth(lang, rom, cls = "rd") {
    if (!rom) return "";
    if (ZH_ROM.has(lang)) {
      const std = romAs("std", () => romHtml(lang, rom));
      const easy = esc(romAs("easy", () => romText(lang, rom)));
      return `<span class="${cls} std">${std}</span><span class="${cls} easy">${easy}</span>`;
    }
    if (lang === "tr") return `<span class="${cls} easy">${esc(easyMe("tr", rom))}</span>`;
    return `<span class="${cls} std">${esc(rom)}</span><span class="${cls} easy">${esc(easyMe(lang, rom))}</span>`;
  }

  const romInline = (lang, rom) => romBoth(lang, rom, "ri");

  function romFullHtml(p, lang) {
    if (ZH_ROM.has(lang)) return romBoth(lang, (p[lang] || []).map(t => t.rom).filter(Boolean).join(" "));
    if (lang === "tr") return romBoth("tr", fullText(p, "tr"));
    const r = romLine(p, lang);
    return r ? romBoth(lang, r) : "";
  }

  function romText(lang, rom) {''')

rep('''    const rom = (lang === "yue" || lang === "tsn" || lang === "cmn") ? romText(lang, (p[lang] || []).map(t => t.rom).filter(Boolean).join(" ")) : romLine(p, lang);
    d.querySelector(".sm-rom").textContent = rom;''', '''    d.querySelector(".sm-rom").innerHTML = romFullHtml(p, lang);''')
rep('''<div class="rom">${toks.map(t => romHtml(lang, t.rom)).join(" ")}</div>''', '''<div class="rom">${romBoth(lang, toks.map(t => t.rom).filter(Boolean).join(" "))}</div>''')
rep('''(m, lang, r) => `<span class="nr">${romText(lang || "yue", r)}</span>`);''', '''(m, lang, r) => `<span class="nr">${romInline(lang || "yue", r)}</span>`);''')
rep('''${p.g_yue_rom ? `<span class="nr">${esc(romText("yue", p.g_yue_rom))}</span>` : ""}''', '''${p.g_yue_rom ? `<span class="nr">${romInline("yue", p.g_yue_rom)}</span>` : ""}''')
rep('''${p.g_cmn_rom ? `<span class="nr">${esc(romText("cmn", p.g_cmn_rom))}</span>` : ""}''', '''${p.g_cmn_rom ? `<span class="nr">${romInline("cmn", p.g_cmn_rom)}</span>` : ""}''')
rep('''    const rom = romText("yue", p.yue.map(t => t.rom).join(" "));
    btn.innerHTML = `<span><div class="en">${esc(p.en)}</div><div class="pv"><span class="hz-yue">${esc(yue)}</span><span class="rom">${esc(rom)}</span></div></span>${chevron}`;''',
'''    const rom = romInline("yue", p.yue.map(t => t.rom).join(" "));
    btn.innerHTML = `<span><div class="en">${esc(p.en)}</div><div class="pv"><span class="hz-yue">${esc(yue)}</span><span class="rom">${rom}</span></div></span>${chevron}`;''')
rep('''      const ft = el("span", "fr-text " + cls, esc(text) + (romLine(p, lang) ? `<span class="fr-rom" dir="ltr">${esc(easyMe(lang, romLine(p, lang)))}</span>` : ""));''',
'''      const fr = romFullHtml(p, lang);
      const ft = el("span", "fr-text " + cls, esc(text) + (fr ? `<span class="fr-rom" dir="ltr">${fr}</span>` : ""));''')

rep('''        <span class="label" data-i18n="notes_spelling">Notes spelling</span>
        <label for="spelling">
          <select id="spelling">
            <option value="easy" data-i18n="sp_easy">Easy English</option>
            <option value="std" data-i18n="sp_std">Standard (Jyutping, pinyin, Stephen Li)</option>
          </select>
        </label>''', '''        <span class="label" data-i18n="rom_label">Pronunciation lines</span>
        <label for="rom-std"><input type="checkbox" id="rom-std" checked> <span data-i18n="sp_std">Standard (Jyutping, pinyin, Stephen Li)</span></label>
        <label for="rom-easy"><input type="checkbox" id="rom-easy" checked> <span data-i18n="sp_easy">Easy English</span></label>''')

rep('''  const spelling = $("spelling");
  spelling.value = store.get("phrasebook-spelling") === "std" ? "std" : "easy";
  ROMAN.mode = spelling.value;
  spelling.addEventListener("change", () => {
    ROMAN.mode = spelling.value;
    store.set("phrasebook-spelling", spelling.value);
    renderList();
    const q = $("q").value.trim();
    if (result.children.length && q) showResult(q); else clearResult();
  });''', '''  const romStd = $("rom-std"), romEasy = $("rom-easy");
  romStd.checked = store.get("polylang-rom-std") !== "0";
  romEasy.checked = store.get("polylang-rom-easy") !== "0";
  const applyRom = () => {
    document.body.classList.toggle("no-std", !romStd.checked);
    document.body.classList.toggle("no-easy", !romEasy.checked);
    ROMAN.mode = romEasy.checked || !romStd.checked ? "easy" : "std";
  };
  applyRom();
  [romStd, romEasy].forEach(b => b.addEventListener("change", () => {
    store.set("polylang-rom-std", romStd.checked ? "1" : "0");
    store.set("polylang-rom-easy", romEasy.checked ? "1" : "0");
    applyRom();
    renderList();
    const q = $("q").value.trim();
    if (result.children.length && q) showResult(q); else clearResult();
  }));''')

rep('''  .now-tip { ''', '''  .rd { display: block; }
  .rd.easy { font-style: italic; }
  .fr-rom .rd.std, .pb-rom .rd.std { font-style: normal; }
  .ri.std .syl sup, .rd.std .syl sup { display: inline; }
  body:not(.no-std):not(.no-easy) .ri.easy::before { content: " · "; font-style: normal; }
  .ri.easy { font-style: italic; }
  body.no-std .rom.std, body.no-std .rd.std, body.no-std .ri.std, body.no-std .pr-rom .std { display: none !important; }
  body.no-easy .rom.easy, body.no-easy .rd.easy, body.no-easy .ri.easy, body.no-easy .pr-rom .easy { display: none !important; }
  .now-tip { ''')

T = {"en": "Pronunciation lines", "es": "Líneas de pronunciación", "fr": "Lignes de prononciation", "de": "Aussprachezeilen", "yue": "讀音行", "cmn": "读音行"}
anchors = {"en": '_name: "English", _lang: "en",', "es": '_name: "Español", _lang: "es",', "fr": '_name: "Français", _lang: "fr",', "de": '_name: "Deutsch", _lang: "de",', "yue": '_name: "廣東話", _lang: "zh-HK",', "cmn": '_name: "普通话", _lang: "zh-CN",'}
for k, v in T.items():
    rep(anchors[k], anchors[k] + f" rom_label: {json.dumps(v, ensure_ascii=False)},")
open(p, "w", encoding="utf-8").write(s)
print("romsel ok")
