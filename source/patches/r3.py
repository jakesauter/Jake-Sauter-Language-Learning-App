p = "composer.js"
s = open(p, encoding="utf-8").read()
def rep(a, b, c=1):
    global s
    assert s.count(a) == c, (s.count(a), a[:90])
    s = s.replace(a, b)

rep('''      const pi = P.subj === "who" ? 2 : P.subj && P.subj.includes(" ") ? 2 : P.subj === "everyone" ? 4 : person === 5 ? 6 : person === 3 ? 4 : person === 4 ? 5 : person;''',
    '''      const pi = P.subj === "who" ? 2 : P.subj && P.subj.includes(" ") && P.subj !== "you all" ? 2 : P.subj === "everyone" ? 5 : person;''')

rep('''      milk: W(''', '''      cantonese: W("廣東話", "gwong2 dung1 waa2", "粤语", "yuè yǔ", "廣東話", "gɔŋ55 əŋ33 va325", false),
      mandarin: W("普通話", "pou2 tung1 waa2", "普通话", "pǔ tōng huà", "國語", "kɔk33 ŋi21", false),
      taishanese: W("台山話", "toi4 saan1 waa2", "台山话", "tái shān huà", "台山話", "hɔi22 san33 va325"),
      english: W("英文", "jing1 man2", "英语", "yīng yǔ", "英文", "yein33 mun22", false),
      chinese: W("中文", "zung1 man2", "中文", "zhōng wén", "唐話", "hɔŋ22 va325", false),
      key: W("鎖匙", "so2 si4", "钥匙", "yào shi", "鎖匙", "ɬɔ55 si22"),
      find: W("搵到", "wan2 dou2", "找到", "zhǎo dào", "搵到", "vun55 ɔu55"),
      sit: W("坐低", "co5 dai1", "坐下", "zuò xià", "坐", "tɔ33"),
      bathroom: W("廁所", "ci3 so2", "洗手间", "xǐ shǒu jiān", "廁所", "tsi33 sɔ55", false),
      toilet: W("廁所", "ci3 so2", "厕所", "cè suǒ", "廁所", "tsi33 sɔ55", false),
      milk: W(''')

rep('''      let w = raw.slice();''', '''      let w = raw.join(" ").replace(/\\byou guys\\b|\\by'all\\b|\\byou two\\b/g, "you all").split(" ");''')
rep('''          if (w[0] === "up" || w[0] === "out" || w[0] === "off" || w[0] === "on") {''', '''          if ((w[0] === "down" || w[0] === "up") && ["sit", "stand", "calm", "lie", "wake", "get", "hurry", "shut"].includes(P.verb)) w = w.slice(1);
          if (w[0] === "well") { P.well = true; w = w.slice(1); }
          if (w[0] === "up" || w[0] === "out" || w[0] === "off" || w[0] === "on") {''')
rep('''          if (["me", "you", "him", "her", "us", "them"].includes(w[0])) { P.objPron = w[0]; w = w.slice(1); }''',
    '''          if (w[0] === "you" && w[1] === "all") { P.objPron = "you all"; w = w.slice(2); }
          else if (["me", "you", "him", "her", "us", "them"].includes(w[0])) { P.objPron = w[0]; w = w.slice(1); }''')
rep('''        else if (h === "yet") { P.yet = true; w = w.slice(1); }''', '''        else if (h === "yet") { P.yet = true; w = w.slice(1); }
        else if (h === "well") { P.well = true; w = w.slice(1); }''')

rep('''    function compose(text) {
      const P = parse(text);''', open("/tmp/claude-0/-home-claude/d0a8b9a3-91fd-50e7-97d5-399d63c71b81/scratchpad/patches/special.js", encoding="utf-8").read() + '''
    function compose(text) {
      const sp = special(text);
      if (sp) {
        return { p: { en: text, ...sp, guess: true, composed: true, tip: tr("c_note") }, found: sp.gloss.length, counted: sp.gloss.length };
      }
      const P = parse(text);''')

rep('''      if (modal) {
        if (aNotA && !P.neg && !pastYesNo) { aNotAWord(modal, ix.modal ?? ix.fut); aNotA = false; }
        else put(modal, ix.modal ?? ix.fut);
      }
      preVerb();''', '''      const RES = { find: { yue: ["搵", "wan2"], cmn: ["找", "zhǎo"], tsn: ["搵", "vun55"] }, see: { yue: ["睇", "tai2"], cmn: ["看", "kàn"], tsn: ["睇", "hai55"] }, hear: { yue: ["聽", "teng1"], cmn: ["听", "tīng"], tsn: ["聽", "hiaŋ33"] }, sleep: { yue: ["瞓", "fan3"], cmn: ["睡", "shuì"], tsn: ["瞓", "fun33"] } };
      const resV = P.modal === "can" && RES[P.verb];
      if (resV) {
        preVerb();
        const st = resV[L];
        const mid = P.neg ? (L === "cmn" ? ["不", "bu"] : L === "tsn" ? ["唔", "m22"] : ["唔", "m4"]) : (L === "cmn" ? ["得", "de"] : L === "tsn" ? ["得", "ak33"] : ["得", "dak1"]);
        const endc = L === "cmn" ? (P.verb === "see" ? ["见", "jiàn"] : ["到", "dào"]) : L === "tsn" ? ["到", "ɔu55"] : ["到", "dou2"];
        if (yesno && !P.neg && L !== "cmn") toks.push({ hz: st[0] + "唔" + st[0] + "得到", rom: st[1] + (L === "tsn" ? " m22 " : " m4 ") + st[1] + " " + (L === "tsn" ? "ak33 ɔu55" : "dak1 dou2"), refs: [ix.modal, ix.verb], sure: L !== "tsn" });
        else toks.push({ hz: st[0] + mid[0] + endc[0], rom: st[1] + " " + mid[1] + " " + endc[1], refs: [ix.modal, ix.neg, ix.verb].filter(x => x !== undefined), sure: L !== "tsn" });
        npZh(P.obj, ix.obj);
        if (yesno) put(FN.q, ix.q); else if (P.wh) put(FN.qWh, null);
        return toks;
      }

      if (modal) {
        if (aNotA && !P.neg && !pastYesNo) { aNotAWord(modal, ix.modal ?? ix.fut); aNotA = false; }
        else put(modal, ix.modal ?? ix.fut);
      }
      preVerb();''')
