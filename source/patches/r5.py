p = "composer.js"
s = open(p, encoding="utf-8").read()
def rep(a, b, c=1):
    global s
    assert s.count(a) == c, (s.count(a), a[:90])
    s = s.replace(a, b)

# vocabulary
rep('''      milk: W(''', '''      "go out": W("出去", "ceot1 heoi3", "出去", "chū qù", "出去", "tsut55 hui33"),
      "help n": W("幫手", "bong1 sau2", "帮助", "bāng zhù", "幫手", "bɔŋ33 siu55", false),
      something: W("嘢", "je5", "东西", "dōng xi", "嘢", "yia33"),
      anything: W("任何嘢", "jam6 ho4 je5", "任何东西", "rèn hé dōng xi", "乜嘢", "mɔt55 yia33", false),
      it: W("佢", "keoi5", "它", "tā", "佢", "kui33"),
      milk: W(''')
rep('''      sit: ["sentarse", "s'asseoir", "sich setzen"],''', '''      sit: ["sentarse", "s'asseoir", "sich setzen"], "go out": ["salir", "sortir", "ausgehen"],''')

# special phrases
rep('''      "excuse me": [''', '''      "why not": [["點解唔得", "dim2 gaai2 m4 dak1"], ["为什么不呢", "wèi shén me bù ne"], ["做乜唔得", "du33 mɔt55 m22 ak55", false], "¿Por qué no?", "Pourquoi pas?", "Warum nicht?", ["Why", "not"]],
      "how much is it": [["幾多錢呀", "gei2 do1 cin2 aa3"], ["多少钱", "duō shao qián"], ["幾多錢啊", "gi55 ɔ335 tein225 a33", false], "¿Cuánto cuesta?", "C'est combien?", "Wie viel kostet das?", ["How much", "is it"]],
      "how many people": [["有幾多人呀", "jau5 gei2 do1 jan4 aa3"], ["几个人", "jǐ ge rén"], ["有幾多人啊", "yiu33 gi55 ɔ335 ŋin22 a33", false], "¿Cuántas personas?", "Combien de personnes?", "Wie viele Leute?", ["How many", "people"]],
      "excuse me": [''')

# parse: "need" not past; adverbs; phrasal go out; dem/it objects; need help; really
rep('''          if (PAST_EN[w[0]] || (/ed$/.test(w[0]) && aux !== "have")) {''', '''          if (PAST_EN[w[0]] || (/ed$/.test(w[0]) && w[0] !== vw && aux !== "have")) {''')
rep('''      if (w[0] === "not") { P.neg = true; w = w.slice(1); }

      if (w[0] === "going" && w[1] === "to")''', '''      if (w[0] === "not") { P.neg = true; w = w.slice(1); }
      while (["really", "just", "usually", "still"].includes(w[0])) { if (w[0] === "really") P.really = true; w = w.slice(1); }

      if (w[0] === "going" && w[1] === "to")''')
rep('''          if (w[0] === "up" || w[0] === "out" || w[0] === "off" || w[0] === "on") {
            const ph = P.verb + " " + w[0];
            if (LEX[ph]) { P.verb = ph; w = w.slice(1); }
          }''', '''          if (w[0] === "up" || w[0] === "out" || w[0] === "off" || w[0] === "on") {
            const ph = P.verb + " " + w[0];
            if (LEX[ph] || CORE[ph]) { P.verb = ph; w = w.slice(1); }
          }''')
rep('''      if (P.there) { while (w[0] === "any" || w[0] === "some") w = w.slice(1); P.obj = np(); }''', '''      if (P.there) { while (w[0] === "any" || w[0] === "some") w = w.slice(1); P.obj = np(); }
      const ADV = new Set(["together", "too", "also", "well", "yet", "now", "here", "there", "later", "again", "already", "home"]);
      if ((P.verb || P.copula) && ["it", "this", "that"].includes(w[0]) && (!w[1] || ADV.has(w[1]) || ["with", "to", "at", "for"].includes(w[1]))) { P.objDem = w[0]; w = w.slice(1); }
      if ((P.modal === "need" || P.verb === "need") && P.verb === "help" && !w.length) { P.verb = "need"; P.modal = null; P.obj = { word: "help n" }; }
      if (P.verb === "need" && w[0] === "help") { P.obj = { word: "help n" }; w = w.slice(1); }
      if (["anything", "something"].includes(w[0])) { P.obj = { word: w[0] }; w = w.slice(1); }''')
