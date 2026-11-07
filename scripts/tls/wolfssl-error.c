/* 在手机上直接问 wolfSSL：某个负错误码到底是什么意思。
 *
 * 动机：QQ（turingfd）的 TLS 握手报 "verify problem on certificate (error code: -329)"，
 * 这个数字来自 wolfSSL JSSE provider 的原生层，不查表就只能猜。这里 dlopen 设备的
 * libwolfssl.so.42，调 wolfSSL_ERR_reason_error_string 拿到官方字符串。
 *
 * 用法：wolfssl-error [-329] ...   不给参数就打印 -300..-340 一整段。
 */
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>

typedef const char *(*reason_fn)(unsigned long);

int main(int argc, char **argv)
{
    const char *paths[] = {
        "/home/art/lib/libwolfssl.so.42",
        "/home/art/lib/libwolfssl.so.42.3.0",
        "libwolfssl.so.42",
        NULL,
    };
    void *h = NULL;
    for (int i = 0; paths[i]; i++) {
        h = dlopen(paths[i], RTLD_NOW);
        if (h)
            break;
    }
    if (!h) {
        fprintf(stderr, "DLOPEN_FAIL %s\n", dlerror());
        return 2;
    }
    reason_fn reason = (reason_fn)dlsym(h, "wolfSSL_ERR_reason_error_string");
    if (!reason) {
        fprintf(stderr, "DLSYM_FAIL wolfSSL_ERR_reason_error_string\n");
        return 2;
    }
    long version_fn = (long)dlsym(h, "wolfSSL_lib_version_hex");
    if (version_fn) {
        unsigned int (*vh)(void) = (unsigned int (*)(void))version_fn;
        printf("WOLFSSL_VERSION_HEX=0x%08x\n", vh());
    }
    if (argc > 1) {
        for (int i = 1; i < argc; i++) {
            long code = strtol(argv[i], NULL, 10);
            printf("CODE=%ld REASON=%s\n", code, reason((unsigned long)code));
        }
        return 0;
    }
    for (long code = -300; code >= -340; code--)
        printf("CODE=%ld REASON=%s\n", code, reason((unsigned long)code));
    return 0;
}
