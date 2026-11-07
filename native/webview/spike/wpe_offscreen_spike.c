/*
 * WPE WebKit offscreen spike for SailDroid's WebView provider.
 *
 * Proves, on the real Sailfish host, that the installed WPE WebKit (2.54.1,
 * libWPEWebKit-2.0.so.1.11.4) + WPEBackend-fdo (1.17) can render a real page
 * with JavaScript into CPU-visible pixels without any compositor window.
 *
 * Path: wpe_fdo_initialize_shm() + wpe_view_backend_exportable_fdo_create()
 *       -> webkit_web_view_backend_new() -> webkit_web_view_new()
 *       -> export_shm_buffer -> PNG frames.
 *
 * It also exercises the pieces the Android WebView contract needs:
 *   - load_html + JS execution + canvas paint
 *   - load-changed / load-failed / decide-policy signals
 *   - CookieManager get_cookies round trip
 *   - synthetic axis (scroll) input through wpe_view_backend_dispatch_axis_event
 *
 * Output: PNG frames + a key=value report on stdout. No window, no EGL in this
 * process; WPEWebProcess is spawned by WebKit and isolated.
 */

#define _GNU_SOURCE
#include <errno.h>
#include <stdarg.h>
#include <glib.h>
#include <gio/gio.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <zlib.h>

#include <wpe/webkit.h>
#include <wpe/wpe.h>
#include <wpe/fdo.h>
#include <wpe/unstable/fdo-shm.h>
/* wl_shm_buffer_* is the server-side shm access API: WPEBackend-fdo gives us a
 * wl_shm_buffer living on its internal wl_display, so this is exactly the API
 * to read it. libwayland-server provides the symbols. */
#include <wayland-server-core.h>

/* ------------------------------------------------------------------ logging */

static void
report(const char *fmt, ...)
{
    va_list ap;
    va_start(ap, fmt);
    fputs("SDWEBVIEW=", stdout);
    vprintf(fmt, ap);
    fputc('\n', stdout);
    fflush(stdout);
    va_end(ap);
}

/* ------------------------------------------------------------------ PNG out */

static void
put_be32(uint8_t *p, uint32_t v)
{
    p[0] = (uint8_t)(v >> 24);
    p[1] = (uint8_t)(v >> 16);
    p[2] = (uint8_t)(v >> 8);
    p[3] = (uint8_t)v;
}

static void
png_chunk(FILE *f, const char *type, const uint8_t *data, size_t len)
{
    uint8_t hdr[8];
    uint8_t *crcbuf = g_malloc(len + 4);
    uLong crc;

    put_be32(hdr, (uint32_t)len);
    memcpy(hdr + 4, type, 4);
    fwrite(hdr, 1, 8, f);

    if (len)
        fwrite(data, 1, len, f);

    memcpy(crcbuf, type, 4);
    if (len)
        memcpy(crcbuf + 4, data, len);
    crc = crc32(0L, Z_NULL, 0);
    crc = crc32(crc, crcbuf, (uInt)(len + 4));
    put_be32(hdr, (uint32_t)crc);
    fwrite(hdr, 1, 4, f);
    g_free(crcbuf);
}

/*
 * src is a WL_SHM_FORMAT_ARGB8888 / XRGB8888 buffer: little-endian bytes B,G,R,A.
 * PNG wants R,G,B in that order, so we swizzle while copying.
 * Returns 0 on success.
 */
