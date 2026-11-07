#pragma once

#include <cerrno>
#include <cstddef>
#include <linux/audit.h>
#include <linux/filter.h>
#include <linux/seccomp.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <unistd.h>

// Android app domains cannot create hard links, including between their own
// files (b/19953790). SailDroid does not own the phone's SELinux policy, so
// enforce that one app-process restriction at the kernel syscall boundary.
// This is deliberately not a claim of a complete Android app sandbox.
inline bool sd_install_app_filesystem_policy() {
#if defined(__aarch64__)
  constexpr unsigned int architecture = AUDIT_ARCH_AARCH64;
#elif defined(__x86_64__)
  constexpr unsigned int architecture = AUDIT_ARCH_X86_64;
#else
#error Unsupported application syscall architecture
#endif
  const sock_filter instructions[] = {
      BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(seccomp_data, arch)),
      BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, architecture, 1, 0),
      // SECCOMP_RET_KILL is supported by the phone's Linux 4.9 kernel.
      BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL),
      BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(seccomp_data, nr)),
#ifdef SYS_link
      BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, SYS_link, 0, 1),
      BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | EACCES),
#endif
      BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, SYS_linkat, 0, 1),
      BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | EACCES),
      BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW),
  };
  sock_fprog program{static_cast<unsigned short>(
                         sizeof(instructions) / sizeof(instructions[0])),
                     const_cast<sock_filter *>(instructions)};
  if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0))
    return false;
  // The native host already has D-Bus threads. Synchronize every existing
  // thread; subsequently created threads and child processes inherit it.
  // A positive return is the unsynchronized TID, not successful installation.
  long result = syscall(SYS_seccomp, SECCOMP_SET_MODE_FILTER,
                        SECCOMP_FILTER_FLAG_TSYNC, &program);
  if (result > 0)
    errno = EBUSY;
  return result == 0;
}