rep('''        if (w[0] && !["to", "at", "in", "with", "for", "from", "on"].includes(w[0])) P.obj = np();''', '''        if (!P.obj && !P.objDem && w[0] && !["to", "at", "in", "with", "for", "from", "on"].includes(w[0]) && !ADV.has(w[0])) P.obj = np();''')
rep('''        else if (!P.obj && (P.verb || P.copula)) { P.obj = np(); }''', '''        else if (!P.obj && !P.objDem && (P.verb || P.copula) && !ADV.has(h)) { P.obj = np(); }''')

# progressive: keep for motion verbs and wh, except "when"
rep('''        P.prog = P.tense !== "past" && !P.wh && !MOTION.has(pv) && !P.time.some(t => /tomorrow|tonight|next|later|soon|weekend/.test(t));
        if (!P.prog && P.tense !== "past" && (MOTION.has(pv) || P.time.some(t => /tomorrow|tonight|next|later|soon|weekend/.test(t)))) P.tense = "fut";''', '''        const futT = P.time.some(t => /tomorrow|tonight|next|later|soon|weekend/.test(t));
        P.prog = P.tense !== "past" && P.wh !== "when" && !futT;
        if (!P.prog && P.tense !== "past" && futT) P.tense = "fut";
        P.motionProg = P.prog && MOTION.has(pv);''')

# want + what -> 想要
rep('''      if (P.verb === "want" && P.obj) P.wantN = true;''', '''      if (P.verb === "want" && (P.obj || P.wh === "what")) P.wantN = true;''')

# Chinese: neg fut no double; intransitive generic object; did you eat idiom; dem objects; really; ready; well+neg; motion prog cmn
rep('''      const modal = P.modal ? {''', '''      const modal = (P.tense === "fut" && P.neg && !P.modal) ? null : P.modal ? {''')
rep('''        let vw = goHome ? homeV[P.verb] : P.wantN ? { yue: ["要", "jiu3"], cmn: ["要", "yào"], tsn: ["要", "yiau33", false] }''', '''        if (P.verb === "eat" && pastYesNo && !P.obj && !P.wh) {
          const ate = { yue: [["你", "nei5"], ["食咗飯", "sik6 zo2 faan6"], ["未呀", "mei6 aa3"]], cmn: [["你", "nǐ"], ["吃饭", "chī fàn"], ["了吗", "le ma"]], tsn: [["你", "ni33"], ["吃啊飯", "hiak33 ə33 fan32"], ["唔曾", "miaŋ21"]] }[L];
          toks.length = 0;
          if (P.subj && P.subj !== "you") { const z = zhWord(P.subj); if (z) toks.push({ hz: z[L][0], rom: z[L][1], refs: [ix.subj], sure: true }); } else toks.push({ hz: ate[0][0], rom: ate[0][1], refs: [ix.subj], sure: true });
          toks.push({ hz: ate[1][0], rom: ate[1][1], refs: [ix.verb], sure: true });
          toks.push({ hz: ate[2][0], rom: ate[2][1], refs: [ix.q], sure: true });
          return toks;
        }
        if (P.really && P.verb === "like") put({ yue: ["真係好", "zan1 hai6 hou2"], cmn: ["非常", "fēi cháng"], tsn: ["真係好", "tsin33 hai32 hɔu55", false] }, ix.really);
        let vw = goHome ? homeV[P.verb] : P.wantN ? (P.wh === "what" ? { yue: ["想要", "soeng2 jiu3"], cmn: ["想要", "xiǎng yào"], tsn: ["想要", "ɬiaŋ55 yiau33", false] } : { yue: ["要", "jiu3"], cmn: ["要", "yào"], tsn: ["要", "yiau33", false] })''')
