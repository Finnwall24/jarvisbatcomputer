#!/bin/bash
# Batcomputer, hands-free launcher (macOS). Double-click this file.
#
# It starts the app from a tiny local-only web server (127.0.0.1, this computer only, serving just the
# docs folder, never your other files) and opens it as its own Chrome app window with:
#   - the microphone permission pre-approved, so it can start listening with nobody touching anything
#   - audio allowed to play without a click
# and "?handsfree=1", which turns hands-free mode on. After that you only talk: "Hey <name>, ..."
#
# NOTE: this uses its own Chrome profile (~/.batcomputer-chrome), so it starts with an empty Batcomputer.
# Paste your AI key once in CONFIG, or move your data over: in your usual browser ARCHIVE -> EXPORT_ALL_JSON,
# then here ARCHIVE -> IMPORT_JSON. To start it at login: System Settings -> General -> Login Items -> add this file.

cd "$(dirname "$0")" || exit 1
PORT="${BATCOMPUTER_PORT:-8790}"
DIR="docs"
PROFILE="${BATCOMPUTER_PROFILE:-$HOME/.batcomputer-chrome}"

if [ ! -f "$DIR/index.html" ]; then
  echo "Building the app first..."
  python3 tools/publish.py || { echo "Could not build the app."; read -r -p "Press Return to close."; exit 1; }
fi

if ! curl -s -o /dev/null "http://127.0.0.1:$PORT/index.html"; then
  nohup python3 -m http.server "$PORT" --bind 127.0.0.1 --directory "$DIR" >/dev/null 2>&1 &
  for _ in 1 2 3 4 5 6 7 8 9 10; do sleep 0.3; curl -s -o /dev/null "http://127.0.0.1:$PORT/index.html" && break; done
fi

# Claude Code bridge: lets the assistant PROPOSE a real coding task on this project's own files; it only
# ever actually runs once you click RUN yourself inside the app. Needs the `claude` CLI on PATH.
BRIDGE_PORT="${BATCOMPUTER_BRIDGE_PORT:-8791}"
if command -v claude >/dev/null 2>&1; then
  if ! curl -s -o /dev/null "http://127.0.0.1:$BRIDGE_PORT/health"; then
    if [ ! -f ".batcomputer_bridge_key" ]; then
      echo "Starting the Claude Code bridge for the first time..."
      python3 tools/claude_code_bridge.py &
      sleep 1.5
      echo
      read -r -p "Paste the CLAUDE_CODE_KEY shown above into Batcomputer's CONFIG screen, then press Return to continue..."
    else
      nohup python3 tools/claude_code_bridge.py >/dev/null 2>&1 &
    fi
  fi
else
  echo "(claude CLI not found on PATH -- skipping the Claude Code bridge; the app's own file tools still work.)"
fi

URL="http://localhost:$PORT/index.html?handsfree=1"
if [ -n "$NO_OPEN" ]; then echo "$URL"; exit 0; fi

CHROME="/Applications/Google Chrome.app"
if [ ! -d "$CHROME" ]; then
  echo "Google Chrome is not installed in /Applications. Install it, or open $URL in Chrome yourself."
  read -r -p "Press Return to close."; exit 1
fi
open -na "Google Chrome" --args --user-data-dir="$PROFILE" --app="$URL" \
  --use-fake-ui-for-media-stream --autoplay-policy=no-user-gesture-required --no-first-run --no-default-browser-check
