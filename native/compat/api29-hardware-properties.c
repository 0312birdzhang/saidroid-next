#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>

#ifndef SD_HOST_PROPERTY_LIBRARY
#define SD_HOST_PROPERTY_LIBRARY "/usr/lib64/libhybris-common.so.1"
#endif

/* The component's Android properties describe its private userland. Hardware
 * service readiness belongs to the running phone, rather than build.prop.
 * Import only this non-secret, read-only host fact through libhybris's native
 * property reader. The setter handle is the private translator's property
 * table; no host property setter or external command is used. */
int sd_import_host_hardware_properties(void *private_libc) {
    int (*set_private)(const char *, const char *) =
        dlsym(private_libc, "bionic___system_property_set");
    struct stat info;
    if (!set_private || stat(SD_HOST_PROPERTY_LIBRARY, &info) ||
        !S_ISREG(info.st_mode) || info.st_uid != 0 || (info.st_mode & 022)) {
        fputs("SDHARDWARE_PROPERTIES=unavailable|reason=trusted-reader-missing\n", stderr);
        return 0;
    }
    void *library = dlopen(SD_HOST_PROPERTY_LIBRARY, RTLD_NOW | RTLD_LOCAL);
    int (*get_host)(const char *, char *, const char *) =
        library ? dlsym(library, "my_property_get") : NULL;
    if (!get_host) {
        fputs("SDHARDWARE_PROPERTIES=unavailable|reason=host-reader-missing\n", stderr);
        if (library) dlclose(library);
        return 0;
    }
    const char *key = "hwservicemanager.ready";
    char value[92] = {0};
    int count = get_host(key, value, "");
    if (count <= 0 || count >= (int)sizeof(value) ||
        strnlen(value, sizeof(value)) != (size_t)count) {
        fputs("SDHARDWARE_PROPERTIES=unavailable|reason=host-value-absent\n", stderr);
        dlclose(library);
        return 0;
    }
    if (strcmp(value, "true") && strcmp(value, "false")) {
        fputs("SDHARDWARE_PROPERTIES=unavailable|reason=host-value-invalid\n", stderr);
        dlclose(library);
        return 0;
    }
    int result = set_private(key, value);
    fprintf(stderr, "SDHARDWARE_PROPERTIES=%s|property=%s|source=host-libhybris|value=%s\n",
            result ? "error" : "imported", key, value);
    dlclose(library);
    return result ? -1 : 1;
}