rep('''        if (P.prog && L !== "cmn") put({ yue: ["緊", "gan2"], tsn: ["緊", "gin55", false] }, ix.verb);''', '''        if (P.prog && L !== "cmn" && !P.neg) put({ yue: ["緊", "gan2"], tsn: ["緊", "gin55", false] }, ix.verb);
        if (P.objDem) put({ it: (P.verb === "like" && !yesno) ? CORE.it : null, this: FN.this, that: FN.that }[P.objDem] || { yue: null, cmn: null, tsn: null }, ix.objDem);
        if (!P.obj && !P.objDem && !P.wh && !P.place && !P.objPron && ["eat"].includes(P.verb) && !P.neg && !P.prog === false) put({ yue: ["嘢", "je5"], cmn: ["东西", "dōng xi"], tsn: ["嘢", "yia33"] }, ix.verb);
        else if (!P.obj && !P.objDem && !P.wh && !P.place && P.verb === "eat" && (P.modal === "want") && !P.neg) put({ yue: ["嘢", "je5"], cmn: ["东西", "dōng xi"], tsn: ["嘢", "yia33"] }, ix.verb);''')
rep('''        if (P.well) {
          const st =''', '''        if (P.well && P.neg) {
          const st0 = { sleep: { yue: ["瞓", "fan3"], cmn: ["睡", "shuì"], tsn: ["瞓", "fun33"] }, eat: { yue: ["食", "sik6"], cmn: ["吃", "chī"], tsn: ["吃", "hiak33"] } }[P.verb] || zhWord(P.verb);
          const x0 = st0 && st0[L];
          if (x0) {
            const n = toks.findIndex(t => /^(冇|没|唔|不)$/.test(t.hz));
            if (n >= 0) toks.splice(n, 1);
            if (L === "cmn") toks.push({ hz: "没" + x0[0] + "好", rom: "méi " + x0[1].split(" ")[0] + " hǎo", refs: [ix.neg, ix.verb], sure: true });
            else toks.push({ hz: x0[0] + "得唔好", rom: x0[1].split(" ")[0] + (L === "tsn" ? " ak33 m22 hɔu55" : " dak1 m4 hou2"), refs: [ix.verb, ix.neg], sure: true });
            return toks;
          }
        }
        if (P.well) {
          const st =''')
rep('''      if (P.adj) {
        if (P.subj == null && !P.imperative) {
        }''', '''      if (P.adj && ["ready", "done", "finished"].includes(P.adj)) {
        const R = { yue: ["準備好", "zeon2 bei6 hou2"], cmn: ["准备好", "zhǔn bèi hǎo"], tsn: ["準備好", "dzun55 bi32 hɔu55", false] }[L];
        if (P.neg) toks.push({ hz: L === "cmn" ? "还没" : L === "tsn" ? "還唔曾" : "仲未", rom: L === "cmn" ? "hái méi" : L === "tsn" ? "van21 miaŋ21" : "zung6 mei6", refs: [ix.neg], sure: L !== "tsn" });
        toks.push({ hz: R[0], rom: R[1], refs: [ix.adj], sure: R[2] !== false });
        if (yesno) toks.push(L === "cmn" ? { hz: "了吗", rom: "le ma", refs: [ix.q], sure: true } : L === "tsn" ? { hz: "唔曾", rom: "miaŋ21", refs: [ix.q], sure: true } : { hz: "未呀", rom: "mei6 aa3", refs: [ix.q], sure: true });
        else if (!P.neg) toks.push(L === "cmn" ? { hz: "了", rom: "le", refs: [ix.adj], sure: true } : L === "tsn" ? { hz: "啦", rom: "la55", refs: [ix.adj], sure: true } : { hz: "喇", rom: "laa3", refs: [ix.adj], sure: true });
        return toks;
      }
      if (P.adj && P.adj === "good" && P.subj === "it" && !P.degree && !yesno && !P.neg && L === "yue") { toks.push({ hz: "好正", rom: "hou2 zeng3", refs: [ix.adj], sure: true }); return toks; }
      if (P.adj) {''')
