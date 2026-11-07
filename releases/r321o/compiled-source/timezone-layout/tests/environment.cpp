#ifndef SAIDROID_TIMEZONE_ENTRY_SOURCE
#error Exact native host entry source required
#endif
#define main unused_real_host_main
#include SAIDROID_TIMEZONE_ENTRY_SOURCE
#undef main
int main(int argc,char **argv) {
  if(argc!=2 || getuid()==0) return 2;
  try {
    fs::path root=fs::canonical(argv[1]);
    environment(root);
    Json values;
    for(auto key : {"ANDROID_ROOT","ANDROID_RUNTIME_ROOT","ANDROID_TZDATA_ROOT","ANDROID_DATA","ICU_DATA","SD_BUILD_PROP"})
      values[key]=getenv(key)?Json(getenv(key)):Json();
    std::cout<<values.dump()<<'\n';return 0;
  }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
