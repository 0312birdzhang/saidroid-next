/* SaiDroid Wayland 窗口层
 * 负责：创建 xdg-shell 窗口、EGL surface、渲染循环
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <wayland-client.h>
#include <wayland-egl.h>
#include <EGL/egl.h>
#include <GLES2/gl2.h>
#include "xdg-shell-client-protocol.h"

typedef struct {
    struct wl_display    *display;
    struct wl_registry   *registry;
    struct wl_compositor *compositor;
    struct wl_shm        *shm;
    struct wl_seat       *seat;
    struct wl_pointer    *pointer;
    struct wl_keyboard   *keyboard;
    struct wl_touch      *touch;
    struct xdg_wm_base   *wm_base;
    struct xdg_surface   *xdg_surface;
    struct xdg_toplevel  *xdg_toplevel;
    struct wl_surface    *surface;
    struct wl_egl_window *egl_window;
    EGLDisplay            egl_display;
    EGLContext            egl_context;
    EGLSurface            egl_surface;
    int width, height;
    int configured;
    int running;
    /* 输入状态 */
    int ptr_x, ptr_y;
    int ptr_pressed;
    int touch_active;
} sd_state;

static sd_state g;

/* ---------- 输入事件 ---------- */
static void ptr_enter(void *d, struct wl_pointer *p, uint32_t serial,
                      struct wl_surface *s, wl_fixed_t x, wl_fixed_t y) {
    (void)d;(void)p;(void)serial;(void)s;
    g.ptr_x = wl_fixed_to_int(x);
    g.ptr_y = wl_fixed_to_int(y);
    printf("sd_input=ptr_enter|x=%d|y=%d\n", g.ptr_x, g.ptr_y);
    fflush(stdout);
}
static void ptr_leave(void *d, struct wl_pointer *p, uint32_t serial,
                      struct wl_surface *s) {
    (void)d;(void)p;(void)serial;(void)s;
    printf("sd_input=ptr_leave\n"); fflush(stdout);
}
static void ptr_motion(void *d, struct wl_pointer *p, uint32_t t,
                       wl_fixed_t x, wl_fixed_t y) {
    (void)d;(void)p;(void)t;
    g.ptr_x = wl_fixed_to_int(x);
    g.ptr_y = wl_fixed_to_int(y);
}
static void ptr_button(void *d, struct wl_pointer *p, uint32_t serial,
                       uint32_t t, uint32_t button, uint32_t state) {
    (void)d;(void)p;(void)serial;(void)t;(void)button;
    g.ptr_pressed = (state == WL_POINTER_BUTTON_STATE_PRESSED);
    printf("sd_input=ptr_button|pressed=%d|x=%d|y=%d\n",
           g.ptr_pressed, g.ptr_x, g.ptr_y);
    fflush(stdout);
}
static void ptr_axis(void *d, struct wl_pointer *p, uint32_t t,
                     uint32_t axis, wl_fixed_t v) {
    (void)d;(void)p;(void)t;(void)axis;(void)v;
}
static const struct wl_pointer_listener ptr_listener = {
    ptr_enter, ptr_leave, ptr_motion, ptr_button, ptr_axis,
};

static void kbd_keymap(void *d, struct wl_keyboard *k, uint32_t fmt,
                       int32_t fd, uint32_t size) {
    (void)d;(void)k;(void)fmt;(void)size;
    if (fd >= 0) close(fd);
}
static void kbd_enter(void *d, struct wl_keyboard *k, uint32_t serial,
                      struct wl_surface *s, struct wl_array *keys) {
    (void)d;(void)k;(void)serial;(void)s;(void)keys;
    printf("sd_input=kbd_enter\n"); fflush(stdout);
}
static void kbd_leave(void *d, struct wl_keyboard *k, uint32_t serial,
                      struct wl_surface *s) {
    (void)d;(void)k;(void)serial;(void)s;
}
static void kbd_key(void *d, struct wl_keyboard *k, uint32_t serial,
                    uint32_t t, uint32_t key, uint32_t state) {
    (void)d;(void)k;(void)serial;(void)t;
    printf("sd_input=key|code=%u|state=%u\n", key, state);
    fflush(stdout);
}
static void kbd_modifiers(void *d, struct wl_keyboard *k, uint32_t serial,
                          uint32_t a, uint32_t b, uint32_t c, uint32_t e) {
    (void)d;(void)k;(void)serial;(void)a;(void)b;(void)c;(void)e;
}
static void kbd_repeat(void *d, struct wl_keyboard *k, int32_t rate, int32_t delay) {
    (void)d;(void)k;(void)rate;(void)delay;
}
static const struct wl_keyboard_listener kbd_listener = {
    kbd_keymap, kbd_enter, kbd_leave, kbd_key, kbd_modifiers, kbd_repeat,
};