rep('''        if (P.prog && L === "cmn") put({ cmn: ["在", "zài"] }, ix.verb);''', '''        if (P.prog && L === "cmn" && !P.neg) put(P.motionProg ? { cmn: ["要", "yào"] } : { cmn: ["在", "zài"] }, ix.verb);''')
rep('''      const aNotAWord = (w, ref) => {''', '''      if (P.motionProg && P.neg && L !== "cmn") { put(FN.notWill, ix.neg); }
      const aNotAWord = (w, ref) => {''')
rep('''        if (P.modal || P.tense !== "past") put(neg, ix.neg); else put(FN.notPast, ix.neg);''', '''        if (P.motionProg && L !== "cmn") {}
        else if (P.modal || P.tense !== "past") put(neg, ix.neg); else put(FN.notPast, ix.neg);''')
rep('''        if (aNotA && !P.neg && !pastYesNo && vw && !P.yet) { aNotAWord(vw, ix.verb); aNotA = false; }''', '''        if (aNotA && !P.neg && !pastYesNo && vw && !P.yet && !P.prog) { aNotAWord(vw, ix.verb); aNotA = false; }''')

# gloss for new roles
rep('''      if (P.more) ix.more = gl("more");''', '''      if (P.more) ix.more = gl("more");
      if (P.objDem) ix.objDem = gl(P.objDem);
      if (P.really) ix.really = gl("really");''')

# Spanish: progressive, it/this objects, anything->nada, really, need help, yet with neg
rep('''          } else if (P.tense === "past") {
            push(esPret(inf, p5), ix.verb);
          } else {
            push(esPresent(inf, p5), ix.verb);
          }''', '''          } else if (P.tense === "past") {
            push(esPret(inf, p5), ix.verb);
          } else if (P.prog && !P.motionProg && !P.neg) {
            const ger = { dormir: "durmiendo", leer: "leyendo", ir: "yendo", decir: "diciendo", venir: "viniendo", pedir: "pidiendo", oír: "oyendo", traer: "trayendo" }[inf] || inf.replace(/ar$/, "ando").replace(/[eií]r$/, "iendo");
            push(esPresent("estar", p5), ix.verb); push(ger, ix.verb);
          } else {
            push(esPresent(inf, p5), ix.verb);
          }''')
rep('''          if (refl) push(esRefl[p5], ix.verb);
          if (objPronEs) push(objPronEs, ix.objPron);''', '''          if (refl) push(esRefl[p5], ix.verb);
          if (objPronEs) push(objPronEs, ix.objPron);
          if (P.objDem === "it" && !P.modal && P.tense !== "fut") push("lo", ix.objDem);''')
rep('''          if (P.verb !== "like") push(inf, ix.verb);
          if (obj) push(obj, ix.obj);''', '''          if (P.verb !== "like") push(inf, ix.verb);
          if (obj) push(obj, ix.obj);
          if (P.objDem && P.objDem !== "it") push({ this: "esto", that: "eso" }[P.objDem], ix.objDem);
          if (P.really) push("mucho", ix.really);''')
rep('''          if (!P.meal) push(npEU(P.obj, "es", "obj", P), ix.obj);''', '''          if (P.obj && ["anything", "something"].includes(P.obj.word)) push(P.neg ? "nada" : "algo", ix.obj);
          else if (P.obj && P.obj.word === "help n") push("ayuda", ix.obj);
          else if (!P.meal) push(npEU(P.obj, "es", "obj", P), ix.obj);
          if (P.objDem && P.objDem !== "it") push({ this: "esto", that: "eso" }[P.objDem], ix.objDem);''')
