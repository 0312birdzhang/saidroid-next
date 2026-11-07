/* VM-only native Skia default-font loading through the same file compatibility
 * callback used by the runtime. No Java Typeface or explicit Paint font is used.
 */
#include <dlfcn.h>
#include <stdio.h>
#include "saidroid-system-paths.h"

static const char *font_root;
static unsigned mapped;
static bool translate(char **path) {
    bool changed = saidroid_private_font_path(font_root, path);
    if (changed) mapped++;
    return changed;
}

int main(int argc, char **argv) {
    if (argc != 3) return 2;
    setbuf(stdout, NULL);
    font_root = argv[2];
    void *dl = dlopen("libdl_bio.so.0", RTLD_NOW | RTLD_GLOBAL);
    if (!dl) return 2;
    void (*parse)(const char *, const char *) = dlsym(dl, "dl_parse_library_path");
    void *(*open_bionic)(const char *, int) = dlsym(dl, "bionic_dlopen");
    void *(*lookup)(void *, const char *) = dlsym(dl, "bionic_dlsym");
    if (!parse || !open_bionic || !lookup) return 2;
    parse(argv[1], ":");
    const char *preloads[] = {"libpthread_bio.so.0", "libc_bio.so.0", "libstdc++_bio.so.0", NULL};
    for (int i = 0; preloads[i]; i++) {
        void *handle = dlopen(preloads[i], RTLD_NOW | RTLD_GLOBAL);
        if (!handle) return 2;
        if (!strcmp(preloads[i], "libc_bio.so.0")) {
            void (*set_paths)(bool (*)(char **)) = dlsym(handle, "libc_bio_set_apply_path_overrides_func");
            if (!set_paths) return 2;
            set_paths(translate);
        }
    }
    char name[4096];
    snprintf(name, sizeof(name), "%s/libpthread_names.so", argv[1]);
    if (!open_bionic(name, RTLD_NOW)) return 2;
    snprintf(name, sizeof(name), "%s/libskia.so", argv[1]);
    void *skia = open_bionic(name, RTLD_NOW);
    if (!skia) return 2;
    void *(*default_manager)(void) = lookup(skia, "_ZN9SkFontMgr10RefDefaultEv");
    int (*family_count)(const void *) = lookup(skia, "_ZNK9SkFontMgr13countFamiliesEv");
    if (!default_manager || !family_count) return 2;
    void *manager = default_manager();
    int count = manager ? family_count(manager) : 0;
    printf("NATIVE_DEFAULT_FONTS=families:%d|mapped_paths:%u\n", count, mapped);
    if (count < 1 || mapped < 1) return 1;
    puts("NATIVE_DEFAULT_FONTS=PASS");
    return 0;
}
