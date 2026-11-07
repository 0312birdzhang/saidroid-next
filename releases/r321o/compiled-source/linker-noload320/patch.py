"""Honor Android's no-load query without mapping ELF or running constructors."""
def patch(source):
    old='\tTRACE("[ %5d \'%s\' has not been loaded yet.  Locating...]\\n", apkenv_pid, name);\n'
    assert source.count(old)==1
    return source.replace(old,'''\t/* RTLD_NOLOAD is a query, including for ELF files that exist on disk.
\t * A preload guard must not run constructors or make a JNI library appear
\t * loaded before ART has performed its real load/JNI_OnLoad transaction. */
\tif (glibc_flag & RTLD_NOLOAD) {
\t\tif (try_glibc && glibc_handle) {
\t\t\tint flags = glibc_flag;
\t\t\tif (!(flags & (RTLD_LAZY | RTLD_NOW))) flags |= RTLD_NOW;
\t\t\t*glibc_handle = dlopen(name, flags);
\t\t\tif (*glibc_handle) return NULL;
\t\t}
\t\tDL_ERR("Library '%s' is not loaded", name);
\t\treturn NULL;
\t}

'''+old)
