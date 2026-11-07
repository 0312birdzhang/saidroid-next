/* Stable per-application host. It owns the desktop PID, maps the Wayland
 * parent before ART, then creates ART in this same process. */
#include "jni.h"
#include "nativehelper/JniInvocation.h"
#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <dlfcn.h>
#include <memory>
#include <string>
#include <unistd.h>
#include <vector>
#include <time.h>
static long long startup_ns(){timespec t{};clock_gettime(CLOCK_MONOTONIC,&t);return (long long)t.tv_sec*1000000000+t.tv_nsec;}
static void startup_phase(const char*name){fprintf(stderr,"SDSTARTUP_NATIVE=phase|name=%s|time_ns=%lld\n",name,startup_ns());}


typedef int (*Bootstrap)(const char *, const char *, int, int);
typedef void (*BindVm)(JavaVM *);
static int invoke(JNIEnv *env, char **argv) {
  int count = 0;
  while (argv[count + 1])
    count++;
  jclass stringClass = env->FindClass("java/lang/String");
  if (!stringClass)
    return 1;
  jobjectArray args = env->NewObjectArray(count, stringClass, nullptr);
  env->DeleteLocalRef(stringClass);
  if (!args)
    return 1;
  for (int i = 0; i < count; i++) {
    jstring value = env->NewStringUTF(argv[i + 1]);
    if (!value)
      return 1;
    env->SetObjectArrayElement(args, i, value);
    env->DeleteLocalRef(value);
  }
  std::string name(argv[0]);
  std::replace(name.begin(), name.end(), '.', '/');
  jclass klass = env->FindClass(name.c_str());
  if (!klass) {
    fprintf(stderr, "SDHOST=java_class_failed|class=%s\n", argv[0]);
    env->ExceptionDescribe();
    return 1;
  }
  jmethodID main =
      env->GetStaticMethodID(klass, "main", "([Ljava/lang/String;)V");
  if (!main) {
    env->ExceptionDescribe();
    return 1;
  }
  env->CallStaticVoidMethod(klass, main, args);
  if (env->ExceptionCheck()) {
    env->ExceptionDescribe();
    return 1;
  }
  return 0;
}
static std::string window_library(int argc, char **argv) {
  for (int i = 0; i < argc; i++) {
    const char *prefix = "-Dsaidroid.window.library=";
    size_t n = strlen(prefix);
    if (!strncmp(argv[i], prefix, n))
      return argv[i] + n;
  }
  return "/home/art/api29-root/lib/libsdwindow.so";
}
extern "C" int sd_host_prepare_art();
extern "C" int sd_host_wait_broker();
extern "C" void sd_host_window_event(const char *, int);
extern "C" void sd_host_java_ready();
int sd_art_main(int argc, char **argv) {
  setvbuf(stdout, nullptr, _IONBF, 0);
  if (argc < 2) {
    fprintf(stderr, "usage: saildroid-app [ART options] class args...\n");
    return 2;
  }
  std::string library = window_library(argc, argv);
  void *handle = dlopen(library.c_str(), RTLD_NOW | RTLD_GLOBAL);
  Bootstrap bootstrap =
      handle ? (Bootstrap)dlsym(handle, "sd_window_bootstrap") : nullptr;
  BindVm bind = handle ? (BindVm)dlsym(handle, "sd_window_bind_vm") : nullptr;
  if (!bootstrap || !bind) {
    fprintf(stderr, "SDHOST=window_library_failed|path=%s|error=%s\n",
            library.c_str(), dlerror());
    return 125;
  }
  auto hooks = (void (*)(void (*)(const char *, int), void (*)(void)))dlsym(
      handle, "sd_window_bind_host_hooks");
  if (!hooks) {
    fprintf(stderr, "SDHOST=window_hooks_missing\n");
    return 125;
  }
  hooks(sd_host_window_event, sd_host_java_ready);
  const char *headless = getenv("SAILDROID_HEADLESS");
  const char *title = getenv("SAILDROID_PACKAGE");
  if (!title || !*title)
    title = "SailDroid";
  const char *id = getenv("SAILDROID_DESKTOP_ID");
  if (!id || !*id)
    id = title;
  int width = 1080, height = 2160;
  const char *w = getenv("SAILDROID_DISPLAY_WIDTH"),
             *h = getenv("SAILDROID_DISPLAY_HEIGHT");
  if (w)
    width = atoi(w);
  if (h)
    height = atoi(h);
  if (!headless && !bootstrap(title, id, width, height)) {
    fprintf(stderr, "SDHOST=early_window_failed\n");
    return 125;
  }
  startup_phase("window_ready");
  int prepare = sd_host_prepare_art();
  startup_phase("vm_admitted");
  if (prepare)
    return prepare;
  /* Match dalvikvm's option parser. The first non-option token is the Java
   * main class; all prior arguments are VM options. */
  int class_index = 1;
  bool extra = false;
  for (; class_index < argc; class_index++) {
    const char *a = argv[class_index];
    if (a[0] != '-' && !extra)
      break;
    extra = false;
    if (!strcmp(a, "-cp") || !strcmp(a, "-classpath"))
      extra = true;
  }
  if (class_index >= argc) {
    fprintf(stderr, "SDHOST=class_missing\n");
    return 2;
  }
  int options_count = class_index - 1;
  std::unique_ptr<JavaVMOption[]> options(new JavaVMOption[options_count]());
  for (int i = 1; i < class_index; i++)
    options[i - 1].optionString = argv[i];
  JniInvocation invocation;
  const char *jni_lib = nullptr;
  std::string selected_art;
  for (int i = 1; i < class_index; i++) {
    const char *prefix = "-Dsaidroid.art.library=";
    if (!strncmp(argv[i], prefix, strlen(prefix)))
      selected_art = argv[i] + strlen(prefix);
  }
  void *selected_handle = nullptr;
  if (!selected_art.empty()) {
    // libnativehelper has an ORIGIN RPATH: LD_LIBRARY_PATH alone cannot pin
    // its dlopen("libart.so"). Load the validated component path explicitly.
    selected_handle = dlopen(selected_art.c_str(), RTLD_NOW | RTLD_NODELETE);
    if (!selected_handle || !dlsym(selected_handle, "JNI_CreateJavaVM")) {
      fprintf(stderr, "SDHOST=art_library_failed|path=%s\n", selected_art.c_str());
      return 125;
    }
    jni_lib = selected_art.c_str();
  }
  if (!invocation.Init(jni_lib)) {
    fprintf(stderr, "SDHOST=jni_init_failed\n");
    return 125;
  }
  JavaVMInitArgs args{};
  args.version = JNI_VERSION_1_6;
  args.options = options.get();
  args.nOptions = options_count;
  args.ignoreUnrecognized = JNI_FALSE;
  JavaVM *vm = nullptr;
  JNIEnv *env = nullptr;
  startup_phase("vm_create_start");
  if (JNI_CreateJavaVM(&vm, &env, &args) != JNI_OK) {
    fprintf(stderr, "SDHOST=jvm_create_failed\n");
    return 125;
  }
  startup_phase("vm_created");
  if(sd_host_wait_broker()!=0){vm->DestroyJavaVM();return 125;}
  startup_phase("broker_ready");
  bool debuggable=false;
  for(int i=1;i<class_index;i++)
    if(!strcmp(argv[i],"-Dsaidroid.package.debuggable=true"))debuggable=true;
  void *art=selected_handle ? selected_handle : dlopen("libart.so",RTLD_NOW|RTLD_NOLOAD);
  auto allow=art?reinterpret_cast<void(*)(bool)>(dlsym(art,"_ZN3art3Dbg14SetJdwpAllowedEb")):nullptr;
  if(!allow){fprintf(stderr,"SDHOST=debug_policy_unavailable\n");return 125;}
  allow(debuggable);
  if(art)dlclose(art);
  if (!selected_art.empty())
    fprintf(stderr, "SDHOST=art_library|path=%s|selection=explicit-component\n", selected_art.c_str());
  fprintf(stderr,"SDHOST=debug_policy|allowed=%s|scope=process|source=installed-manifest-record\n",debuggable?"true":"false");
  bind(vm);
  fprintf(stderr, "SDHOST=art_bound|pid=%d|same_pid=true\n", getpid());
  int rc = invoke(env, &argv[class_index]);
  vm->DestroyJavaVM();
  return rc;
}
