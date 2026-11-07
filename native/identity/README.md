# App identity backend

`app-identity.hpp` implements durable, privileged Android app-ID allocation in
10000–19999. Each application receives a different real Linux UID/GID; host
account IDs are skipped. A package keeps its ID on a same-signer update or
reinstall. Retired IDs remain reserved and cannot migrate to another package.

The registry requires a root caller, root-owned state directory and ancestors,
no symlinks or writable ancestors, single-link regular files, an exclusive lock,
and synchronized atomic state replacement. Initialization is explicit and
requires a new empty directory. Missing or corrupt existing state fails closed;
it never silently resets the allocator and reuses IDs.

This is a backend primitive. Its `allocate_verified` method accepts certificate
fingerprints **only after** a trusted installer has genuinely verified the
immutable APK. It is not an APK verifier, package installer, permission service,
launcher broker, or setuid executable. Shared UIDs, signer rotation and Android
user/profile allocation are not implemented. It has not changed the phone's
current shared-user launch path.

VM checks exercise persistence, failed signer updates, malformed state, concurrent
allocation and real kernel UID/file/signal boundaries. Synthetic public digest
fixtures in these allocator checks are not presented as signed APK verification.

`VerifiedApkIdentity.java` uses the matching Android 10 `PackageParser` and real
`collectCertificates` verifier in an ordinary UID. It requires an immutable,
root-staged APK and does not load the application's DEX. The verified worker
result is passed directly to the root allocator only after its process exits
successfully and the staged file hash is rechecked.

`identity-exec.cpp` is a root-only primitive for a trusted supervisor. It executes
an already selected native ELF using a pinned file descriptor, drops all real
UID/GID values and supplementary groups, empties capability bounding/permitted/
effective sets, enables `no_new_privs`, closes inherited descriptors, and clears
the inherited environment. Setuid/file-capability/symlink entrypoints and another
application's private data directory are rejected. It inherits the current
runtime's verified scheduling limit of 40; no additional capability is retained.

`private-userdb.hpp` supplies the actual numeric UID/GID's account entry through
read-only tmpfs-backed `/etc/passwd`, `/etc/group` and NSS views in a new private
mount namespace. Global host account files remain unchanged. This enables
ordinary libc and D-Bus account lookup without an environment-preload fake UID.
The temporary source mount is detached and removed before exec; only the private
read-only account views remain for that process family.

The private session-bus template imports no host activation directories. The
supervisor must substitute only its known per-UID Unix socket address and keep
the runtime directory owned by that UID with mode 0700. Actual D-Bus EXTERNAL
authentication and Unix credential queries identify the numeric UID; another
UID cannot connect through the private directory.

VM integration now genuinely verifies two signed APKs, allocates identities and
launches native worker processes as those UIDs. Tampered and unsigned fixtures
are rejected before allocation. These are backend and launch-primitive checks;
Android Activity launch, Binder services, launcher integration, complete package
installation and phone migration remain separate work.

`service-access.hpp` binds root-verified APK service declarations and permission
requests to durable app identities. Registration requires the actual owner UID.
Resolution uses the kernel Binder caller UID: own UID, exported service, declared
request and real matching certificate set are separate checks. Normal requested
permissions and exact signature matching are implemented. Dangerous grants,
platform/privileged/role permissions, shared UIDs and signer rotation remain
unavailable; unknown cases fail closed. Actual kernel Binder tests use this
policy with genuinely signed APK metadata, including a differently signed
negative fixture. This does not yet execute Android Service classes.

The Java/Parcel/JNI layer now has a real cross-UID VM transport contract in both
directions, including nested Binder callbacks and clear/restoreCallingIdentity.
The non-SELinux VM cannot supply Android's optional transaction security-context
payload, so its explicitly separate fixture uses the real legacy context-manager
ioctl. Actual kernel credentials and LSM transaction checks remain in force. No
fake label or phone Binder change is involved.

`compile-service-policy.cpp` seals the existing genuinely verified APK facts and
identity snapshot into a new root-owned 0444 authorization file. It is not an APK
verifier. `java/VerifiedServicePolicy.java` accepts only a bounded immutable file
with trusted ancestors and uses actual Binder caller credentials. The exact same
four signed metadata fixtures now pass 14 real Java Binder cases for private,
exported, normal/signature/dangerous, unknown UID, undeclared, disabled, and owner
registration authorization. The transaction's claimed UID is ignored. Twelve
compiler and nine ordinary-UID consumer filesystem cases also pass, including
symlinks, hardlinks, owner/mode/ancestor changes and refusing output overwrite.

These are authorization/backend contracts, not execution of the fixtures'
manifest-declared Service classes. A trusted installer and supervisor must still
refresh the sealed snapshot when APK or identity state changes and manage the
corresponding real Android Service lifecycle. Dangerous permission grants,
platform/privileged permissions, shared UIDs and signer rotation remain denied.
No identity/backend changes have been deployed to the phone or added to r194.

`android-hosts-view.hpp` is a source-owned private hosts composition helper.
It preserves host lines and custom aliases byte-for-byte, adds absent Android
loopback names, and rejects conflicting protected aliases or malformed/bounded
input. A separately built private-userdb copy mounts its result read-only beside
the account/NSS files. Actual VM namespace/NSS tests confirm UID10049 resolves
ip6-localhost to::1, preserves a custom alias and leaves parent/global files
unchanged. This is still a backend prototype: the running phone's shared-user
launcher does not yet use this private view.
