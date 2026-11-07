/* Polylang translate proxy: holds the Google key so the website never has to. */

const TARGETS = new Set(["yue", "zh-CN", "zh-TW", "es", "pt", "fr", "de", "fa", "ar", "he", "tr"]);

const MAX_CHARS = 300;

const ALLOWED = [
  /^https:\/\/jakesauter\.github\.io$/,
  /^https:\/\/[a-z0-9-]+\.claudeusercontent\.com$/,
  /^http:\/\/localhost(:\d+)?$/,
];


function cors(origin) {
  const ok = ALLOWED.some(r => r.test(origin || ""));
  return ok ? {
    "Access-Control-Allow-Origin": origin,
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Max-Age": "86400",
    "Vary": "Origin",
  } : null;
}


function reply(status, body, headers) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8", ...(headers || {}) },
  });
}


async function google(q, target, key) {
  const r = await fetch("https://translation.googleapis.com/language/translate/v2?key=" + encodeURIComponent(key), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ q, source: "en", target, format: "text" }),
  });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) {
    const msg = (j.error && j.error.message) || "Google error " + r.status;
    return { error: msg, quota: r.status === 403 && /limit|quota/i.test(msg), status: r.status };
  }
  return { text: j.data.translations[0].translatedText };
}


export default {
  async fetch(request, env, ctx) {
    const origin = request.headers.get("Origin") || "";
    const h = cors(origin);

    if (request.method === "OPTIONS") return new Response(null, { status: h ? 204 : 403, headers: h || {} });
    if (!h) return reply(403, { error: "This translator only works from Polylang." });

    const url = new URL(request.url);
    if (request.method === "GET" && url.pathname === "/health") return reply(200, { ok: true }, h);
    if (request.method !== "POST" || url.pathname !== "/translate") return reply(404, { error: "Not found" }, h);
    if (!env.GOOGLE_KEY) return reply(500, { error: "The server has no Google key yet." }, h);

    let body;
    try { body = await request.json(); } catch (e) { return reply(400, { error: "Bad request" }, h); }
    const q = String(body.q || "").trim();
    const target = String(body.target || "");
    if (!q || q.length > MAX_CHARS) return reply(400, { error: `Send 1 to ${MAX_CHARS} characters.` }, h);
    if (!TARGETS.has(target)) return reply(400, { error: "Unsupported language" }, h);

    const cache = typeof caches !== "undefined" ? caches.default : null;
    const ckey = new Request("https://polylang-cache/" + target + "/" + encodeURIComponent(q.toLowerCase()));
    if (cache) {
      const hit = await cache.match(ckey);
      if (hit) return reply(200, { text: (await hit.json()).text, cached: true }, h);
    }

    const g = await google(q, target, env.GOOGLE_KEY);
    if (g.error) return reply(g.status === 403 ? 429 : 502, { error: g.quota ? "daily-limit" : g.error }, h);

    if (cache) {
      const stored = new Response(JSON.stringify({ text: g.text }), { headers: { "Content-Type": "application/json", "Cache-Control": "public, max-age=2592000" } });
      ctx && ctx.waitUntil ? ctx.waitUntil(cache.put(ckey, stored)) : await cache.put(ckey, stored);
    }
    return reply(200, { text: g.text }, h);
  },
};
