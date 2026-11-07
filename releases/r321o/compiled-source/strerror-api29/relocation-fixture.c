#include <stddef.h>
extern int strerror_r(int, char*, size_t);
extern int *__errno_location(void);
int query_error(int number, char *buffer, size_t size, int *after) {
    *__errno_location() = 123;
    int result = strerror_r(number, buffer, size);
    *after = *__errno_location();
    return result;
}
