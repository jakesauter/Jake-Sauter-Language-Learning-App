import json
p = "page.html"
s = open(p, encoding="utf-8").read()
def rep(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:90])
    s = s.replace(a, b)

rep("  /* search + translate */", open("wikt.js", encoding="utf-8").read() + "\n\n  /* search + translate */")

rep('''    box.appendChild(hb);

    box.hidden = false;
  }''', '''    box.appendChild(hb);
    box.appendChild(Lookup.panel(lang, t.hz));

    box.hidden = false;
  }''')

rep('''  .gt-set { ''', '''  .lookup { display: grid; gap: var(--s-2); border-top: 1px solid var(--line, var(--muted)); padding-top: var(--s-2); }
  .lookup .plays { margin-top: 0; }
  .lk-out { display: grid; gap: var(--s-2); }
  .lk-out .label { margin: 0; }
  .lk-b p { margin: 2px 0 0; line-height: 1.9; }
  .lk-ex { display: grid; grid-template-columns: 1fr auto; column-gap: var(--s-2); align-items: center; }
  .lk-ex .lp { grid-column: 2; grid-row: 1 / span 3; }
  .lk-ex-t { font-size: 1.05rem; line-height: 1.9; }
  .lk-ex-en { color: var(--muted); font-size: var(--t-sm); }
  .lk-ex-by, .lk-src { font-size: var(--t-xs); color: var(--muted); }
  .lk-src { margin: 0; }
  .lookup a { color: inherit; }
  .gt-set { ''')

K = ["wk_btn", "wk_h", "wk_none", "wk_fail", "wk_more", "wk_lic", "tb_btn", "tb_h", "tb_none", "tb_fail", "tb_more", "tb_lic"]
T = {
 "en": ["Word origin", "Origin · Wiktionary", "Wiktionary has no origin notes for this word yet.", "Couldn't reach Wiktionary. Check your connection.", "Open on Wiktionary", "Text: Wiktionary, CC BY-SA 4.0", "Real examples", "Examples · Tatoeba", "Tatoeba has no examples with this word yet.", "Couldn't reach Tatoeba. Check your connection.", "More on Tatoeba", "Sentences: Tatoeba, CC BY 2.0 FR"],
 "es": ["Origen", "Origen · Wiktionary", "Wiktionary aún no tiene el origen de esta palabra.", "No se pudo conectar con Wiktionary. Revisa tu conexión.", "Abrir en Wiktionary", "Texto: Wiktionary, CC BY-SA 4.0", "Ejemplos reales", "Ejemplos · Tatoeba", "Tatoeba aún no tiene ejemplos con esta palabra.", "No se pudo conectar con Tatoeba. Revisa tu conexión.", "Más en Tatoeba", "Frases: Tatoeba, CC BY 2.0 FR"],
 "fr": ["Origine", "Origine · Wiktionary", "Wiktionary n'a pas encore l'origine de ce mot.", "Impossible de joindre Wiktionary. Vérifie ta connexion.", "Ouvrir sur Wiktionary", "Texte : Wiktionary, CC BY-SA 4.0", "Vrais exemples", "Exemples · Tatoeba", "Tatoeba n'a pas encore d'exemples avec ce mot.", "Impossible de joindre Tatoeba. Vérifie ta connexion.", "Plus sur Tatoeba", "Phrases : Tatoeba, CC BY 2.0 FR"],
 "de": ["Herkunft", "Herkunft · Wiktionary", "Wiktionary hat noch keine Herkunft für dieses Wort.", "Wiktionary nicht erreichbar. Prüfe deine Verbindung.", "Auf Wiktionary öffnen", "Text: Wiktionary, CC BY-SA 4.0", "Echte Beispiele", "Beispiele · Tatoeba", "Tatoeba hat noch keine Beispiele mit diesem Wort.", "Tatoeba nicht erreichbar. Prüfe deine Verbindung.", "Mehr auf Tatoeba", "Sätze: Tatoeba, CC BY 2.0 FR"],
 "yue": ["字源", "字源 · Wiktionary", "Wiktionary 暫時未有呢個字嘅來源。", "連唔到 Wiktionary，睇下網絡。", "喺 Wiktionary 打開", "內容：Wiktionary，CC BY-SA 4.0", "真實例句", "例句 · Tatoeba", "Tatoeba 暫時未有用呢個字嘅例句。", "連唔到 Tatoeba，睇下網絡。", "喺 Tatoeba 睇多啲", "例句：Tatoeba，CC BY 2.0 FR"],
 "cmn": ["字源", "字源 · Wiktionary", "Wiktionary 暂时没有这个词的来源。", "连不上 Wiktionary，请检查网络。", "在 Wiktionary 打开", "内容：Wiktionary，CC BY-SA 4.0", "真实例句", "例句 · Tatoeba", "Tatoeba 暂时没有用这个词的例句。", "连不上 Tatoeba，请检查网络。", "在 Tatoeba 查看更多", "例句：Tatoeba，CC BY 2.0 FR"],
}
anchors = {"en": '_name: "English", _lang: "en",', "es": '_name: "Español", _lang: "es",', "fr": '_name: "Français", _lang: "fr",', "de": '_name: "Deutsch", _lang: "de",', "yue": '_name: "廣東話", _lang: "zh-HK",', "cmn": '_name: "普通话", _lang: "zh-CN",'}
for k, vals in T.items():
    add = " ".join(f"{key}: {json.dumps(v, ensure_ascii=False)}," for key, v in zip(K, vals))
    rep(anchors[k], anchors[k] + " " + add)
open(p, "w", encoding="utf-8").write(s)
print("lookup ok")
