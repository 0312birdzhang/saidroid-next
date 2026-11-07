#!/bin/bash
cd /tmp/art-build/art-standalone
python3 - <<'PY'
p="/tmp/art-build/art-standalone/art/runtime/parsed_options.cc"
src=open(p).read()
# 修掉 use-after-free
src = src.replace('''      char *bootclasspath_prefix = realpath(libart_so_full_path, NULL);
      free(libart_so_full_path);
      if (bootclasspath_prefix == nullptr) {
        // Boot classpath dir missing; let the caller use the default (env or -Xbootclasspath).
        LOG(WARNING) << "Boot classpath prefix not found: " << libart_so_full_path;
        return;
      }''',
'''      char *bootclasspath_prefix = realpath(libart_so_full_path, NULL);
      if (bootclasspath_prefix == nullptr) {
        // Boot classpath dir missing; fall back to the default boot class path.
        LOG(WARNING) << "Boot classpath prefix not found: " << libart_so_full_path;
        free(libart_so_full_path);
        return;
      }
      free(libart_so_full_path);''')
open(p,"w").write(src)
print("已修正 use-after-free")
PY
echo "=== 验证 ==="
sed -n '585,600p' art/runtime/parsed_options.cc 2>/dev/null
