/* AUDIT FX-05: scope-derived prefix (fixes /tech-blog-en/ subpath), install precache,
   CACHE_NAME v1 -> v2, and cleanup of old caches on activate. */
const CACHE_NAME = "tech-intel-v2";
// registration scope ends with "/" → "/tech-blog/" or "/tech-blog-en/"
const SCOPE = self.registration.scope;
const STATIC_ASSETS = ["css/", "js/", "fonts/", "images/icon-"];

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME)
      .then((c) => c.addAll([
        SCOPE,                                   // homepage (HTML core shell)
        SCOPE + "css/bbc.css?v=8",
        SCOPE + "css/bbc-label.css?v=8",
        SCOPE + "css/news-ticker.css?v=1",
        SCOPE + "manifest.json",
        SCOPE + "fonts/Bornomala-Regular.woff2",
        SCOPE + "fonts/Bornomala-Bold.woff2",
      ]))
      .catch(() => {})                           // one failed URL must not break install
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
  const isStatic = STATIC_ASSETS.some((p) => url.pathname.startsWith(SCOPE + p));
  if (isStatic) {
    // cache-first + background fill (now with correct scope prefix)
    e.respondWith(
      caches.open(CACHE_NAME).then((c) =>
        c.match(e.request).then((r) =>
          r || fetch(e.request).then((resp) => {
            if (resp.ok) c.put(e.request, resp.clone());
            return resp;
          }).catch(() => r)
        )
      )
    );
  } else {
    // HTML/images: network-first + cache fallback
    e.respondWith(
      fetch(e.request)
        .then((resp) => {
          if (resp.ok && resp.type === "basic") {
            const clone = resp.clone();
            caches.open(CACHE_NAME).then((c) => c.put(e.request, clone));
          }
          return resp;
        })
        .catch(() => caches.match(e.request))
    );
  }
});
