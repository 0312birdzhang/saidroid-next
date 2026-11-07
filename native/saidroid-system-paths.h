#ifndef SAIDROID_SYSTEM_PATHS_H
#define SAIDROID_SYSTEM_PATHS_H
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

/* Native Android font readers use absolute system paths independently of Java
 * Typeface. Translate only this platform-owned font namespace in this process.
 * The compatibility library owns/frees a successful replacement string.
 */
static bool saidroid_private_font_path(const char *root, char **path) {
    if (!root || root[0] != '/' || !path || !*path) return false;
    const char *suffix = NULL;
    if (!strcmp(*path, "/system/etc/fonts.xml")) suffix = "/etc/fonts.xml";
    else if (!strcmp(*path, "/system/etc/system_fonts.xml")) suffix = "/etc/system_fonts.xml";
    else if (!strcmp(*path, "/system/etc/fallback_fonts.xml")) suffix = "/etc/fallback_fonts.xml";
    else if (!strncmp(*path, "/system/fonts/", 14)) suffix = *path + 7;
    else if (!strcmp(*path, "/system/fonts")) suffix = "/fonts";
    if (!suffix) return false;
    size_t length = strlen(root) + strlen(suffix) + 1;
    char *replacement = malloc(length);
    if (!replacement) return false;
    strcpy(replacement, root);
    strcat(replacement, suffix);
    *path = replacement;
    return true;
}

static bool saidroid_private_api29_path(const char *root, char **path) {
    if (!root || root[0] != '/' || !path || !*path) return false;
    const char *value=*path;
    /* RS verifies the exact compiler and core bitcode as part of its real
     * build checksum. Keep these files in the same isolated toolchain used
     * by the compiler subprocess; never read the host's Android /system. */
    const char *rs_suffix=NULL;
    if(!strcmp(value,"/system/bin/bcc"))rs_suffix="/rs/bin/bcc";
    else if(!strcmp(value,"/system/bin/ld.mc"))rs_suffix="/rs/bin/ld.mc";
    else if(!strcmp(value,"/system/lib64/libclcore.bc"))rs_suffix="/rs/lib/libclcore.bc";
    else if(!strcmp(value,"/system/lib64/libclcore_g.bc"))rs_suffix="/rs/lib/libclcore_g.bc";
    else if(!strcmp(value,"/system/lib64/libclcore_debug.bc"))rs_suffix="/rs/lib/libclcore_debug.bc";
    else if(!strcmp(value,"/system/lib64/libclcore_debug_g.bc"))rs_suffix="/rs/lib/libclcore_debug_g.bc";
    if(rs_suffix){
        size_t length=strlen(root)+strlen(rs_suffix)+1;char *replacement=malloc(length);
        if(!replacement)return false;
        strcpy(replacement,root);strcat(replacement,rs_suffix);*path=replacement;return true;
    }
    if (strncmp(value,"/system/fonts",13) &&
        strncmp(value,"/system/etc/font",16) &&
        strcmp(value,"/system/framework/framework-res.apk") &&
        strncmp(value,"/system/usr/hyphen-data",23) &&
        strncmp(value,"/apex/com.android.runtime/etc/icu",33)) return false;
    // The runtime APEX is expanded privately under its actual archive name.
    const char *apex="/apex/com.android.runtime/";
    const char *replacement_prefix="/apex/com.android.runtime.debug/";
    size_t length=strlen(root)+strlen(value)+strlen(replacement_prefix)+1;
    char *replacement=malloc(length);if(!replacement)return false;
    strcpy(replacement,root);
    if (!strncmp(value,apex,strlen(apex))) {
        strcat(replacement,replacement_prefix);strcat(replacement,value+strlen(apex));
    } else strcat(replacement,value);
    *path=replacement;return true;
}
#endif
