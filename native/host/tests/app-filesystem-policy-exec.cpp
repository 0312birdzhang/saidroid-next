#include "../app-filesystem-policy.hpp"
#include <cstdio>

// VM diagnostic launcher: use the exact product policy before an unchanged
// ART executable and original APK. This is not an instrumentation replacement.
int main(int argc, char **argv) {
  if (getuid() == 0 || argc < 2) return 125;
  if (!sd_install_app_filesystem_policy()) {
    perror("application filesystem policy");
    return 125;
  }
  fprintf(stderr, "APP_FILESYSTEM_POLICY=installed|uid=%u|backend=kernel-seccomp\n",
          static_cast<unsigned int>(getuid()));
  execvp(argv[1], argv + 1);
  perror("exec actual ART");
  return 125;
}
