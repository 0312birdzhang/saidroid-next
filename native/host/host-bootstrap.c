#define _GNU_SOURCE
#include <limits.h>
#include <linux/capability.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/prctl.h>
#include <sys/resource.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <unistd.h>
/* Only this small entry has CAP_SYS_RESOURCE. It execs the unprivileged
 * native host before any window exists, preserving the desktop caller PID.
 * A file-capability executable cannot safely self-exec to enable LD_PRELOAD:
 * glibc's secure-execution mode strips those variables again. */
int main(int argc, char **argv) {
  (void)argc;
  if (!getuid() || geteuid() != getuid()) {
    fputs("Run SailDroid as the phone user\n", stderr);
    return 125;
  }
  struct rlimit current;
  if (getrlimit(RLIMIT_NICE, &current))
    return 125;
  if (current.rlim_cur < 40) {
    struct rlimit limit = {40, 40};
    if (setrlimit(RLIMIT_NICE, &limit)) {
      perror("SailDroid scheduling setup");
      return 125;
    }
  }
  struct __user_cap_header_struct header = {_LINUX_CAPABILITY_VERSION_3, 0};
  struct __user_cap_data_struct caps[2] = {{0}};
  if (syscall(SYS_capset, &header, caps) ||
      prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0))
    return 125;
  char path[PATH_MAX];
  ssize_t count = readlink("/proc/self/exe", path, sizeof(path) - 1);
  if (count <= 0 || count >= (ssize_t)sizeof(path) - 1)
    return 125;
  path[count] = 0;
  char *last = strrchr(path, '/');
  if (!last)
    return 125;
  if (sizeof(path) - (size_t)(last + 1 - path) < sizeof("saildroid-host"))
    return 125;
  strcpy(last + 1, "saildroid-host");
  struct stat status;
  if (lstat(path, &status) || !S_ISREG(status.st_mode) || status.st_uid ||
      (status.st_mode & 022)) {
    fputs("Untrusted SailDroid native host\n", stderr);
    return 125;
  }
  argv[0] = path;
  execv(path, argv);
  perror("SailDroid native host exec");
  return 125;
}