static int
write_png(const char *path, const uint8_t *src, int w, int h, int stride)
{
    FILE *f;
    uint8_t *rows, *rp;
    uLongf zlen;
    uint8_t *zbuf;
    uint8_t ihdr[13];
    int y, x, rc = -1;

    if (w <= 0 || h <= 0 || stride < w * 4)
        return -1;

    rows = g_malloc((size_t)(w * 3 + 1) * (size_t)h);
    for (y = 0; y < h; y++) {
        const uint8_t *sp = src + (size_t)y * (size_t)stride;
        rp = rows + (size_t)y * (size_t)(w * 3 + 1);
        *rp++ = 0; /* filter: none */
        for (x = 0; x < w; x++) {
            rp[0] = sp[2];
            rp[1] = sp[1];
            rp[2] = sp[0];
            rp += 3;
            sp += 4;
        }
    }

    zlen = compressBound((uLong)w * 3 * (uLong)h + (uLong)h);
    zbuf = g_malloc(zlen);
    if (compress2(zbuf, &zlen, rows, (uLong)w * 3 * (uLong)h + (uLong)h, 6) != Z_OK)
        goto out;

    f = fopen(path, "wb");
    if (!f) {
        report("spike_error|png_open|path=%s|errno=%d", path, errno);
        goto out;
    }
    fwrite("\x89PNG\r\n\x1a\n", 1, 8, f);
    put_be32(ihdr, (uint32_t)w);
    put_be32(ihdr + 4, (uint32_t)h);
    ihdr[8] = 8;  /* bit depth */
    ihdr[9] = 2;  /* colour type: truecolour RGB */
    ihdr[10] = 0;
    ihdr[11] = 0;
    ihdr[12] = 0;
    png_chunk(f, "IHDR", ihdr, sizeof(ihdr));
    png_chunk(f, "IDAT", zbuf, zlen);
    png_chunk(f, "IEND", NULL, 0);
    rc = fclose(f) == 0 ? 0 : -1;

out:
    g_free(zbuf);
    g_free(rows);
    return rc;
}

/* --------------------------------------------------------------- frame state */

static struct wpe_view_backend_exportable_fdo *g_exportable;
static struct wpe_view_backend *g_backend;
static WebKitWebView *g_view;
static GMainLoop *g_loop;
static int g_width = 720, g_height = 1280;

static GMutex g_frame_lock;
static uint8_t *g_frame;          /* latest frame, packed w*4 */
static int g_frame_w, g_frame_h, g_frame_stride, g_frame_format;
static guint64 g_frame_seq;       /* increments for every exported buffer */
static guint64 g_shm_frames, g_other_frames;
static gint64 g_first_frame_us, g_last_frame_us;

static void
save_frame(const char *name)
{
    uint8_t *copy = NULL;
    int w = 0, h = 0, stride = 0, seq = 0;

    g_mutex_lock(&g_frame_lock);
    if (g_frame) {
        w = g_frame_w;
        h = g_frame_h;
        /* The exported buffer's width is authoritative: it can differ from the
         * requested view size (e.g. when WebKit exports a partial/scaled frame),
         * and copying g_width*4 bytes out of it would read past the mapping. */
        stride = g_frame_w * 4;
        seq = (int)g_frame_seq;
        copy = g_malloc((size_t)stride * (size_t)h);
        memcpy(copy, g_frame, (size_t)stride * (size_t)h);
    }
    g_mutex_unlock(&g_frame_lock);

    if (!copy || w <= 0 || h <= 0) {
        report("spike_frame|name=%s|missing=1", name);
        g_free(copy);
        return;
    }

    gchar *path = g_strdup_printf("%s/%s.png", g_getenv("SD_SPIKE_OUT") ? g_getenv("SD_SPIKE_OUT") : ".", name);
    int rc = write_png(path, copy, w, h, stride);

    /* Cheap content proof: non-black pixel count + centre pixel. */
    guint64 nonblack = 0;
    const uint8_t *centre = copy + ((size_t)(h / 2) * (size_t)stride) + (size_t)(w / 2) * 4;
    for (int y = 0; y < h; y += 8) {
        const uint8_t *p = copy + (size_t)y * (size_t)stride;
        for (int x = 0; x < w; x += 8, p += 4) {
            if (p[0] || p[1] || p[2])
                nonblack++;
        }
    }
    report("spike_frame|name=%s|png=%d|w=%d|h=%d|seq=%d|nonblack_sampled=%llu|centre_bgr=%u,%u,%u",
           name, rc, w, h, seq, (unsigned long long)nonblack, centre[0], centre[1], centre[2]);

    g_free(path);
    g_free(copy);
}