static void touch_down(void *d, struct wl_touch *t, uint32_t serial,
                       uint32_t time, struct wl_surface *s, int32_t id,
                       wl_fixed_t x, wl_fixed_t y) {
    (void)d;(void)t;(void)serial;(void)time;(void)s;(void)id;
    g.touch_active = 1;
    printf("sd_input=touch_down|x=%d|y=%d\n",
           wl_fixed_to_int(x), wl_fixed_to_int(y));
    fflush(stdout);
}
static void touch_up(void *d, struct wl_touch *t, uint32_t serial,
                     uint32_t time, int32_t id) {
    (void)d;(void)t;(void)serial;(void)time;(void)id;
    g.touch_active = 0;
    printf("sd_input=touch_up\n"); fflush(stdout);
}
static void touch_motion(void *d, struct wl_touch *t, uint32_t time,
                         int32_t id, wl_fixed_t x, wl_fixed_t y) {
    (void)d;(void)t;(void)time;(void)id;
    g.ptr_x = wl_fixed_to_int(x);
    g.ptr_y = wl_fixed_to_int(y);
}
static void touch_frame(void *d, struct wl_touch *t) { (void)d;(void)t; }
static void touch_cancel(void *d, struct wl_touch *t) { (void)d;(void)t; }
static const struct wl_touch_listener touch_listener = {
    touch_down, touch_up, touch_motion, touch_frame, touch_cancel,
};

static void seat_capabilities(void *d, struct wl_seat *s, uint32_t caps) {
    (void)d;
    printf("sd_seat=caps|0x%x\n", caps); fflush(stdout);
    if ((caps & WL_SEAT_CAPABILITY_POINTER) && !g.pointer) {
        g.pointer = wl_seat_get_pointer(s);
        wl_pointer_add_listener(g.pointer, &ptr_listener, NULL);
        printf("sd_seat=pointer_ok\n"); fflush(stdout);
    }
    if ((caps & WL_SEAT_CAPABILITY_KEYBOARD) && !g.keyboard) {
        g.keyboard = wl_seat_get_keyboard(s);
        wl_keyboard_add_listener(g.keyboard, &kbd_listener, NULL);
        printf("sd_seat=keyboard_ok\n"); fflush(stdout);
    }
    if ((caps & WL_SEAT_CAPABILITY_TOUCH) && !g.touch) {
        g.touch = wl_seat_get_touch(s);
        wl_touch_add_listener(g.touch, &touch_listener, NULL);
        printf("sd_seat=touch_ok\n"); fflush(stdout);
    }
}
static void seat_name(void *d, struct wl_seat *s, const char *name) {
    (void)d;(void)s;
    printf("sd_seat=name|%s\n", name ? name : "?"); fflush(stdout);
}
static const struct wl_seat_listener seat_listener = { seat_capabilities, seat_name };

/* ---------- xdg-shell ---------- */
static void xdg_wm_ping(void *d, struct xdg_wm_base *b, uint32_t serial) {
    (void)d;
    xdg_wm_base_pong(b, serial);
}
static const struct xdg_wm_base_listener wm_listener = { xdg_wm_ping };

