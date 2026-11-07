#!/usr/bin/env python3
"""修 ART 上游缺陷：OatFileAssistant::GetBestOatFile() 计算 framework-res 后缀时下溢。

原代码：
    bool is_framework_res = dex_location_.compare(
        dex_location_.size() - (sizeof("framework-res.apk")-1),
        sizeof("framework-res.apk")-1, "framework-res.apk") == 0;

当 dex_location_ 短于 17 个字符时，size()-17 下溢成极大值（-3 之类），
std::string::compare 的 _M_check 抛 std::out_of_range，异常没人接 -> terminate -> SIGABRT。
宿主上短 boot classpath 项就会触发。AOSP 后来改用 EndsWith 修掉了，这里补上长度判断。
"""
import sys

OLD = (
    '  bool is_framework_res = dex_location_.compare(dex_location_.size() - '
    '(sizeof("framework-res.apk")-1), sizeof("framework-res.apk")-1, '
    '"framework-res.apk") == 0;\n'
)

NEW = '''  // framework-res.apk contains no dex files.
  // 注意：dex_location_ 可能比这个后缀还短（宿主上短 boot classpath 项就会这样）。
  // 直接 size()-17 会下溢成极大值，std::string::compare 抛 std::out_of_range 直接终止进程。
  constexpr size_t kFrameworkResSuffixLen = sizeof("framework-res.apk") - 1;
  if (dex_location_.size() < kFrameworkResSuffixLen) {
    LOG(WARNING) << "Short dex location, skip framework-res check: " << dex_location_;
  }
  bool is_framework_res =
      dex_location_.size() >= kFrameworkResSuffixLen &&
      dex_location_.compare(dex_location_.size() - kFrameworkResSuffixLen,
                            kFrameworkResSuffixLen, "framework-res.apk") == 0;
'''


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else \
        "/tmp/art-build/art-standalone/art/runtime/oat_file_assistant.cc"
    src = open(path).read()
    if NEW.splitlines()[2].strip() in src:
        print("已打过补丁，跳过")
        return 0
    if OLD not in src:
        print("未找到原始语句，请检查文件：", path)
        return 1
    src = src.replace(OLD, NEW, 1)
    open(path, "w").write(src)
    print("补丁已应用：", path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
