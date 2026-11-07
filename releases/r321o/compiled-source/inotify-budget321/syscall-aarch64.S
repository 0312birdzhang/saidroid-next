/* Linux AArch64 syscall ABI: number x0; arguments x1..x6. No C varargs read.
 * Only the three inotify operations dispatch to policy; other numbers retain
 * syscall semantics, including -1 and thread-local errno. */
.text
.p2align 2
.global syscall
.type syscall,%function
syscall:
.Lcommon:
    cmp x0,#26
    b.eq .Linit
    cmp x0,#27
    b.eq .Ladd
    cmp x0,#28
    b.eq .Lremove
    b saildroid_raw_syscall6
.Linit:
    mov x0,x1
    b sd_guard_sys_init
.Ladd:
    mov x0,x1
    mov x1,x2
    mov x2,x3
    b sd_guard_sys_add
.Lremove:
    mov x0,x1
    mov x1,x2
    b sd_guard_sys_remove
.size syscall,.-syscall
.global bionic_syscall
.type bionic_syscall,%function
bionic_syscall:
    cmp x0,#27
    b.eq .Lbionic_add
    b .Lcommon
.Lbionic_add:
    mov x0,x1
    mov x1,x2
    mov x2,x3
    b sd_guard_sys_android_add
.size bionic_syscall,.-bionic_syscall
.global saildroid_raw_syscall6
.hidden saildroid_raw_syscall6
.type saildroid_raw_syscall6,%function
saildroid_raw_syscall6:
    mov x8,x0
    mov x0,x1
    mov x1,x2
    mov x2,x3
    mov x3,x4
    mov x4,x5
    mov x5,x6
    svc #0
    cmn x0,#4095
    b.cs .Lerror
    ret
.Lerror:
    stp x29,x30,[sp,#-32]!
    mov x29,sp
    neg x1,x0
    str w1,[sp,#16]
    bl __errno_location
    ldr w1,[sp,#16]
    str w1,[x0]
    mov x0,#-1
    ldp x29,x30,[sp],#32
    ret
.size saildroid_raw_syscall6,.-saildroid_raw_syscall6
.section .note.GNU-stack,"",%progbits
