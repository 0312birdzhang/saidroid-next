/* SaiDroid 看图器：把 Android 渲染出的 ARGB 像素贴到 Wayland 窗口。
 * 输入文件格式：魔数 "SDRGBA\0\0" + uint32 w + uint32 h + w*h 个 uint32(ARGB, LE)
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <poll.h>
#include <time.h>
#include <wayland-client.h>
#include "xdg-shell-client-protocol.h"

static struct wl_display *dpy;
static struct wl_compositor *comp;
static struct wl_shm *shm;
static struct xdg_wm_base *wmb;
static struct wl_seat *seat;
static struct wl_touch *touch;
static struct wl_pointer *ptr;
static int W = 0, H = 0, configured = 0, running = 1;
static int auto_exit_secs = 90;   /* 安全阀：到时自动退出，绝不长期占用屏幕 */
static int cfg_w = 0, cfg_h = 0;
static int target_w = 540;   /* 预览窗口宽度（不占满屏） */

/* 把触摸事件写到一个文件里，交给 Android 侧轮询；同时按 mtime 自动重载帧，
 * 这样手指一动 -> Java 侧重画 -> 屏幕跟着变，形成真正的交互闭环。 */
static int ev_fd = -1;
static const char *frame_path = NULL;
static int watch_frame = 0;
static int pattern_mode = 0;
static int scale_step = 1;
static uint32_t *src_pixels = NULL;
static int src_w = 0, src_h = 0;
static double ev_sx = 1.0, ev_sy = 1.0;   /* surface 坐标 -> 帧坐标 */
static uint32_t *frame_pixels = NULL;   /* 原始分辨率的帧 */
static int ptr_x = 0, ptr_y = 0;
static void *shm_data = NULL;
static size_t shm_size = 0;
static struct wl_surface *g_surf = NULL;

static void emit_event(char kind, int x, int y)
{
	if (ev_fd < 0) return;
	char line[64];
	int n;
	if (kind == 'U') n = snprintf(line, sizeof(line), "U\n");
	else n = snprintf(line, sizeof(line), "%c %d %d\n", kind, x, y);
	if (n > 0) { ssize_t r = write(ev_fd, line, (size_t)n); (void)r; }
}

static void wm_ping(void *d, struct xdg_wm_base *b, uint32_t serial) {
    (void)d; xdg_wm_base_pong(b, serial);
}
static const struct xdg_wm_base_listener wm_listener = { wm_ping };

/* --- 触摸 --- */
static void t_down(void *d, struct wl_touch *t, uint32_t serial, uint32_t time,
                   struct wl_surface *s, int32_t id, wl_fixed_t x, wl_fixed_t y) {
    (void)d;(void)t;(void)serial;(void)time;(void)s;(void)id;
    printf("TOUCH_DOWN x=%d y=%d\n", wl_fixed_to_int(x), wl_fixed_to_int(y));
    emit_event('D', (int)(wl_fixed_to_int(x) * ev_sx), (int)(wl_fixed_to_int(y) * ev_sy));
    fflush(stdout);
}
static void t_up(void *d, struct wl_touch *t, uint32_t serial, uint32_t time, int32_t id) {
    (void)d;(void)t;(void)serial;(void)time;(void)id;
    printf("TOUCH_UP\n");
    emit_event('U', 0, 0);
    fflush(stdout);
}
static void t_motion(void *d, struct wl_touch *t, uint32_t time, int32_t id, wl_fixed_t x, wl_fixed_t y) {
    (void)d;(void)t;(void)time;(void)id;
    printf("TOUCH_MOVE x=%d y=%d\n", wl_fixed_to_int(x), wl_fixed_to_int(y));
    emit_event('M', (int)(wl_fixed_to_int(x) * ev_sx), (int)(wl_fixed_to_int(y) * ev_sy));
    fflush(stdout);
    (void)id;
}
static void t_frame(void *d, struct wl_touch *t) { (void)d;(void)t; }
static void t_cancel(void *d, struct wl_touch *t) { (void)d;(void)t; printf("TOUCH_CANCEL\n"); emit_event('C', 0, 0); fflush(stdout); }
static const struct wl_touch_listener touch_listener = { t_down, t_up, t_motion, t_frame, t_cancel };

