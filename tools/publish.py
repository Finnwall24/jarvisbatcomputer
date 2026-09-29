#!/usr/bin/env python3
"""Builds the app and assembles a ready-to-publish GitHub Pages folder.

  python3 tools/publish.py            # -> docs/   (safe to delete and regenerate any time)

The folder holds ONLY what the website needs (no personal files, no vault). Publish it as its own GitHub repo;
see docs/README.md. Re-run this after any change to source/batcomputer.src.html, then commit and push.
"""
import hashlib, json, os, re, subprocess, sys, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs")

def sh(*args):
    r = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    if r.returncode: sys.exit(f"FAILED: {' '.join(args)}\n{r.stdout}{r.stderr}")
    return r.stdout

SW = '''/* Batcomputer service worker: lets the app install to a phone's home screen and open with no connection.
   The app page is fetched fresh whenever you are online (so updates arrive) and the saved copy is used offline.
   Nothing you type or any AI / GitHub / device request is ever stored here -- only the app's own files and fonts. */
const CACHE = "batcomputer-__VERSION__";
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
  if (/(^|\\.)fonts\\.(googleapis|gstatic)\\.com$/.test(url.hostname)) {
    e.respondWith(caches.match(req).then(hit => hit || fetch(req).then(res => keep(req, res))));
    return;
  }
  if (url.origin === location.origin) {
    e.respondWith(caches.match(req).then(hit => hit || fetch(req).then(res => (res.ok ? keep(req, res) : res))));
  }
  // anything else (the AI provider, GitHub, Vercel, your devices) goes straight to the network and is never cached
});
'''

README = '''# Batcomputer MK-IV

A voice-first project console that runs entirely in your browser: a project board, idea map, file store, AI
agents, live request tracking, and connections to smart lights and online services. There is no server and no
account -- your data and your API keys stay in *your* browser on *your* device.

![Batcomputer](logo/social-preview.png)

## Use it on your phone

1. Open the site's address (`https://<your-github-name>.github.io/<repo-name>/`) on your phone.
2. **iPhone / iPad (Safari):** Share -> *Add to Home Screen*.  **Android (Chrome):** menu -> *Install app* (or *Add to Home screen*).
3. Open it from the new icon. It starts full-screen and keeps working with no connection (AI replies still need one).
4. First run: open **CONFIG** (top right) and paste your AI key.

## What works where

| | Phone / GitHub Pages (https) | Laptop opened from a local file |
|---|---|---|
| Projects, ideas, files, agents, tracker | yes | yes |
| AI replies, GitHub / Vercel / Netlify / Notion / Linear, weather, reminders | yes | yes |
| Home Assistant | only if it is reachable over `https` (e.g. Nabu Casa) | yes, on the same network |
| Voice input | Chrome on Android; not iPhone Safari (type instead) | Chrome / Edge |
| Home Control app (Hue lights and other gadgets on your Wi-Fi) | **no** (see below) | yes, on the same network |
| Phone alerts: your calls and texts shown as they arrive (via ntfy) | yes | yes |
| Car display (`?car=1`, full-screen phone display) | yes | yes |
| APPS (built-in apps, plus pages it builds for you) | yes | yes |
| Obsidian vault folder | no (browsers on phones cannot open folders) | Chrome / Edge |

**Why Hue doesn't work from the phone site:** the bridge only speaks plain `http` on your home network, and a browser
will not let an `https` website talk to plain `http` devices. Open the app from the file on your computer (or any
`http` address on your network) when you want to control lights.

## Your data

Everything is stored in the browser you use. The phone and the laptop are separate copies. To move data between them:
**ARCHIVE -> EXPORT_ALL_JSON** on one, **IMPORT_JSON** on the other. The export file contains your saved tokens, so keep it private.

## Updating

Edit `source/batcomputer.src.html` in the original project, run `python3 tools/publish.py`, then commit and push this
folder. Installed copies pick up the new version the next time they open while online.

## Publish it (once)

```bash
cd docs
git init -b main && git add . && git commit -m "Batcomputer"
# create an empty repo on github.com (public), then:
git remote add origin https://github.com/<your-github-name>/<repo-name>.git
git push -u origin main
```

Then on GitHub: **Settings -> Pages -> Build and deployment -> Deploy from a branch -> `main` / `(root)`**. The site
appears at `https://<your-github-name>.github.io/<repo-name>/` after a minute. (Pages on a private repo needs a paid
GitHub plan; a public repo is fine because the app holds no secrets -- anyone opening it still needs their own AI key.)
Set `logo/social-preview.png` as the repo's social preview under **Settings -> General** if you like.

## Logo

`logo/` has the mark and wordmark as SVG and PNG. `icons/` has the phone and browser icons. Regenerate with
`python3 tools/make_logo.py`.
'''