static void
on_export_shm(void *data, struct wpe_fdo_shm_exported_buffer *buffer)
{
    struct wl_shm_buffer *shm = wpe_fdo_shm_exported_buffer_get_shm_buffer(buffer);
    (void)data;
    if (!shm) {
        report("spike_error|shm_buffer_null");
        return;
    }

    int w = wl_shm_buffer_get_width(shm);
    int h = wl_shm_buffer_get_height(shm);
    int stride = wl_shm_buffer_get_stride(shm);
    uint32_t format = wl_shm_buffer_get_format(shm);

    wl_shm_buffer_begin_access(shm);
    const uint8_t *src = wl_shm_buffer_get_data(shm);

    g_mutex_lock(&g_frame_lock);
    size_t need = (size_t)w * 4 * (size_t)h;
    if (!g_frame || g_frame_w != w || g_frame_h != h)
        g_frame = g_realloc(g_frame, need);
    for (int y = 0; y < h; y++)
        memcpy(g_frame + (size_t)y * (size_t)w * 4,
               src + (size_t)y * (size_t)stride,
               (size_t)w * 4);
    g_frame_w = w;
    g_frame_h = h;
    g_frame_stride = stride;
    g_frame_format = (int)format;
    g_frame_seq++;
    if (g_shm_frames == 0)
        g_first_frame_us = g_get_monotonic_time();
    g_last_frame_us = g_get_monotonic_time();
    g_shm_frames++;
    g_mutex_unlock(&g_frame_lock);

    wl_shm_buffer_end_access(shm);
    wpe_view_backend_exportable_fdo_dispatch_release_shm_exported_buffer(g_exportable, buffer);
    wpe_view_backend_exportable_fdo_dispatch_frame_complete(g_exportable);
}

static void
on_export_buffer_resource(void *data, struct wl_resource *resource)
{
    (void)data;
    g_other_frames++;
    if (g_other_frames < 3)
        report("spike_frame_path|kind=wl_resource");
    wpe_view_backend_exportable_fdo_dispatch_release_buffer(g_exportable, resource);
}

static void
on_export_dmabuf(void *data, struct wpe_view_backend_exportable_fdo_dmabuf_resource *dmabuf)
{
    (void)data;
    g_other_frames++;
    if (g_other_frames < 3)
        report("spike_frame_path|kind=dmabuf|w=%u|h=%u|format=%u|planes=%u",
               dmabuf->width, dmabuf->height, dmabuf->format, dmabuf->n_planes);
    /* We did not ask for dmabuf; close the fds we were handed. */
    for (uint8_t i = 0; i < dmabuf->n_planes; i++)
        if (dmabuf->fds[i] >= 0)
            close(dmabuf->fds[i]);
}

static const struct wpe_view_backend_exportable_fdo_client g_client = {
    .export_buffer_resource = on_export_buffer_resource,
    .export_dmabuf_resource = on_export_dmabuf,
    .export_shm_buffer = on_export_shm,
};

/* --------------------------------------------------------------- page + test */

static const char *PAGE_HTML =
"<!doctype html><html><head><meta charset='utf-8'>"
"<meta name='viewport' content='width=device-width,initial-scale=1'>"
"<style>"
"html,body{margin:0;padding:0;background:#f2f2f2;font-family:sans-serif}"
".band{height:640px;color:#fff;font-size:44px;padding:28px;box-sizing:border-box}"
"#b1{background:#0b3d91}#b2{background:#b5651d}#b3{background:#1d7a3d}"
"#out{font-size:64px;font-weight:bold}"
"#cv{display:block;margin-top:20px;background:#fff}"
"</style></head><body>"
"<div class='band' id='b1'><div id='out'>JS: (pending)</div>"
"<canvas id='cv' width='560' height='220'></canvas>"
"<div id='cookie' style='font-size:28px'>cookie: (pending)</div></div>"
"<div class='band' id='b2'>BAND 2 (scroll target)</div>"
"<div class='band' id='b3'>BAND 3</div>"
"<script>"
"var cv=document.getElementById('cv'),cx=cv.getContext('2d');"
"cx.fillStyle='#0b3d91';cx.fillRect(0,0,560,220);"
"cx.fillStyle='#ffffff';cx.font='bold 52px sans-serif';"
"cx.fillText('CANVAS '+(7*6),24,90);"
"cx.fillStyle='#ffd24a';cx.font='28px sans-serif';"
"cx.fillText('rAF='+window.__raf,24,160);"
"document.getElementById('out').textContent='JS: '+(7*6)+' (7x6)';"
"document.cookie='sdspike=42; path=/';"
"document.getElementById('cookie').textContent='cookie: '+document.cookie;"
"window.__raf=0;(function tick(){window.__raf++;"
"if(window.__raf<40)requestAnimationFrame(tick);})();"
"document.title='loaded';"
"window.addEventListener('scroll',function(){"
"document.title='scrollY='+Math.round(window.scrollY);});"
"</script></body></html>";