static void p_enter(void *d, struct wl_pointer *p, uint32_t serial, struct wl_surface *s, wl_fixed_t x, wl_fixed_t y) {
    (void)d;(void)p;(void)serial;(void)s;
    printf("PTR_ENTER x=%d y=%d\n", wl_fixed_to_int(x), wl_fixed_to_int(y)); fflush(stdout);
}
static void p_leave(void *d, struct wl_pointer *p, uint32_t serial, struct wl_surface *s) { (void)d;(void)p;(void)serial;(void)s; }
static void p_motion(void *d, struct wl_pointer *p, uint32_t t, wl_fixed_t x, wl_fixed_t y) {
    (void)d;(void)p;(void)t;
    ptr_x = wl_fixed_to_int(x); ptr_y = wl_fixed_to_int(y);
    printf("PTR_MOVE x=%d y=%d\n", wl_fixed_to_int(x), wl_fixed_to_int(y)); fflush(stdout);
}
static void p_button(void *d, struct wl_pointer *p, uint32_t serial, uint32_t t, uint32_t b, uint32_t state) {
    if (b == 0 /*BTN_LEFT*/) {
        emit_event(state ? 'D' : 'U', (int)(ptr_x * ev_sx), (int)(ptr_y * ev_sy));
    }
    (void)d;(void)p;(void)serial;(void)t;(void)b;
    printf("PTR_BUTTON state=%u\n", state); fflush(stdout);
}
static void p_axis(void *d, struct wl_pointer *p, uint32_t t, uint32_t a, wl_fixed_t v) { (void)d;(void)p;(void)t;(void)a;(void)v; }
static const struct wl_pointer_listener ptr_listener = { p_enter, p_leave, p_motion, p_button, p_axis };

static void seat_caps(void *d, struct wl_seat *s, uint32_t caps) {
    (void)d;
    if ((caps & WL_SEAT_CAPABILITY_TOUCH) && !touch) {
        touch = wl_seat_get_touch(s);
        wl_touch_add_listener(touch, &touch_listener, NULL);
        printf("SEAT touch=1\n"); fflush(stdout);
    }
    if ((caps & WL_SEAT_CAPABILITY_POINTER) && !ptr) {
        ptr = wl_seat_get_pointer(s);
        wl_pointer_add_listener(ptr, &ptr_listener, NULL);
        printf("SEAT pointer=1\n"); fflush(stdout);
    }
}
static void seat_name(void *d, struct wl_seat *s, const char *n) { (void)d;(void)s;(void)n; }
static const struct wl_seat_listener seat_listener = { seat_caps, seat_name };

static void reg_global(void *d, struct wl_registry *r, uint32_t name, const char *iface, uint32_t ver) {
    (void)d;(void)ver;
    if (!strcmp(iface, wl_compositor_interface.name)) comp = wl_registry_bind(r, name, &wl_compositor_interface, 3);
    else if (!strcmp(iface, wl_shm_interface.name)) shm = wl_registry_bind(r, name, &wl_shm_interface, 1);
    else if (!strcmp(iface, xdg_wm_base_interface.name)) {
        wmb = wl_registry_bind(r, name, &xdg_wm_base_interface, 1);
        xdg_wm_base_add_listener(wmb, &wm_listener, NULL);
    }
    else if (!strcmp(iface, wl_seat_interface.name)) {
        seat = wl_registry_bind(r, name, &wl_seat_interface, 3);
        wl_seat_add_listener(seat, &seat_listener, NULL);
    }
}
static void reg_remove(void *d, struct wl_registry *r, uint32_t n) { (void)d;(void)r;(void)n; }
static const struct wl_registry_listener reg_listener = { reg_global, reg_remove };

static void xs_configure(void *d, struct xdg_surface *xs, uint32_t serial) {
    (void)d; xdg_surface_ack_configure(xs, serial); configured = 1;
    printf("XDG_CONFIGURE\n"); fflush(stdout);
}
static const struct xdg_surface_listener xs_listener = { xs_configure };

static void tl_configure(void *d, struct xdg_toplevel *t, int32_t w, int32_t h, struct wl_array *st) {
    (void)d;(void)t;(void)st;
    cfg_w = w; cfg_h = h;
    printf("TL_CONFIGURE w=%d h=%d\n", w, h); fflush(stdout);
}
static void tl_close(void *d, struct xdg_toplevel *t) { (void)d;(void)t; running = 0; }
static const struct xdg_toplevel_listener tl_listener = { tl_configure, tl_close };

static ssize_t read_full(int fd, void *buf, size_t n) {
    size_t got = 0;
    while (got < n) {
        ssize_t r = read(fd, (char*)buf + got, n - got);
        if (r <= 0) return got;
        got += (size_t)r;
    }
    return (ssize_t)got;
}

static int load_frame(const char *path, uint32_t **out) {
    int fd = open(path, O_RDONLY);
    if (fd < 0) { perror("open frame"); return -1; }
    char magic[7]; uint32_t w, h;
    if (read_full(fd, magic, 7) != 7 || memcmp(magic, "SDRGBA", 6)) { fprintf(stderr, "bad magic\n"); close(fd); return -1; }
    if (read_full(fd, &w, 4) != 4 || read_full(fd, &h, 4) != 4) { close(fd); return -1; }
    size_t sz = (size_t)w * h * 4;
    uint32_t *buf = malloc(sz);
    if (read_full(fd, buf, sz) != (ssize_t)sz) { fprintf(stderr, "short read\n"); free(buf); close(fd); return -1; }
    close(fd);
    *out = buf;
    src_w = (int)w; src_h = (int)h;
    printf("FRAME_LOADED w=%u h=%u\n", w, h); fflush(stdout);
    return 0;
}

