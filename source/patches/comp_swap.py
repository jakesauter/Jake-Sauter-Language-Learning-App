p = "page.html"
s = open(p, encoding="utf-8").read()
c = open("composer.js", encoding="utf-8").read()
k = "  const Composer = (() => {"
a = s.index(k)
b = s.index("\n  })();", a) + len("\n  })();")
ca = c.index(k)
cb = c.rindex("  })();") + len("  })();")
s = s[:a] + c[ca:cb] + s[b:]
open(p, "w", encoding="utf-8").write(s)
print("composer swapped")
