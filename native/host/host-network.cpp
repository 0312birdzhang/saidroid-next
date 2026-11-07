#include "host-common.hpp"
#include <jni.h>

// Query ConnMan's actual radio state. There is deliberately no setter, scan,
// network mutation, credential query or shell command on this boundary.
extern "C" JNIEXPORT jint JNICALL
Java_org_saildroid_host_HostApi_wifiEnabledState(JNIEnv *env,jclass) {
    GError *error=nullptr;
    auto bus=g_bus_get_sync(G_BUS_TYPE_SYSTEM,nullptr,&error);
    if(!bus){
        g_clear_error(&error);
        env->ThrowNew(env->FindClass("java/lang/IllegalStateException"),"Host network bus unavailable");
        return 4;
    }
    auto reply=g_dbus_connection_call_sync(bus,"net.connman","/","net.connman.Manager",
            "GetTechnologies",nullptr,G_VARIANT_TYPE("(a(oa{sv}))"),
            G_DBUS_CALL_FLAGS_NONE,1500,nullptr,&error);
    g_object_unref(bus);
    if(!reply){
        g_clear_error(&error);
        env->ThrowNew(env->FindClass("java/lang/IllegalStateException"),"Host Wi-Fi technology query unavailable");
        return 4;
    }
    auto technologies=g_variant_get_child_value(reply,0);
    GVariantIter iterator;g_variant_iter_init(&iterator,technologies);
    const char *path=nullptr;GVariant *properties=nullptr;
    int state=4,count=0;
    while(g_variant_iter_next(&iterator,"(&o@a{sv})",&path,&properties)){
        const char *type=nullptr;gboolean powered=false;
        if(g_variant_lookup(properties,"Type","&s",&type)&&!strcmp(type,"wifi")){
            count++;
            if(g_variant_lookup(properties,"Powered","b",&powered))state=powered?3:1;
        }
        g_variant_unref(properties);
    }
    g_variant_unref(technologies);g_variant_unref(reply);
    if(count!=1||state==4){
        env->ThrowNew(env->FindClass("java/lang/IllegalStateException"),"Host Wi-Fi technology state is missing or ambiguous");
        return 4;
    }
    return state;
}
