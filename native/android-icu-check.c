/* VM-only check of the exact Android ICU/SQLite libraries through bionic.
 * No ART, phone writes, JNI replacement or fake SQLite implementation.
 */
#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void *required(void *handle, const char *name,
                      void *(*lookup)(void *, const char *)) {
    void *result = lookup(handle, name);
    if (!result) { fprintf(stderr, "Missing native symbol: %s\n", name); exit(2); }
    return result;
}

int main(int argc, char **argv) {
    if (argc != 3) return 2;
    setbuf(stdout, NULL);
    void *dl = dlopen("libdl_bio.so.0", RTLD_NOW | RTLD_GLOBAL);
    if (!dl) { fprintf(stderr, "%s\n", dlerror()); return 2; }
    void (*parse)(const char *, const char *) = dlsym(dl, "dl_parse_library_path");
    void *(*open_bionic)(const char *, int) = dlsym(dl, "bionic_dlopen");
    void *(*lookup)(void *, const char *) = dlsym(dl, "bionic_dlsym");
    if (!parse || !open_bionic || !lookup) return 2;
    parse(argv[1], ":");
    const char *preload[] = {"libpthread_bio.so.0", "libc_bio.so.0",
                            "libstdc++_bio.so.0", NULL};
    for (int i = 0; preload[i]; i++) {
        if (!dlopen(preload[i], RTLD_NOW | RTLD_GLOBAL)) return 2;
    }
    char path[4096];
    snprintf(path, sizeof(path), "%s/libpthread_names.so", argv[1]);
    if (!open_bionic(path, RTLD_NOW)) return 2;
    snprintf(path, sizeof(path), "%s/libicui18n.so", argv[1]);
    void *icu = open_bionic(path, RTLD_NOW);
    if (!icu) return 2;
    void (*set_data)(const char *) = required(icu, "u_setDataDirectory_55", lookup);
    void *(*collator_open)(const char *, int32_t *) = required(icu, "ucol_open_55", lookup);
    void (*collator_close)(void *) = required(icu, "ucol_close_55", lookup);
    int (*compare)(const void *, const char *, int32_t, const char *, int32_t, int32_t *) =
            required(icu, "ucol_strcollUTF8_55", lookup);
    set_data(argv[2]);
    int32_t status = 0;
    puts("ICU_CHECK=open");
    void *collator = collator_open(NULL, &status);
    printf("ICU_CHECK=opened|status=%d|valid=%d\n", status, collator != NULL);
    if (!collator || status > 0) return 1;
    if (compare(collator, "abc", 3, "abd", 3, &status) >= 0 || status > 0) return 1;
    collator_close(collator);
    puts("ICU_CHECK=PASS|collation=true");
    snprintf(path, sizeof(path), "%s/libsqlite.so", argv[1]);
    void *sqlite = open_bionic(path, RTLD_NOW);
    if (!sqlite) return 2;
    int (*sql_open)(const char *, void **, int, const char *) = required(sqlite, "sqlite3_open_v2", lookup);
    int (*sql_register)(void *, int) = required(sqlite, "register_android_functions", lookup);
    int (*sql_localize)(void *, const char *, int) = required(sqlite, "register_localized_collators", lookup);
    int (*sql_exec)(void *, const char *, void *, void *, char **) = required(sqlite, "sqlite3_exec", lookup);
    int (*sql_close)(void *) = required(sqlite, "sqlite3_close", lookup);
    void *db = NULL;
    if (sql_open(":memory:", &db, 6, NULL) != 0) return 1;
    int result = sql_register(db, 0);
    printf("SQLITE_NATIVE_CHECK=registered|result=%d\n", result);
    if (result != 0) return 1;
    result = sql_localize(db, "en_US", 0);
    printf("SQLITE_NATIVE_CHECK=localized|result=%d\n", result);
    if (result != 0) return 1;
    result = sql_exec(db, "CREATE TABLE evidence(value TEXT COLLATE LOCALIZED);"
                     "INSERT INTO evidence VALUES('abc'); SELECT value FROM evidence ORDER BY value;",
                     NULL, NULL, NULL);
    printf("SQLITE_NATIVE_CHECK=executed|result=%d\n", result);
    sql_close(db);
    if (result != 0) return 1;
    puts("SQLITE_NATIVE_CHECK=PASS");
    return 0;
}
