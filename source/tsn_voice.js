  /* Taishanese voice: a source-filter speech synthesizer for Stephen Li romanization */

  const TsnVoice = (() => {
    const SR = 22050;
    let VG = 1, AG = 0.55, FG = 3.2;
    const FR = 200;
    const FS = 1.08;

    const V = {
      i: [300, 2300, 3000], e: [440, 2050, 2750], "ɛ": [570, 1850, 2650], a: [820, 1320, 2650],
      "ɔ": [600, 950, 2550], o: [470, 860, 2500], u: [330, 760, 2400], "ə": [520, 1380, 2550],
      y: [300, 1950, 2450], m: [260, 1000, 2300], n: [260, 1650, 2600], "ŋ": [260, 1300, 2300],
    };

    const TONES = {
      "55": [5, 5], "33": [3, 3], "22": [2, 2], "32": [3, 2], "21": [2, 1], "31": [3, 1],
      "335": [3, 3, 5], "215": [2, 1, 5], "325": [3, 2, 5], "225": [2, 2, 5], "553": [5, 5, 3],
      "44": [4, 4], "35": [3, 5], "5": [5, 5], "3": [3, 3], "2": [2, 2], "333": [3, 3], "321": [3, 2, 1],
    };

    const STOP = { b: "lab", d: "alv", g: "vel", p: "lab", t: "alv", k: "vel" };
    const ASP = { p: 1, t: 1, k: 1, ts: 1 };

    function parse(raw) {
      let s = String(raw || "").toLowerCase().replace(/^[?ʔ]/, "").replace(/ng/g, "ŋ").replace(/[*()]/g, "");
      const tm = s.match(/(\d+)$/);
      const tone = tm ? tm[1] : "33";
      s = s.replace(/\d+$/, "");
      const im = s.match(/^(ts|dz|ɬ|ŋ|[bpmfdtnlgkhvysz])/);
      let ini = im ? im[1] : "";
      let fin = s.slice(ini.length);
      if (!fin && (ini === "m" || ini === "ŋ")) { fin = ini; ini = ""; }
      if (ini === "y" && !/^i/.test(fin)) fin = "i" + fin;
      if (ini === "y") ini = "";
      if (ini === "z") ini = "dz";

      let coda = "";
      const cm = fin.match(/(m|n|ŋ|p|t|k)$/);
      if (cm && fin.length > 1) { coda = cm[1]; fin = fin.slice(0, -1); }

      const vs = [...fin.replace(/ei/g, "e").replace(/ii/g, "i").replace(/[^aeiouɔəɛy]/g, "")];
      if (!vs.length) vs.push(fin === "m" ? "m" : fin === "ŋ" ? "ŋ" : "ə");

      const levels = TONES[tone] || (tone.length >= 2 ? [...tone].map(Number) : [3, 3]);
      return { ini, vs, coda, levels, tone };
    }

    const fmt = v => (V[v] || V["ə"]).map(f => f * FS);

    function locus(place, f2v) {
      if (place === "lab") return [250, 900 * FS, 2200 * FS];
      if (place === "alv") return [260, 1750 * FS, 2750 * FS];
      return [260, (f2v > 1500 * FS ? 2350 : 1250) * FS, 2050 * FS];
    }

    const placeOf = c => STOP[c] || { m: "lab", n: "alv", "ŋ": "vel", l: "alv", s: "alv", "ɬ": "alv", ts: "alv", dz: "alv", f: "lab", v: "lab" }[c] || null;

    /* build a frame track of parameters for a list of syllables */

    function plan(list, rate) {
      const k = 0.8 / (rate || 1);
      const frames = [];
      let t = 0;

      const key = [];
      const push = (time, p) => key.push({ time, ...p });

      const pitchKeys = [];
      const lvHz = lv => 168 * Math.pow(2, ((lv - 1) * 2.45) / 12);

      push(0, { av: 0, ah: 0, af: 0, f: fmt("ə"), nas: 0, fric: null });
      t = 0.06;

      list.forEach((sy, si) => {
        const last = si === list.length - 1;
        const checked = /[ptk]/.test(sy.coda);
        const rising = sy.levels.length === 3;
        let stretch = k * (last ? 1.22 : 1) * (rising ? 1.18 : 1);

        const first = fmt(sy.vs[0]);
        const lastV = fmt(sy.vs[sy.vs.length - 1]);
        const place = placeOf(sy.ini);
        const lo = place ? locus(place, first[1]) : first;
        const onset = [lo[0], (lo[1] + first[1]) / 2, (lo[2] + first[2]) / 2];

        const c = sy.ini;
        let voiceStart;

        if (STOP[c] || c === "ts" || c === "dz") {
          push(t, { av: 0, ah: 0, af: 0, f: onset, nas: 0, fric: null });
          t += (si ? 0.035 : 0.02) * stretch;
          push(t, { av: 0, ah: 0, af: 0, f: onset, nas: 0, fric: null });
          const burst = c === "ts" || c === "dz" ? "alv" : STOP[c];
          push(t + 0.001, { av: 0, ah: 0, af: 1, f: onset, nas: 0, fric: "b-" + burst + (burst === "vel" ? (first[1] > 1500 * FS ? "f" : "b") : "") });
          t += 0.012 * stretch;
          if (c === "dz" || c === "ts") {
            push(t, { av: 0, ah: 0, af: 0.7, f: onset, nas: 0, fric: "s" });
            t += (c === "ts" ? 0.075 : 0.055) * stretch;
            push(t, { av: 0, ah: 0, af: 0.55, f: onset, nas: 0, fric: "s" });
          }
          if (ASP[c]) {
            push(t + 0.002, { av: 0, ah: 0.55, af: 0, f: onset, nas: 0, fric: null });
            t += 0.06 * stretch;
            push(t, { av: 0, ah: 0.4, af: 0, f: [first[0] * 0.8, first[1], first[2]], nas: 0, fric: null });
          } else {
            push(t + 0.002, { av: 0, ah: 0.25, af: 0, f: onset, nas: 0, fric: null });
            t += 0.012 * stretch;
          }
          voiceStart = t;
          push(t + 0.004, { av: 0.6, ah: 0.06, af: 0, f: onset, nas: 0, fric: null });
        } else if (c === "s" || c === "ɬ" || c === "f") {
          const amp = c === "f" ? 0.4 : c === "ɬ" ? 0.5 : 0.8;
          push(t, { av: 0, ah: 0, af: 0, f: onset, nas: 0, fric: c });
          push(t + 0.025 * stretch, { av: 0, ah: 0, af: amp, f: onset, nas: 0, fric: c });
          t += (c === "f" ? 0.085 : 0.1) * stretch;
          push(t, { av: 0, ah: 0, af: amp * 0.85, f: onset, nas: 0, fric: c });
          voiceStart = t + 0.01 * stretch;
          push(voiceStart, { av: 0.55, ah: 0.05, af: 0, f: onset, nas: 0, fric: null });
        } else if (c === "h") {
          push(t, { av: 0, ah: 0, af: 0, f: first, nas: 0, fric: null });
          push(t + 0.02 * stretch, { av: 0, ah: 0.5, af: 0, f: first, nas: 0, fric: null });
          t += 0.075 * stretch;
          push(t, { av: 0, ah: 0.4, af: 0, f: first, nas: 0, fric: null });
          voiceStart = t;
          push(t + 0.012 * stretch, { av: 0.7, ah: 0.08, af: 0, f: first, nas: 0, fric: null });
        } else if (c === "m" || c === "n" || c === "ŋ") {
          if (si > 0) { push(t, { av: 0.15, ah: 0, af: 0, f: fmt(c), nas: 1, fric: null }); }
          voiceStart = t;
          push(t + 0.01, { av: 0.42, ah: 0, af: 0, f: fmt(c), nas: 1, fric: null });
          t += 0.06 * stretch;
          push(t, { av: 0.45, ah: 0, af: 0, f: fmt(c), nas: 1, fric: null });
          push(t + 0.012, { av: 0.75, ah: 0, af: 0, f: onset, nas: 0.25, fric: null });
        } else if (c === "l") {
          voiceStart = t;
          push(t + 0.01, { av: 0.5, ah: 0, af: 0, f: [360 * FS, 1150 * FS, 2850 * FS], nas: 0, fric: null, lat: 1 });
          t += 0.06 * stretch;
          push(t, { av: 0.55, ah: 0, af: 0, f: [360 * FS, 1200 * FS, 2850 * FS], nas: 0, fric: null, lat: 1 });
        } else if (c === "v") {
          voiceStart = t;
          push(t + 0.01, { av: 0.45, ah: 0, af: 0.08, f: [300 * FS, 1000 * FS, 2300 * FS], nas: 0, fric: "f" });
          t += 0.055 * stretch;
          push(t, { av: 0.5, ah: 0, af: 0.05, f: [320 * FS, 1050 * FS, 2350 * FS], nas: 0, fric: "f" });
        } else {
          voiceStart = t;
          push(t, { av: 0, ah: 0.05, af: 0, f: first, nas: 0, fric: null });
          push(t + 0.025 * stretch, { av: 0.8, ah: 0.04, af: 0, f: first, nas: 0, fric: null });
        }

        const nasalCoda = /[mnŋ]/.test(sy.coda);
        let vowelDur = (checked ? 0.115 : nasalCoda ? 0.15 : 0.2) * stretch;
        if (sy.vs.length > 1) vowelDur *= 1.12;

        const n = sy.vs.length;
        const shares = sy.vs.map((v, i) => {
          if (n === 1) return 1;
          if (i === 0 && (v === "i" || v === "u") && n > 1 && !(n === 2 && i === 0 && (sy.vs[1] === "i" || sy.vs[1] === "u"))) return 0.22;
          if (i === n - 1 && (v === "i" || v === "u")) return 0.38;
          return 1;
        });
        const sum = shares.reduce((a, b) => a + b, 0);

        let vt = t;
        sy.vs.forEach((v, i) => {
          const d = vowelDur * shares[i] / sum;
          const f = fmt(v);
          const glide = shares[i] < 1;
          push(vt + d * (glide ? 0.5 : 0.35), { av: 1, ah: 0.04, af: 0, f, nas: 0, fric: null });
          if (!glide) push(vt + d * 0.75, { av: 1, ah: 0.04, af: 0, f, nas: 0, fric: null });
          vt += d;
        });
        t = vt;

        if (nasalCoda) {
          const mf = fmt(sy.coda);
          push(t, { av: 0.85, ah: 0.02, af: 0, f: locus(placeOf(sy.coda), lastV[1]).map((x, i) => (x + lastV[i]) / 2), nas: 0.5, fric: null });
          push(t + 0.015 * stretch, { av: 0.48, ah: 0, af: 0, f: mf, nas: 1, fric: null });
          t += (last ? 0.12 : 0.085) * stretch;
          push(t, { av: 0.35, ah: 0, af: 0, f: mf, nas: 1, fric: null });
          pitchKeys.push({ a: voiceStart, b: t, levels: sy.levels });
          push(t + 0.025 * stretch, { av: 0, ah: 0, af: 0, f: mf, nas: 1, fric: null });
          t += 0.02 * stretch;
        } else if (checked) {
          const lf = locus(placeOf(sy.coda), lastV[1]);
          t += 0.03 * stretch;
          push(t, { av: 0.8, ah: 0.02, af: 0, f: [lf[0] + 120, lf[1], lf[2]], nas: 0, fric: null });
          pitchKeys.push({ a: voiceStart, b: t, levels: sy.levels });
          push(t + 0.008, { av: 0, ah: 0, af: 0, f: lf, nas: 0, fric: null });
          t += 0.06 * stretch;
          push(t, { av: 0, ah: 0, af: 0, f: lf, nas: 0, fric: null });
        } else {
          pitchKeys.push({ a: voiceStart, b: t + 0.03 * stretch, levels: sy.levels });
          push(t + 0.03 * stretch, { av: last ? 0.55 : 0.75, ah: 0.06, af: 0, f: lastV, nas: 0, fric: null });
          t += (last ? 0.09 : 0.045) * stretch;
          push(t, { av: last ? 0 : 0.3, ah: last ? 0.02 : 0.04, af: 0, f: lastV, nas: 0, fric: null });
          if (!last) t += 0.02 * stretch;
        }
      });

      t += 0.08;
      push(t, { av: 0, ah: 0, af: 0, f: fmt("ə"), nas: 0, fric: null });

      key.sort((a, b) => a.time - b.time);

      const total = t;
      const nf = Math.ceil(total * FR) + 1;
      let j = 0;
      for (let i = 0; i < nf; i++) {
        const time = i / FR;
        while (j < key.length - 2 && key[j + 1].time <= time) j++;
        const A = key[j], B = key[Math.min(j + 1, key.length - 1)];
        const span = Math.max(1e-6, B.time - A.time);
        const x = Math.max(0, Math.min(1, (time - A.time) / span));
        const mix = (a, b) => a + (b - a) * x;
        frames.push({
          av: mix(A.av, B.av), ah: mix(A.ah, B.ah), af: mix(A.af, B.af),
          f: [0, 1, 2].map(q => mix(A.f[q], B.f[q])),
          nas: mix(A.nas, B.nas), lat: mix(A.lat || 0, B.lat || 0),
          fric: x < 0.5 ? (A.fric || B.fric) : (B.fric || A.fric),
          f0: 0,
        });
      }

      const smooth = (get, set, a) => {
        let y = get(frames[0]);
        frames.forEach(fr => { y += (get(fr) - y) * a; set(fr, y); });
      };
      for (let q = 0; q < 3; q++) smooth(fr => fr.f[q], (fr, y) => { fr.f[q] = y; }, 0.45);

      const f0 = new Float32Array(nf);
      const dec = lvHz(1) * 0;
      pitchKeys.forEach((pk, pi) => {
        const a = Math.floor(pk.a * FR), b = Math.ceil(pk.b * FR);
        const L = pk.levels;
        for (let i = a; i <= b && i < nf; i++) {
          const x = Math.max(0, Math.min(1, (i - a) / Math.max(1, b - a)));
          const u = Math.min(1, Math.max(0, (x - 0.08) / 0.84)) * (L.length - 1);
          const q = Math.min(L.length - 2, Math.floor(u));
          const w = u - q;
          const ease = w * w * (3 - 2 * w);
          const lv = L.length === 1 ? L[0] : L[q] + (L[q + 1] - L[q]) * ease;
          const decl = 1 - 0.035 * (pi / Math.max(1, pitchKeys.length));
          f0[i] = lvHz(lv) * decl + dec;
        }
      });

      let prev = lvHz(3);
      for (let i = 0; i < nf; i++) {
        if (f0[i] > 0) prev = f0[i];
        else {
          let nx = i;
          while (nx < nf && !(f0[nx] > 0)) nx++;
          f0[i] = nx < nf ? f0[nx] : prev;
        }
      }
      let y = f0[0];
      for (let i = 0; i < nf; i++) { y += (f0[i] - y) * 0.55; frames[i].f0 = y; }

      return { frames, total };
    }

    /* two-pole resonator and antiresonator (Klatt 1980) */

    function Res() { this.y1 = 0; this.y2 = 0; this.a = 0; this.b = 0; this.c = 0; }
    Res.prototype.set = function (f, bw) {
      const T = 1 / SR;
      const c = -Math.exp(-2 * Math.PI * bw * T);
      const b = 2 * Math.exp(-Math.PI * bw * T) * Math.cos(2 * Math.PI * f * T);
      this.a = 1 - b - c; this.b = b; this.c = c;
    };
    Res.prototype.run = function (x) {
      const y = this.a * x + this.b * this.y1 + this.c * this.y2;
      this.y2 = this.y1; this.y1 = y;
      return y;
    };

    function BP() { this.x1 = 0; this.x2 = 0; this.y1 = 0; this.y2 = 0; }
    BP.prototype.set = function (f, bw) {
      const w = 2 * Math.PI * Math.min(f, SR * 0.45) / SR;
      const q = Math.max(0.3, f / bw);
      const al = Math.sin(w) / (2 * q);
      const a0 = 1 + al;
      this.b0 = al / a0; this.b2 = -al / a0; this.a1 = -2 * Math.cos(w) / a0; this.a2 = (1 - al) / a0;
    };
    BP.prototype.run = function (x) {
      const y = this.b0 * x + this.b2 * this.x2 - this.a1 * this.y1 - this.a2 * this.y2;
      this.x2 = this.x1; this.x1 = x; this.y2 = this.y1; this.y1 = y;
      return y;
    };

    function Anti() { this.x1 = 0; this.x2 = 0; this.a = 1; this.b = 0; this.c = 0; }
    Anti.prototype.set = function (f, bw) {
      const T = 1 / SR;
      const c0 = -Math.exp(-2 * Math.PI * bw * T);
      const b0 = 2 * Math.exp(-Math.PI * bw * T) * Math.cos(2 * Math.PI * f * T);
      const a0 = 1 - b0 - c0;
      this.a = 1 / a0; this.b = -b0 / a0; this.c = -c0 / a0;
    };
    Anti.prototype.run = function (x) {
      const y = this.a * x + this.b * this.x1 + this.c * this.x2;
      this.x2 = this.x1; this.x1 = x;
      return y;
    };

    const FRIC = {
      s: [[6200, 1800, 1], [4200, 1500, 0.35]],
      "ɬ": [[3300, 1900, 0.8], [5600, 2600, 0.6], [1400, 500, 0.12]],
      f: [[7000, 4000, 0.6], [2500, 3000, 0.25]],
      "b-lab": [[900, 1400, 0.5], [3000, 3000, 0.15]],
      "b-alv": [[4200, 1800, 1], [2800, 1200, 0.4]],
      "b-velf": [[2500, 700, 1], [4000, 2000, 0.3]],
      "b-velb": [[1500, 600, 1], [3200, 2000, 0.25]],
    };

    function synth(rom, rate) {
      const list = String(rom || "").split(/\s+/).filter(Boolean).map(parse);
      if (!list.length) return null;

      const { frames, total } = plan(list, rate);
      const n = Math.ceil(total * SR);
      const out = new Float32Array(n);

      const R = [new Res(), new Res(), new Res(), new Res(), new Res()];
      const NP = new Res(), NZ = new Anti();
      const tilt = new Res();
      tilt.set(0, 900);
      const fr = {};
      ["s", "ɬ", "f", "b-lab", "b-alv", "b-velf", "b-velb"].forEach(k => { fr[k] = FRIC[k].map(() => new BP()); fr[k].forEach((r, i) => r.set(FRIC[k][i][0], FRIC[k][i][1])); });

      let phase = 0, seed = 22222;
      const noise = () => { seed = (seed * 1103515245 + 12345) & 0x7fffffff; return seed / 0x3fffffff - 1; };
      let jit = 1, lastPrev = 0, hp = 0;
      let open = 0.62;

      for (let i = 0; i < n; i++) {
        const fpos = i / SR * FR;
        const a = Math.min(frames.length - 1, Math.floor(fpos));
        const b = Math.min(frames.length - 1, a + 1);
        const x = fpos - a;
        const A = frames[a], B = frames[b];
        const L = (p, q) => p + (q - p) * x;

        if (i % 32 === 0) {
          const F = [L(A.f[0], B.f[0]), L(A.f[1], B.f[1]), L(A.f[2], B.f[2])];
          const nas = L(A.nas, B.nas);
          const lat = L(A.lat, B.lat);
          R[0].set(F[0], 70 + 120 * nas);
          R[1].set(F[1], 90 + 160 * nas + 120 * lat);
          R[2].set(F[2], 150 + 140 * nas);
          R[3].set(3700 * FS, 260);
          R[4].set(4600 * FS, 320);
          NP.set(270, 100);
          NZ.set(270 + (1 - nas) * 1, 100 + nas * 0);
          if (nas > 0.02) NZ.set(450 + (1 - nas) * 200, 110);
          else NZ.set(270, 100);
        }

        const f0 = L(A.f0, B.f0) * jit;
        phase += f0 / SR;
        let pulse = 0;
        if (phase >= 1) { phase -= 1; jit = 1 + noise() * 0.006; }
        if (phase < open) {
          const u = phase / open;
          pulse = 2 * u - 3 * u * u;
        }
        const g = pulse - 0.5 * tilt.run(pulse);

        const av = L(A.av, B.av);
        const ah = L(A.ah, B.ah);
        const af = L(A.af, B.af);
        const nz = noise();
        const breath = nz * (phase < open ? 1 : 0.4);

        let src = av * g * VG + ah * breath * AG;
        const nas = L(A.nas, B.nas);
        if (nas > 0.02) src = NZ.run(NP.run(src));

        let y = src;
        for (let q = 0; q < 5; q++) y = R[q].run(y);
        if (nas > 0.6) y *= 1 - (nas - 0.6) * 0.8;

        const fk = x < 0.5 ? (A.fric || B.fric) : (B.fric || A.fric);
        if (af > 0.001 && fk && fr[fk]) {
          let fy = 0;
          fr[fk].forEach((r, k) => { fy += r.run(nz) * FRIC[fk][k][2]; });
          y += fy * af * FG;
        }

        hp = 0.995 * (hp + y - lastPrev);
        lastPrev = y;
        out[i] = hp;
      }

      let peak = 0;
      for (let i = 0; i < n; i++) peak = Math.max(peak, Math.abs(out[i]));
      if (peak) for (let i = 0; i < n; i++) out[i] = out[i] / peak * 0.88;
      return out;
    }

    function wav(buf) {
      const n = buf.length;
      const bytes = new Uint8Array(44 + n * 2);
      const dv = new DataView(bytes.buffer);
      const str = (o, t) => { for (let i = 0; i < t.length; i++) bytes[o + i] = t.charCodeAt(i); };
      str(0, "RIFF"); dv.setUint32(4, 36 + n * 2, true); str(8, "WAVE");
      str(12, "fmt "); dv.setUint32(16, 16, true); dv.setUint16(20, 1, true); dv.setUint16(22, 1, true);
      dv.setUint32(24, SR, true); dv.setUint32(28, SR * 2, true); dv.setUint16(32, 2, true); dv.setUint16(34, 16, true);
      str(36, "data"); dv.setUint32(40, n * 2, true);
      for (let i = 0; i < n; i++) dv.setInt16(44 + i * 2, Math.max(-1, Math.min(1, buf[i])) * 32767, true);
      return bytes;
    }

    function dataUri(rom, rate) {
      const buf = synth(rom, rate);
      if (!buf) return null;
      const bytes = wav(buf);
      let bin = "";
      for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
      return "data:audio/wav;base64," + btoa(bin);
    }

    const gains = (v, a, f) => { VG = v; AG = a; FG = f; };

    return { SR, parse, synth, wav, dataUri, gains };
  })();

  if (typeof module !== "undefined") module.exports = TsnVoice;
