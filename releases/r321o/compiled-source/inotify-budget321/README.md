# Cooperative process inotify limits

SailDroid applications share the Sailfish user's kernel UID. One application's
unbounded file observers can exhaust that UID's inotify watches and affect the
desktop. This adapter counts live `/proc/self/fdinfo` rows before allocation and
limits each cooperating process to 512 watch rows and 16 inotify descriptor
references. It returns real `ENOSPC`/`EMFILE`; it never invents a successful watch,
allocates then removes a watch, changes sysctls, or suppresses delivered events.
Remove, one-shot expiry, descriptor close and normal fork reconcile through live
kernel state.

The private allocation lock serializes cooperating mutations, including those
on inherited instances. Cancellation is disabled only while locks and scoped
descriptors are held. A duplicate of the inotify descriptor keeps its open file
description stable. The requested watch target is never opened or pinned:
below the quota, the kernel receives the original pathname and flags, including
`IN_DONT_FOLLOW`, and performs the actual lookup and permission checks.
Non-inotify `syscall` calls retain all six AArch64 arguments and libc errno ABI.
The optional path mapper is **not wired into the accepted bridge**: the old
inotify binding did not translate paths, and this adapter preserves that behavior.

At the policy cap, **all add-watch requests return `ENOSPC`, including updates
of existing watches**. Removing a watch restores capacity and permits updates
again. An existing-inode check followed by a pathname syscall cannot safely
make an exception: a concurrent rename can turn the apparent update into a new
allocation. Linux 4.9 has no atomic update-existing-only inotify operation.
This is an explicit conservative policy change from the earlier pinned-target
implementation. `ENOSPC` can also take precedence over the kernel's eventual
path, mask or permission error at the cap. Below the cap, real kernel errors
and update semantics are preserved.

The earlier O_PATH target pin generated an extra `IN_CLOSE_NOWRITE` after watch
installation on the phone's 4.9 kernel. A successful watch is not proof of
correct event behavior. The replacement does not open the target, drain events,
or hide the extra event from an application. VM 6.8 does not reproduce the
O_PATH notification behavior, so a VM event test is not sufficient evidence for
the phone fix.

These are process limits, not a hard global UID reservation or a security
boundary. Duplicate/inherited descriptors can overcount the same kernel watch;
uncooperative raw syscalls and other processes still share the kernel UID limit.
An unreadable self census fails closed. Peer process access is never required.
Concurrent unguarded descriptor mutation is not a newly solved guarantee.

On the tested phone kernel **4.9.124**, an ordinary UID100000 process that
sets `PR_SET_DUMPABLE=0` loses access to its own fdinfo directory and entries
(`EACCES`), although `/proc/self/fd` stays accessible. The guard then fails
closed: `inotify_init1` returns `EMFILE` and `inotify_add_watch` returns
`EACCES`. Direct libc inotify calls still succeed. This is a known
**self-nondumpable compatibility limitation**, not actual exhaustion of the
16-instance quota, and not fixed by the target-event repair. The guard does
not change the application's dumpability or bypass the inaccessible census.
VM kernel6.8 permits the self-census and therefore does not exhibit this
boundary. The independent target diagnostic restored dumpability and cleaned
up all owned resources; its successful execution is not a compatibility pass.

An inaccessible *peer* is a separate case: the corrected fixture establishes
the peer's own watch before it drops dumpability, proves peer fdinfo is
inaccessible, then verifies the parent can still create/update its watches.
That case passes on the phone and does not claim the peer can make new guarded
calls while nondumpable. The old test's failed setup is retained separately.

The review-only candidate and tests are under
`build/evidence/apps-performance321-20261104/performance/no-opath-candidate-v1`.
Its baseline rebuild reproduces installed host SHA256
`226006ca8fe0d61e93210c5005da1b130f50a10046e3f2988067a3c0a1fcc65b`;
the candidate changes only the guard translation unit and preserves exports,
DT_NEEDED, Java and AOT inputs. VM fixtures explicitly test the new at-cap
contract, below-cap update/recovery, deterministic rename races, forked/shared
instances, cancellation, real permissions, flags and syscall forwarding.
Candidate activation and real-app acceptance are separate parent-run steps.

Historical evidence remains under
`build/evidence/apps-performance321-20261104/performance/inotify-budget-analysis-v1`.
The rejected peer-census policy and older pinned-target results are retained,
not relabelled as evidence for this replacement. The target reproduction is
`performance/signal-causality-v1/proc-mem-events-target-v2/result.json` beneath
the same task evidence directory; its earlier v1 permission failure is retained.

Target candidate results are retained under `no-opath-candidate-v1/`:
`no-opath-native-target-v2/phone/result.json` records production512/16 caps,
the corrected native policy suite, cancellation, and the explicitly classified
self-nondumpable limitation. Candidate SHA256 remains
`832548d373dfa2b17b87076cbff23f8ea78d52849611ebb9166c18686441e76c`.