static void
on_load_changed(WebKitWebView *view, WebKitLoadEvent event, gpointer user_data)
{
    (void)user_data;
    const char *name = "?";
    switch (event) {
    case WEBKIT_LOAD_STARTED: name = "started"; break;
    case WEBKIT_LOAD_REDIRECTED: name = "redirected"; break;
    case WEBKIT_LOAD_COMMITTED: name = "committed"; break;
    case WEBKIT_LOAD_FINISHED: name = "finished"; break;
    }
    report("spike_load|event=%s|uri=%s|title=%s|progress=%.2f",
           name,
           webkit_web_view_get_uri(view) ? webkit_web_view_get_uri(view) : "(null)",
           webkit_web_view_get_title(view) ? webkit_web_view_get_title(view) : "(null)",
           webkit_web_view_get_estimated_load_progress(view));
}

static gboolean
on_load_failed(WebKitWebView *view, WebKitLoadEvent event, const char *uri,
               GError *error, gpointer user_data)
{
    (void)view; (void)event; (void)user_data;
    report("spike_load_failed|uri=%s|error=%s", uri ? uri : "(null)", error->message);
    return FALSE;
}

static gboolean
on_decide_policy(WebKitWebView *view, WebKitPolicyDecision *decision,
                 WebKitPolicyDecisionType type, gpointer user_data)
{
    (void)view; (void)user_data;
    const char *name = type == WEBKIT_POLICY_DECISION_TYPE_NAVIGATION_ACTION ? "navigation" :
                       type == WEBKIT_POLICY_DECISION_TYPE_NEW_WINDOW_ACTION ? "new_window" :
                       type == WEBKIT_POLICY_DECISION_TYPE_RESPONSE ? "response" : "other";
    const char *uri = "";
    if (type == WEBKIT_POLICY_DECISION_TYPE_NAVIGATION_ACTION) {
        WebKitNavigationAction *action =
            webkit_navigation_policy_decision_get_navigation_action(WEBKIT_NAVIGATION_POLICY_DECISION(decision));
        WebKitURIRequest *request = webkit_navigation_action_get_request(action);
        uri = webkit_uri_request_get_uri(request);
    }
    report("spike_policy|type=%s|uri=%s", name, uri ? uri : "");
    webkit_policy_decision_use(decision);
    return TRUE;
}

static void
on_title_changed(GObject *object, GParamSpec *pspec, gpointer user_data)
{
    (void)pspec; (void)user_data;
    report("spike_title|title=%s",
           webkit_web_view_get_title(WEBKIT_WEB_VIEW(object)) ?: "(null)");
}

static void
on_cookies(GObject *source, GAsyncResult *res, gpointer user_data)
{
    WebKitCookieManager *cm = WEBKIT_COOKIE_MANAGER(source);
    GError *error = NULL;
    GList *cookies = webkit_cookie_manager_get_cookies_finish(cm, res, &error);
    if (error) {
        report("spike_cookie|error=%s", error->message);
        g_error_free(error);
        return;
    }
    report("spike_cookie|count=%u", g_list_length(cookies));
    g_list_free(cookies);
}

