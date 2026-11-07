import json
p = "page.html"
s = open(p, encoding="utf-8").read()
def rep(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:80])
    s = s.replace(a, b)

g = "  const PINYIN_RAW = " + json.dumps(open("pinyin.txt", encoding="utf-8").read(), ensure_ascii=False) + ";\n\n" + open("gtrans.js", encoding="utf-8").read()
rep("  /* search + translate */", g + "\n\n  /* search + translate */")
rep('''    result.appendChild(renderDetail(g.p));''', '''    result.appendChild(renderDetail(g.p));
    const gts = GT.section(text);
    if (gts) result.appendChild(gts);''')
rep('''  .now-tip { ''', '''  .gt-set { margin-top: var(--s-3); }
  .gt .label { margin-bottom: 4px; }
  .gt .lp:disabled { opacity: 0.3; }
  .now-tip { ''')

K = ["gt_h", "gt_set", "gt_ph", "gt_ok", "gt_fail", "gt_quota", "gt_help"]
T = {
 "en": ["Google Translate", "Google Translate key (optional)", "Paste your API key", "Working", "Google Translate didn't work: {msg}", "Today's Google Translate limit is used up. It resets at midnight Pacific time.", "Typed sentences also get a Google Translate version. The key is saved only on this phone."],
 "es": ["Google Translate", "Clave de Google Translate (opcional)", "Pega tu clave de API", "Funciona", "Google Translate no funcionó: {msg}", "Se agotó el límite diario de Google Translate. Se reinicia a medianoche (hora del Pacífico).", "Las frases que escribas también tendrán una versión de Google Translate. La clave solo se guarda en este teléfono."],
 "fr": ["Google Traduction", "Clé Google Traduction (facultatif)", "Colle ta clé d'API", "Ça marche", "Google Traduction n'a pas fonctionné : {msg}", "La limite quotidienne de Google Traduction est atteinte. Elle se réinitialise à minuit (heure du Pacifique).", "Les phrases que tu tapes auront aussi une version Google Traduction. La clé reste uniquement sur ce téléphone."],
 "de": ["Google Übersetzer", "Google-Übersetzer-Schlüssel (optional)", "API-Schlüssel einfügen", "Funktioniert", "Google Übersetzer hat nicht funktioniert: {msg}", "Das Tageslimit für Google Übersetzer ist aufgebraucht. Es wird um Mitternacht (Pazifikzeit) zurückgesetzt.", "Eingetippte Sätze bekommen zusätzlich eine Google-Übersetzung. Der Schlüssel bleibt nur auf diesem Telefon."],
 "yue": ["Google 翻譯", "Google 翻譯金鑰（可選）", "貼上你嘅 API 金鑰", "用得", "Google 翻譯用唔到：{msg}", "今日嘅 Google 翻譯限額用晒，太平洋時間半夜重設。", "你打嘅句子都會有 Google 翻譯版本。金鑰只會儲喺呢部手機。"],
 "cmn": ["Google 翻译", "Google 翻译密钥（可选）", "粘贴你的 API 密钥", "可以使用", "Google 翻译出错：{msg}", "今天的 Google 翻译额度已用完，太平洋时间午夜重置。", "你输入的句子也会有 Google 翻译版本。密钥只保存在这部手机上。"],
}
anchors = {"en": '_name: "English", _lang: "en",', "es": '_name: "Español", _lang: "es",', "fr": '_name: "Français", _lang: "fr",', "de": '_name: "Deutsch", _lang: "de",', "yue": '_name: "廣東話", _lang: "zh-HK",', "cmn": '_name: "普通话", _lang: "zh-CN",'}
for k, vals in T.items():
    add = " ".join(f"{key}: {json.dumps(v, ensure_ascii=False)}," for key, v in zip(K, vals))
    rep(anchors[k], anchors[k] + " " + add)
open(p, "w", encoding="utf-8").write(s)
print("gt ok")
