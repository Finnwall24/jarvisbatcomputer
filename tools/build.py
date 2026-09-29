#!/usr/bin/env python3
"""Builds the compressed batcomputer.html from the readable source.

  python3 tools/build.py            # source/batcomputer.src.html  ->  batcomputer.html

Edit source/batcomputer.src.html (readable, commented). This strips comments and whitespace from the CSS
and the markup, then syntax-checks the result before writing it, so a bad build never replaces a working
file. Needs:  pip install rcssmin

The JavaScript is copied through UNTOUCHED — do not reintroduce rjsmin (or any other regex-based minifier)
for it. rjsmin was tried here and quietly corrupts content: this codebase builds UI strings with template
literals nested inside other template literals (`` `...${cond?`...`:...}...` ``, all over the view code),
and rjsmin loses track of nesting depth inside them — it silently collapsed " · " to "·" inside one, and in
a separate test deleted a "/* ... */"-shaped chunk of plain text inside another, both while still producing
syntactically valid, so `new Function()` and every syntax check here saw nothing wrong. That is a correctness
bug, not a style choice: whitespace-only JS minification is not safe for this file's coding style."""
import os, re, subprocess, sys, tempfile
import rcssmin

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "source", "batcomputer.src.html")
OUT = os.path.join(ROOT, "batcomputer.html")

def js_ok(js):
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write(js); path = f.name
    jxa = ('ObjC.import("Foundation");'
           f'var s=$.NSString.stringWithContentsOfFileEncodingError("{path}",$.NSUTF8StringEncoding,null).js;'
           'try{ new Function(s); "OK" }catch(e){ "SYNTAX_ERROR: "+e.message }')
    out = subprocess.run(["osascript", "-l", "JavaScript", "-e", jxa], capture_output=True, text=True).stdout.strip()
    os.unlink(path); return out

def main():
    src = open(SRC, encoding="utf-8").read()
    style = re.search(r"<style>([\s\S]*?)</style>", src)
    script = re.search(r"<script>([\s\S]*)</script>", src)
    assert style and script, "could not find the <style> or <script> block"
    css = rcssmin.cssmin(style.group(1))
    js = script.group(1)   # verbatim — see the module docstring for why this must not be minified
    check = js_ok(js)
    if check != "OK":
        sys.exit("BUILD FAILED — JavaScript does not parse: " + check)
    head_body = src[:style.start()] + "<style>" + css + "</style>" + src[style.end():script.start()]
    # markup only: drop comments and indentation (the JS/CSS are already handled above)
    pre, _, rest = head_body.partition("<body")
    rest = re.sub(r"<!--[\s\S]*?-->", "", rest)
    rest = "\n".join(l.strip() for l in rest.split("\n") if l.strip())
    pre = "\n".join(l.strip() for l in pre.split("\n") if l.strip())
    out = pre + "\n<body" + rest + "\n<script>" + js + "</script>\n</body>\n</html>\n"
    open(OUT, "w", encoding="utf-8").write(out)
    a, b = len(src.encode()), len(out.encode())
    print(f"built {os.path.relpath(OUT, ROOT)}: {a/1024:.0f} KB -> {b/1024:.0f} KB ({100-b*100//a}% smaller)")

main()
