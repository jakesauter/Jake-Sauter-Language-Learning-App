p = "page.html"
s = open(p, encoding="utf-8").read()
c = open("tsn_voice.js", encoding="utf-8").read()
k = "  const TsnVoice = (() => {"
a = s.index(k)
b = s.index("\n  })();", a) + len("\n  })();")
ca = c.index(k)
cb = c.index("\n  })();", ca) + len("\n  })();")
s = s[:a] + c[ca:cb] + s[b:]
open(p, "w", encoding="utf-8").write(s)
print("tsn voice swapped")