/* --------------------------------------------------------------- main flow */

static gboolean
t_log_title(gpointer data)
{
    (void)data;
    report("spike_state|t=%s|title=%s|seq=%llu|shm_frames=%llu|other=%llu",
           (const char *)data,
           webkit_web_view_get_title(g_view) ?: "(null)",
           (unsigned long long)g_frame_seq,
           (unsigned long long)g_shm_frames,
           (unsigned long long)g_other_frames);
    return G_SOURCE_REMOVE;
}

static gboolean
t_save(gpointer data)
{
    save_frame((const char *)data);
    return G_SOURCE_REMOVE;
}

static void
send_scroll(int direction)
{
    struct wpe_input_axis_event event;
    memset(&event, 0, sizeof(event));
    event.type = wpe_input_axis_event_type_motion_smooth;
    event.x = g_width / 2;
    event.y = g_height / 2;
    event.axis = 0;
    event.value = direction;
    wpe_view_backend_dispatch_axis_event(g_backend, &event);
    report("spike_input|kind=axis|dir=%d|x=%d|y=%d", direction, event.x, event.y);
}

static gboolean
t_scroll_down(gpointer data)
{
    (void)data;
    send_scroll(-600);
    return G_SOURCE_REMOVE;
}

static gboolean
t_scroll_up(gpointer data)
{
    (void)data;
    send_scroll(600);
    return G_SOURCE_REMOVE;
}

static gboolean
t_cookies(gpointer data)
{
    WebKitNetworkSession *session = webkit_web_view_get_network_session(g_view);
    (void)data;
    if (!session) {
        report("spike_cookie|error=no_network_session");
        return G_SOURCE_REMOVE;
    }
    WebKitCookieManager *cm = webkit_network_session_get_cookie_manager(session);
    if (!cm) {
        report("spike_cookie|error=no_cookie_manager");
        return G_SOURCE_REMOVE;
    }
    webkit_cookie_manager_get_cookies(cm, "https://ptlogin2.qq.com/", NULL, on_cookies, NULL);
    report("spike_cookie|requested=1");
    return G_SOURCE_REMOVE;
}

static gboolean
t_finish(gpointer data)
{
    (void)data;
    double span = 0.0;
    if (g_first_frame_us && g_last_frame_us > g_first_frame_us)
        span = (double)(g_last_frame_us - g_first_frame_us) / 1e6;

    save_frame("frame-final");
    report("spike_result|shm_frames=%llu|other_frames=%llu|frame_span_s=%.3f|title=%s|backend=%s|pid=%d|uid=%d",
             (unsigned long long)g_shm_frames,
             (unsigned long long)g_other_frames,
             span,
             webkit_web_view_get_title(g_view) ?: "(null)",
             wpe_loader_get_loaded_implementation_library_name() ?: "(none)",
             (int)getpid(), (int)getuid());
    g_main_loop_quit(g_loop);
    return G_SOURCE_REMOVE;
}

static gboolean
t_watchdog(gpointer data)
{
    (void)data;
    report("spike_error|watchdog_timeout");
    g_main_loop_quit(g_loop);
    return G_SOURCE_REMOVE;
}