static void xdg_surf_configure(void *d, struct xdg_surface *s, uint32_t serial) {
    (void)d;
    xdg_surface_ack_configure(s, serial);
    g.configured = 1;
    printf("sd_surface=configured\n"); fflush(stdout);
}
static const struct xdg_surface_listener surf_listener = { xdg_surf_configure };

static void top_configure(void *d, struct xdg_toplevel *t, int32_t w, int32_t h,
                          struct wl_array *states) {
    (void)d;(void)t;(void)states;
    if (w > 0) g.width = w;
    if (h > 0) g.height = h;
    printf("sd_toplevel=configure|w=%d|h=%d\n", w, h); fflush(stdout);
}
static void top_close(void *d, struct xdg_toplevel *t) {
    (void)d;(void)t;
    printf("sd_toplevel=close\n"); fflush(stdout);
    g.running = 0;
}
static const struct xdg_toplevel_listener top_listener = { top_configure, top_close };

/* ---------- registry ---------- */
static void reg_global(void *d, struct wl_registry *r, uint32_t name,
                       const char *iface, uint32_t version) {
    (void)d;
    printf("sd_global=%s|ver=%u\n", iface, version);
    if (strcmp(iface, wl_compositor_interface.name) == 0) {
        g.compositor = wl_registry_bind(r, name, &wl_compositor_interface, 3);
    } else if (strcmp(iface, wl_shm_interface.name) == 0) {
        g.shm = wl_registry_bind(r, name, &wl_shm_interface, 1);
    } else if (strcmp(iface, wl_seat_interface.name) == 0) {
        g.seat = wl_registry_bind(r, name, &wl_seat_interface, 3);
        wl_seat_add_listener(g.seat, &seat_listener, NULL);
    } else if (strcmp(iface, xdg_wm_base_interface.name) == 0) {
        g.wm_base = wl_registry_bind(r, name, &xdg_wm_base_interface, 1);
        xdg_wm_base_add_listener(g.wm_base, &wm_listener, NULL);
    }
}
static void reg_remove(void *d, struct wl_registry *r, uint32_t name) {
    (void)d;(void)r;(void)name;
}
static const struct wl_registry_listener reg_listener = { reg_global, reg_remove };

/* ---------- EGL ---------- */
static int egl_init(void) {
    g.egl_display = eglGetDisplay((EGLNativeDisplayType)g.display);
    if (g.egl_display == EGL_NO_DISPLAY) {
        printf("sd_egl=fail|no_display\n"); return -1;
    }
    EGLint major, minor;
    if (!eglInitialize(g.egl_display, &major, &minor)) {
        printf("sd_egl=fail|init\n"); return -1;
    }
    printf("sd_egl=version|%d.%d\n", major, minor);

    EGLint cfg_attr[] = {
        EGL_SURFACE_TYPE, EGL_WINDOW_BIT,
        EGL_RENDERABLE_TYPE, EGL_OPENGL_ES2_BIT,
        EGL_RED_SIZE, 8, EGL_GREEN_SIZE, 8, EGL_BLUE_SIZE, 8, EGL_ALPHA_SIZE, 8,
        EGL_NONE
    };
    EGLConfig cfg; EGLint n = 0;
    if (!eglChooseConfig(g.egl_display, cfg_attr, &cfg, 1, &n) || n < 1) {
        printf("sd_egl=fail|choose_config\n"); return -1;
    }
    EGLint ctx_attr[] = { EGL_CONTEXT_CLIENT_VERSION, 2, EGL_NONE };
    g.egl_context = eglCreateContext(g.egl_display, cfg, EGL_NO_CONTEXT, ctx_attr);
    if (g.egl_context == EGL_NO_CONTEXT) {
        printf("sd_egl=fail|create_context\n"); return -1;
    }
    g.egl_surface = eglCreateWindowSurface(g.egl_display, cfg,
                        (EGLNativeWindowType)g.egl_window, NULL);
    if (g.egl_surface == EGL_NO_SURFACE) {
        printf("sd_egl=fail|create_surface\n"); return -1;
    }
    if (!eglMakeCurrent(g.egl_display, g.egl_surface, g.egl_surface, g.egl_context)) {
        printf("sd_egl=fail|make_current\n"); return -1;
    }
    printf("sd_egl=ready\n");
    printf("sd_gl=vendor|%s\n", (const char*)glGetString(GL_VENDOR));
    printf("sd_gl=renderer|%s\n", (const char*)glGetString(GL_RENDERER));
    printf("sd_gl=version|%s\n", (const char*)glGetString(GL_VERSION));
    fflush(stdout);
    return 0;
}

