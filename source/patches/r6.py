p = "composer.js"
s = open(p, encoding="utf-8").read()
def rep(a, b, c=1):
    global s
    assert s.count(a) == c, (s.count(a), a[:90])
    s = s.replace(a, b)
rep('''        P.motionProg = P.prog && MOTION.has(pv);''', '''        P.motionProg = P.prog && MOTION.has(pv);
        if (P.motionProg && P.time.length) { P.prog = false; P.motionNow = true; }''')
rep('''P.verb === "cook" && P.obj ? {''', '''P.verb === "cook" && (P.obj || P.objDem) ? {''')
rep('''!pastYesNo && !(L === "cmn" && !P.obj && !P.wh) ||''', '''!pastYesNo && !(L === "cmn" && !P.obj && !P.objDem && !P.wh) ||''')
rep('''        if (P.tense === "past" && !P.neg && !P.modal && L === "cmn" && !pastYesNo && !P.obj && !P.wh) put(FN.past, ix.verb);''', '''        if (P.tense === "past" && !P.neg && !P.modal && L === "cmn" && !pastYesNo && !P.obj && !P.objDem && !P.wh) put(FN.past, ix.verb);''')
rep('''      milk: W(''', '''      need: W("需要", "seoi1 jiu3", "需要", "xū yào", "需要", "ɬui33 yiau33", false),
      milk: W(''')
open(p, "w", encoding="utf-8").write(s)
print("ok")
