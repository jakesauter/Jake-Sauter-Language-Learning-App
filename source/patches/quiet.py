p = "page.html"
s = open(p, encoding="utf-8").read()
def rep(a, b, n):
    global s
    assert s.count(a) == n, (s.count(a), a)
    s = s.replace(a, b)
rep('''    const k = "phrasebook-toast-" + key;''', '''    return;
    const k = "phrasebook-toast-" + key;''', 1)
rep('''pr.catch(() => toast(tr("t_blocked")))''', '''pr.catch(() => {})''', 2)
rep('''    if (r === "ok") return;
    toast(r === "missing" ? tr("t_missing", { lang: NAMES[lang] }) : tr("t_nospeech"));''', '''    if (r === "ok") return;''', 1)
open(p, "w", encoding="utf-8").write(s)
print("quiet ok")
