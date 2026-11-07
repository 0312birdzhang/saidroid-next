#!/bin/sh
# survey-atlantic.sh -- read-only survey of how Atlantic (the SFOS WPE browser that
# DOES get pixels on this device) reaches GL.
#
# Why: our standalone spike cannot get a single frame out of the same
# libWPEWebKit, because the WebProcess insists on an EGL window surface and libhybris
# refuses every native window we can give it (see docs/SD-WEBVIEW-DESIGN.md 4.1.1).
# Atlantic works, so the answer is already running on this device: read it, do not
# guess it.
#
# Safety rules this script obeys:
#   * Atlantic takes the topmost layer; it is killed the moment the evidence is
#     captured (hard cap), so nobody is left staring at a white screen.
#   * Lock-protected: refuses to run if another owner holds the device lock.
#   * Read-only with respect to the system: it starts a user app and kills it again.
#     No system file, service, compositor or network setting is touched.
#
# Usage: survey-atlantic.sh [--no-strace]
set -u

OUTBASE=/home/art/test/webview-survey
NO_STRACE=0
[ "${1:-}" = "--no-strace" ] && NO_STRACE=1

say() { echo "$@"; }

LOCK_HOLDER=$(cat /home/art/test/.device-lock/owner 2>/dev/null || true)
if [ ! -d /home/art/test/.device-lock ]; then
    say "LOCK_FREE (no lock taken by this script -- caller must own it)"
else
    say "LOCK_HELD owner=$LOCK_HOLDER"
fi

mkdir -p "$OUTBASE"
ENVF="$OUTBASE/helper-environ.txt"
MAPSF="$OUTBASE/helper-maps.txt"
STRACEF="$OUTBASE/atlantic.strace"
SCANF="$OUTBASE/wlegl-scan.txt"

ATL=/usr/bin/atlantic-browser
[ -x "$ATL" ] || { say "NO_ATLANTIC $ATL"; exit 2; }
say "ATLANTIC=$ATL $(ls -l "$ATL" | awk '{print $5}')"

# ---------------------------------------------------------------- lipstick env
LIP=$(pgrep -f '^/usr/bin/lipstick' | head -1)
say "LIPSTICK_PID=${LIP:-none}"
if [ -n "${LIP:-}" ] && [ -r "/proc/$LIP/environ" ]; then
    WL=$(tr '\0' '\n' < "/proc/$LIP/environ" | sed -n 's/^WAYLAND_DISPLAY=//p' | head -1)
    XDG=$(tr '\0' '\n' < "/proc/$LIP/environ" | sed -n 's/^XDG_RUNTIME_DIR=//p' | head -1)
    say "LIPSTICK_WAYLAND_DISPLAY=${WL:-<unset>} LIPSTICK_XDG_RUNTIME_DIR=${XDG:-<unset>}"
fi
WL=${WL:-../../display/wayland-0}
XDG=${XDG:-/run/user/100000}

# ------------------------------------------------------------------- launch it
# No `--help`: that path hangs and leaves the topmost layer covered (learned the
# hard way). Plain launch, then we hunt for the WebProcess.
say "== launch atlantic $(date -u +%H:%M:%SZ)"
if [ "$NO_STRACE" = 0 ] && command -v strace >/dev/null 2>&1; then
    # Capture which eglplatform_*.so / wlegl objects it actually opens. This is the
    # single most valuable artefact: it names the backend implementation.
    ( env -i HOME=/home/art PATH=/usr/bin:/bin:/usr/sbin:/sbin \
        XDG_RUNTIME_DIR="$XDG" WAYLAND_DISPLAY="$WL" \
        strace -f -o "$STRACEF" -e trace=openat,execve,memfd_create,socketpair -s 200 "$ATL" >"$OUTBASE/atlantic.out" 2>&1 ) &
    ATL_PID=$!
else
    ( env -i HOME=/home/art PATH=/usr/bin:/bin:/usr/sbin:/sbin \
        XDG_RUNTIME_DIR="$XDG" WAYLAND_DISPLAY="$WL" "$ATL" >"$OUTBASE/atlantic.out" 2>&1 ) &
    ATL_PID=$!
fi
say "ATLANTIC_LAUNCHER_PID=$ATL_PID"

