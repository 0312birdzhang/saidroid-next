/* SaiDroid JNI 桥接 v3：Wayland + wl_egl_window（与已验证方案一致）
 * 关键：eglGetDisplay 必须传 wl_display，不能用 EGL_DEFAULT_DISPLAY
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <unistd.h>
#include <jni.h>
#include <wayland-client.h>
#include <wayland-egl.h>
#include <EGL/egl.h>
#include <GLES2/gl2.h>
#include "xdg-shell-client-protocol.h"

typedef struct {
    struct wl_display *display;
    struct wl_registry *registry;
    struct wl_compositor *compositor;
    struct wl_seat *seat;
    struct wl_pointer *pointer;
    struct wl_touch *touch;
    struct wl_keyboard *keyboard;
    struct xdg_wm_base *wm_base;
    struct xdg_surface *xdg_surface;
    struct xdg_toplevel *xdg_toplevel;
    struct wl_surface *surface;
    struct wl_egl_window *egl_window;
    EGLDisplay egl_display;
    EGLContext egl_context;
    EGLSurface egl_surface;
    int width, height, configured, inited;
    GLuint program, texture;
    GLint a_pos, a_tex, u_tex;
    int ptr_events, touch_events, key_events;
    int tex_allocated, tex_w, tex_h;
} jb_state;

static jb_state J;
static JavaVM *g_jvm;
static jclass g_class;

/* ---------- 输入 ---------- */
static void notify(const char *type, int a, int b, int c) {
    if (!g_jvm) return;
    JNIEnv *env; int detach = 0;
    if ((*g_jvm)->GetEnv(g_jvm, (void**)&env, JNI_VERSION_1_6) != JNI_OK) {
        if ((*g_jvm)->AttachCurrentThread(g_jvm, (void**)&env, NULL) != JNI_OK) return;
        detach = 1;
    }
    if (g_class) {
        jmethodID m = (*env)->GetStaticMethodID(env, g_class, "onNativeInput",
                                                "(Ljava/lang/String;III)V");
        if (m) {
            jstring s = (*env)->NewStringUTF(env, type);
            (*env)->CallStaticVoidMethod(env, g_class, m, s, a, b, c);
            (*env)->DeleteLocalRef(env, s);
        }
    }
    if (detach) (*g_jvm)->DetachCurrentThread(g_jvm);
}

static void ptr_enter(void *d, struct wl_pointer *p, uint32_t s, struct wl_surface *sf,
                      wl_fixed_t x, wl_fixed_t y) {
    (void)d;(void)p;(void)s;(void)sf;
    J.ptr_events++;
    notify("ptr_enter", wl_fixed_to_int(x), wl_fixed_to_int(y), 0);
}
static void ptr_leave(void *d, struct wl_pointer *p, uint32_t s, struct wl_surface *sf) {
    (void)d;(void)p;(void)s;(void)sf;
}
static void ptr_motion(void *d, struct wl_pointer *p, uint32_t t, wl_fixed_t x, wl_fixed_t y) {
    (void)d;(void)p;(void)t;
    J.ptr_events++;
    notify("ptr_motion", wl_fixed_to_int(x), wl_fixed_to_int(y), 0);
}
static void ptr_button(void *d, struct wl_pointer *p, uint32_t s, uint32_t t,
                       uint32_t b, uint32_t st) {
    (void)d;(void)p;(void)s;(void)t;(void)b;
    J.ptr_events++;
    notify("ptr_button", (int)st, 0, 0);
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
    J.key_events++;
    notify("key", (int)key, (int)st, 0);
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
    (void)d;(void)t;(void)s;(void)tm;(void)sf;(void)id;
    J.touch_events++;
    notify("touch_down", wl_fixed_to_int(x), wl_fixed_to_int(y), (int)id);
}
static void touch_up(void *d, struct wl_touch *t, uint32_t s, uint32_t tm, int32_t id) {
    (void)d;(void)t;(void)s;(void)tm;(void)id;
    J.touch_events++;
    notify("touch_up", 0, 0, (int)id);
}
static void touch_motion(void *d, struct wl_touch *t, uint32_t tm, int32_t id,
                         wl_fixed_t x, wl_fixed_t y) {
    (void)d;(void)t;(void)tm;(void)id;
    J.touch_events++;
    notify("touch_motion", wl_fixed_to_int(x), wl_fixed_to_int(y), (int)id);
}
static void touch_frame(void *d, struct wl_touch *t) { (void)d;(void)t; }
static void touch_cancel(void *d, struct wl_touch *t) { (void)d;(void)t; }
static const struct wl_touch_listener touch_l = { touch_down, touch_up, touch_motion, touch_frame, touch_cancel };

