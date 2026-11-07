#include "host-common.hpp"
#include <dlfcn.h>
#include <jni.h>
static std::string text(JNIEnv *e, jstring v) {
  if (!v)
    throw std::runtime_error("Missing API argument");
  const char *s = e->GetStringUTFChars(v, nullptr);
  if (!s)
    throw std::runtime_error("Invalid API argument");
  std::string r = s;
  e->ReleaseStringUTFChars(v, s);
  return r;
}
static GDBusConnection *session() {
  GError *e = nullptr;
  auto c = g_bus_get_sync(G_BUS_TYPE_SESSION, nullptr, &e);
  if (!c) {
    std::string msg = e ? e->message : "Session bus unavailable";
    g_clear_error(&e);
    throw std::runtime_error(msg);
  }
  return c;
}
static void error(JNIEnv *e, const std::exception &ex) {
  if (!e->ExceptionCheck())
    e->ThrowNew(e->FindClass("java/lang/IllegalStateException"), ex.what());
}
extern "C" JNIEXPORT void JNICALL
Java_org_saildroid_host_HostApi_openApplication(JNIEnv *e, jclass,
                                                jstring value) {
  try {
    auto s = text(e, value);
    auto c = session();
    auto v = call(c, "OpenApplication", g_variant_new("(s)", s.c_str()));
    g_variant_unref(v);
    g_object_unref(c);
  } catch (const std::exception &ex) {
    error(e, ex);
  }
}
extern "C" JNIEXPORT void JNICALL Java_org_saildroid_host_HostApi_startService(
    JNIEnv *e, jclass, jstring package, jstring service, jstring process) {
  try {
    auto a = text(e, package), b = text(e, service), d = text(e, process);
    auto c = session();
    auto v = call(c, "StartService",
                  g_variant_new("(sss)", a.c_str(), b.c_str(), d.c_str()));
    g_variant_unref(v);
    g_object_unref(c);
  } catch (const std::exception &ex) {
    error(e, ex);
  }
}
extern "C" JNIEXPORT jstring JNICALL
Java_org_saildroid_host_HostApi_state(JNIEnv *e, jclass, jstring package) {
  try {
    auto s = text(e, package);
    auto c = session();
    auto v = call(c, "GetState", g_variant_new("(s)", s.c_str()));
    const char *reply;
    g_variant_get(v, "(&s)", &reply);
    jstring result = e->NewStringUTF(reply);
    g_variant_unref(v);
    g_object_unref(c);
    return result;
  } catch (const std::exception &ex) {
    error(e, ex);
    return nullptr;
  }
}
extern "C" JNIEXPORT void JNICALL
Java_org_saildroid_host_HostApi_startActivityProcess(
    JNIEnv *e, jclass, jstring package, jstring activity, jstring process) {
  try {
    auto a = text(e, package), b = text(e, activity), d = text(e, process);
    auto c = session();
    auto v = call(c, "StartActivityProcess",
                  g_variant_new("(sss)", a.c_str(), b.c_str(), d.c_str()));
    g_variant_unref(v);
    g_object_unref(c);
  } catch (const std::exception &ex) {
    error(e, ex);
  }
}
extern "C" JNIEXPORT void JNICALL
Java_org_saildroid_host_HostApi_startProviderProcess(
    JNIEnv *e, jclass, jstring package, jstring provider, jstring process) {
  try {
    auto a = text(e, package), b = text(e, provider), d = text(e, process);
    auto c = session();
    auto v = call(c, "StartProviderProcess",
                  g_variant_new("(sss)", a.c_str(), b.c_str(), d.c_str()));
    g_variant_unref(v);
    g_object_unref(c);
  } catch (const std::exception &ex) {
    error(e, ex);
  }
}
extern "C" JNIEXPORT void JNICALL
Java_org_saildroid_host_HostApi_startReceiverProcess(
    JNIEnv *e, jclass, jstring package, jstring receiver, jstring process) {
  try {
    auto a = text(e, package), b = text(e, receiver), d = text(e, process);
    auto c = session();
    auto v = call(c, "StartReceiverProcess",
                  g_variant_new("(sss)", a.c_str(), b.c_str(), d.c_str()));
    g_variant_unref(v);
    g_object_unref(c);
  } catch (const std::exception &ex) {
    error(e, ex);
  }
}
extern "C" JNIEXPORT void JNICALL
Java_org_saildroid_host_HostApi_activateSelf(JNIEnv *e, jclass) {
  try {
    const char *key = getenv("SAILDROID_HOST_INSTANCE");
    const char *generation = getenv("SAILDROID_HOST_LAUNCH_ID");
    if (!key || !generation)
      throw std::runtime_error("Host generation is unavailable");
    auto c = session();
    auto mapped = call(c, "WindowEvent", g_variant_new("(ssi)", key, "mapped", 1));
    g_variant_unref(mapped);
    auto v = call(c, "Activate", g_variant_new("(ss)", key, generation));
    g_variant_unref(v);
    g_object_unref(c);
  } catch (const std::exception &ex) {
    error(e, ex);
  }
}
static GVariant *mce(const std::string &method) {
  if (method != "get_display_status" && method != "get_tklock_mode" &&
      method != "get_psm_state")
    throw std::runtime_error("MCE method is not read-only");
  GError *e = nullptr;
  auto c = g_bus_get_sync(G_BUS_TYPE_SYSTEM, nullptr, &e);
  if (!c) {
    g_clear_error(&e);
    throw std::runtime_error("System bus unavailable");
  }
  auto r = g_dbus_connection_call_sync(
      c, "com.nokia.mce", "/com/nokia/mce/request", "com.nokia.mce.request",
      method.c_str(), nullptr, nullptr, G_DBUS_CALL_FLAGS_NONE, 1000, nullptr,
      &e);
  g_object_unref(c);
  if (!r) {
    std::string s = e ? e->message : "MCE request failed";
    g_clear_error(&e);
    throw std::runtime_error(s);
  }
  return r;
}
extern "C" JNIEXPORT jstring JNICALL
Java_org_saildroid_host_HostApi_mceString(JNIEnv *e, jclass, jstring method) {
  try {
    auto v = mce(text(e, method));
    if (!g_variant_is_of_type(v, G_VARIANT_TYPE("(s)"))) {
      g_variant_unref(v);
      throw std::runtime_error("MCE string type differs");
    }
    const char *s;
    g_variant_get(v, "(&s)", &s);
    auto result = e->NewStringUTF(s);
    g_variant_unref(v);
    return result;
  } catch (const std::exception &ex) {
    error(e, ex);
    return nullptr;
  }
}
extern "C" JNIEXPORT jboolean JNICALL
Java_org_saildroid_host_HostApi_mceBoolean(JNIEnv *e, jclass, jstring method) {
  try {
    auto v = mce(text(e, method));
    if (!g_variant_is_of_type(v, G_VARIANT_TYPE("(b)"))) {
      g_variant_unref(v);
      throw std::runtime_error("MCE boolean type differs");
    }
    gboolean b;
    g_variant_get(v, "(b)", &b);
    g_variant_unref(v);
    return b ? JNI_TRUE : JNI_FALSE;
  } catch (const std::exception &ex) {
    error(e, ex);
    return JNI_FALSE;
  }
}

extern "C" JNIEXPORT void JNICALL
Java_org_saildroid_host_HostApi_ready(JNIEnv *e, jclass) {
  try {
    auto ready = (void (*)(void))dlsym(RTLD_DEFAULT, "sd_host_java_ready");
    if (!ready)
      throw std::runtime_error("Native host lifecycle unavailable");
    ready();
  } catch (const std::exception &ex) {
    error(e, ex);
  }
}
