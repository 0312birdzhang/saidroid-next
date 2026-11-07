#ifndef SAIDROID_TRIG_ENTRY_SOURCE
#error Exact native host entry source required
#endif
#define main unused_real_host_main
#include SAIDROID_TRIG_ENTRY_SOURCE
#undef main
int main(int argc, char **argv) {
  if (argc != 2 || getuid() == 0) return 2;
  try {
    fs::path root = fs::canonical(argv[1]); environment(root);
    std::string preload = getenv("LD_PRELOAD");
    if (preload.find((root / "lib/libsdstrictmath-fdlibm.so").string()) == std::string::npos ||
        preload.find((root / "lib/libsdmath-trig.so").string()) == std::string::npos)
      throw std::runtime_error("Actual production environment omitted trigonometry backend");
    if (!dlopen((root / "lib/libsdstrictmath-fdlibm.so").c_str(), RTLD_NOW | RTLD_GLOBAL) ||
        !dlopen((root / "lib/libsdmath-trig.so").c_str(), RTLD_NOW | RTLD_GLOBAL))
      throw std::runtime_error(dlerror());
    Json owners;
    for (const char *symbol : {"Math_sin", "Math_cos", "Math_tan"}) {
      Dl_info owner{}; void *entry = dlsym(RTLD_DEFAULT, symbol);
      if (!entry || !dladdr(entry, &owner) || !owner.dli_fname ||
          fs::canonical(owner.dli_fname) != root / "lib/libsdmath-trig.so")
        throw std::runtime_error("Actual private native owner differs");
      owners[symbol] = owner.dli_fname;
    }
    void *libm = dlopen("libm.so.6", RTLD_NOW);
    auto libc_tan = reinterpret_cast<double (*)(double)>(dlsym(libm, "tan"));
    auto android_tan = reinterpret_cast<double (*)(double)>(dlsym(RTLD_DEFAULT, "Math_tan"));
    Dl_info owner{};
    if (!libc_tan || !dladdr(reinterpret_cast<void *>(libc_tan), &owner) || !owner.dli_fname ||
        fs::canonical(owner.dli_fname) == root / "lib/libsdmath-trig.so")
      throw std::runtime_error("Ordinary libc math was interposed");
    if (android_tan(5.319372648326541E255) != -2.13348538575370394E18 ||
        libc_tan(5.319372648326541E255) != -2.13348538575370752E18)
      throw std::runtime_error("Actual independent math boundaries differ");
    std::cout << Json({{"passed", true}, {"uid", getuid()}, {"preload", preload},
                      {"owners", owners}, {"ordinary_libc_tan_owner", owner.dli_fname}}).dump() << '\n';
    return 0;
  } catch (const std::exception &e) { std::cerr << e.what() << '\n'; return 1; }
}