/* 把 src 帧按最近邻缩放贴到 dst(dw x dh)。屏幕 1080x2160 与 540x1080 正好 2 倍，
 * 所以这一步通常是精确的整数放大，不会有插值模糊。 */
static void blit_scale(uint32_t *dst, int dw, int dh, const uint32_t *src, int sw, int sh)
{
    if (dw <= 0 || dh <= 0 || sw <= 0 || sh <= 0) return;
    for (int y = 0; y < dh; ++y) {
        int sy = (int)((long long)y * sh / dh);
        const uint32_t *srow = src + (size_t)sy * sw;
        uint32_t *drow = dst + (size_t)y * dw;
        for (int x = 0; x < dw; ++x)
            drow[x] = srow[(int)((long long)x * sw / dw)];
    }
}

/* 诊断花纹：四角标记 + 网格，用来肉眼确认窗口是不是真的铺满整屏 */
static void fill_pattern(uint32_t *dst, int dw, int dh)
{
    for (int y = 0; y < dh; ++y) {
        for (int x = 0; x < dw; ++x) {
            uint32_t c = ((x / 120) + (y / 120)) & 1 ? 0xFF101820 : 0xFF1B2836;
            dst[(size_t)y * dw + x] = c;
        }
    }
    int m = 80;
    for (int y = 0; y < dh; ++y) {
        for (int x = 0; x < dw; ++x) {
            int corner = (x < m && y < m) || (x >= dw - m && y < m) ||
                         (x < m && y >= dh - m) || (x >= dw - m && y >= dh - m);
            if (corner) dst[(size_t)y * dw + x] = 0xFFE05252;
            if (x < 4 || y < 4 || x >= dw - 4 || y >= dh - 4)
                dst[(size_t)y * dw + x] = 0xFF4CC38A;   /* 边框：应该正好贴着屏幕四边 */
        }
    }
}

/* 重新读帧文件，缩放进 shm，供 --watch 用 */
static int reload_frame(void)
{
    if (!frame_path || !shm_data) return -1;
    int fd = open(frame_path, O_RDONLY);
    if (fd < 0) return -1;
    char magic[7]; uint32_t w, h;
    if (read_full(fd, magic, 7) != 7 || memcmp(magic, "SDRGBA", 6)) { close(fd); return -1; }
    if (read_full(fd, &w, 4) != 4 || read_full(fd, &h, 4) != 4) { close(fd); return -1; }
    size_t sz = (size_t)w * h * 4;
    uint32_t *buf = malloc(sz);
    if (!buf) { close(fd); return -1; }
    if (read_full(fd, buf, sz) != (ssize_t)sz) { free(buf); close(fd); return -1; }
    close(fd);

    if ((int)w != src_w || (int)h != src_h) {
        free(src_pixels);
        src_pixels = buf;
        src_w = (int)w; src_h = (int)h;
        ev_sx = (double)src_w / (double)W;
        ev_sy = (double)src_h / (double)H;
        printf("RELOAD_SIZE w=%d h=%d\n", src_w, src_h);
    } else {
        free(src_pixels);
        src_pixels = buf;
    }
    blit_scale((uint32_t *)shm_data, W, H, src_pixels, src_w, src_h);

    wl_surface_commit(g_surf);
    wl_display_flush(dpy);
    return 0;
}

