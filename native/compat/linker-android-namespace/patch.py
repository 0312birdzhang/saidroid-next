"""Keep Android ELF enumeration in its ABI domain; retain mixed native unwind."""
def patch(source):
    source=source.replace('struct dl_phdr_info dl_info;','struct dl_phdr_info dl_info = {0};',1)
    source=source.replace('dl_info.dlpi_addr = si->linkmap.l_addr;', 'dl_info.dlpi_addr = si->base;', 1)
    source=source.replace('dl_info.dlpi_name = si->linkmap.l_name;', 'dl_info.dlpi_name = si->fullpath[0] ? si->fullpath : si->name;', 1)
    needle='''\tif (rv)
\t\treturn rv;
\telse
\t\treturn dl_iterate_phdr(cb, data);
}'''
    replacement='''\treturn rv;
}

/* Android callbacks parse Bionic ELF dynamic entries, whose d_ptr values
 * remain load-relative. glibc relocates those entries in-place. Exposing
 * host implementation libraries through the Android iterator mixes ABIs and
 * makes normal Android ELF parsers add the load bias twice. Native unwinding
 * still needs both domains and uses this explicitly private combined view. */
int sd_mixed_dl_iterate_phdr(int (*cb)(struct dl_phdr_info *, size_t, void *),
                            void *data)
{
    int result = bionic_dl_iterate_phdr(cb, data);
    return result ? result : dl_iterate_phdr(cb, data);
}'''
    assert source.count(needle)==1
    source=source.replace(needle,replacement,1)
    needle='unw_set_iterate_phdr_function(unw_local_addr_space, &bionic_dl_iterate_phdr);'
    assert source.count(needle)==1
    return source.replace(needle,'unw_set_iterate_phdr_function(unw_local_addr_space, &sd_mixed_dl_iterate_phdr);',1)
