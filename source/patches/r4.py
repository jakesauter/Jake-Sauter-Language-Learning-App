p = "composer.js"
s = open(p, encoding="utf-8").read()
def rep(a, b, c=1):
    global s
    assert s.count(a) == c, (s.count(a), a[:90])
    s = s.replace(a, b)

rep('''      if (neg && !(P.imperative)) {''', '''      if (neg && !(P.imperative) && !(P.modal === "can" && ["find", "see", "hear", "sleep"].includes(P.verb))) {''')
rep('''    function euWord(key, lang) {
      const v = LEX[key];''', '''    const EUX = {
      cantonese: ["cantonés", "le cantonais", "Kantonesisch"], mandarin: ["mandarín", "le mandarin", "Mandarin"], taishanese: ["taishanés", "le taïshanais", "Taishanesisch"],
      english: ["inglés", "l'anglais", "Englisch"], chinese: ["chino", "le chinois", "Chinesisch"], spanish: ["español", "l'espagnol", "Spanisch"], french: ["francés", "le français", "Französisch"], german: ["alemán", "l'allemand", "Deutsch"],
      sit: ["sentarse", "s'asseoir", "sich setzen"], bathroom: ["el baño", "les toilettes", "die Toilette"], key: ["la llave", "la clé", "der Schlüssel"],
    };

    function euWord(key, lang) {
      if (EUX[key]) return EUX[key][{ es: 0, fr: 1, de: 2 }[lang]];
      const v = LEX[key];''')
rep('''      "excuse me": [''', '''      "what is your name": [["你叫乜嘢名呀", "nei5 giu3 mat1 je5 meng2 aa3"], ["你叫什么名字", "nǐ jiào shén me míng zi"], ["你估乜名啊", "ni33 gu55 mɔt55 miaŋ22 a33"], "¿Cómo te llamas?", "Comment tu t'appelles?", "Wie heißt du?", ["What", "is", "your name"]],
      "excuse me": [''')
rep('''      if (P.wh && ["is", "are", "was"].includes(aux) && w.length && !w.some(x => isVerbWord(x) && !nounOf(x))) {''', '''      if (P.wh && ["is", "are", "was"].includes(aux) && !w.length && P.subj && P.subj.includes(" ") && P.subj !== "you all") {
        const [d0, n0] = P.subj.split(" ");
        P.whBe = { word: n0, det: d0 }; return P;
      }
      if (P.wh && ["is", "are", "was"].includes(aux) && w.length && !w.some(x => isVerbWord(x) && !nounOf(x))) {''')
open(p, "w", encoding="utf-8").write(s)
print("ok")
