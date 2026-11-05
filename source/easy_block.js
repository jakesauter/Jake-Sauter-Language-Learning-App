  /* easy English spelling for Jyutping, pinyin and Stephen Li's Taishanese */

  const ROMAN = { mode: "easy" };

  const YUE_F = {
    aa: "ah", aai: "ai", aau: "ow", aam: "ahm", aan: "ahn", aang: "ahng", aap: "ahp", aat: "aht", aak: "ahk",
    ai: "ai", au: "ow", am: "um", an: "un", ang: "ung", ap: "up", at: "ut", ak: "uk",
    e: "eh", ei: "ay", eng: "eng", ek: "ek", eu: "ew", em: "em", ep: "ep",
    i: "ee", iu: "yoo", im: "eem", in: "een", ing: "ing", ip: "eep", it: "eet", ik: "ik",
    o: "aw", oi: "oy", ou: "oh", on: "awn", ong: "awng", ot: "awt", ok: "awk",
    u: "oo", ui: "ooy", un: "oon", ung: "oong", ut: "oot", uk: "ook",
    oe: "eu", oeng: "eung", oek: "euk", eoi: "eui", eon: "un", eot: "ut",
    yu: "yu", yun: "yun", yut: "yut",
  };

  function easyYue(s) {
    if (s === "m" || s === "ng" || s === "hm" || s === "hng") return s;
    const m = s.match(/^(ng|gw|kw|[bpmfdtnlgkhwzcsj])?(.*)$/);
    const ini = m[1] || "";
    const fin = m[2];
    const f = YUE_F[fin] ?? fin;
    let I = { z: "j", c: "ch", j: "y" }[ini] ?? ini;
    if (ini === "j" && (f.startsWith("y") || fin.startsWith("yu"))) I = "";
    return I + f;
  }

  const CMN_WHOLE = {
    yi: "ee", yin: "een", ying: "ing", yu: "yu", yue: "yweh", yuan: "ywen", yun: "yun",
    ya: "yah", yao: "yow", yan: "yen", yang: "yahng", ye: "yeh", you: "yo", yong: "yoong",
    wu: "woo", wa: "wah", wo: "waw", wai: "wai", wei: "way", wan: "wahn", wen: "wun", wang: "wahng", weng: "wung",
    er: "ar", a: "ah", ai: "ai", ao: "ow", an: "ahn", ang: "ahng", o: "aw", ou: "oh", e: "uh", ei: "ay", en: "un", eng: "ung",
  };

  const CMN_F = {
    a: "ah", ai: "ai", ao: "ow", an: "ahn", ang: "ahng", o: "aw", ou: "oh", ong: "oong", e: "uh", ei: "ay", en: "un", eng: "ung",
    i: "ee", ia: "yah", iao: "yow", ian: "yen", iang: "yahng", ie: "yeh", in: "een", ing: "ing", iong: "yoong", iu: "yo",
    u: "oo", ua: "wah", uai: "wai", uan: "wahn", uang: "wahng", ui: "way", un: "oon", uo: "waw",
    "ü": "yu", "üe": "weh", "üan": "wen", "ün": "yun",
  };

  const CMN_I = { q: "ch", x: "sh", zh: "j", z: "dz", c: "ts" };
  const CMN_BUZZ = { zh: "jr", ch: "chr", sh: "shr", r: "r", z: "dz", c: "ts", s: "s" };

  function easyCmn(syl) {
    let s = syl.normalize("NFD").replace(/[\u0300\u0301\u0304\u030c]/g, "").normalize("NFC").toLowerCase().replace(/v/g, "ü");
    let er = "";
    if (s.length > 2 && s.endsWith("r") && s !== "er") { s = s.slice(0, -1); er = "r"; }
    if (CMN_WHOLE[s]) return CMN_WHOLE[s] + er;
    const m = s.match(/^(zh|ch|sh|[bpmfdtnlgkhjqxrzcs])?(.*)$/);
    const ini = m[1] || "";
    let fin = m[2];
    if (fin === "i" && CMN_BUZZ[ini]) return CMN_BUZZ[ini] + er;
    if (/^[jqx]$/.test(ini) && fin.startsWith("u")) fin = "ü" + fin.slice(1);
    return (CMN_I[ini] ?? ini) + (CMN_F[fin] ?? fin) + er;
  }

  const TSN_F = {
    a: "ah", ai: "ai", au: "ow", am: "ahm", an: "ahn", ang: "ahng", ap: "ahp", at: "aht", ak: "ahk",
    "ɔ": "aw", "ɔi": "oy", "ɔu": "oh", "ɔn": "awn", "ɔng": "awng", "ɔk": "awk", "ɔt": "awt", "ɔm": "awm", "ɔp": "awp",
    "ə": "uh", "əu": "eu", "əng": "ung", "ək": "uk", "əm": "um", "ən": "un", "əp": "up", "ət": "ut",
    "ɛ": "eh", "ɛt": "et", "ɛk": "ek", "ɛn": "en", "ɛng": "eng", "ɛp": "ep", "ɛm": "em",
    e: "eh", ei: "ay", ein: "ayn", eng: "eng", et: "et", ek: "ek",
    i: "ee", ia: "yah", iak: "yahk", iang: "yahng", iam: "yahm", iap: "yahp", iat: "yaht", ian: "yahn", iau: "yow", iu: "yoo",
    im: "eem", in: "een", ip: "eep", it: "eet", ik: "ik", ing: "ing",
    o: "aw", u: "oo", ui: "ooy", un: "oon", ut: "oot", uk: "ook", ung: "oong",
  };

  function easyTsn(s) {
    let t = s.replace(/ŋ/g, "ng");
    if (t === "m" || t === "ng") return t;
    const m = t.match(/^(ng|ts|dz|ɬ|[bpmfdtnlgkhvysz])?(.*)$/);
    const ini = m[1] || "";
    const fin = m[2];
    let f = TSN_F[fin];
    if (f === undefined) f = fin.replace(/ɔ/g, "aw").replace(/ə/g, "uh").replace(/ɛ/g, "eh");
    let I = { ts: "ch", dz: "j", "ɬ": "lh" }[ini] ?? ini;
    if (ini === "y" && f.startsWith("y")) I = "";
    if (ini === "y" && f.startsWith("ee")) I = "y";
    return I + f;
  }

  function easySyl(lang, base) {
    if (lang === "yue") return easyYue(base);
    if (lang === "tsn") return easyTsn(base);
    return easyCmn(base);
  }

  function romParts(lang, rom) {
    return String(rom || "").split(" ").filter(Boolean).map(s => {
      if (lang === "cmn") return { show: ROMAN.mode === "easy" ? easyCmn(s) : s, num: "" };
      const x = splitSyl(lang, s);
      if (!x.levels) return { show: s, num: "" };
      return { show: ROMAN.mode === "easy" ? easySyl(lang, x.base) : x.base, num: x.num };
    });
  }

  function romHtml(lang, rom) {
    return romParts(lang, rom).map(x => x.num
      ? `<span class="syl">${esc(x.show)}<sup>${x.num}</sup></span>`
      : esc(x.show)).join(" ");
  }

  function romText(lang, rom) {
    return romParts(lang, rom).map(x => ROMAN.mode === "easy" ? x.show : x.show + x.num).join(" ");
  }

  function lanePlay(lang, p) {
    const slot = el("div", "lane-play");
    if (lang === "en") return slot;

    const toks = p[lang] || [];
    const text = toks.map(t => t.hz).join("");
    const rom = toks.map(t => t.rom).join(" ");

    if (lang !== "tsn") {
      const b = el("button", "lp", speaker);
      b.type = "button";
      b.setAttribute("aria-label", `Listen to the whole sentence in ${NAMES[lang]}`);
      b.addEventListener("click", e => { e.stopPropagation(); sayVoice(text, lang); });
      slot.appendChild(b);
    }

    const h = el("button", lang === "tsn" ? "lp" : "lp alt", wave);
    h.type = "button";
    h.setAttribute("aria-label", `Play the ${NAMES[lang]} tones for the whole sentence`);
    h.addEventListener("click", e => { e.stopPropagation(); sayTones(lang, rom); });
    slot.appendChild(h);

    return slot;
  }