static void draw_frame(float t) {
    glViewport(0, 0, g.width, g.height);
    float r = 0.5f + 0.5f * (float)((int)(t) % 2);
    glClearColor(0.1f, 0.2f + 0.2f*r, 0.4f, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT);
    eglSwapBuffers(g.egl_display, g.egl_surface);
}

int main(int argc, char **argv) {
    printf("sd=start\n"); fflush(stdout);
    g.width = 1080; g.height = 2160; g.running = 1;

    g.display = wl_display_connect(NULL);
    if (!g.display) { printf("sd=fail|no_wayland_display\n"); return 1; }
    printf("sd=wayland_connected\n"); fflush(stdout);

    g.registry = wl_display_get_registry(g.display);
    wl_registry_add_listener(g.registry, &reg_listener, NULL);
    wl_display_roundtrip(g.display);
    wl_display_roundtrip(g.display);

    if (!g.compositor) { printf("sd=fail|no_compositor\n"); return 1; }
    if (!g.wm_base) { printf("sd=fail|no_xdg_wm_base\n"); return 1; }
    printf("sd=globals_ok|compositor=%d|shm=%d|seat=%d\n",
           !!g.compositor, !!g.shm, !!g.seat); fflush(stdout);

    g.surface = wl_compositor_create_surface(g.compositor);
    g.xdg_surface = xdg_wm_base_get_xdg_surface(g.wm_base, g.surface);
    xdg_surface_add_listener(g.xdg_surface, &surf_listener, NULL);
    g.xdg_toplevel = xdg_surface_get_toplevel(g.xdg_surface);
    xdg_toplevel_add_listener(g.xdg_toplevel, &top_listener, NULL);
    xdg_toplevel_set_title(g.xdg_toplevel, "SaiDroid");
    xdg_toplevel_set_app_id(g.xdg_toplevel, "org.saidroid.test");

    /* 先 commit 让 compositor 发 configure */
    wl_surface_commit(g.surface);
    printf("sd=commit_sent\n"); fflush(stdout);

    /* 等 configure（最多 50 次 roundtrip） */
    int wait = 0;
    while (!g.configured && wait < 50) {
        if (wl_display_roundtrip(g.display) < 0) break;
        wait++;
    }
    printf("sd=configure_wait|roundtrips=%d|configured=%d\n", wait, g.configured);
    fflush(stdout);

    if (!g.configured) {
        printf("sd=warn|no_configure_continuing\n"); fflush(stdout);
    }

    /* configure 之后才创建 egl window */
    g.egl_window = wl_egl_window_create(g.surface, g.width, g.height);
    if (!g.egl_window) {
        printf("sd=fail|egl_window_null\n");
        return 1;
    }
    printf("sd=egl_window_created|w=%d|h=%d\n", g.width, g.height); fflush(stdout);

    if (egl_init() != 0) {
        printf("sd=fail|egl_init\n");
        return 1;
    }

    printf("sd=render_loop_start\n"); fflush(stdout);
    int frames = 0;
    while (g.running && frames < 60) {
        wl_display_dispatch_pending(g.display);
        draw_frame((float)frames);
        wl_display_flush(g.display);
        if (frames == 0 || frames == 30 || frames == 59) {
            printf("sd_frame=%d\n", frames); fflush(stdout);
        }
        frames++;
        usleep(16000);  /* ~60fps */
    }
    printf("sd=render_loop_end|frames=%d\n", frames);
    printf("sd=SUCCESS\n");
    return 0;
}
