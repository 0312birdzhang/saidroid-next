"""Restore each ELF PT_LOAD's declared permissions after relocation."""
def patch(source):
    start=source.index('\n#if 0\n\t/* This is the way that the old dynamic linker did protection of')
    end=source.index('\n\tif (si->gnu_relro_start',start)
    replacement=r'''
    /* A 32-bit aggregate write-protect range truncates aarch64 addresses.
     * Its coarse RX mask also loses the distinction between R and RX data.
     * Restore each PT_LOAD from the mapped ELF's own flags, before constructors
     * execute. RELRO below then removes write access from its subset. */
    for (size_t index = 0; index < si->phnum; ++index) {
        const ElfW(Phdr) *segment = &si->phdr[index];
        if (segment->p_type != PT_LOAD || !segment->p_memsz) continue;
        ElfW(Addr) address = si->base + segment->p_vaddr;
        ElfW(Addr) start = address & ~((ElfW(Addr))PAGE_MASK);
        size_t length = (size_t)((address - start + segment->p_memsz + PAGE_MASK)
                                & ~((ElfW(Addr))PAGE_MASK));
        if (mprotect((void *)(uintptr_t)start, length,
                     PFLAGS_TO_PROT(segment->p_flags)) < 0) {
            DL_ERR("PT_LOAD mprotect of library '%s' failed: %d (%s)",
                   si->name, errno, strerror(errno));
            goto fail;
        }
    }
'''
    return source[:start]+'\n'+replacement+source[end:]