rep('''          const obj = P.obj && P.verb === "like" ? npEU({ ...P.obj, det: P.obj.det || "the" }, "es", "subj", P) : "";''', '''          const obj = P.obj && P.verb === "like" && !["anything", "something"].includes(P.obj.word) ? npEU({ ...P.obj, det: P.obj.det || "the" }, "es", "subj", P) : "";''')
rep('''      if (P.yet) push("ya", ix.yet);''', '''      if (P.yet && !P.neg) push("ya", ix.yet);
      if (P.yet && P.neg) { const k = T.findIndex(t => t.hz === "no"); if (k >= 0) T[k].hz = "todavía no"; }''')

# Spanish adj with "it": está listo ok; "es bueno" -> "está bueno" for food? keep

# French: c'est with it; dem objects; need help; anything; yet+neg; prog stays present
rep('''          if (!subj && !P.imperative) { subj = "c'"; push("C'est", ix.adj); push((deg ? deg + " " : "") + a, ix.adj); }''', '''          if ((!subj || P.subj === "it") && !P.imperative) { push(P.neg ? (P.yet ? "Ce n'est pas encore" : "Ce n'est pas") : "C'est", [ix.adj, ix.neg].filter(x => x !== undefined)); push((deg ? deg + " " : "") + a, ix.adj); }''')
rep('''        if (P.more && !P.obj) push("plus", ix.more);
        if (!P.meal) push(npEU(P.obj, "fr", "obj", P), ix.obj);''', '''        if (P.more && !P.obj) push("plus", ix.more);
        if (P.really) push("vraiment", ix.really);
        if (P.objDem) push("ça", ix.objDem);
        if (P.obj && ["anything", "something"].includes(P.obj.word)) { if (P.neg) { const k = T.findIndex(t => / pas$/.test(t.hz)); if (k >= 0) T[k].hz = T[k].hz.replace(/ pas$/, ""); } push(inf === "avoir" && extra === "besoin" ? (P.neg ? "de rien" : "de quelque chose") : (P.neg ? "rien" : "quelque chose"), ix.obj); }
        else if (P.obj && P.obj.word === "help n") push("d'aide", ix.obj);
        else if (!P.meal) push(npEU(P.obj, "fr", "obj", P), ix.obj);''')
rep('''      if (P.yet) push("déjà", ix.yet);''', '''      if (P.yet && !P.neg) push("déjà", ix.yet);''')

# German: dem/it objects, nichts, Hilfe, gerade, nicht gut, noch nicht
rep('''        const objS = P.meal ? "" : npEU(P.obj, "de", "obj", P);''', '''        const objS = P.meal ? "" : P.obj && ["anything", "something"].includes(P.obj.word) ? (P.neg ? "nichts" : "etwas") : P.obj && P.obj.word === "help n" ? "Hilfe" : npEU(P.obj, "de", "obj", P);
        if (P.objDem) mid.push([{ it: "es", this: "das", that: "das" }[P.objDem], ix.objDem]);
        if (P.really) mid.push(["wirklich", ix.really]);
        if (P.prog && !P.motionProg && !P.neg && P.tense === "pres" && !P.modal) mid.push(["gerade", ix.verb]);''')
rep('''        if (P.neg && !(objS && /^kein/.test(objS))) tail.unshift(["nicht", ix.neg]);''', '''        if (P.neg && !(objS && /^(kein|nichts)/.test(objS))) tail.unshift([P.yet ? "noch nicht" : P.well ? "nicht gut" : "nicht", ix.neg]);''')
rep('''      if (P.well) push("gut", ix.verb);''', '''      if (P.well && !P.neg) push("gut", ix.verb);''')
rep('''          if (P.neg) mid.push(["nicht", ix.neg]);
          mid.push([(deg ? deg + " " : "") + (euWord(P.adj, "de") || P.adj), ix.adj]);''', '''          if (P.neg) mid.push([P.yet ? "noch nicht" : "nicht", ix.neg]);
          mid.push([(deg ? deg + " " : "") + (euWord(P.adj, "de") || P.adj), ix.adj]);''')
rep('''      if (P.yet) push("schon", ix.yet);''', '''      if (P.yet && !P.neg) push("schon", ix.yet);''')
open(p, "w", encoding="utf-8").write(s)
print("ok")
