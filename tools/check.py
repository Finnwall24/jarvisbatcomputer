#!/usr/bin/env python3
"""Syntax guard for batcomputer.html / source/batcomputer.src.html. Parses the inline <script> with macOS's built-in JavaScript engine
(osascript -l JavaScript — no Node needed) and sanity-checks the CSS. Exit 0 = fine, 1 = broken.

  python3 tools/check.py [path/to/batcomputer.html]

As a Claude Code hook it reads the tool JSON on stdin and only checks edits to batcomputer.html."""
import json, os, re, subprocess, sys, tempfile

def target():
    if len(sys.argv) > 1:
        return sys.argv[1]
    try:
        data = json.load(sys.stdin)
        path = (data.get("tool_input") or {}).get("file_path") or ""
    except Exception:
        path = ""
    if not (path.endswith("batcomputer.html") or path.endswith("batcomputer.src.html")):
        sys.exit(0)
    return path

def main():
    path = target()
    src = open(path, encoding="utf-8").read()
    problems = []
    blocks = re.findall(r"<script>([\s\S]*?)</script>", src)   # the app's own code has no literal </script> (escaped), so this ends where it should
    m = re.search(r"<script>(" + re.escape(max(blocks, key=len)) + r")</script>", src) if blocks else None
    if not m:
        problems.append("no inline <script> found")
    else:
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
            f.write(m.group(1)); js_path = f.name
        jxa = ('ObjC.import("Foundation");'
               f'var s=$.NSString.stringWithContentsOfFileEncodingError("{js_path}",$.NSUTF8StringEncoding,null).js;'
               'try{ new Function(s); "OK" }catch(e){ "SYNTAX_ERROR: "+e.message }')
        out = subprocess.run(["osascript", "-l", "JavaScript", "-e", jxa], capture_output=True, text=True).stdout.strip()
        os.unlink(js_path)
        if out != "OK":
            problems.append(out or "could not run the JavaScript engine")
    css = src[: src.find("</style>")]
    if css.count("{") != css.count("}"):
        problems.append(f"CSS braces unbalanced ({css.count('{')} open, {css.count('}')} close)")
    ids = re.findall(r'\sid="([^"]+)"', src[src.find("<body"):src.find("<script>", src.find("<body"))])
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        problems.append("duplicate element ids: " + ", ".join(dupes))
    if problems:
        print("batcomputer.html check FAILED:\n - " + "\n - ".join(problems), file=sys.stderr)
        sys.exit(2 if len(sys.argv) == 1 else 1)
    print("batcomputer.html check OK")

main()
