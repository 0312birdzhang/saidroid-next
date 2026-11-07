F=/tmp/shimtest/libandroidfw.so
echo "=== AssetManager 构造/资源相关导出 ==="
nm -D --defined-only -C $F 2>/dev/null | grep -E "AssetManager::(AssetManager|addDefaultAssets|addAssetPath|getResources|setLocale)" | head -20
echo "=== 原始修饰名 ==="
nm -D --defined-only $F 2>/dev/null | grep -E "_ZN7android12AssetManager(C|14addDefault|12addAssetPath|12getResources)" | head -20
echo "=== ResTable 相关 ==="
nm -D --defined-only $F 2>/dev/null | grep -E "_ZNK7android8ResTable(9isLoaded|13getTableCount)Ev" | head
echo "=== String8 ctor ==="
nm -D --defined-only $F 2>/dev/null | grep -E "_ZN7android7String8C1EPKc" | head -2
echo "=== ZipFileRO::open ==="
nm -D --defined-only $F 2>/dev/null | grep -E "_ZN7android9ZipFileRO4openEPKc" | head -2