static void seat_caps(void *d, struct wl_seat *s, uint32_t caps) {
    (void)d;
    if ((caps & WL_SEAT_CAPABILITY_POINTER) && !J.pointer) {
        J.pointer = wl_seat_get_pointer(s);
        wl_pointer_add_listener(J.pointer, &ptr_l, NULL);
        printf("[jni] pointer ok\n");
    }
    if ((caps & WL_SEAT_CAPABILITY_KEYBOARD) && !J.keyboard) {
        J.keyboard = wl_seat_get_keyboard(s);
        wl_keyboard_add_listener(J.keyboard, &kbd_l, NULL);
        printf("[jni] keyboard ok\n");
    }
    if ((caps & WL_SEAT_CAPABILITY_TOUCH) && !J.touch) {
        J.touch = wl_seat_get_touch(s);
        wl_touch_add_listener(J.touch, &touch_l, NULL);
        printf("[jni] touch ok\n");
    }
    fflush(stdout);
}
static void seat_name(void *d, struct wl_seat *s, const char *n) { (void)d;(void)s;(void)n; }
static const struct wl_seat_listener seat_l = { seat_caps, seat_name };

static void wm_ping(void *d, struct xdg_wm_base *b, uint32_t s) { (void)d; xdg_wm_base_pong(b, s); }
static const struct xdg_wm_base_listener wm_l = { wm_ping };
static void surf_cfg(void *d, struct xdg_surface *s, uint32_t serial) {
    (void)d; xdg_surface_ack_configure(s, serial); J.configured = 1;
}
static const struct xdg_surface_listener surf_l = { surf_cfg };
static void top_cfg(void *d, struct xdg_toplevel *t, int32_t w, int32_t h, struct wl_array *st) {
    (void)d;(void)t;(void)st;
    if (w > 0) J.width = w;
    if (h > 0) J.height = h;
}
static void top_close(void *d, struct xdg_toplevel *t) { (void)d;(void)t; }
static const struct xdg_toplevel_listener top_l = { top_cfg, top_close };

static void reg_global(void *d, struct wl_registry *r, uint32_t name,
                       const char *iface, uint32_t ver) {
    (void)d;
    if (!strcmp(iface, wl_compositor_interface.name))
        J.compositor = wl_registry_bind(r, name, &wl_compositor_interface, 3);
    else if (!strcmp(iface, wl_seat_interface.name)) {
        J.seat = wl_registry_bind(r, name, &wl_seat_interface, 3);
        wl_seat_add_listener(J.seat, &seat_l, NULL);
    } else if (!strcmp(iface, xdg_wm_base_interface.name)) {
        J.wm_base = wl_registry_bind(r, name, &xdg_wm_base_interface, 1);
        xdg_wm_base_add_listener(J.wm_base, &wm_l, NULL);
    }
}
static void reg_remove(void *d, struct wl_registry *r, uint32_t name) { (void)d;(void)r;(void)name; }
static const struct wl_registry_listener reg_l = { reg_global, reg_remove };

static const char *VS =
    "attribute vec2 a_pos;attribute vec2 a_tex;varying vec2 v_tex;"
    "void main(){gl_Position=vec4(a_pos,0.0,1.0);v_tex=a_tex;}";
static const char *FS =
    "precision mediump float;varying vec2 v_tex;uniform sampler2D u_tex;"
    "void main(){gl_FragColor=texture2D(u_tex,v_tex);}";

