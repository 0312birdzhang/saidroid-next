/* SaiDroid 渲染桥接
 * 职责：接收 ARGB 像素缓冲区，上传为 GLES 纹理并渲染到 Wayland surface
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <wayland-client.h>
#include <wayland-egl.h>
#include <EGL/egl.h>
#include <GLES2/gl2.h>
#include "xdg-shell-client-protocol.h"

typedef struct {
    struct wl_display    *display;
    struct wl_registry   *registry;
    struct wl_compositor *compositor;
    struct wl_seat       *seat;
    struct wl_pointer    *pointer;
    struct wl_touch      *touch;
    struct wl_keyboard   *keyboard;
    struct xdg_wm_base   *wm_base;
    struct xdg_surface   *xdg_surface;
    struct xdg_toplevel  *xdg_toplevel;
    struct wl_surface    *surface;
    struct wl_egl_window *egl_window;
    EGLDisplay egl_display;
    EGLContext egl_context;
    EGLSurface egl_surface;
    int width, height, configured, running;
    /* 纹理渲染 */
    GLuint program;
    GLuint texture;
    GLint  a_pos, a_tex, u_tex;
    /* 输入回调计数 */
    int ptr_events, touch_events, key_events;
} rb_state;

static rb_state R;

/* ---------- 输入：只统计并打印关键事件 ---------- */
static void ptr_enter(void *d, struct wl_pointer *p, uint32_t s, struct wl_surface *sf,
                      wl_fixed_t x, wl_fixed_t y) {
    (void)d;(void)p;(void)s;(void)sf;(void)x;(void)y;
    R.ptr_events++;
}
static void ptr_leave(void *d, struct wl_pointer *p, uint32_t s, struct wl_surface *sf) {
    (void)d;(void)p;(void)s;(void)sf;
}
static void ptr_motion(void *d, struct wl_pointer *p, uint32_t t, wl_fixed_t x, wl_fixed_t y) {
    (void)d;(void)p;(void)t;(void)x;(void)y;
    R.ptr_events++;
}
static void ptr_button(void *d, struct wl_pointer *p, uint32_t s, uint32_t t,
                       uint32_t b, uint32_t st) {
    (void)d;(void)p;(void)s;(void)t;(void)b;
    R.ptr_events++;
    printf("rb_input=pointer_button|state=%u\n", st); fflush(stdout);
}
static void ptr_axis(void *d, struct wl_pointer *p, uint32_t t, uint32_t a, wl_fixed_t v) {
    (void)d;(void)p;(void)t;(void)a;(void)v;
}
static const struct wl_pointer_listener ptr_l = { ptr_enter, ptr_leave, ptr_motion, ptr_button, ptr_axis };

static void kbd_keymap(void *d, struct wl_keyboard *k, uint32_t f, int32_t fd, uint32_t sz) {
    (void)d;(void)k;(void)f;(void)sz; if (fd>=0) close(fd);
}
static void kbd_enter(void *d, struct wl_keyboard *k, uint32_t s, struct wl_surface *sf, struct wl_array *a) {
    (void)d;(void)k;(void)s;(void)sf;(void)a;
}
static void kbd_leave(void *d, struct wl_keyboard *k, uint32_t s, struct wl_surface *sf) {
    (void)d;(void)k;(void)s;(void)sf;
}
static void kbd_key(void *d, struct wl_keyboard *k, uint32_t s, uint32_t t,
                    uint32_t key, uint32_t st) {
    (void)d;(void)k;(void)s;(void)t;
    R.key_events++;
    printf("rb_input=key|code=%u|state=%u\n", key, st); fflush(stdout);
}
static void kbd_mods(void *d, struct wl_keyboard *k, uint32_t s, uint32_t a,
                     uint32_t b, uint32_t c, uint32_t e) {
    (void)d;(void)k;(void)s;(void)a;(void)b;(void)c;(void)e;
}
static void kbd_rep(void *d, struct wl_keyboard *k, int32_t r, int32_t dl) {
    (void)d;(void)k;(void)r;(void)dl;
}
static const struct wl_keyboard_listener kbd_l = { kbd_keymap, kbd_enter, kbd_leave, kbd_key, kbd_mods, kbd_rep };

