// AUDIT FX-05: scope-derived prefix, install precache, CACHE_NAME v4.
const CACHE_NAME = "tech-intel-v4";
const SCOPE = self.registration.scope;
const SCOPE_PATH = new URL(SCOPE).pathname;
const STATIC_ASSETS = ["css/", "js/", "fonts/", "images/icon-"];

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME)
      .then((c) => c.addAll([
        SCOPE,
        SCOPE + "css/bbc.css?v=9",
        SCOPE + "css/header.css?v=2",
        SCOPE + "css/news-ticker.css?v=3",
        SCOPE + "css/polish.css?v=1",
        SCOPE + "manifest.json",
        SCOPE + "fonts/Bornomala-Regular.woff2",
        SCOPE + "fonts/Bornomala-Bold.woff2",
      ]))
      .catch(() => {})
  );
  self.skipWaiting();
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET") return;
  const url = new URL(e.request.url);
  const isStatic = STATIC_ASSETS.some((p) => url.pathname.startsWith(SCOPE_PATH + p));
  if (isStatic) {
    e.respondWith(
      caches.match(e.request).then((cached) => {
        if (cached) {
          const fetchP = fetch(e.request).then((response) => {
            if (response && response.status === 200) {
              caches.open(CACHE_NAME).then((cache) => cache.put(e.request, response));
            }
            return response;
          }).catch(() => cached);
          return cached;
        }
        return fetch(e.request).then((response) => {
          if (response && response.status === 200) {
            const respClone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(e.request, respClone));
          }
          return response;
        }).catch(() => new Response('Offline', { status: 503 }));
      })
    );
  }
});
