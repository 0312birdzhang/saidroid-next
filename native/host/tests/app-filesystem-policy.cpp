#include "../app-filesystem-policy.hpp"
#include <atomic>
#include <cstdio>
#include <cstdlib>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <thread>

static void require(bool condition, const char *what) {
  if (!condition) {
    perror(what);
    _exit(1);
  }
}
static void denied(const char *source, const char *destination) {
  errno = 0;
  require(link(source, destination) == -1 && errno == EACCES, "link denied");
  errno = 0;
  require(syscall(SYS_linkat, AT_FDCWD, source, AT_FDCWD, destination, 0) == -1
              && errno == EACCES, "direct linkat denied");
  errno = 0;
  require(syscall(SYS_linkat, AT_FDCWD, source, AT_FDCWD, destination,
                  AT_SYMLINK_FOLLOW) == -1 && errno == EACCES,
          "linkat follow denied");
  struct stat s{};
  require(lstat(destination, &s) == -1 && errno == ENOENT,
          "no denied destination created");
  require(stat(source, &s) == 0 && s.st_nlink == 1, "source unchanged");
}
int main() {
  require(getuid() != 0, "test must use ordinary UID");
  char directory[] = "/tmp/saidroid-app-link-policy-XXXXXX";
  require(mkdtemp(directory), "private directory");
  require(chdir(directory) == 0, "private cwd");
  int fd = open("original", O_CREAT | O_EXCL | O_WRONLY, 0600);
  require(fd >= 0 && write(fd, "payload", 7) == 7 && close(fd) == 0,
          "create original");
  require(link("original", "baseline") == 0, "baseline real hardlink");
  require(unlink("baseline") == 0, "baseline cleanup");
  pid_t child = fork();
  require(child >= 0, "fork isolated filter process");
  if (!child) {
    std::atomic<int> ready{0};
    std::atomic<bool> run{false};
    auto existing = [&]() {
      ++ready;
      while (!run.load()) std::this_thread::yield();
      denied("original", "existing-thread-link");
    };
    std::thread first(existing), second(existing);
    while (ready.load() != 2) std::this_thread::yield();
    require(sd_install_app_filesystem_policy(), "install real TSYNC filter");
    require(prctl(PR_GET_NO_NEW_PRIVS, 0, 0, 0, 0) == 1, "no new privileges");
    run.store(true);
    first.join(); second.join();
    denied("original", "main-link");
    std::thread later([] { denied("original", "future-thread-link"); });
    later.join();
    pid_t descendant = fork();
    require(descendant >= 0, "fork filtered descendant");
    if (!descendant) { denied("original", "child-link"); _exit(0); }
    int status;
    require(waitpid(descendant, &status, 0) == descendant && status == 0,
            "child inherits policy");
    require(symlink("original", "symbolic") == 0, "symlinks remain available");
    require(rename("symbolic", "renamed") == 0, "rename remains available");
    char content[8]{};
    int input = open("renamed", O_RDONLY);
    require(input >= 0 && read(input, content, 8) == 7 && close(input) == 0,
            "read through symlink");
    require(unlink("renamed") == 0, "unlink remains available");
    _exit(0);
  }
  int status;
  require(waitpid(child, &status, 0) == child && status == 0,
          "isolated filter process passed");
  require(link("original", "parent-after") == 0, "parent policy unchanged");
  require(unlink("parent-after") == 0 && unlink("original") == 0,
          "remove private files");
  require(chdir("/") == 0 && rmdir(directory) == 0, "remove private directory");
  puts("APP_FILESYSTEM_POLICY=PASS|ordinary_uid=true|kernel_filter=true|existing_threads=true|future_threads=true|child=true|parent_unaffected=true");
}
