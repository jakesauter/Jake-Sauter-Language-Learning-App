// Polylang offline copy. The app is one page, so this keeps the last good copy of it (and its icons)
// for when there is no signal: on a plane, underground, or a weak connection.
// Always asks the network first, so an online visit gets the newest version; the saved copy is used
// only when the network fails or takes longer than a few seconds.
// Only this app's own files are saved: the home computer, recordings and translation services never are.

const CACHE = "polylang-v1";
const SHELL = ["./", "manifest.webmanifest", "icon.svg", "icon-192.png", "apple-touch-icon.png"];
const SLOW_NETWORK_MS = 4000;

self.addEventListener("install", event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(SHELL)).catch(() => {}));
  self.skipWaiting();
});

self.addEventListener("activate", event => {
  event.waitUntil((async () => {
    for (const key of await caches.keys()) if (key !== CACHE) await caches.delete(key);
    await self.clients.claim();
  })());
});

const scope_path = new URL(self.registration.scope).pathname;

self.addEventListener("fetch", event => {
  const request = event.request;
  const url = new URL(request.url);
  if (request.method !== "GET" || url.origin !== location.origin || !url.pathname.startsWith(scope_path)) return;

  // Every visit to the page is saved under one key, whatever #phrase or ?query it had.
  const key = request.mode === "navigate" ? new URL("./", self.registration.scope).href : request;

  event.respondWith((async () => {
    // The page itself always asks the server whether it changed (no-cache), so a new version shows on the next visit.
    const from_network = (request.mode === "navigate" ? fetch(url.href.split("#")[0], { cache: "no-cache", credentials: "same-origin" }) : fetch(request)).then(async response => {
      if (response.ok) await (await caches.open(CACHE)).put(key, response.clone());
      return response;
    });
    const saved = await caches.match(key, { ignoreSearch: true });
    if (!saved) return from_network;
    // With a saved copy: use the network unless it fails or is slow; a slow download still refreshes the copy.
    const slow = new Promise(resolve => setTimeout(() => resolve(saved), SLOW_NETWORK_MS));
    return Promise.race([from_network.catch(() => saved), slow]);
  })());
});