static void touch_down(void *d, struct wl_touch *t, uint32_t s, uint32_t tm,
                       struct wl_surface *sf, int32_t id, wl_fixed_t x, wl_fixed_t y) {
    (void)d;(void)t;(void)s;(void)tm;(void)sf;(void)id;(void)x;(void)y;
    R.touch_events++;
    printf("rb_input=touch_down|x=%d|y=%d\n", wl_fixed_to_int(x), wl_fixed_to_int(y));
    fflush(stdout);
}
static void touch_up(void *d, struct wl_touch *t, uint32_t s, uint32_t tm, int32_t id) {
    (void)d;(void)t;(void)s;(void)tm;(void)id;
    R.touch_events++;
    printf("rb_input=touch_up\n"); fflush(stdout);
}
static void touch_motion(void *d, struct wl_touch *t, uint32_t tm, int32_t id,
                         wl_fixed_t x, wl_fixed_t y) {
    (void)d;(void)t;(void)tm;(void)id;(void)x;(void)y;
    R.touch_events++;
}
static void touch_frame(void *d, struct wl_touch *t) { (void)d;(void)t; }
static void touch_cancel(void *d, struct wl_touch *t) { (void)d;(void)t; }
static const struct wl_touch_listener touch_l = { touch_down, touch_up, touch_motion, touch_frame, touch_cancel };

static void seat_caps(void *d, struct wl_seat *s, uint32_t caps) {
    (void)d;
    if ((caps & WL_SEAT_CAPABILITY_POINTER) && !R.pointer) {
        R.pointer = wl_seat_get_pointer(s);
        wl_pointer_add_listener(R.pointer, &ptr_l, NULL);
        printf("rb_seat=pointer\n");
    }
    if ((caps & WL_SEAT_CAPABILITY_KEYBOARD) && !R.keyboard) {
        R.keyboard = wl_seat_get_keyboard(s);
        wl_keyboard_add_listener(R.keyboard, &kbd_l, NULL);
        printf("rb_seat=keyboard\n");
    }
    if ((caps & WL_SEAT_CAPABILITY_TOUCH) && !R.touch) {
        R.touch = wl_seat_get_touch(s);
        wl_touch_add_listener(R.touch, &touch_l, NULL);
        printf("rb_seat=touch\n");
    }
    fflush(stdout);
}
static void seat_name(void *d, struct wl_seat *s, const char *n) { (void)d;(void)s;(void)n; }
static const struct wl_seat_listener seat_l = { seat_caps, seat_name };

static void wm_ping(void *d, struct xdg_wm_base *b, uint32_t s) {
    (void)d; xdg_wm_base_pong(b, s);
}
static const struct xdg_wm_base_listener wm_l = { wm_ping };

static void surf_cfg(void *d, struct xdg_surface *s, uint32_t serial) {
    (void)d; xdg_surface_ack_configure(s, serial);
    R.configured = 1;
    printf("rb_surface=configured\n"); fflush(stdout);
}
static const struct xdg_surface_listener surf_l = { surf_cfg };

static void top_cfg(void *d, struct xdg_toplevel *t, int32_t w, int32_t h, struct wl_array *st) {
    (void)d;(void)t;(void)st;
    if (w > 0) R.width = w;
    if (h > 0) R.height = h;
    printf("rb_toplevel=configure|w=%d|h=%d\n", w, h); fflush(stdout);
}
static void top_close(void *d, struct xdg_toplevel *t) { (void)d;(void)t; R.running = 0; }
static const struct xdg_toplevel_listener top_l = { top_cfg, top_close };

static void reg_global(void *d, struct wl_registry *r, uint32_t name,
                       const char *iface, uint32_t ver) {
    (void)d;
    if (!strcmp(iface, wl_compositor_interface.name))
        R.compositor = wl_registry_bind(r, name, &wl_compositor_interface, 3);
    else if (!strcmp(iface, wl_seat_interface.name)) {
        R.seat = wl_registry_bind(r, name, &wl_seat_interface, 3);
        wl_seat_add_listener(R.seat, &seat_l, NULL);
    } else if (!strcmp(iface, xdg_wm_base_interface.name)) {
        R.wm_base = wl_registry_bind(r, name, &xdg_wm_base_interface, 1);
        xdg_wm_base_add_listener(R.wm_base, &wm_l, NULL);
    }
}
static void reg_remove(void *d, struct wl_registry *r, uint32_t name) { (void)d;(void)r;(void)name; }
static const struct wl_registry_listener reg_l = { reg_global, reg_remove };

