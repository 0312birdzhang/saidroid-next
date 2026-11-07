#!/bin/bash
cd /tmp/art-build/art-standalone
cp art/runtime/parsed_options.cc art/runtime/parsed_options.cc.bak 2>/dev/null
python3 - <<'PY'
p="/tmp/art-build/art-standalone/art/runtime/parsed_options.cc"
src=open(p).read()
old = '''      char *bootclasspath_prefix = realpath(libart_so_full_path, NULL);
      free(libart_so_full_path);
      std::string bootclasspath_final = (std::string)
                                        bootclasspath_prefix + "/core-oj-hostdex.jar"      + ':' +'''
new = '''      char *bootclasspath_prefix = realpath(libart_so_full_path, NULL);
      free(libart_so_full_path);
      if (bootclasspath_prefix == nullptr) {
        // Boot classpath dir missing; let the caller use the default (env or -Xbootclasspath).
        LOG(WARNING) << "Boot classpath prefix not found: " << libart_so_full_path;
        return;
      }
      std::string bootclasspath_final = (std::string)
                                        bootclasspath_prefix + "/core-oj-hostdex.jar"      + ':' +'''
if old in src:
    src = src.replace(old, new)
    open(p,"w").write(src)
    print("已加 realpath NULL 检查")
else:
    print("未找到")
PY
