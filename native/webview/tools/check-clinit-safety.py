#!/usr/bin/env python3
"""Refuse a build in which SdWebViewProvider's <clinit> could touch graphics.

Why this exists (real outage, 2026-10-26): a `static final Paint` field made class
initialisation call android.graphics.Paint.nInit(). SdWebViewProvider is also loaded
in the binder broker, which has no graphics natives, so the broker died with

    java.lang.UnsatisfiedLinkError: android.graphics.Paint.nInit
        at android.graphics.Paint.<init>
        at SdWebViewProvider.<clinit>
    SDBINDER=registry_failed  -> System.exit(12)

and every app launch on the device failed. This checker is run by
native/webview/tools/vm-javac-provider.sh before javac, so the mistake cannot come
back quietly.

Rule: every static field initialiser and every `static { }` block may contain only
literals, `new` of plain JDK collections/strings, and calls to our own static
helpers that are themselves literal-only. Anything from android.graphics /
android.view / android.webkit is rejected.

Exit 0 = safe, 1 = violation (printed with line numbers).
"""
import re
import sys

ALLOWED_NEW = {
    "String", "StringBuilder", "StringBuffer", "HashMap", "LinkedHashMap", "TreeMap",
    "ArrayList", "LinkedList", "HashSet", "LinkedHashSet", "TreeSet", "AtomicInteger",
    "AtomicLong", "AtomicBoolean", "Object", "Integer", "Long", "Double", "Float",
    "Boolean", "String[]", "ArrayDeque", "ConcurrentHashMap",
}
# Anything else that would drag a graphics class or a native call into <clinit>.
BANNED_CALL = re.compile(
    r"\b(?:Paint|Canvas|Bitmap|Typeface|Path|Matrix|Shader|Gradient|Rect|RectF|Region|"
    r"Picture|NinePatch|ColorFilter|PorterDuff|RenderNode|Xfermode|Movie|Camera|Mesh|"
    r"PathMeasure|Color|ColorSpace|Typeface|Layout|StaticLayout|TextPaint)\b\s*[.(]"
)
NEW_RE = re.compile(r"\bnew\s+([A-Za-z_$][\w$.]*)")


def strip_comments_and_strings(src: str) -> str:
    """Blank out comments/strings/chars, keeping newlines so line numbers survive."""
    out = []
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        nxt = src[i + 1] if i + 1 < n else ""
        if c == "/" and nxt == "/":
            while i < n and src[i] != "\n":
                out.append(" ")
                i += 1
        elif c == "/" and nxt == "*":
            out.append("  ")
            i += 2
            while i + 1 < n and not (src[i] == "*" and src[i + 1] == "/"):
                out.append("\n" if src[i] == "\n" else " ")
                i += 1
            out.append("  ")
            i += 2
        elif c in "\"'":
            quote = c
            out.append(" ")
            i += 1
            while i < n and src[i] != quote:
                if src[i] == "\\":
                    out.append(" ")
                    i += 1
                out.append("\n" if src[i] == "\n" else " ")
                i += 1
            out.append(" ")
            i += 1
        else:
            out.append(c)
            i += 1
    return "".join(out)


def find_static_regions(clean: str):
    """Yield (start_line, end_line, text) for static blocks and static field inits."""
    lines = clean.split("\n")
    # 1) `static { ... }` blocks, brace matched.
    for idx, line in enumerate(lines):
        if re.search(r"\bstatic\s*\{", line):
            depth = 0
            started = False
            body = []
            for j in range(idx, len(lines)):
                for ch in lines[j]:
                    if ch == "{":
                        depth += 1
                        started = True
                    elif ch == "}":
                        depth -= 1
                body.append(lines[j])
                if started and depth <= 0:
                    yield idx + 1, j + 1, "\n".join(body)
                    break
    # 2) static field declarations: `static <mods>? Type name = <init>;`
    for idx, line in enumerate(lines):
        if re.match(r"\s*(?:@\w+\s*)*(?:public|private|protected|final|static|\s)*\bstatic\b", line) \
                and "=" in line and "(" not in line.split("=", 1)[1].split(";")[0]:
            yield idx + 1, idx + 1, line
        elif re.match(r"\s*(?:@\w+\s*)*(?:public|private|protected|final|static|\s)*\bstatic\b", line) \
                and "=" in line:
            yield idx + 1, idx + 1, line


def main(argv):
    path = argv[1] if len(argv) > 1 else "scripts/device/SdWebViewProvider.java"
    src = open(path, encoding="utf-8").read()
    clean = strip_comments_and_strings(src)
    problems = []
    for start, end, text in find_static_regions(clean):
        for m in NEW_RE.finditer(text):
            if m.group(1) not in ALLOWED_NEW:
                problems.append((start, "new %s" % m.group(1)))
        for m in BANNED_CALL.finditer(text):
            problems.append((start, m.group(0).strip()))
    if problems:
        print("CLINIT_UNSAFE file=%s" % path)
        for line, what in problems:
            print("  line %d: %s" % (line, what))
        print("Rule: <clinit> must stay literal-only; graphics/native objects must be")
        print("created lazily (see ensurePaints()). This class is loaded in the binder")
        print("broker, which has no graphics natives.")
        return 1
    print("CLINIT_SAFE file=%s" % path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
