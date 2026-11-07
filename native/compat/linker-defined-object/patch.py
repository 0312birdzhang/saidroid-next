"""Keep a DSO's defined ELF data symbols out of host function hook resolution."""
def patch(source):
    needle='\t\t\tif ((sym_addr = (uintptr_t)dlsym(RTLD_DEFAULT, wrap_sym_name))) {'
    replacement='''\t\t\t/* A defined data symbol can have the same name as a host API
\t\t\t * function (e.g. a client's extension-function pointer). Preserve
\t\t\t * its local storage; redirecting it to executable host code turns
\t\t\t * normal assignments into writes through a function address. */
\t\t\tif (ELF_ST_TYPE(si->symtab[sym].st_info) == STT_OBJECT &&
\t\t\t    si->symtab[sym].st_shndx != SHN_UNDEF) {
\t\t\t\ts = &si->symtab[sym];
\t\t\t\tbase = s->st_shndx == SHN_ABS ? 0 : si->base;
\t\t\t\tapkenv_last_library_used = si->name;
\t\t\t} else if ((sym_addr = (uintptr_t)dlsym(RTLD_DEFAULT, wrap_sym_name))) {'''
    assert source.count(needle)==1
    return source.replace(needle,replacement,1)
