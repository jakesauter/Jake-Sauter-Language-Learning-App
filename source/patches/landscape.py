p = "page.html"
s = open(p, encoding="utf-8").read()
a = "  @media (max-width: 400px) {"
assert s.count(a) == 1
s = s.replace(a, '''  @media (max-height: 540px) and (orientation: landscape) {
    .bar { position: relative; top: auto; padding-block: var(--s-2); }
    .langs { flex-wrap: nowrap; overflow-x: auto; scrollbar-width: none; }
    header.top { padding-block: var(--s-2); }
    .banner { padding: 8px 12px 8px 10px; gap: 12px; border-radius: 14px; }
    .banner .b-mark { width: 40px; height: 40px; }
    .banner .b-word { height: 26px; }
    .banner .tag { display: none; }
  }

''' + a, 1)
open(p, "w", encoding="utf-8").write(s)
print("landscape ok")