rep('''        let vw = goHome ? homeV[P.verb]''', '''        if (P.well) {
          const st = { sleep: { yue: ["瞓", "fan3"], cmn: ["睡", "shuì"], tsn: ["瞓", "fun33"] }, eat: { yue: ["食", "sik6"], cmn: ["吃", "chī"], tsn: ["吃", "hiak33"] } }[P.verb] || zhWord(P.verb);
          const x = st && st[L];
          if (x) {
            const de = L === "cmn" ? ["得", "de"] : L === "tsn" ? ["得", "ak33"] : ["得", "dak1"];
            const good = L === "cmn" ? ["好", "hǎo"] : L === "tsn" ? ["好", "hɔu55"] : ["好", "hou2"];
            const tail = yesno ? (L === "cmn" ? good : [good[0] + "唔" + good[0], good[1] + (L === "tsn" ? " m22 " : " m4 ") + good[1]]) : good;
            toks.push({ hz: x[0] + de[0] + tail[0], rom: x[1].split(" ")[0] + " " + de[1] + " " + tail[1], refs: [ix.verb], sure: true });
            if (yesno) put(FN.q, ix.q);
            return toks;
          }
        }
        let vw = goHome ? homeV[P.verb]''')
rep('''      if (pastYesNo && !P.yet) put(FN.haveNot, ix.q);''', '''      if (pastYesNo && !P.yet && !P.well) put(FN.haveNot, ix.q);''')

rep('''        const objPronEs = P.objPron ? { me: "me", you: "te", him: "lo", her: "la", us: "nos", them: "los" }[P.objPron] : null;''',
    '''        const objPronEs = P.objPron ? { me: "me", you: "te", him: "lo", her: "la", us: "nos", them: "los", "you all": "los" }[P.objPron] : null;''')
rep('''        const objPronFr = P.objPron ? { me: "me", you: "te", him: "le", her: "la", us: "nous", them: "les" }[P.objPron] : null;''',
    '''        const objPronFr = P.objPron ? { me: "me", you: "te", him: "le", her: "la", us: "nous", them: "les", "you all": "vous" }[P.objPron] : null;''')
rep('''{ me: "mich", you: "dich", him: "ihn", her: "sie", us: "uns", them: "sie" } : { me: "mir", you: "dir", him: "ihm", her: "ihr", us: "uns", them: "ihnen" })[P.objPron] : null;''',
    '''{ me: "mich", you: "dich", him: "ihn", her: "sie", us: "uns", them: "sie", "you all": "euch" } : { me: "mir", you: "dir", him: "ihm", her: "ihr", us: "uns", them: "ihnen", "you all": "euch" })[P.objPron] : null;''')
rep('''      if (P.yet) push("ya", ix.yet);''', '''      if (P.yet) push("ya", ix.yet);
      if (P.well) push("bien", ix.verb);''')
rep('''            verbGroup((objLead) + auxF, ix.verb, pp);''', '''            verbGroup((objLead) + auxF, ix.verb, (P.well ? "bien " : "") + pp);''')
rep('''      if (P.yet) push("schon", ix.yet);''', '''      if (P.yet) push("schon", ix.yet);
      if (P.well) push("gut", ix.verb);''')
rep('''&& !MEALS[n.word]) art =''', '''&& !MEALS[n.word] && !LANGS.has(n.word)) art =''', 2)
rep('''    const KIN = new Set(''', '''    const LANGS = new Set("cantonese mandarin taishanese english chinese spanish french german".split(" "));
    const KIN = new Set(''')

# where/what/who/how + be + NP
rep('''      if (P.wh === "who" && !P.subj) P.subj = "who";''', '''      if (P.wh && ["is", "are", "was"].includes(aux) && w.length && !w.some(x => isVerbWord(x) && !nounOf(x))) {
        const save = w;
        let det = null;
        while (DET.has(w[0])) { det = det || w[0]; w = w.slice(1); }
        const n = w.join(" ");
        const cand = lemmas(n).find(l => LEX[l] || CORE[l]);
        if (cand) { P.whBe = { word: cand, det, plural: n !== cand && /s$/.test(n) }; return P; }
        w = save;
      }
      if (P.wh === "who" && !P.subj) P.subj = "who";''')
rep('''      const P = parse(text);
      if (!P) return null;
      let B;''', '''      const P = parse(text);
      if (!P) return null;
      if (P.whBe) return whBe(text, P);
      let B;''')
open(p, "w", encoding="utf-8").write(s)
print("ok")