def main():
    sh(sys.executable, "tools/build.py")
    html = open(os.path.join(ROOT, "batcomputer.html"), encoding="utf-8").read()
    n0 = len(html)
    html, a = re.subn(r'<link rel="icon" href="data:[^"]*">', '<link rel="icon" type="image/svg+xml" href="icons/favicon.svg">\n<link rel="icon" type="image/png" sizes="32x32" href="icons/favicon-32.png">', html, count=1)
    html, b = re.subn(r'<link rel="apple-touch-icon" href="data:[^"]*">', '<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">', html, count=1)
    html, c = re.subn(r"<link rel=\"manifest\" href='data:[^']*'>", '<link rel="manifest" href="manifest.webmanifest">', html, count=1)
    if (a, b, c) != (1, 1, 1): sys.exit(f"could not swap the inline icon/manifest tags (found {a},{b},{c}) - the head changed; update tools/publish.py")
    reg = ("<script>if('serviceWorker' in navigator&&(location.protocol==='https:'||location.hostname==='localhost'))"
           "addEventListener('load',()=>{navigator.serviceWorker.register('sw.js').catch(()=>{});});</script>\n")
    # in the <head>, ahead of the app's own script (the FIRST </head> is the real one -- it comes before any of the app's code,
    # whose template strings also contain "</head>" and "</body>")
    i = html.index("</head>")
    html = html[:i] + reg + html[i:]

    if os.path.isdir(OUT):
        for name in os.listdir(OUT):
            if name == ".git": continue
            p = os.path.join(OUT, name); shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(html)
    version = hashlib.sha1(html.encode()).hexdigest()[:10]
    open(os.path.join(OUT, "sw.js"), "w").write(SW.replace("__VERSION__", version))
    manifest = {"id": "./", "name": "Batcomputer MK-IV", "short_name": "Batcomputer", "description": "Voice-first project console that runs in your browser.",
                "start_url": "./", "scope": "./", "display": "standalone", "orientation": "any", "background_color": "#040302", "theme_color": "#0a0705",
                "shortcuts": [{"name": "Car display", "short_name": "Car", "description": "Full-screen phone display for calls and texts", "url": "./?car=1", "icons": [{"src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png"}]}, {"name": "Apps", "short_name": "Apps", "url": "./?view=apps", "icons": [{"src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png"}]}],
                "icons": [{"src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png"}, {"src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png"},
                          {"src": "icons/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}]}
    open(os.path.join(OUT, "manifest.webmanifest"), "w").write(json.dumps(manifest, indent=2) + "\n")
    open(os.path.join(OUT, "README.md"), "w").write(README)
    open(os.path.join(OUT, ".nojekyll"), "w").write("")
    open(os.path.join(OUT, ".gitignore"), "w").write(".DS_Store\n")
    sh(sys.executable, "tools/make_logo.py", OUT)
    sh(sys.executable, "tools/check.py", os.path.join(OUT, "index.html"))
    print(f"published to {os.path.relpath(OUT, ROOT)}/  (index.html {n0//1024} KB, cache version {version})")

main()