/* ---------- GLES 着色器 ---------- */
static const char *VS =
    "attribute vec2 a_pos;\n"
    "attribute vec2 a_tex;\n"
    "varying vec2 v_tex;\n"
    "void main() {\n"
    "  gl_Position = vec4(a_pos, 0.0, 1.0);\n"
    "  v_tex = a_tex;\n"
    "}\n";

static const char *FS =
    "precision mediump float;\n"
    "varying vec2 v_tex;\n"
    "uniform sampler2D u_tex;\n"
    "void main() {\n"
    "  gl_FragColor = texture2D(u_tex, v_tex);\n"
    "}\n";

static GLuint compile(GLenum type, const char *src) {
    GLuint s = glCreateShader(type);
    glShaderSource(s, 1, &src, NULL);
    glCompileShader(s);
    GLint ok = 0;
    glGetShaderiv(s, GL_COMPILE_STATUS, &ok);
    if (!ok) {
        char log[512];
        glGetShaderInfoLog(s, sizeof(log), NULL, log);
        printf("rb_gl=shader_fail|%s\n", log);
    }
    return s;
}

static int gl_setup(void) {
    GLuint vs = compile(GL_VERTEX_SHADER, VS);
    GLuint fs = compile(GL_FRAGMENT_SHADER, FS);
    R.program = glCreateProgram();
    glAttachShader(R.program, vs);
    glAttachShader(R.program, fs);
    glLinkProgram(R.program);
    GLint ok = 0;
    glGetProgramiv(R.program, GL_LINK_STATUS, &ok);
    if (!ok) { printf("rb_gl=link_fail\n"); return -1; }
    R.a_pos = glGetAttribLocation(R.program, "a_pos");
    R.a_tex = glGetAttribLocation(R.program, "a_tex");
    R.u_tex = glGetUniformLocation(R.program, "u_tex");

    glGenTextures(1, &R.texture);
    glBindTexture(GL_TEXTURE_2D, R.texture);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);

    printf("rb_gl=ready|prog=%u|tex=%u\n", R.program, R.texture);
    fflush(stdout);
    return 0;
}

/* 上传 ARGB 像素到纹理并绘制 */
static void draw_argb(const uint32_t *pixels, int w, int h) {
    glViewport(0, 0, R.width, R.height);
    glClearColor(0.0f, 0.0f, 0.0f, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT);

    glUseProgram(R.program);
    glActiveTexture(GL_TEXTURE0);
    glBindTexture(GL_TEXTURE_2D, R.texture);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA,
                 GL_UNSIGNED_BYTE, pixels);

    /* 全屏四边形（注意纹理 Y 翻转） */
    static const GLfloat verts[] = {
        -1.0f, -1.0f,   0.0f, 1.0f,
         1.0f, -1.0f,   1.0f, 1.0f,
        -1.0f,  1.0f,   0.0f, 0.0f,
         1.0f,  1.0f,   1.0f, 0.0f,
    };
    glEnableVertexAttribArray(R.a_pos);
    glEnableVertexAttribArray(R.a_tex);
    glVertexAttribPointer(R.a_pos, 2, GL_FLOAT, GL_FALSE, 16, verts);
    glVertexAttribPointer(R.a_tex, 2, GL_FLOAT, GL_FALSE, 16, verts + 2);
    glUniform1i(R.u_tex, 0);
    glDrawArrays(GL_TRIANGLE_STRIP, 0, 4);

    eglSwapBuffers(R.egl_display, R.egl_surface);
}

/* 生成测试图案：渐变色 + 移动方块 */
static void gen_test_pattern(uint32_t *buf, int w, int h, int frame) {
    for (int y = 0; y < h; y++) {
        for (int x = 0; x < w; x++) {
            uint8_t r = (uint8_t)(x * 255 / w);
            uint8_t g = (uint8_t)(y * 255 / h);
            uint8_t b = (uint8_t)((frame * 4) & 0xff);
            buf[y * w + x] = 0xff000000u | (r << 16) | (g << 8) | b;
        }
    }
    /* 移动的方块 */
    int bs = 160;
    int bx = (frame * 12) % (w - bs);
    int by = h / 2 - bs / 2;
    for (int y = by; y < by + bs && y < h; y++)
        for (int x = bx; x < bx + bs && x < w; x++)
            buf[y * w + x] = 0xffff8800u;
}

