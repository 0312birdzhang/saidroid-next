/*
 * Copyright (C) 2011 The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include "thread.h"

#include <algorithm>
#include <cerrno>
#include <signal.h>
#include <sys/mman.h>
#include <unistd.h>

#include "base/logging.h"  // For VLOG.
#include "base/utils.h"

namespace art {

static void SigAltStack(stack_t* new_stack, stack_t* old_stack) {
  if (sigaltstack(new_stack, old_stack) == -1) {
    PLOG(FATAL) << "sigaltstack failed";
  }
}

// The glibc AArch64 fatal reporter can consume over 200KiB while reading maps
// and unwinding. The historical 32KiB malloc-backed stack corrupts adjacent
// allocations. Keep this native signal stack separate from the managed heap,
// and guard both ends so an unexpected overflow cannot silently damage it.
static size_t HostSignalPageSize() {
  long page_size = sysconf(_SC_PAGESIZE);
  CHECK_GT(page_size, 0);
  return static_cast<size_t>(page_size);
}

static size_t HostSignalStackSize() {
  size_t minimum = static_cast<size_t>(MINSIGSTKSZ);
#if defined(_SC_SIGSTKSZ)
  long recommended = sysconf(_SC_SIGSTKSZ);
  if (recommended > 0) {
    minimum = std::max(minimum, static_cast<size_t>(recommended));
  }
#endif
  size_t size = std::max(minimum, static_cast<size_t>(256 * KB));
  size_t page = HostSignalPageSize();
  return (size + page - 1) / page * page;
}

void Thread::SetUpAlternateSignalStack() {
  // Create and set an alternate signal stack.
#ifdef ART_TARGET_ANDROID
  LOG(FATAL) << "Invalid use of alternate signal stack on Android";
#endif
  stack_t ss;
  size_t page = HostSignalPageSize();
  size_t size = HostSignalStackSize();
  void* region = mmap(nullptr, size + 2 * page, PROT_NONE,
                      MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
  CHECK_NE(region, MAP_FAILED);
  ss.ss_sp = reinterpret_cast<uint8_t*>(region) + page;
  ss.ss_size = size;
  if (mprotect(ss.ss_sp, size, PROT_READ | PROT_WRITE) != 0) {
    int saved_errno = errno;
    munmap(region, size + 2 * page);
    errno = saved_errno;
    PLOG(FATAL) << "mprotect alternate signal stack failed";
  }
  ss.ss_flags = 0;
  CHECK(ss.ss_sp != nullptr);
  SigAltStack(&ss, nullptr);

  // Double-check that it worked.
  ss.ss_sp = nullptr;
  SigAltStack(nullptr, &ss);
  VLOG(threads) << "Alternate signal stack is " << PrettySize(ss.ss_size) << " at " << ss.ss_sp;
}

void Thread::TearDownAlternateSignalStack() {
  // Get the pointer so we can free the memory.
  stack_t ss;
  SigAltStack(nullptr, &ss);
  uint8_t* allocated_signal_stack = reinterpret_cast<uint8_t*>(ss.ss_sp);
  size_t allocated_size = ss.ss_size;
  size_t page = HostSignalPageSize();

  // Tell the kernel to stop using it.
  ss.ss_sp = nullptr;
  ss.ss_flags = SS_DISABLE;
  ss.ss_size = allocated_size;
  SigAltStack(&ss, nullptr);

  // Free it.
  CHECK_EQ(munmap(allocated_signal_stack - page, allocated_size + 2 * page), 0);
}

}  // namespace art
