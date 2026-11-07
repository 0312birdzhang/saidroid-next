/*
 * fdo-load-object-probe.c -- ask WPEBackend-fdo, via its own loader contract,
 * which interface objects this build actually provides.
 *
 * Background: `nm -D` on libWPEBackend-fdo only shows `_wpe_loader_interface`.
 * The other `_wpe_*_interface` names are not exported symbols at all: fdo is C++
 * and its `_wpe_loader_interface` holds a lambda that maps a name to an internal
 * static object (symbol `_ZN21_wpe_loader_interfaceMUlPKcE_4_FUNES0_`). So the only
 * correct way to know whether this build can do offscreen rendering is to call
 * that lambda, i.e. `load_object("<name>")`, and look at the answer.
 *
 * Build/run: native/webview/probes/vm-fdo-load-object.sh
 */
#include <dlfcn.h>
#include <stdio.h>

/* struct wpe_loader_interface from libwpe's private loader.h: one function pointer. */
struct wpe_loader_interface {
    void* (*load_object)(const char*);
};

static const char* k_names[] = {
    "_wpe_view_backend_interface",
    "_wpe_renderer_backend_egl_interface",
    "_wpe_renderer_backend_egl_target_interface",
    "_wpe_renderer_backend_egl_offscreen_target_interface",
    "_wpe_renderer_host_interface",
    "_wpe_pasteboard_interface",
};

/* struct wpe_renderer_host_interface from libwpe's private renderer-host.h. */
struct wpe_renderer_host_interface {
    void* (*create)(void);
    void (*destroy)(void*);
    int (*create_client)(void*);
};

int main(int argc, char** argv)
{
    if (argc < 2) { printf("USAGE: %s <libWPEBackend-fdo.so>\n", argv[0]); return 2; }
    void* h = dlopen(argv[1], RTLD_NOW | RTLD_LOCAL);
    if (!h) { printf("DLOPEN_FAIL|%s\n", dlerror()); return 1; }
    printf("DLOPEN_OK|%s\n", argv[1]);

    struct wpe_loader_interface* li =
        (struct wpe_loader_interface*)dlsym(h, "_wpe_loader_interface");
    if (!li) { printf("NO_LOADER_SYMBOL|%s\n", dlerror()); return 1; }
    printf("LOADER_OBJECT|%p|load_object=%p\n", (void*)li, (void*)li->load_object);
    if (!li->load_object) { printf("NO_LOAD_OBJECT\n"); return 1; }

    int provided = 0;
    for (unsigned i = 0; i < sizeof(k_names) / sizeof(k_names[0]); i++) {
        void* obj = li->load_object(k_names[i]);
        printf("OBJECT|%s|%s|%p\n", k_names[i], obj ? "PROVIDED" : "NULL", obj);
        if (obj) provided++;
    }
    printf("SUMMARY|provided=%d|offscreen_target=%s\n", provided,
           li->load_object("_wpe_renderer_backend_egl_offscreen_target_interface")
               ? "YES" : "NO");

    /*
     * Second question, same contract: is the RENDERER HOST side implemented by
     * this backend? If yes, we can implement a tiny view backend whose
     * get_renderer_host_fd() hands the WebProcess a real renderer-host fd, and the
     * WebProcess renders through the host protocol instead of trying to build its
     * own Wayland EGL window (which is what dies on this device).
     *
     * create()/create_client() are socketpair-level operations in libwpe's
     * reference implementation, so this is safe to call in a probe process.
     */
    struct wpe_renderer_host_interface* rh =
        (struct wpe_renderer_host_interface*)li->load_object("_wpe_renderer_host_interface");
    if (!rh) { printf("RENDERER_HOST|NULL\n"); return 0; }
    printf("RENDERER_HOST|iface=%p|create=%p|destroy=%p|create_client=%p\n",
           (void*)rh, (void*)rh->create, (void*)rh->destroy, (void*)rh->create_client);
    if (!rh->create || !rh->create_client) { printf("RENDERER_HOST|INCOMPLETE\n"); return 0; }
    void* host = rh->create();
    printf("RENDERER_HOST_CREATE|%p\n", host);
    if (!host) return 0;
    int fd = rh->create_client(host);
    printf("RENDERER_HOST_CREATE_CLIENT|fd=%d\n", fd);
    return 0;
}
