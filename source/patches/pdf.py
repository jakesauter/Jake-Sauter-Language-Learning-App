import json
p = "page.html"
s = open(p, encoding="utf-8").read()
def rep(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:80])
    s = s.replace(a, b)

rep('''  .now-tip { ''', '''  #print-book { display: none; }

  @media print {
    @page { margin: 14mm; }
    html, body { background: #fff !important; color: #000 !important; }
    body > *:not(#print-book) { display: none !important; }
    #print-book { display: block !important; font-family: -apple-system, "Helvetica Neue", Arial, "PingFang HK", "PingFang SC", "Noto Sans CJK TC", sans-serif; font-size: 11pt; color: #000; }
    .pb-head { border-bottom: 2px solid #000; margin-bottom: 10mm; padding-bottom: 3mm; }
    .pb-head h1 { margin: 0 0 2mm; font-size: 20pt; }
    .pb-head p { margin: 0; color: #444; font-size: 9pt; }
    .pb-item { break-inside: avoid; page-break-inside: avoid; padding: 0 0 5mm; margin: 0 0 5mm; border-bottom: 0.5pt solid #bbb; }
    .pb-item h2 { margin: 0 0 3mm; font-size: 13pt; }
    .pb-row { display: grid; grid-template-columns: 30mm 1fr; gap: 3mm; margin: 0 0 3mm; }
    .pb-lang { font-size: 8.5pt; color: #444; padding-top: 1mm; }
    .pb-text { font-size: 13pt; }
    .pb-rom { font-size: 9.5pt; color: #333; font-style: italic; margin-top: 1mm; }
    .pb-words, #print-book .rec-gloss { display: flex; flex-wrap: wrap; gap: 1mm 3mm; margin-top: 2mm; }
    .pb-w, #print-book .gl { display: inline-grid; justify-items: center; line-height: 1.2; }
    .pb-w b, #print-book .gl b { font-size: 12pt; font-weight: 600; }
    .pb-w small, #print-book .gl small { font-size: 7pt; color: #444; }
    .pb-note { font-size: 10pt; margin: 0 0 3mm; padding: 2mm 3mm; border-left: 2pt solid #000; background: #f3f3f3; }
    .pb-meta { font-size: 8.5pt; color: #444; margin-top: 2mm; }
  }

  .anchor-note { margin-top: 6px; }
  .list li .anchor-note { padding: 0 0 12px; }
  .book-acts .anchor-note { flex-basis: 100%; }
  .now-tip { ''')

N = {"en": ["My memory anchor", "What does it sound like to you? e.g. happy → hoh hoy, like a jolly \"ho ho\""], "es": ["Mi ancla de memoria", "¿A qué te suena? p. ej. feliz → hoh hoy, como un alegre \"jo jo\""], "fr": ["Mon ancre mémoire", "À quoi ça te fait penser ? ex. heureux → hoh hoy, comme un joyeux « ho ho »"], "de": ["Meine Eselsbrücke", "Woran erinnert es dich? z. B. glücklich → hoh hoy, wie ein fröhliches „ho ho“"], "yue": ["我嘅記憶錨", "你覺得似乜嘢？例如：開心 → hoh hoy，好似開心咁「呵呵」"], "cmn": ["我的记忆锚点", "它听起来像什么？例如：开心 → hoh hoy，像开心的“呵呵”"]}
T = {"en": "Save as PDF", "es": "Guardar como PDF", "fr": "Enregistrer en PDF", "de": "Als PDF speichern", "yue": "儲存做 PDF", "cmn": "保存为 PDF"}
anchors = {"en": '_name: "English", _lang: "en",', "es": '_name: "Español", _lang: "es",', "fr": '_name: "Français", _lang: "fr",', "de": '_name: "Deutsch", _lang: "de",', "yue": '_name: "廣東話", _lang: "zh-HK",', "cmn": '_name: "普通话", _lang: "zh-CN",'}
for k, v in T.items():
    rep(anchors[k], anchors[k] + f" b_pdf: {json.dumps(v, ensure_ascii=False)}, bk_anchor: {json.dumps(N[k][0], ensure_ascii=False)}, bk_anchor_ph: {json.dumps(N[k][1], ensure_ascii=False)},")
open(p, "w", encoding="utf-8").write(s)
print("pdf ok")