int main(int argc, char **argv) {
    const char *path = "/home/art/frame.rgba";
    for (int i = 1; i < argc; ++i) {
        if (!strcmp(argv[i], "--evfile") && i + 1 < argc) {
            ev_fd = open(argv[++i], O_WRONLY | O_APPEND | O_CREAT, 0644);
            if (ev_fd < 0) perror("open evfile");
        }
        else if (!strcmp(argv[i], "--watch")) watch_frame = 1;
        else if (!strcmp(argv[i], "--pattern")) pattern_mode = 1;
        else if (!strcmp(argv[i], "-t") && i + 1 < argc) auto_exit_secs = atoi(argv[++i]);
        else if (!strcmp(argv[i], "-w") && i + 1 < argc) target_w = atoi(argv[++i]);
        else path = argv[i];
    }
    uint32_t *pixels = NULL;
    frame_path = path;
    if (load_frame(path, &pixels) < 0) return 2;

    src_pixels = pixels;
    /* 输出尺寸不再由 -w 决定：合成器可能强制整屏，buffer 必须跟 configure 尺寸一致，
     * 否则内容只占窗口左上角、其余是空区（看起来就是"只有左上角一块"）。 */

    dpy = wl_display_connect(NULL);
    if (!dpy) { fprintf(stderr, "wl_display_connect failed\n"); return 3; }
    struct wl_registry *reg = wl_display_get_registry(dpy);
    wl_registry_add_listener(reg, &reg_listener, NULL);
    wl_display_roundtrip(dpy);
    if (!comp || !shm || !wmb) { fprintf(stderr, "missing globals comp=%p shm=%p wmb=%p\n", (void*)comp, (void*)shm, (void*)wmb); return 4; }

    struct wl_surface *surf = wl_compositor_create_surface(comp);
    struct xdg_surface *xs = xdg_wm_base_get_xdg_surface(wmb, surf);
    xdg_surface_add_listener(xs, &xs_listener, NULL);
    struct xdg_toplevel *tl = xdg_surface_get_toplevel(xs);
    xdg_toplevel_add_listener(tl, &tl_listener, NULL);
    xdg_toplevel_set_title(tl, "SaiDroid");
    xdg_toplevel_set_min_size(tl, src_w / 2, src_h / 2);
    xdg_toplevel_set_max_size(tl, src_w, src_h);
    xdg_toplevel_set_app_id(tl, "saidroid-viewer");
    wl_surface_commit(surf);
    wl_display_roundtrip(dpy);

    /* 到这一步已经收到第一次 xdg_toplevel.configure，知道合成器想要的尺寸 */
    W = (cfg_w > 0) ? cfg_w : src_w;
    H = (cfg_h > 0) ? cfg_h : src_h;
    ev_sx = (double)src_w / (double)W;
    ev_sy = (double)src_h / (double)H;
    printf("OUT w=%d h=%d src=%dx%d scale=%.3fx%.3f\n", W, H, src_w, src_h,
           (double)W / (double)src_w, (double)H / (double)src_h);
    fflush(stdout);

    size_t sz = (size_t)W * H * 4;
    int fd = memfd_create("sdview", MFD_CLOEXEC);
    if (fd < 0 || ftruncate(fd, sz) < 0) { perror("memfd"); return 5; }
    void *data = mmap(NULL, sz, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (data == MAP_FAILED) { perror("mmap"); return 6; }
    if (pattern_mode) {
        fill_pattern((uint32_t *)data, W, H);
        printf("PATTERN w=%d h=%d\n", W, H); fflush(stdout);
    } else {
        blit_scale((uint32_t *)data, W, H, src_pixels, src_w, src_h);
    }
    shm_data = data;
    shm_size = sz;
    g_surf = surf;
    struct wl_shm_pool *pool = wl_shm_create_pool(shm, fd, sz);
    struct wl_buffer *buf = wl_shm_pool_create_buffer(pool, 0, W, H, W * 4, WL_SHM_FORMAT_ARGB8888);
    wl_surface_attach(surf, buf, 0, 0);
    wl_surface_damage(surf, 0, 0, W, H);
    wl_surface_commit(surf);
    wl_display_flush(dpy);
    printf("VIEWER_READY\n"); fflush(stdout);

    time_t start = time(NULL);
    struct stat st;
    time_t last_mtime = 0;
    if (watch_frame && stat(frame_path, &st) == 0) last_mtime = st.st_mtime;
    printf("VIEWER_TIMEOUT %d\n", auto_exit_secs);
    if (watch_frame) printf("VIEWER_WATCHING %s\n", frame_path);
    if (ev_fd >= 0) printf("VIEWER_EVFILE ready\n");
    fflush(stdout);

    while (running) {
        /* 用 poll 带超时，才能在没事件的时候也去检查帧文件有没有更新 */
        while (wl_display_prepare_read(dpy) != 0) {
            if (wl_display_dispatch_pending(dpy) < 0) { running = 0; break; }
        }
        if (!running) { wl_display_cancel_read(dpy); break; }
        wl_display_flush(dpy);
        struct pollfd pfd = { wl_display_get_fd(dpy), POLLIN, 0 };
        int pr = poll(&pfd, 1, 100);
        if (pr > 0) {
            if (wl_display_read_events(dpy) < 0) { running = 0; break; }
            if (wl_display_dispatch_pending(dpy) < 0) { running = 0; break; }
        } else if (pr == 0) {
            wl_display_cancel_read(dpy);
        } else {
            wl_display_cancel_read(dpy);
            break;
        }
        if (watch_frame && stat(frame_path, &st) == 0 && st.st_mtime != last_mtime) {
            last_mtime = st.st_mtime;
            reload_frame();
        }
        if (auto_exit_secs > 0 && (time(NULL) - start) >= auto_exit_secs) {
            printf("VIEWER_TIMEOUT_EXIT\n"); fflush(stdout);
            break;
        }
    }
    printf("VIEWER_EXIT\n"); fflush(stdout);
    return 0;
}
