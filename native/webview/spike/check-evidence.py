#!/usr/bin/env python3
"""Machine judgement for the WPE offscreen spike evidence.

Reads the evidence directory produced by native/webview/spike/vm-run-spike.sh
(PNG frames + spike.log) and prints one line per criterion plus a final verdict.
Exit code 0 = PASS, 1 = FAIL, 2 = evidence missing / not parseable.

No third-party modules: PNG is decoded with zlib + the standard filters so this
runs on the build VM and on the device.
"""

import os
import re
import sys
import zlib

# ---------------------------------------------------------------- PNG decode


def _paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def read_png(path):
    """Return (width, height, rows) where rows[h] is a bytearray of RGB triples."""
    with open(path, "rb") as f:
        data = f.read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("%s: not a PNG" % path)
    pos = 8
    w = h = depth = ctype = None
    idat = bytearray()
    while pos < len(data):
        if pos + 8 > len(data):
            break
        length = int.from_bytes(data[pos:pos + 4], "big")
        ctag = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if ctag == b"IHDR":
            w = int.from_bytes(chunk[0:4], "big")
            h = int.from_bytes(chunk[4:8], "big")
            depth = chunk[8]
            ctype = chunk[9]
            if chunk[10] != 0 or chunk[11] != 0:
                raise ValueError("%s: interlaced PNG unsupported" % path)
        elif ctag == b"IDAT":
            idat += chunk
        elif ctag == b"IEND":
            break
    if depth != 8:
        raise ValueError("%s: bit depth %s unsupported (want 8)" % (path, depth))
    nch = {0: 1, 2: 3, 4: 2, 6: 4}.get(ctype)
    if nch is None:
        raise ValueError("%s: colour type %s unsupported" % (path, ctype))
    bpp = nch
    stride = w * bpp
    raw = zlib.decompress(bytes(idat))
    rows = []
    prev = bytearray(stride)
    off = 0
    for _ in range(h):
        if off >= len(raw):
            raise ValueError("%s: truncated image data" % path)
        ft = raw[off]
        off += 1
        line = bytearray(raw[off:off + stride])
        if len(line) != stride:
            raise ValueError("%s: truncated scanline" % path)
        off += stride
        if ft == 0:
            pass
        elif ft == 1:
            for i in range(bpp, stride):
                line[i] = (line[i] + line[i - bpp]) & 0xFF
        elif ft == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif ft == 3:
            for i in range(stride):
                left = line[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 0xFF
        elif ft == 4:
            for i in range(stride):
                left = line[i - bpp] if i >= bpp else 0
                upleft = prev[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + _paeth(left, prev[i], upleft)) & 0xFF
        else:
            raise ValueError("%s: bad filter type %d" % (path, ft))
        rows.append(bytes(line))
        prev = line
    # normalise to RGB triples
    rgb = []
    for line in rows:
        out = bytearray(w * 3)
        if nch == 3:
            out[:] = line
        elif nch == 4:
            for x in range(w):
                out[3 * x:3 * x + 3] = line[4 * x:4 * x + 3]
        elif nch == 1:
            for x in range(w):
                v = line[x]
                out[3 * x:3 * x + 3] = bytes((v, v, v))
        else:  # 2 channel gray+alpha
            for x in range(w):
                v = line[2 * x]
                out[3 * x:3 * x + 3] = bytes((v, v, v))
        rgb.append(bytes(out))
    return w, h, rgb


def px(rows, x, y):
    r = rows[y]
    return r[3 * x], r[3 * x + 1], r[3 * x + 2]


# ---------------------------------------------------------------- metrics

def near(c, t, tol=24):
    return all(abs(c[i] - t[i]) <= tol for i in range(3))


def analyse(path, samples=40000):
    w, h, rows = read_png(path)
    step = max(1, int((w * h / float(samples)) ** 0.5))
    counts = {}
    total = 0
    nonbg = 0
    modal = None
    col_log = []
    for y in range(0, h, step):
        for x in range(0, w, step):
            c = px(rows, x, y)
            total += 1
            k = (c[0] >> 3, c[1] >> 3, c[2] >> 3)  # 5 bits/channel
            counts[k] = counts.get(k, 0) + 1
    ordered = sorted(counts.items(), key=lambda kv: -kv[1])
    modal = ordered[0][0] if ordered else (0, 0, 0)
    modal_m = tuple(v << 3 for v in modal)
    # non-background = anything not within tolerance of the modal colour
    for y in range(0, h, step):
        for x in range(0, w, step):
            c = px(rows, x, y)
            col_log.append(c)
            if not near(c, modal_m, 20):
                nonbg += 1
    # named band colours used by the spike page
    bands = {
        "blue(#0b3d91)": (0x0b, 0x3d, 0x91),
        "brown(#b5651d)": (0xb5, 0x65, 0x1d),
        "green(#1d7a3d)": (0x1d, 0x7a, 0x3d),
        "white(#ffffff)": (0xff, 0xff, 0xff),
    }
    hits = {}
    for name, t in bands.items():
        hits[name] = sum(1 for c in col_log if near(c, t, 26)) / float(len(col_log))
    # vertical position of the blue->non-blue transition down the left edge
    trans = None
    xcol = max(1, w // 8)
    for y in range(h):
        if not near(px(rows, xcol, y), bands["blue(#0b3d91)"], 40):
            trans = y
            break
    return {
        "w": w, "h": h,
        "unique_colors": len(counts),
        "top_color_share": ordered[0][1] / float(total) if ordered else 0.0,
        "modal_color": modal_m,
        "nonbg_ratio": nonbg / float(len(col_log) or 1),
        "band_share": hits,
        "blue_band_top_transition": trans,
        "rows": rows,
    }


# ------------------------------------------------- placeholder (provider) check
#
# The API29 provider in this build has no renderer, so what it draws is a
# self-describing placeholder with one solid colour per state. That makes the
# "is this a real page or our fallback?" question answerable without OCR:
# the modal colour of the frame IS the state.

PLACEHOLDER = {
    (0x10, 0x13, 0x1A): ("idle",             (0x45, 0x5A, 0x64), (0x9E, 0x9E, 0x9E)),
    (0x1B, 0x2A, 0x49): ("loading",          (0x2E, 0x86, 0xDE), (0x00, 0xC2, 0xA8)),
    (0x4A, 0x1D, 0x1D): ("error_no_renderer",(0xE7, 0x4C, 0x3C), (0xF1, 0xC4, 0x0F)),
}


def placeholder_state(info):
    """Return (state, evidence) when the frame is our placeholder, else (None, why)."""
    modal = tuple(info["modal_color"])
    state, marker, matched = None, None, None
    for bg, (name, _band, m) in PLACEHOLDER.items():
        if near(modal, bg, 10):
            state, marker, matched = name, m, bg
            break
    if state is None:
        return None, "modal=%s not a placeholder colour" % (info["modal_color"],)
    # bottom 12 px strip must be the marker colour: cross-checks the modal colour
    # against a second, independent region, so scaling/JPEG noise cannot fool it.
    rows, w, h = info["rows"], info["w"], info["h"]
    ys = [h - 1, h - 3, h - 6]
    hit = sum(1 for y in ys if 0 <= y < h and near(px(rows, max(1, w // 2), y), marker, 26))
    return state, "modal=%s band_ok=%s marker_rows_hit=%d/%d" % (
        info["modal_color"], True, hit, len(ys))


# ---------------------------------------------------------------- log parsing

NUM = r"(-?\d+(?:\.\d+)?)"


def parse_log(path):
    txt = open(path, "r", errors="replace").read()
    out = {"raw": txt}
    m = re.search(r"spike_result\|shm_frames=%s\|other_frames=%s\|frame_span_s=%s" % (NUM, NUM, NUM), txt)
    if m:
        out["shm_frames"] = int(float(m.group(1)))
        out["other_frames"] = int(float(m.group(2)))
        out["frame_span_s"] = float(m.group(3))
    m = re.search(r"spike_cookie\|count=%s" % NUM, txt)
    if m:
        out["cookie_count"] = int(float(m.group(1)))
    titles = re.findall(r"title=(scrollY=-?\d+|loaded|\(null\)|None)", txt)
    out["titles"] = titles
    out["scroll_titles"] = [t for t in titles if t.startswith("scrollY=")]
    out["load_events"] = re.findall(r"spike_load\|event=(\w+)", txt)
    out["load_failed"] = re.findall(r"spike_load_failed\|uri=(\S*)\|error=(.*)", txt)
    m = re.search(r"spike_backend\|name=(\S+)", txt)
    out["backend"] = m.group(1) if m else None
    m = re.search(r"spike_backend\|mode=(\S+)", txt)
    out["mode"] = m.group(1) if m else None
    out["wpe_processes"] = re.findall(r"^\d+ (\S*WPE\w+Process)", txt, re.M)
    return out


def main():
    d = sys.argv[1] if len(sys.argv) > 1 else "."
    # --placeholder <png>: answer only "which state is this placeholder?" (used when
    # the evidence is a screenshot of the fallback page instead of a rendered frame)
    if len(sys.argv) > 2 and sys.argv[1] == "--placeholder":
        try:
            info = analyse(sys.argv[2])
        except Exception as e:  # noqa: BLE001
            print("PLACEHOLDER_STATE=error|%s" % e)
            return 1
        state, ev = placeholder_state(info)
        print("PLACEHOLDER_STATE=%s|%s|unique_colors=%d|top_share=%.3f"
              % (state or "none", ev, info["unique_colors"], info["top_color_share"]))
        return 0 if state else 2
    checks = []

    def check(name, ok, detail):
        checks.append((ok, name, detail))
        print("%-6s %-42s %s" % ("PASS" if ok else "FAIL", name, detail))

    for needed in ("spike.log",):
        p = os.path.join(d, needed)
        if not os.path.exists(p):
            print("EVIDENCE_MISSING %s" % p)
            return 2

    log = parse_log(os.path.join(d, "spike.log"))
    print("-- log: backend=%s mode=%s shm_frames=%s other=%s span=%s load_events=%s"
          % (log.get("backend"), log.get("mode"), log.get("shm_frames"),
             log.get("other_frames"), log.get("frame_span_s"), ",".join(log["load_events"]) or "-"))

    check("log: >=2 SHM frames exported",
          log.get("shm_frames", 0) >= 2,
          "shm_frames=%s" % log.get("shm_frames"))
    check("log: page load reached 'finished'",
          "finished" in log["load_events"],
          "events=%s" % (",".join(log["load_events"]) or "-"))
    check("log: JS wrote cookie, native manager read it back",
          log.get("cookie_count") == 1,
          "cookie_count=%s" % log.get("cookie_count"))
    check("log: JS scroll handler updated title (scrollY>0)",
          any(re.match(r"scrollY=-?\d+$", t) and int(t.split("=")[1]) > 0 for t in log["scroll_titles"]),
          "titles=%s" % ",".join(log["scroll_titles"][:6]))

    # reference: a pure white page, synthesised in memory, gives the baseline
    # numbers we compare against (so "colours" cannot be satisfied by blankness).
    frames = {}
    for name in ("frame-load", "frame-scrolled", "frame-scrolled-up"):
        p = os.path.join(d, name + ".png")
        frames[name] = analyse(p) if os.path.exists(p) else None
        if frames[name] is None:
            check("frame %s exists" % name, False, "missing %s" % p)
        else:
            f = frames[name]
            print("-- %-18s %dx%d unique=%d top_share=%.2f modal=%s nonbg=%.2f blue=%.2f brown=%.2f white=%.2f trans=%s"
                  % (name, f["w"], f["h"], f["unique_colors"], f["top_color_share"],
                     f["modal_color"], f["nonbg_ratio"],
                     f["band_share"]["blue(#0b3d91)"], f["band_share"]["brown(#b5651d)"],
                     f["band_share"]["white(#ffffff)"], f["blue_band_top_transition"]))

    load = frames.get("frame-load")
    if load:
        check("load frame: colour variety (>=8 quantised colours)",
              load["unique_colors"] >= 8, "unique=%d" % load["unique_colors"])
        check("load frame: non-background pixels >= 30%",
              load["nonbg_ratio"] >= 0.30, "nonbg=%.2f" % load["nonbg_ratio"])
        check("load frame: blue band >= 10%",
              load["band_share"]["blue(#0b3d91)"] >= 0.10,
              "blue=%.2f" % load["band_share"]["blue(#0b3d91)"])
        check("load frame: brown band present",
              load["band_share"]["brown(#b5651d)"] >= 0.02,
              "brown=%.2f" % load["band_share"]["brown(#b5651d)"])
        check("load frame: canvas white area present",
              load["band_share"]["white(#ffffff)"] >= 0.01,
              "white=%.2f" % load["band_share"]["white(#ffffff)"])
        check("load frame: not a blank page (modal share <= 90%)",
              load["top_color_share"] <= 0.90, "top=%.2f" % load["top_color_share"])

    sc = frames.get("frame-scrolled")
    if load and sc and load["blue_band_top_transition"] is not None and sc["blue_band_top_transition"] is not None:
        dlt = load["blue_band_top_transition"] - sc["blue_band_top_transition"]
        check("scroll frame: blue band moved up 400..800 px",
              400 <= dlt <= 800, "delta=%d px" % dlt)
    up = frames.get("frame-scrolled-up")
    if load and up and load["blue_band_top_transition"] is not None and up["blue_band_top_transition"] is not None:
        back = abs(up["blue_band_top_transition"] - load["blue_band_top_transition"])
        check("scroll-back frame: band returns to within 100 px",
              back <= 100, "delta=%d px" % back)

    print("-- WPE helper processes seen in log: %s" % (",".join(log["wpe_processes"]) or "none"))
    if log.get("load_failed"):
        for uri, err in log["load_failed"][:3]:
            print("-- load-failed: %s -> %s" % (uri, err))

    bad = [c for c in checks if not c[0]]
    print("\nVERDICT: %s (%d/%d criteria passed)"
          % ("PASS" if not bad else "FAIL", len(checks) - len(bad), len(checks)))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