int
main(int argc, char **argv)
{
    const char *out = g_getenv("SD_SPIKE_OUT");
    const char *backend_lib = g_getenv("SD_WPE_BACKEND") ?: "libWPEBackend-fdo-1.0.so";

    setvbuf(stdout, NULL, _IOLBF, 0);
    report("spike_start|pid=%d|uid=%d|euid=%d|out=%s|backend_env=%s",
           (int)getpid(), (int)getuid(), (int)geteuid(), out ? out : "(unset)", backend_lib);
    report("spike_env|WPE_BACKEND=%s|LD_LIBRARY_PATH=%s|WEBKIT_EXEC_PATH=%s|WEBKIT_DISABLE_SANDBOX=%s",
           g_getenv("WPE_BACKEND") ?: "", g_getenv("LD_LIBRARY_PATH") ?: "",
           g_getenv("WEBKIT_EXEC_PATH") ?: "", g_getenv("WEBKIT_DISABLE_SANDBOX_THIS_IS_DANGEROUS") ?: "");

    if (!out || !*out) {
        report("spike_error|no_out_dir");
        return 2;
    }

    if (argc > 2) {
        g_width = atoi(argv[1]);
        g_height = atoi(argv[2]);
    }

    if (!wpe_loader_init(backend_lib)) {
        report("spike_error|wpe_loader_init|lib=%s", backend_lib);
        return 3;
    }
    report("spike_backend|name=%s", wpe_loader_get_loaded_implementation_library_name() ?: "(none)");

    if (!wpe_fdo_initialize_shm()) {
        report("spike_error|wpe_fdo_initialize_shm");
        return 4;
    }
    report("spike_backend|mode=shm");

    g_exportable = wpe_view_backend_exportable_fdo_create(&g_client, NULL, (uint32_t)g_width, (uint32_t)g_height);
    if (!g_exportable) {
        report("spike_error|exportable_create");
        return 5;
    }
    g_backend = wpe_view_backend_exportable_fdo_get_view_backend(g_exportable);
    if (!g_backend) {
        report("spike_error|get_view_backend");
        return 6;
    }

    WebKitWebViewBackend *view_backend = webkit_web_view_backend_new(g_backend, NULL, NULL);
    g_view = WEBKIT_WEB_VIEW(webkit_web_view_new(view_backend));
    if (!g_view) {
        report("spike_error|web_view_new");
        return 7;
    }
    report("spike_view|created=1|w=%d|h=%d", g_width, g_height);

    g_mutex_init(&g_frame_lock);

    WebKitSettings *settings = webkit_web_view_get_settings(g_view);
    webkit_settings_set_enable_javascript(settings, TRUE);
    webkit_settings_set_enable_developer_extras(settings, FALSE);
    webkit_settings_set_enable_write_console_messages_to_stdout(settings, TRUE);
    webkit_settings_set_javascript_can_open_windows_automatically(settings, FALSE);
    webkit_settings_set_user_agent(settings,
        "Mozilla/5.0 (Linux; Android 10; SailDroid) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Mobile Safari/537.36");

    g_signal_connect(g_view, "load-changed", G_CALLBACK(on_load_changed), NULL);
    g_signal_connect(g_view, "load-failed", G_CALLBACK(on_load_failed), NULL);
    g_signal_connect(g_view, "decide-policy", G_CALLBACK(on_decide_policy), NULL);
    g_signal_connect(g_view, "notify::title", G_CALLBACK(on_title_changed), NULL);

    webkit_web_view_load_html(g_view, PAGE_HTML, "https://ptlogin2.qq.com/");
    report("spike_load_html|base=https://ptlogin2.qq.com/|len=%zu", strlen(PAGE_HTML));

    g_loop = g_main_loop_new(NULL, FALSE);
    g_timeout_add(1200, t_cookies, NULL);
    g_timeout_add(1800, t_save, (gpointer)"frame-load");
    g_timeout_add(2000, t_log_title, (gpointer)"2.0s");
    g_timeout_add(2200, t_scroll_down, NULL);
    g_timeout_add(3200, t_log_title, (gpointer)"3.2s-after-scroll-down");
    g_timeout_add(3400, t_save, (gpointer)"frame-scrolled");
    g_timeout_add(4200, t_scroll_up, NULL);
    g_timeout_add(5200, t_log_title, (gpointer)"5.2s-after-scroll-up");
    g_timeout_add(5400, t_save, (gpointer)"frame-scrolled-up");
    g_timeout_add(6500, t_finish, NULL);

    /* Hard watchdog: never leave a stuck process behind on the device. */
    g_timeout_add(20000, t_watchdog, NULL);

    g_main_loop_run(g_loop);

    save_frame("frame-cleanup");
    report("spike_exit|frames=%llu", (unsigned long long)g_shm_frames);
    return g_shm_frames > 0 ? 0 : 8;
}
