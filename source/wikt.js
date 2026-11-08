  /* Wiktionary word origins and Tatoeba example sentences, fetched on tap */

  const Lookup = (() => {

    const WK = "https://en.wiktionary.org/w/api.php";
    const TB = "https://api.tatoeba.org/v1/sentences";

    const WK_LANG = {
      tsn: ["Chinese"], yue: ["Chinese"], cmn: ["Chinese"], en: ["English"],
      es: ["Spanish"], pt: ["Portuguese"], fr: ["French"], de: ["German"],
      fa: ["Persian"], apc: ["North Levantine Arabic", "South Levantine Arabic", "Arabic"],
      he: ["Hebrew"], tr: ["Turkish"],
    };

    const TB_LANG = { en: "eng", yue: "yue", cmn: "cmn", es: "spa", pt: "por", fr: "fra", de: "deu", fa: "pes", apc: "apc", he: "heb", tr: "tur" };

    const ZH = /[⺀-⿟㐀-鿿]/;
    const MAX = 700;


    function timed(url, ms = 9000) {
      const ac = typeof AbortController !== "undefined" ? new AbortController() : null;
      const t = ac ? setTimeout(() => ac.abort(), ms) : 0;
      return fetch(url, ac ? { signal: ac.signal } : {}).finally(() => clearTimeout(t));
    }

    async function getJson(url) {
      const r = await timed(url);
      if (!r.ok) throw new Error(String(r.status));
      return r.json();
    }

    function cached(key, make, keep) {
      const hit = store.get(key);
      if (hit) { try { return Promise.resolve(JSON.parse(hit)); } catch (e) {} }
      return make().then(v => { if (keep(v)) store.set(key, JSON.stringify(v)); return v; });
    }


    /* sound + meaning over every Chinese character, in the lane's own sounds */

    function ruby(html, lang) {
      if (lang !== "cmn" || typeof GT === "undefined") return zhRuby(html);
      const m = GT.py();
      const g = zhMeanings();
      return String(html).split(/(<[^>]+>)/).map(part => part.startsWith("<") ? part : part.replace(/[⺀-⿟㐀-鿿]/g, c => {
        const snd = m.has(c) ? esc(romText("cmn", m.get(c))) : "";
        const mean = g.has(c) ? esc(g.get(c)) : "";
        if (!snd && !mean) return c;
        return `<span class="zg"><small class="zs">${snd || "&nbsp;"}</small><b>${c}</b><small class="zm">${mean || "&nbsp;"}</small></span>`;
      })).join("");
    }


    /* Wiktionary */

    const wkUrl = q => WK + "?" + new URLSearchParams({ action: "parse", format: "json", formatversion: "2", redirects: "1", origin: "*", ...q });

    function clean(word, lang) {
      let w = String(word || "").replace(/[.,!?¿¡;:"“”«»()،؟]/g, "").trim();
      if (lang === "apc" || lang === "fa") w = w.replace(/[ً-ْٰ]/g, "");
      if (lang === "he") w = w.replace(/[֑-ׇ]/g, "");
      return w;
    }

    function candidates(word, lang) {
      const w = clean(word, lang);
      const out = [w];
      if (w.toLowerCase() !== w) out.push(w.toLowerCase());
      const parts = w.split(/\s+/).filter(x => x.length > 1);
      if (parts.length > 1) parts.slice().sort((a, b) => b.length - a.length).slice(0, 2).forEach(x => out.push(x, x.toLowerCase()));
      return [...new Set(out)].filter(Boolean);
    }

    function textOf(html) {
      const doc = new DOMParser().parseFromString(`<div>${html}</div>`, "text/html");
      const root = doc.querySelector(".mw-parser-output") || doc.body.firstElementChild;
      root.querySelectorAll(".mw-editsection, sup, style, script, table, figure, .thumb, .gallery, .NavFrame, .maintenance-box, .request-box, .checksense, .mw-empty-elt").forEach(n => n.remove());
      const isHead = n => /^H[1-6]$/.test(n.tagName) || (n.classList && n.classList.contains("mw-heading"));
      const out = [];
      let started = false;
      for (const n of root.children) {
        if (isHead(n)) { if (started) break; started = true; continue; }
        started = true;
        if (/^(P|UL|OL|DL)$/.test(n.tagName)) {
          const items = n.tagName === "P" ? [n] : [...n.children];
          items.forEach(x => { const t = x.textContent.replace(/\s+/g, " ").trim(); if (t) out.push(t); });
        }
      }
      return out;
    }

    function seeTarget(html) {
      const doc = new DOMParser().parseFromString(`<div>${html}</div>`, "text/html");
      for (const n of doc.querySelectorAll("p, div, td, span")) {
        if (!/For pronunciation and definitions of/i.test(n.textContent)) continue;
        const a = [...n.querySelectorAll("a[title]")].find(x => ZH.test(x.getAttribute("title")));
        if (a) return a.getAttribute("title").replace(/#.*/, "");
      }
      return null;
    }

    async function sectionsFor(page, heads) {
      const j = await getJson(wkUrl({ page, prop: "sections" }));
      if (j.error || !j.parse) return null;
      const secs = j.parse.sections || [];
      const plain = s => String(s.line || "").replace(/<[^>]+>/g, "").trim();
      let at = -1;
      for (const h of heads) { at = secs.findIndex(s => s.toclevel === 1 && plain(s) === h); if (at >= 0) break; }
      if (at < 0) return null;
      const lang = secs[at];
      const mine = [];
      for (let i = at + 1; i < secs.length && secs[i].toclevel > 1; i++) mine.push(secs[i]);
      const want = mine.filter(s => /^(Etymology|Glyph origin)/.test(plain(s)) && /^\d+$/.test(String(s.index)));
      return { title: j.parse.title, lang, want, plain };
    }

    async function originOf(page, heads, hop = 0) {
      const s = await sectionsFor(page, heads);
      if (!s) return null;
      const blocks = [];
      for (const sec of s.want.slice(0, 3)) {
        const j = await getJson(wkUrl({ page: s.title, section: sec.index, prop: "text", disabletoc: "1" }));
        const lines = j.parse ? textOf(j.parse.text) : [];
        if (lines.length) blocks.push({ head: s.plain(sec), lines });
      }
      if (!blocks.length && heads[0] === "Chinese" && hop === 0 && /^\d+$/.test(String(s.lang.index))) {
        const j = await getJson(wkUrl({ page: s.title, section: s.lang.index, prop: "text", disabletoc: "1" }));
        const to = j.parse && seeTarget(j.parse.text);
        if (to && to !== s.title) return originOf(to, heads, 1);
      }
      return { title: s.title, blocks };
    }

    async function origin(word, lang) {
      const heads = WK_LANG[lang] || ["English"];
      return cached("polygrok-wk-" + lang + "-" + word, async () => {
        for (const c of candidates(word, lang)) {
          const o = await originOf(c, heads);
          if (o && o.blocks.length) return o;
        }
        const chars = [...clean(word, lang)].filter(c => ZH.test(c));
        if (chars.length > 1) {
          const blocks = [];
          for (const c of [...new Set(chars)].slice(0, 4)) {
            const o = await originOf(c, heads);
            if (o && o.blocks.length) blocks.push({ head: c, lines: o.blocks[0].lines.slice(0, 1), page: o.title });
          }
          if (blocks.length) return { title: clean(word, lang), blocks, perChar: true };
        }
        return { title: clean(word, lang), blocks: [] };
      }, o => o.blocks.length > 0);
    }


    /* Tatoeba */

    function flat(x, out = []) {
      if (Array.isArray(x)) x.forEach(y => flat(y, out));
      else if (x && typeof x === "object" && x.text) out.push(x);
      return out;
    }

    function parseTb(j) {
      const rows = j.data || j.results || [];
      return rows.map(s => ({
        id: s.id, text: s.text, owner: s.owner && (s.owner.username || s.owner) || s.user && s.user.username || "",
        license: s.license || "CC BY 2.0 FR",
        en: flat(s.translations).filter(t => t.lang === "eng").map(t => t.text)[0] || "",
      })).filter(s => s.text);
    }

    async function examples(word, lang) {
      const L = TB_LANG[lang];
      const q = clean(word, lang);
      return cached("polygrok-tb-" + lang + "-" + q, async () => {
        const qs = new URLSearchParams({ lang: L, q, "trans:lang": "eng", sort: "words" });
        let j = null;
        try { j = await getJson(TB + "?" + qs); }
        catch (e) {
          if (typeof GT_PROXY === "undefined" || !GT_PROXY) throw e;
          j = await getJson(GT_PROXY.replace(/\/+$/, "") + "/tatoeba?" + new URLSearchParams({ lang: L, q }));
        }
        return parseTb(j).filter(s => s.en).slice(0, 6);
      }, rows => rows.length > 0);
    }


    /* panel */

    function render(out, html) {
      out.innerHTML = html;
      out.hidden = false;
    }

    function wkHtml(o, lang) {
      const link = t => `https://en.wiktionary.org/wiki/${encodeURIComponent(t)}`;
      if (!o.blocks.length) return `<p>${esc(tr("wk_none"))} <a href="${link(o.title)}" target="_blank" rel="noopener">${esc(tr("wk_more"))}</a></p>`;
      const body = o.blocks.map(b => {
        let t = b.lines.join(" ");
        const cut = t.length > MAX;
        if (cut) t = t.slice(0, MAX).replace(/\s+\S*$/, "") + "…";
        const head = o.perChar ? `<b class="${lang === "cmn" ? "hz-cmn" : "hz-yue"}">${ruby(esc(b.head), lang)}</b>` : `<b>${esc(b.head)}</b>`;
        return `<div class="lk-b">${head}<p>${ruby(esc(t), lang)}</p></div>`;
      }).join("");
      return `<div class="label">${esc(tr("wk_h"))}</div>${body}<p class="lk-src"><a href="${link(o.title)}" target="_blank" rel="noopener">${esc(tr("wk_more"))}</a> · ${esc(tr("wk_lic"))}</p>`;
    }

    function tbHtml(rows, lang, word) {
      const search = `https://tatoeba.org/en/sentences/search?from=${TB_LANG[lang]}&to=eng&query=${encodeURIComponent(clean(word, lang))}`;
      if (!rows.length) return `<p>${esc(tr("tb_none"))} <a href="${search}" target="_blank" rel="noopener">${esc(tr("tb_more"))}</a></p>`;
      const zh = lang === "yue" || lang === "cmn";
      const rtl = RTL.has(lang);
      const body = rows.map((s, i) => `<div class="lk-ex" data-i="${i}">
        <div class="lk-ex-t ${zh ? (lang === "cmn" ? "hz-cmn" : "hz-yue") : ""}"${rtl ? ` dir="rtl" lang="${HTML_LANG[lang]}"` : ""}>${zh ? ruby(esc(s.text), lang) : esc(s.text)}</div>
        <div class="lk-ex-en">${esc(s.en)}</div>
        <div class="lk-ex-by"><a href="https://tatoeba.org/en/sentences/show/${encodeURIComponent(s.id)}" target="_blank" rel="noopener">#${esc(s.id)}</a>${s.owner ? " · " + esc(s.owner) : ""}</div>
      </div>`).join("");
      return `<div class="label">${esc(tr("tb_h"))}</div>${body}<p class="lk-src"><a href="${search}" target="_blank" rel="noopener">${esc(tr("tb_more"))}</a> · ${esc(tr("tb_lic"))}</p>`;
    }

    function panel(lang, word) {
      const wrap = el("div", "lookup");
      const row = el("div", "plays");
      const out = el("div", "lk-out");
      out.hidden = true;
      wrap.addEventListener("click", e => e.stopPropagation());

      const wb = el("button", "pbtn", `${icon("book")}${esc(tr("wk_btn"))}`);
      wb.type = "button";
      wb.addEventListener("click", () => {
        render(out, `<p class="pr-hint">…</p>`);
        origin(word, lang)
          .then(o => render(out, wkHtml(o, lang)))
          .catch(e => render(out, `<p>${esc(tr("wk_fail"))}</p>`));
      });
      row.appendChild(wb);

      if (TB_LANG[lang]) {
        const tb = el("button", "pbtn", `${icon("chat")}${esc(tr("tb_btn"))}`);
        tb.type = "button";
        tb.addEventListener("click", () => {
          render(out, `<p class="pr-hint">…</p>`);
          examples(word, lang)
            .then(rows => {
              render(out, tbHtml(rows, lang, word));
              out.querySelectorAll(".lk-ex").forEach(n => {
                const s = rows[+n.dataset.i];
                const b = el("button", "lp", speaker);
                b.type = "button";
                b.setAttribute("aria-label", tr("listen"));
                b.addEventListener("click", () => sayVoice(s.text, lang));
                n.appendChild(b);
              });
            })
            .catch(e => render(out, `<p>${esc(tr("tb_fail"))}</p>`));
        });
        row.appendChild(tb);
      }

      wrap.appendChild(row);
      wrap.appendChild(out);
      return wrap;
    }

    return { panel, origin, examples };
  })();
