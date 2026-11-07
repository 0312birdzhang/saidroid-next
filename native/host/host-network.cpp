#include "host-common.hpp"
#include <cctype>
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

extern "C" JNIEXPORT jstring JNICALL
Java_org_saildroid_host_HostApi_wifiConnectionInfo(JNIEnv *env,jclass,jboolean include_name) {
    GError *error=nullptr;
    auto bus=g_bus_get_sync(G_BUS_TYPE_SYSTEM,nullptr,&error);
    if(!bus){
        g_clear_error(&error);
        env->ThrowNew(env->FindClass("java/lang/IllegalStateException"),"Host network bus unavailable");
        return nullptr;
    }
    auto reply=g_dbus_connection_call_sync(bus,"net.connman","/","net.connman.Manager",
            "GetServices",nullptr,G_VARIANT_TYPE("(a(oa{sv}))"),
            G_DBUS_CALL_FLAGS_NONE,1500,nullptr,&error);
    g_object_unref(bus);
    if(!reply){
        g_clear_error(&error);
        env->ThrowNew(env->FindClass("java/lang/IllegalStateException"),"Host Wi-Fi connection query unavailable");
        return nullptr;
    }
    Json snapshot={{"connected",false}};
    auto services=g_variant_get_child_value(reply,0);
    GVariantIter iterator;g_variant_iter_init(&iterator,services);
    const char *path=nullptr;GVariant *properties=nullptr;
    int connected=0;
    while(g_variant_iter_next(&iterator,"(&o@a{sv})",&path,&properties)){
        const char *type=nullptr,*state=nullptr;
        bool wifi=g_variant_lookup(properties,"Type","&s",&type)&&!strcmp(type,"wifi");
        bool active=g_variant_lookup(properties,"State","&s",&state)&&
                (!strcmp(state,"ready")||!strcmp(state,"online"));
        if(wifi&&active){
            connected++;
            snapshot["connected"]=true;
            const char *value=nullptr;
            if(include_name&&g_variant_lookup(properties,"Name","&s",&value))snapshot["name"]=value;
            auto ipv4=g_variant_lookup_value(properties,"IPv4",G_VARIANT_TYPE("a{sv}"));
            if(ipv4){
                for(const char *key:{"Method","Address","Netmask","Gateway"}){
                    if(g_variant_lookup(ipv4,key,"&s",&value)){
                        std::string name=key;
                        name[0]=static_cast<char>(std::tolower(name[0]));
                        snapshot[name]=value;
                    }
                }
                g_variant_unref(ipv4);
            }
            auto dns=g_variant_lookup_value(properties,"Nameservers",G_VARIANT_TYPE("as"));
            if(dns){
                snapshot["dns"]=Json::array();
                GVariantIter names;g_variant_iter_init(&names,dns);
                while(g_variant_iter_next(&names,"&s",&value)){
                    auto address=g_inet_address_new_from_string(value);
                    if(address){
                        if(g_inet_address_get_family(address)==G_SOCKET_FAMILY_IPV4)snapshot["dns"].push_back(value);
                        g_object_unref(address);
                    }
                }
                g_variant_unref(dns);
            }
        }
        g_variant_unref(properties);
    }
    g_variant_unref(services);g_variant_unref(reply);
    if(connected>1){
        env->ThrowNew(env->FindClass("java/lang/IllegalStateException"),"Host Wi-Fi connection is ambiguous");
        return nullptr;
    }
    // Serialize only selected connection fields. ConnMan's other properties
    // can contain saved credentials and must never cross this boundary.
    auto text=snapshot.dump(-1,' ',true);
    return env->NewStringUTF(text.c_str());
}
