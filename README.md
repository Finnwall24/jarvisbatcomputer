# Batcomputer MK-IV

A voice-first console that runs entirely in your browser: projects, files, AI agents, apps it builds for you
(a lights panel, remotes...), your phone's calls and texts on a HUD display, and connections to smart lights and
online services. There is no server and no account: your data and your API keys stay in *your* browser.

## Put it on your phone (GitHub Pages)

1. On github.com create a new **public** repository (any name, e.g. `batcomputer`) and push this folder to it (commands below).
2. In the repo: **Settings -> Pages -> Build and deployment -> Deploy from a branch -> `main` / `/docs`** -> Save.
3. After a minute your app is at `https://<your-github-name>.github.io/<repo-name>/`.
4. Open that address on your phone.
   - **iPhone (Safari):** Share -> *Add to Home Screen*.
   - **Android (Chrome):** menu -> *Install app*.
5. Open it from the new icon (full screen). First run: **CONFIG** (top right) -> paste your AI key. It is stored only on that phone.

Long-press the installed icon for shortcuts: **Car display** and **Apps**.

### Push this folder to GitHub

```bash
cd batcomputer-github          # this folder
git init -b main
git add .
git commit -m "Batcomputer"
git remote add origin https://github.com/<your-github-name>/<repo-name>.git
git push -u origin main
```

The app holds no secrets, so a public repo is fine (Pages on a private repo needs a paid GitHub plan). Anyone opening
your site still needs their own AI key, and each browser keeps its own separate data.

## What works on a phone

| | On the phone site (https) |
|---|---|
| Projects, files, ideas, AI agents, tracker, DASHBOARD | yes |
| AI replies, GitHub / Vercel / Netlify / Notion / Linear, weather, reminders | yes |
| APPS: pages it builds, pinned and run inside the console | yes |
| Phone alerts: calls and texts shown as they arrive (through ntfy, see CONFIG -> PHONE_ALERTS) | yes |
| Car display: open `.../?car=1` on a tablet or head unit with a browser (or use the Car shortcut) | yes |
| Voice input | Chrome on Android; not iPhone Safari (type instead) |
| Hue lights / gadgets on your Wi-Fi (Home Control) | **no**: a browser will not let an `https` page talk to a plain `http` device. Use the Mac launcher on your home network. |
| Obsidian vault folder | no (phone browsers cannot open folders) |
| Claude Code bridge | no (needs the Mac) |

## Your data

Everything is stored in the browser you use, so the phone and your computer are separate copies. To move data:
**ARCHIVE -> EXPORT_ALL_JSON** on one, **IMPORT_JSON** on the other. That file contains your saved tokens: keep it private.

## Calls and texts on the display

A web page cannot see your phone, so the phone forwards each call or text to a private topic on an ntfy server
(free `ntfy.sh`, or your own) and Batcomputer listens to that topic. Setup is in **CONFIG -> PHONE_ALERTS** (it generates the
private topic name; the iPhone Shortcut / Android steps are written there). Texts pass through the ntfy server, so keep the
topic name secret or use your own server. Only the sender and time are logged, never the message text.

## Updating

Edit `source/batcomputer.src.html`, then:

```bash
pip install rcssmin        # once
python3 tools/publish.py   # rebuilds docs/
git add . && git commit -m "Update" && git push
```

Installed copies pick up the new version the next time they open while online.

## On a Mac (optional)

- `Batcomputer.command` starts a private local server and opens the app in its own Chrome window with the microphone
  already allowed, so Chrome never asks. `Batcomputer Hands-Free.command` also turns hands-free listening on.
- If the `claude` command is installed, the launchers also start a small bridge so the assistant can *propose* a coding
  task on this project that only runs when you click RUN (it needs the key printed the first time; see CONFIG -> CLAUDE_CODE).

## What is in this folder

```
docs/       the website GitHub Pages serves (index.html, service worker, icons, manifest)
source/     batcomputer.src.html, the readable, commented source of the whole app
tools/      build.py, check.py, publish.py, make_logo.py, claude_code_bridge.py
*.command   Mac launchers
```