static GLuint mk_shader(GLenum t, const char *s) {
    GLuint sh = glCreateShader(t);
    glShaderSource(sh, 1, &s, NULL);
    glCompileShader(sh);
    return sh;
}

JNIEXPORT jboolean JNICALL
Java_org_saidroid_NativeBridge_init(JNIEnv *env, jclass cls, jint w, jint h)
{
    (void)cls;
    printf("[jni] init w=%d h=%d\n", w, h); fflush(stdout);
    (*env)->GetJavaVM(env, &g_jvm);
    J.width = w; J.height = h;

    /* 1. 连接 Wayland */
    J.display = wl_display_connect(NULL);
    if (!J.display) { printf("[jni] fail|wayland\n"); return JNI_FALSE; }
    printf("[jni] wayland ok\n");

    J.registry = wl_display_get_registry(J.display);
    wl_registry_add_listener(J.registry, &reg_l, NULL);
    wl_display_roundtrip(J.display);
    wl_display_roundtrip(J.display);

    if (!J.compositor || !J.wm_base) { printf("[jni] fail|globals\n"); return JNI_FALSE; }

    /* 2. 创建窗口 */
    J.surface = wl_compositor_create_surface(J.compositor);
    J.xdg_surface = xdg_wm_base_get_xdg_surface(J.wm_base, J.surface);
    xdg_surface_add_listener(J.xdg_surface, &surf_l, NULL);
    J.xdg_toplevel = xdg_surface_get_toplevel(J.xdg_surface);
    xdg_toplevel_add_listener(J.xdg_toplevel, &top_l, NULL);
    xdg_toplevel_set_title(J.xdg_toplevel, "SaiDroid JNI");

    wl_surface_commit(J.surface);
    int w2 = 0;
    while (!J.configured && w2 < 50) { if (wl_display_roundtrip(J.display) < 0) break; w2++; }
    printf("[jni] configured wait=%d\n", w2); fflush(stdout);

    /* 3. EGL —— 关键：传 wl_display */
    J.egl_window = wl_egl_window_create(J.surface, J.width, J.height);
    J.egl_display = eglGetDisplay((EGLNativeDisplayType)J.display);
    if (J.egl_display == EGL_NO_DISPLAY) { printf("[jni] fail|no_display\n"); return JNI_FALSE; }
    if (!eglInitialize(J.egl_display, NULL, NULL)) { printf("[jni] fail|egl_init\n"); return JNI_FALSE; }
    printf("[jni] egl ok\n"); fflush(stdout);

    EGLint ca[] = { EGL_SURFACE_TYPE, EGL_WINDOW_BIT, EGL_RENDERABLE_TYPE,
                    EGL_OPENGL_ES2_BIT, EGL_RED_SIZE,8, EGL_GREEN_SIZE,8,
                    EGL_BLUE_SIZE,8, EGL_ALPHA_SIZE,8, EGL_NONE };
    EGLConfig cfg; EGLint n = 0;
    eglChooseConfig(J.egl_display, ca, &cfg, 1, &n);
    EGLint xa[] = { EGL_CONTEXT_CLIENT_VERSION, 2, EGL_NONE };
    J.egl_context = eglCreateContext(J.egl_display, cfg, EGL_NO_CONTEXT, xa);
    J.egl_surface = eglCreateWindowSurface(J.egl_display, cfg,
                        (EGLNativeWindowType)J.egl_window, NULL);
    if (J.egl_surface == EGL_NO_SURFACE) {
        printf("[jni] fail|surface|err=0x%x\n", eglGetError()); return JNI_FALSE;
    }
    if (!eglMakeCurrent(J.egl_display, J.egl_surface, J.egl_surface, J.egl_context)) {
        printf("[jni] fail|current\n"); return JNI_FALSE;
    }
    printf("[jni] egl_surface ok|renderer=%s\n", (const char*)glGetString(GL_RENDERER));

    GLuint vs = mk_shader(GL_VERTEX_SHADER, VS);
    GLuint fs = mk_shader(GL_FRAGMENT_SHADER, FS);
    J.program = glCreateProgram();
    glAttachShader(J.program, vs);
    glAttachShader(J.program, fs);
    glLinkProgram(J.program);
    J.a_pos = glGetAttribLocation(J.program, "a_pos");
    J.a_tex = glGetAttribLocation(J.program, "a_tex");
    J.u_tex = glGetUniformLocation(J.program, "u_tex");

    glGenTextures(1, &J.texture);
    glBindTexture(GL_TEXTURE_2D, J.texture);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);

    J.inited = 1;
    printf("[jni] INIT_OK\n"); fflush(stdout);
    return JNI_TRUE;
}