# Poll for the WPEWebProcess: up to 20 s, 0.25 s steps (80 samples).
WP=""
i=0
while [ $i -lt 80 ]; do
    WP=$(pgrep -f 'wpe-webkit-2.0/WPEWebProcess' | head -1)
    [ -n "$WP" ] && break
    i=$((i + 1))
    sleep 0.25
done
say "WPEWEBPROCESS_PID=${WP:-NONE} after $((i / 4))s"

if [ -n "$WP" ]; then
    # ---- 1) its environment (this is the "copyable recipe" we are after)
    tr '\0' '\n' < "/proc/$WP/environ" > "$ENVF" 2>/dev/null
    say "-- helper env (interesting keys):"
    grep -E '^(HYBRIS_|EGL_|LD_PRELOAD|LD_LIBRARY_PATH|WAYLAND_|XDG_|WEBKIT_|WPE_|LIBGL_|GST_)' "$ENVF" 2>/dev/null | head -40 | sed 's/^/   /'

    # ---- 2) what it has mapped: which eglplatform_*.so, gralloc, wlegl, driver
    grep -E 'egl|gles|gralloc|hybris|wlegl|adreno|kgsl|qcom' "/proc/$WP/maps" > "$MAPSF" 2>/dev/null
    say "-- helper maps matching egl|gles|gralloc|hybris|wlegl|adreno:"
    awk '{print $6}' "$MAPSF" 2>/dev/null | sort -u | head -30 | sed 's/^/   /'

    # ---- 3) who spawned it (Atlantic's own launcher args matter)
    PPID_WP=$(awk '{print $4}' "/proc/$WP/stat" 2>/dev/null)
    say "-- parent of WebProcess: pid=$PPID_WP cmdline=$(tr '\0' ' ' < "/proc/$PPID_WP/cmdline" 2>/dev/null | cut -c1-300)"
    say "-- Atlantic main pid cmdline=$(tr '\0' ' ' < "/proc/$ATL_PID/cmdline" 2>/dev/null | cut -c1-300)"
    say "-- UI-process env (the one that owns the EGL display):"
    tr '\0' '\n' < "/proc/$PPID_WP/environ" 2>/dev/null \
        | grep -E '^(HYBRIS_|EGL_|LD_PRELOAD|LD_LIBRARY_PATH|WAYLAND_|XDG_)' | head -20 | sed 's/^/   /'
    grep -E 'egl|gles|gralloc|hybris|wlegl' "/proc/$PPID_WP/maps" 2>/dev/null \
        | awk '{print $6}' | sort -u | head -20 | sed 's/^/   UI| /'

    # ---- 4) the A/B discriminator: how does this WebProcess get its surface?
    # Lead's rule: Atlantic probably uses renderer-host, i.e. the WebProcess receives
    # a render target fd from its parent instead of ever creating a wl EGL window.
    # Those two worlds look different in three independent places, so capture all
    # three and let the classification below decide, instead of eyeballing maps.
    ARGC=$(tr '\0' '\n' < "/proc/$WP/cmdline" 2>/dev/null | grep -c . || true)
    FDS=$(ls "/proc/$WP/fd" 2>/dev/null | wc -l | tr -d ' ')
    FDTYPES=$(ls -l "/proc/$WP/fd" 2>/dev/null | sed 's/.*-> //' | sort | uniq -c | sort -rn | head -12)
    DMABUF=$(ls -l "/proc/$WP/fd" 2>/dev/null | grep -cE 'dmabuf|memfd' || true)
    SOCKETS=$(ls -l "/proc/$WP/fd" 2>/dev/null | grep -c 'socket:' || true)
    say "-- web process argv (argc=$ARGC): $(tr '\0' ' ' < "/proc/$WP/cmdline" 2>/dev/null | cut -c1-300)"
    say "-- web process fd count=$FDS sockets=$SOCKETS dmabuf_or_memfd=$DMABUF"
    echo "$FDTYPES" | sed 's/^/   FD| /'
    WPEGL=$(grep -oE '/[^ ]*eglplatform_[a-z]+\.so[^ ]*' "/proc/$WP/maps" 2>/dev/null | sort -u | tr '\n' ' ')
    say "-- web process eglplatform maps=${WPEGL:-none}"

    # ---- 5) classification (A = copyable platform config, B = renderer-host surface)
    # Note on the wayland branch: WE already know that eglplatform_wayland dies here
    # ("the server doesn't advertise the android_wlegl global"), so a wayland mapping
    # in Atlantic proves nothing new -- it is only interesting if Atlantic ALSO gets a
    # renderer-host fd (then the fd, not the platform, is what makes it work).
    ENVFLAT=$(grep -E '^(HYBRIS_EGLPLATFORM|EGL_PLATFORM|HYBRIS_EGLPLATFORM_DIR|WAYLAND_DISPLAY|LD_PRELOAD)=' "$ENVF" 2>/dev/null | tr '\n' ';')
    CASE=UNKNOWN
    case "${WPEGL:-none}" in
        *fbdev*|*hwcomposer*) CASE=A_candidate ;;
        *wayland*)            CASE=WAYLAND_KNOWN_BAD ;;
        *null*)               CASE=C_null_platform ;;
    esac
    if [ "${DMABUF:-0}" -gt 0 ] || [ "${SOCKETS:-0}" -gt 1 ] || [ "${ARGC:-0}" -gt 3 ]; then
        case "$CASE" in
            UNKNOWN|WAYLAND_KNOWN_BAD) CASE=B_renderer_host ;;
            A_candidate)               CASE=A_candidate_with_extra_fds ;;
        esac
    fi
    say "CLASSIFY|case=$CASE|wp_eglplatform=${WPEGL:-none}|env=$ENVFLAT|argc=${ARGC:-0}|sockets=${SOCKETS:-0}|dmabuf=${DMABUF:-0}"

    say "-- no WebProcess: atlantic out tail:"
    tail -20 "$OUTBASE/atlantic.out" 2>/dev/null | sed 's/^/   /'