int main(int argc, char **argv) {
    int frames = (argc > 1) ? atoi(argv[1]) : 60;
    printf("rb=start|frames=%d\n", frames); fflush(stdout);
    R.width = 1080; R.height = 2160; R.running = 1;

    R.display = wl_display_connect(NULL);
    if (!R.display) { printf("rb=fail|no_display\n"); return 1; }
    printf("rb=wayland_ok\n");

    R.registry = wl_display_get_registry(R.display);
    wl_registry_add_listener(R.registry, &reg_l, NULL);
    wl_display_roundtrip(R.display);
    wl_display_roundtrip(R.display);

    if (!R.compositor || !R.wm_base) { printf("rb=fail|missing_globals\n"); return 1; }

    R.surface = wl_compositor_create_surface(R.compositor);
    R.xdg_surface = xdg_wm_base_get_xdg_surface(R.wm_base, R.surface);
    xdg_surface_add_listener(R.xdg_surface, &surf_l, NULL);
    R.xdg_toplevel = xdg_surface_get_toplevel(R.xdg_surface);
    xdg_toplevel_add_listener(R.xdg_toplevel, &top_l, NULL);
    xdg_toplevel_set_title(R.xdg_toplevel, "SaiDroid Canvas");

    wl_surface_commit(R.surface);
    int w = 0;
    while (!R.configured && w < 50) { if (wl_display_roundtrip(R.display) < 0) break; w++; }
    printf("rb=configured|wait=%d\n", w);

    R.egl_window = wl_egl_window_create(R.surface, R.width, R.height);
    R.egl_display = eglGetDisplay((EGLNativeDisplayType)R.display);
    if (!eglInitialize(R.egl_display, NULL, NULL)) { printf("rb=fail|egl_init\n"); return 1; }

    EGLint cfg_attr[] = {
        EGL_SURFACE_TYPE, EGL_WINDOW_BIT,
        EGL_RENDERABLE_TYPE, EGL_OPENGL_ES2_BIT,
        EGL_RED_SIZE, 8, EGL_GREEN_SIZE, 8, EGL_BLUE_SIZE, 8, EGL_ALPHA_SIZE, 8,
        EGL_NONE
    };
    EGLConfig cfg; EGLint n = 0;
    eglChooseConfig(R.egl_display, cfg_attr, &cfg, 1, &n);
    EGLint ctx_attr[] = { EGL_CONTEXT_CLIENT_VERSION, 2, EGL_NONE };
    R.egl_context = eglCreateContext(R.egl_display, cfg, EGL_NO_CONTEXT, ctx_attr);
    R.egl_surface = eglCreateWindowSurface(R.egl_display, cfg,
                        (EGLNativeWindowType)R.egl_window, NULL);
    if (!eglMakeCurrent(R.egl_display, R.egl_surface, R.egl_surface, R.egl_context)) {
        printf("rb=fail|make_current\n"); return 1;
    }
    printf("rb_gl=renderer|%s\n", (const char*)glGetString(GL_RENDERER));

    if (gl_setup() != 0) return 1;

    /* 分配 ARGB 缓冲（模拟 Canvas 的 Bitmap） */
    int cw = 540, ch = 1080;  /* 半分辨率以省内存 */
    uint32_t *argb = malloc(cw * ch * 4);
    if (!argb) { printf("rb=fail|oom\n"); return 1; }
    printf("rb=canvas_alloc|w=%d|h=%d|bytes=%d\n", cw, ch, cw*ch*4);

    printf("rb=render_loop\n"); fflush(stdout);
    for (int f = 0; f < frames && R.running; f++) {
        wl_display_dispatch_pending(R.display);
        gen_test_pattern(argb, cw, ch, f);
        draw_argb(argb, cw, ch);
        wl_display_flush(R.display);
        if (f == 0 || f == frames/2 || f == frames-1) {
            printf("rb_frame=%d\n", f); fflush(stdout);
        }
        usleep(16666);
    }
    printf("rb_input_stats|ptr=%d|touch=%d|key=%d\n",
           R.ptr_events, R.touch_events, R.key_events);
    printf("rb=SUCCESS|frames=%d\n", frames);
    free(argb);
    return 0;
}
