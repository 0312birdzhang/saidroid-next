#include <stdint.h>
#include <stdlib.h>
static int calls;
void target(void) {}
void __cfi_check(uint64_t type,void *pointer,void *diagnostic) {
    (void)diagnostic;
    if(type!=42||pointer!=(void *)target)abort();
    calls++;
}
int checks(void){return calls;}