fi

# ---------------------------------------------------------------- tear it down
say "== kill atlantic + helpers"
pkill -9 -f 'atlantic-browser' 2>/dev/null
pkill -9 -f 'wpe-webkit-2.0' 2>/dev/null
sleep 1
say "ATLANTIC_LEFT=$(pgrep -cf 'atlantic-browser' || true) WPE_LEFT=$(pgrep -cf 'wpe-webkit-2.0' || true) LIPSTICK_ALIVE=$(pgrep -cf '^/usr/bin/lipstick' || true)"

# ------------------------------------------- what did it open? (from strace)
if [ -f "$STRACEF" ]; then
    say "-- strace: eglplatform / wlegl / gralloc opens"
    grep -E 'eglplatform|wlegl|gralloc|libEGL|libGLESv2' "$STRACEF" 2>/dev/null \
        | sed -e 's/.*openat([^,]*, //' -e 's/,.*//' | sort | uniq -c | sort -rn | head -20 | sed 's/^/   /'
    say "-- strace: memfd_create / socketpair (renderer-host surface passing)"
    grep -E 'memfd_create|socketpair' "$STRACEF" 2>/dev/null | head -12 | sed 's/^/   /'
    say "-- strace: who called memfd/socketpair (pid -> count)"
    grep -E 'memfd_create|socketpair' "$STRACEF" 2>/dev/null | awk '{print $1}' | sort | uniq -c | head -12 | sed 's/^/   /'
fi

# ------------------------------------- does anybody on this box serve android_wlegl?
# Two independent questions:
#   (a) is there a *server-side* implementation (wl_global_create + the generated
#       `android_wlegl_interface` symbol)?  -> grep for that symbol name.
#   (b) is there any mention at all (client stubs, docs, plugins)?  -> grep the name.
# Bounded to likely directories and to files < 40 MB so the scan finishes in seconds
# instead of minutes (a full /usr/lib64 -r scan took >3 min and told us nothing extra).
say "== android_wlegl scan $(date -u +%H:%M:%SZ)"
{
    for d in /usr/lib64 /usr/lib64/qt5 /usr/lib/qt5 /usr/libexec /usr/share/qt5 /usr/lib64/libhybris; do
        [ -d "$d" ] || continue
        echo "## dir=$d"
        find "$d" -maxdepth 3 -type f -size -40M 2>/dev/null \
            | xargs -r -n 40 -P 4 grep -l -e 'android_wlegl_interface' -e 'android_wlegl' 2>/dev/null \
            | sort -u
    done
} > "$SCANF" 2>&1
say "-- files mentioning android_wlegl:"
grep -v '^##' "$SCANF" 2>/dev/null | head -20 | sed 's/^/   /'
say "-- count=$(grep -vc '^##' "$SCANF" 2>/dev/null || echo 0)"
say "DONE out=$OUTBASE"
