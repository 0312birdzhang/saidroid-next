/* libhwui 最小替身：只提供 libandroid_runtime 链接期需要的 12 个符号。
 * 真实 hwui（硬件渲染 / RenderScript 链）在本项目当前阶段不使用——
 * 渲染走的是 Skia 软件 Canvas（libskia + GraphicsJNI）。
 * 这些符号若被真正调用才需要换成真实实现。 */
#include <stddef.h>

/* 1) 函数：RenderProxy::setName(const char*) */
void hwui_setname_impl(void *self, const char *name)
    __asm__("_ZN7android10uirenderer12renderthread11RenderProxy7setNameEPKc");
void hwui_setname_impl(void *self, const char *name) { (void)self; (void)name; }

/* 2) 数据符号：单例指针 */
void *hwui_caches_sinst __asm__("_ZN7android10uirenderer6Caches9sInstanceE") = NULL;
void *hwui_rcache_lock __asm__("_ZN7android9SingletonINS_10uirenderer13ResourceCacheEE5sLockE") = NULL;
void *hwui_rcache_inst __asm__("_ZN7android9SingletonINS_10uirenderer13ResourceCacheEE9sInstanceE") = NULL;

/* 3) 9 个插值器 vtable（占位数组，足以满足链接） */
#define VT(name) void *name[32] __asm__(#name)
void *vt_cycle[32]   __asm__("_ZTVN7android10uirenderer17CycleInterpolatorE") = {0};
void *vt_bounce[32]  __asm__("_ZTVN7android10uirenderer18BounceInterpolatorE") = {0};
void *vt_over[32]    __asm__("_ZTVN7android10uirenderer21OvershootInterpolatorE") = {0};
void *vt_accel_i[32] __asm__("_ZTVN7android10uirenderer22AccelerateInterpolatorE") = {0};
void *vt_anticip[32] __asm__("_ZTVN7android10uirenderer22AnticipateInterpolatorE") = {0};
void *vt_decel[32]   __asm__("_ZTVN7android10uirenderer22DecelerateInterpolatorE") = {0};
void *vt_anti_ov[32] __asm__("_ZTVN7android10uirenderer31AnticipateOvershootInterpolatorE") = {0};
void *vt_accel_decel[32] __asm__("_ZTVN7android10uirenderer32AccelerateDecelerateInterpolatorE") = {0};
void *vt_linear[32]  __asm__("_ZTVN7android10uirenderer20LinearInterpolatorE") = {0};
