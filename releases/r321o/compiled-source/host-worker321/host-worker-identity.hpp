#pragma once
#include <dirent.h>
#include <fcntl.h>
#include <unistd.h>
#include <cerrno>
#include <cstdio>
#include <cstdlib>
#include <cstring>
// Called once before ART creates any application/Java threads. These are
// implementation workers belonging to the native host, so give them host
// identities instead of leaking a desktop library's generic worker names.
// The application main thread and every subsequently created thread retain
// their original names. No process view or Android API result is filtered.
static int sd_label_host_workers() {
  DIR *directory = opendir("/proc/self/task");
  if (!directory) return -1;
  int count = 0;
  while (dirent *entry = readdir(directory)) {
    char *end = nullptr;
    long tid = strtol(entry->d_name, &end, 10);
    if (!tid || !end || *end || tid == getpid()) continue;
    char path[96], previous[32] = {}, name[16];
    snprintf(path, sizeof(path), "/proc/self/task/%ld/comm", tid);
    int fd = open(path, O_RDONLY | O_CLOEXEC);
    if (fd < 0) continue; // A worker may finish during the snapshot.
    ssize_t size = read(fd, previous, sizeof(previous) - 1);
    close(fd);
    if (size > 0 && previous[size - 1] == '\n') previous[size - 1] = 0;
    snprintf(name, sizeof(name), "sdhost-%ld", tid);
    fd = open(path, O_WRONLY | O_CLOEXEC);
    if (fd < 0) continue;
    bool written = write(fd, name, strlen(name)) == (ssize_t)strlen(name);
    close(fd);
    if (written) {
      ++count;
      fprintf(stderr, "SDHOST_THREAD=owned|tid=%ld|role=pre-vm-worker|previous=%s|name=%s\n", tid, previous, name);
    }
  }
  closedir(directory);
  return count;
}
