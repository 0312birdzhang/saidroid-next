"""Keep sibling ELF dependencies distinct from already loaded platform copies."""
def patch(source):
 old='\tfor(int i = 0; i < lib_override_map.len; i++) {\n'
 assert source.count(old)==1
 source=source.replace(old,'''\t/* These immutable ELF files support dependency inspection. Execution still
\t * uses the existing host ABI bridges, including an explicit Java load. */
\tconst char *root = getenv("ANDROID_ROOT");
\tif (root && root[0] == '/') {
\t\tsize_t n = strlen(root);
\t\tif (!strncmp(name, root, n) && !strncmp(name + n, "/android-libs/", 14)) {
\t\t\tconst char *leaf = name + n + 14;
\t\t\tfor (int i = 0; i < lib_override_map.len; ++i)
\t\t\t\tif (!strcmp(leaf, lib_override_map.overrides[i].from)) { name = leaf; break; }
\t\t}
\t}

'''+old)
 old='\tfor (si = apkenv_solist; si != 0; si = si->next) {\n\t\tconst char *soname = strchr(name, \'/\') ? NULL : apkenv_soname(si);'
 assert source.count(old)==1
 source=source.replace(old,'''\tchar canonical[PATH_MAX];
\tconst bool explicit_path = strchr(name, '/') != NULL;
\tconst char *identity = explicit_path && realpath(name, canonical) ? canonical : name;
\tfor (si = apkenv_solist; si != 0; si = si->next) {
\t\tconst char *soname = explicit_path ? NULL : apkenv_soname(si);''')
 old='\t\tif (!strcmp(bname, si->name) || (soname && !strcmp(name, soname))) {'
 assert source.count(old)==1
 source=source.replace(old,'''\t\tif ((explicit_path ? !strcmp(identity, si->fullpath) : !strcmp(bname, si->name)) ||
\t\t    (soname && !strcmp(name, soname))) {''')
 old='\t\t\tlsi = apkenv_find_library(si->strtab + d->d_un.d_val, true, RTLD_NOW, NULL);'
 assert source.count(old)==1
 source=source.replace(old,'''\t\t\tconst char *needed = si->strtab + d->d_un.d_val;
\t\t\tchar sibling[PATH_MAX];
\t\t\tbool bridged = false;
\t\t\tfor (int i = 0; i < lib_override_map.len; ++i)
\t\t\t\tif (!strcmp(needed, lib_override_map.overrides[i].from)) bridged = true;
\t\t\t/* An APK may bundle its own libcrypto/libssl with the same SONAME
\t\t\t * as the framework. Resolve its real sibling before global reuse;
\t\t\t * existing path trust and ELF validation remain in load_library. */
\t\t\tconst char *slash = strrchr(si->fullpath, '/');
\t\t\tif (!bridged && !strchr(needed, '/') && slash) {
\t\t\t\tsize_t length = (size_t)(slash - si->fullpath) + 1;
\t\t\t\tif (length + strlen(needed) < sizeof(sibling)) {
\t\t\t\t\tmemcpy(sibling, si->fullpath, length);
\t\t\t\t\tstrcpy(sibling + length, needed);
\t\t\t\t\tif (!access(sibling, R_OK)) needed = sibling;
\t\t\t\t}
\t\t\t}
\t\t\tlsi = apkenv_find_library(needed, true, RTLD_NOW, NULL);''')
 return source