JNIEXPORT jboolean JNICALL
Java_org_saidroid_NativeBridge_drawFrame(JNIEnv *env, jclass cls, jintArray argb, jint w, jint h)
{
    (void)cls;
    if (!J.inited) return JNI_FALSE;
    /* 优化：Critical 区避免拷贝 */
    jint *px = (*env)->GetPrimitiveArrayCritical(env, argb, NULL);
    if (!px) return JNI_FALSE;

    wl_display_dispatch_pending(J.display);

    glViewport(0, 0, J.width, J.height);
    glClearColor(0, 0, 0, 1);
    glClear(GL_COLOR_BUFFER_BIT);
    glUseProgram(J.program);
    glActiveTexture(GL_TEXTURE0);
    glBindTexture(GL_TEXTURE_2D, J.texture);
    /* 优化：首帧分配纹理存储，后续只更新数据 */
    if (!J.tex_allocated) {
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA,
                     GL_UNSIGNED_BYTE, px);
        J.tex_allocated = 1;
        J.tex_w = w; J.tex_h = h;
    } else if (J.tex_w == w && J.tex_h == h) {
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, w, h, GL_RGBA,
                        GL_UNSIGNED_BYTE, px);
    } else {
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA,
                     GL_UNSIGNED_BYTE, px);
        J.tex_w = w; J.tex_h = h;
    }

    static const GLfloat verts[] = {
        -1.0f,-1.0f, 0.0f,1.0f,  1.0f,-1.0f, 1.0f,1.0f,
        -1.0f, 1.0f, 0.0f,0.0f,  1.0f, 1.0f, 1.0f,0.0f,
    };
    glEnableVertexAttribArray(J.a_pos);
    glEnableVertexAttribArray(J.a_tex);
    glVertexAttribPointer(J.a_pos, 2, GL_FLOAT, GL_FALSE, 16, verts);
    glVertexAttribPointer(J.a_tex, 2, GL_FLOAT, GL_FALSE, 16, verts + 2);
    glUniform1i(J.u_tex, 0);
    glDrawArrays(GL_TRIANGLE_STRIP, 0, 4);
    eglSwapBuffers(J.egl_display, J.egl_surface);
    wl_display_flush(J.display);

    (*env)->ReleasePrimitiveArrayCritical(env, argb, px, JNI_ABORT);
    return JNI_TRUE;
}

JNIEXPORT void JNICALL
Java_org_saidroid_NativeBridge_setCallback(JNIEnv *env, jclass cls, jobject obj)
{
    (void)obj;
    g_class = (jclass)(*env)->NewGlobalRef(env, cls);
    printf("[jni] callback set\n"); fflush(stdout);
}

JNIEXPORT void JNICALL
Java_org_saidroid_NativeBridge_shutdown(JNIEnv *env, jclass cls)
{
    (void)env;(void)cls;
    printf("[jni] shutdown|ptr=%d|touch=%d|key=%d\n",
           J.ptr_events, J.touch_events, J.key_events);
    fflush(stdout);
}

JNIEXPORT jint JNICALL
Java_org_saidroid_NativeBridge_inputCount(JNIEnv *env, jclass cls, jint which)
{
    (void)env;(void)cls;
    if (which == 0) return J.ptr_events;
    if (which == 1) return J.touch_events;
    return J.key_events;
}

JNIEXPORT jint JNI_OnLoad(JavaVM *vm, void *reserved)
{
    (void)reserved;
    g_jvm = vm;
    printf("[jni] JNI_OnLoad\n"); fflush(stdout);
    return JNI_VERSION_1_6;
}
