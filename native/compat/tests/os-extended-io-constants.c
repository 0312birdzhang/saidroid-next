// Actual VM C headers; no runtime expected-value spoof or phone operation.
#define _GNU_SOURCE
#include <fcntl.h>
#include <stdio.h>
#include <sys/syscall.h>
int main(void) {
  printf("{\"O_DIRECT\":%d,\"SPLICE_F_MOVE\":%d,\"SPLICE_F_NONBLOCK\":%d,\"SPLICE_F_MORE\":%d,\"SYS_splice\":%ld}\n",
         O_DIRECT,SPLICE_F_MOVE,SPLICE_F_NONBLOCK,SPLICE_F_MORE,(long)SYS_splice);
  return 0;
}
