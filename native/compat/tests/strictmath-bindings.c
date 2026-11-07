#define _GNU_SOURCE
#include <dlfcn.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void check(int value, const char *message) {
    if (!value) { fprintf(stderr, "STRICTMATH_BINDING=failed|%s\n", message); exit(1); }
}
int main(int argc, char **argv) {
    check(argc == 2, "expected component library path");
    void *libm = dlopen("libm.so.6", RTLD_NOW | RTLD_GLOBAL);
    check(libm != NULL, "real host libc math is available");
    double (*real_exp)(double) = dlsym(RTLD_DEFAULT, "exp");
    double (*strict_exp)(double) = dlsym(RTLD_DEFAULT, "ieee_exp");
    double (*strict_sqrt)(double) = dlsym(RTLD_DEFAULT, "ieee_sqrt");
    double (*strict_log)(double) = dlsym(RTLD_DEFAULT, "ieee_log");
    check(real_exp && strict_exp && strict_sqrt && strict_log, "actual symbols resolved");
    Dl_info host_owner = {0}, strict_owner = {0};
    check(dladdr((void *)real_exp, &host_owner) && host_owner.dli_fname,
          "host function has real mapping");
    check(dladdr((void *)strict_exp, &strict_owner) && strict_owner.dli_fname,
          "private function has real mapping");
    char *expected = realpath(argv[1], NULL), *actual = realpath(strict_owner.dli_fname, NULL);
    check(expected && actual && !strcmp(expected, actual), "private entry belongs to exact companion");
    check(strcmp(host_owner.dli_fname, strict_owner.dli_fname) != 0,
          "host libc math remains a different implementation");
    check(strict_exp(0.0) == 1.0 && strict_sqrt(4.0) == 2.0,
          "ordinary operations use correct double words");
    check(strict_log(1.0) == 0.0 && !signbit(strict_log(1.0)), "positive zero preserved");
    check(strict_sqrt(-0.0) == 0.0 && signbit(strict_sqrt(-0.0)), "negative zero preserved");
    check(isinf(strict_log(0.0)) && signbit(strict_log(0.0)), "negative infinity preserved");
    check(isnan(strict_sqrt(-1.0)), "NaN domain result preserved");
    check(real_exp(0.0) == 1.0, "host libc math remains callable");
    printf("STRICTMATH_BINDING=PASS|private_owner=%s|host_math_owner=%s|no_JNI_override=true\n",
           actual, host_owner.dli_fname);
    free(expected); free(actual); dlclose(libm);
}
