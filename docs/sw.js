/* Batcomputer service worker: lets the app install to a phone's home screen and open with no connection.
   The app page is fetched fresh whenever you are online (so updates arrive) and the saved copy is used offline.
   Nothing you type or any AI / GitHub / device request is ever stored here -- only the app's own files and fonts. */
const CACHE = "batcomputer-4988ae1d36";
const SHELL = ["./", "index.html", "manifest.webmanifest", "icons/icon-192.png", "icons/icon-512.png", "icons/apple-touch-icon.png", "icons/favicon.svg"];
self.addEventListener("install", e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())); });
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k.startsWith("batcomputer-") && k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
const keep = (req, res) => { const copy = res.clone(); caches.open(CACHE).then(c => c.put(req, copy)); return res; };
self.addEventListener("fetch", e => {
  const req = e.request; if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (req.mode === "navigate") {
    e.respondWith(fetch(req).then(res => { keep("index.html", res); return res; }).catch(() => caches.match("index.html").then(r => r || caches.match("./"))));
    return;
  }
  if (/(^|\.)fonts\.(googleapis|gstatic)\.com$/.test(url.hostname)) {
    e.respondWith(caches.match(req).then(hit => hit || fetch(req).then(res => keep(req, res))));
    return;
  }
  if (url.origin === location.origin) {
    e.respondWith(caches.match(req).then(hit => hit || fetch(req).then(res => (res.ok ? keep(req, res) : res))));
  }
  // anything else (the AI provider, GitHub, Vercel, your devices) goes straight to the network and is never cached
});
