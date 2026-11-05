    function speak(text, lang) {
      if (!ok) return "none";
      load();
      const v = pick(lang);
      if (!v && voices.length) return "missing";
      try {
        const synth = window.speechSynthesis;
        if (synth.speaking || synth.pending) synth.cancel();
        const u = new SpeechSynthesisUtterance(text);
        u.lang = lang === "yue" ? "zh-HK" : "zh-CN";
        if (v) u.voice = v;
        u.rate = settings.rate;
        let started = false;
        u.onstart = () => { started = true; };
        u.onerror = e => {
          if (e && (e.error === "canceled" || e.error === "interrupted")) return;
          toast("The voice couldn't play here. On iPhone, check the side switch isn't on silent, or try the downloaded file in Safari.");
        };
        synth.speak(u);
        if (synth.paused) synth.resume();
        setTimeout(() => {
          if (!started && !synth.speaking) toast("No sound? On iPhone, turn off silent mode and check the volume. Tones play either way.");
        }, 2500);
        return "ok";
      } catch (e) {
        return "none";
      }
    }

    function stop() {
      try {
        const synth = window.speechSynthesis;
        if (ok && (synth.speaking || synth.pending)) synth.cancel();
      } catch (e) {}
    }

    return { speak, stop };
  })();


  /* tone engine: builds a small WAV in JavaScript and plays it through an audio element */

  const Tones = (() => {
    const RATE = 22050;
    let player = null;

    const VOWELS = {
      a: [750, 1200, 2500], e: [550, 1850, 2500], "ɛ": [580, 1800, 2500], i: [300, 2250, 3000],
      o: [500, 850, 2400], "ɔ": [580, 900, 2400], u: [350, 800, 2300], "ə": [500, 1400, 2400],
      y: [300, 1900, 2400], "ü": [300, 1900, 2400], m: [260, 1100, 2300],
    };

    const FRICATIVE = /^(s|ɬ|f|h|sh|ch|c|z|zh|x|q|j|ts|dz)/;

    function vowelOf(base) {
      const b = base.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
      const m = b.match(/[aeiouɔəɛyü]/);
      if (m) return VOWELS[m[0]];
      return VOWELS.m;
    }

    const freq = lv => 140 * Math.pow(2, ((lv - 1) * 3) / 12);

    function syllables(lang, rom) {
      return String(rom || "").split(" ").filter(Boolean).map(s => {
        if (lang === "cmn") return { base: s, levels: pinyinLevels(s) };
        const x = splitSyl(lang, s);
        return { base: x.base, levels: x.levels };
      });
    }

    function render(list) {
      const unit = 0.38 / settings.rate;
      const gap = 0.07 / settings.rate;

      const segs = list.map(sy => {
        const d = !sy.levels ? unit * 0.4 : sy.levels.length === 1 ? unit * 0.6 : sy.levels.length === 3 ? unit * 1.3 : unit;
        return { ...sy, d };
      });

      const total = segs.reduce((a, sg) => a + sg.d + gap, 0.1);
      const n = Math.ceil(total * RATE);
      const buf = new Float32Array(n);
      const bw = [90, 110, 160];
      const fw = [1, 0.6, 0.25];

      let pos = Math.floor(0.05 * RATE);

      segs.forEach(sg => {
        const len = Math.floor(sg.d * RATE);
        if (!sg.levels) { pos += len + Math.floor(gap * RATE); return; }

        const fm = vowelOf(sg.base);
        const noisy = FRICATIVE.test(sg.base.toLowerCase());
        const lv = sg.levels;
        let phase = 0;

        for (let i = 0; i < len && pos + i < n; i++) {
          const x = i / len;
          let level = lv[0];
          if (lv.length > 1) {
            const u = Math.min(1, Math.max(0, (x - 0.1) / 0.8)) * (lv.length - 1);
            const k = Math.min(lv.length - 2, Math.floor(u));
            level = lv[k] + (lv[k + 1] - lv[k]) * (u - k);
          }

          const f0 = freq(level);
          phase += (2 * Math.PI * f0) / RATE;

          let v = 0;
          const maxH = Math.min(28, Math.floor(4000 / f0));
          for (let h = 1; h <= maxH; h++) {
            const fh = f0 * h;
            let amp = 0;
            for (let j = 0; j < 3; j++) amp += fw[j] / (1 + Math.pow((fh - fm[j]) / bw[j], 2));
            v += (amp / Math.sqrt(h)) * Math.sin(h * phase);
          }

          const t = i / RATE;
          const env = Math.min(1, t / 0.025) * Math.min(1, (sg.d - t) / 0.06);
          let smp = v * env;
          if (noisy && t < 0.06) smp = smp * (t / 0.06) + (Math.random() * 2 - 1) * 0.3 * (1 - t / 0.06);

          buf[pos + i] += smp;
        }

        pos += len + Math.floor(gap * RATE);
      });

      let peak = 0;
      for (let i = 0; i < n; i++) peak = Math.max(peak, Math.abs(buf[i]));
      const g = peak ? 0.85 / peak : 1;

      const bytes = new Uint8Array(44 + n * 2);
      const dv = new DataView(bytes.buffer);
      const str = (o, t) => { for (let i = 0; i < t.length; i++) bytes[o + i] = t.charCodeAt(i); };

      str(0, "RIFF"); dv.setUint32(4, 36 + n * 2, true); str(8, "WAVE");
      str(12, "fmt "); dv.setUint32(16, 16, true); dv.setUint16(20, 1, true); dv.setUint16(22, 1, true);
      dv.setUint32(24, RATE, true); dv.setUint32(28, RATE * 2, true); dv.setUint16(32, 2, true); dv.setUint16(34, 16, true);
      str(36, "data"); dv.setUint32(40, n * 2, true);
      for (let i = 0; i < n; i++) dv.setInt16(44 + i * 2, Math.max(-1, Math.min(1, buf[i] * g)) * 32767, true);

      let bin = "";
      for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
      return "data:audio/wav;base64," + btoa(bin);
    }

    function stop() {
      if (player) { try { player.pause(); } catch (e) {} }
    }

    function play(lang, rom) {
      const list = syllables(lang, rom);
      if (!list.some(sy => sy.levels)) return false;
      Voice.stop();
      if (!player) player = new Audio();
      stop();
      player.src = render(list);
      const pr = player.play();
      if (pr && pr.catch) pr.catch(() => toast("Sound was blocked. Tap the button again."));
      return true;
    }

    return { play, stop, render, syllables };
  })();

  function sayVoice(text, lang) {
    Tones.stop();
    const r = Voice.speak(text, lang);
    if (r === "ok") return;
    const name = lang === "yue" ? "Cantonese (Hong Kong)" : "Chinese (China mainland)";
    toast(r === "missing"
      ? `No ${lang === "yue" ? "Cantonese" : "Mandarin"} voice on this device. On iPhone, add one in Settings › Accessibility › Spoken Content › Voices › ${name}.`
      : "This browser can't speak text. Try Safari or Chrome.");
  }

  function sayTones(lang, rom) {
    if (!Tones.play(lang, rom)) toast("There are no tones to play here.");
  }


  /* word card: what a tapped word means, and what grammar words do */

  const MEASURE = "Measure word. Chinese puts one between a number or 'this/that' and the noun, where English just says 'a' or 'the'.";

  const GRAMMAR = {
    yue: {
      "呀": "Softens a question or statement, like a friendly tone of voice. It has no English word.",
      "啊": "Softens a question or statement, like a friendly tone of voice.",
      "啦": "A friendly push at the end: \"let's\", \"go ahead\", \"come on\".",
      "喇": "Marks a change or something now done: \"now\", \"already\".",
      "囉": "\"That's how it is\", \"obviously\".",
      "㗎": "Adds emphasis, or asks about how something is or already happened.",
      "嘅": "Like English \"of\" or \"'s\". At the end of a sentence it describes what kind of thing or person.",
      "咗": "After a verb: the action is done, like English \"-ed\".",
      "緊": "After a verb: in the middle of doing it, like English \"-ing\".",
      "過": "After a verb: have ever done it.",
      "吓": "After a verb: do it a little or briefly (試吓 \"have a try\").",
      "啲": "\"Some\", or \"the\" for things you don't count. After an adjective it means \"a bit more\" (慢啲 \"slower\").",
      "得": "After a verb it links to how things turned out (瞓得好 \"slept well\"). It can also mean \"can\" (食得 \"can eat\").",
      "先": "At the end of a sentence: \"first\", before anything else.",
      "都": "\"Also\" or \"all\". Often needed with \"every\".",
      "未": "\"Not yet?\" at the end of a question.",
      "未呀": "\"Not yet?\" at the end of a question, softened with 呀.",
      "唔": "Not.",
      "冇": "Don't have, or there isn't.",
      "係": "Is, am, are.",
      "喺": "At, in.",
      "將": "Moves the object before the verb, like Mandarin 把.",
      "定": "\"Or\", in questions only.",
      "啫": "\"Only, just\".",
      "晒": "\"All, completely\" (恭喜晒 \"congratulations all round\").",
      "個": MEASURE + " 個 is the all-purpose one.",
    },
    cmn: {
      "吗": "Turns a statement into a yes/no question.",
      "吧": "\"Let's\", or softens a suggestion.",
      "了": "Marks a change or a finished action.",
      "的": "Like English \"of\" or \"'s\". At the end it describes how or when something happened.",
      "啊": "Softens a statement or exclamation.",
      "呢": "Softens a question, like \"then?\" or \"and?\".",
      "过": "After a verb: have ever done it.",
      "着": "After a verb: an ongoing state.",
      "得": "Links a verb to how well it went (睡得好 \"slept well\").",
      "把": "Moves the object before the verb. It's also a measure word for things with handles.",
      "在": "At, in. Before a verb it can mean \"in the middle of\".",
      "都": "\"Also\" or \"all\".",
      "就": "\"Then\", or \"right away\".",
      "还": "Still.",
      "也": "Also.",
      "个": MEASURE + " 个 is the all-purpose one.",
      "就像": "\"Just like\".",
      "来": "Before a verb it means \"let me\" or \"I'll\" (我来做 \"I'll do it\").",
    },
    tsn: {
      "啊": "Softens a question or statement, like Cantonese 呀.",
      "啦": "A friendly push or \"now, already\", like Cantonese 啦 and 喇.",
      "個": "Measure word, and also \"of\" or \"'s\", like Cantonese 嘅.",
      "得": "After a verb it links to how things turned out, or means \"can\", like Cantonese 得.",
      "尼": "\"Some\" or \"a bit\", like Cantonese 啲.",
      "唔曾": "\"Not yet, never\", like Cantonese 未.",
      "冇": "Don't have, or there isn't.",
      "還": "Still.",
      "都": "\"Also\" or \"all\".",
    },
  };

  const MEASURES = new Set("張件隻架部條對雙把間味舊本份首輪粒杯碗支枝座位艘张条双间块本份首轮粒".split(""));

  function grammarNote(lang, hz) {
    const g = GRAMMAR[lang] || {};
    if (g[hz]) return g[hz];
    if (hz.length === 1 && MEASURES.has(hz)) return MEASURE;
    if (hz.length > 1 && MEASURES.has(hz[0]) && hz.length <= 3) return `Starts with the measure word ${hz[0]}. ` + MEASURE;
    return null;
  }

  function showInfo(entry, tok) {
    const box = entry.info;
    if (!tok || !tok._tok) { box.hidden = true; box.innerHTML = ""; return; }

    const t = tok._tok;
    const lang = tok._lang;
    const p = entry.p;
    const means = (t.refs || []).map(r => p.gloss[r]).filter(Boolean);
    const gnote = grammarNote(lang, t.hz);

    const parts = [];
    if (means.length) parts.push(`<p><b>Means:</b> ${esc(means.join(" + "))}</p>`);
    if (gnote) parts.push(`<p>${esc(gnote)}</p>`);
    if (!means.length && !gnote) parts.push("<p>A grammar word with no direct English equivalent. It shapes the tone or structure of the sentence.</p>");
    if (t.sure === false) parts.push("<p>Not confirmed in this use, so check it with a native speaker.</p>");

    const kind = means.length ? NAMES[lang] : `${NAMES[lang]} · grammar word`;

    box.innerHTML = `<div class="wi-head"><span class="wi-hz ${lang === "cmn" ? "hz-cmn" : "hz-yue"}">${esc(t.hz)}</span><span class="wi-rom">${romHtml(lang, t.rom)}</span><span class="wi-kind">${esc(kind)}</span></div>${parts.join("")}<div class="plays"></div>`;

    const plays = box.querySelector(".plays");
    if (/[㐀-鿿]/.test(t.hz)) {
      if (lang !== "tsn") {
        const b = el("button", "pbtn", `${speaker}Listen`);
        b.type = "button";
        b.addEventListener("click", () => sayVoice(t.hz, lang));
        plays.appendChild(b);
      }
      const h = el("button", "pbtn", `${wave}Tones`);
      h.type = "button";
      h.addEventListener("click", () => sayTones(lang, t.rom));
      plays.appendChild(h);
    }

    box.hidden = false;
  }