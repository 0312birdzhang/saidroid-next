#pragma once
// Read-only Sailfish lock-state backend. Endpoint selection belongs to the
// trusted service launcher; no Binder/app argument or environment supplies it.
// This backend is separate from authentication, keystore encryption and Android
// user/profile state. Only Sailfish user0 is supported here.
#include <gio/gio.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <poll.h>
#include <condition_variable>
#include <thread>
#include <mutex>
#include <chrono>
#include <string>
#include <stdexcept>
#include <cstring>
#include <cerrno>

namespace sd_keylock {
class MceState {
    GDBusConnection* bus=nullptr;
    struct Fd {int n=-1;explicit Fd(int v=-1):n(v){}~Fd(){if(n>=0)close(n);}};
    static void require(bool value,const char*message){if(!value)throw std::runtime_error(message);}
    struct Deadline {
        GCancellable* cancel=g_cancellable_new();std::mutex mutex;std::condition_variable changed;bool done=false;std::thread timer;
        Deadline():timer([this]{std::unique_lock<std::mutex> guard(mutex);if(!changed.wait_for(guard,std::chrono::seconds(2),[this]{return done;}))g_cancellable_cancel(cancel);}){}
        ~Deadline(){{std::lock_guard<std::mutex> guard(mutex);done=true;}changed.notify_one();timer.join();g_object_unref(cancel);}
    };
    static void check_path(const std::string&path){
        require(!path.empty()&&path[0]=='/'&&path.size()<sizeof(sockaddr_un::sun_path),"Lock-state bus requires a bounded absolute pathname");
        Fd directory(open("/",O_RDONLY|O_DIRECTORY|O_CLOEXEC));require(directory.n>=0,"Cannot inspect bus root");
        size_t offset=1;
        while(true){
            size_t slash=path.find('/',offset);std::string part=path.substr(offset,slash==std::string::npos?std::string::npos:slash-offset);
            require(!part.empty()&&part!="."&&part!="..","Noncanonical lock-state bus path");
            struct stat parent{};require(fstat(directory.n,&parent)==0&&S_ISDIR(parent.st_mode)&&parent.st_uid==0&&!(parent.st_mode&0022),"Untrusted bus directory");
            if(slash==std::string::npos){struct stat socket{};require(fstatat(directory.n,part.c_str(),&socket,AT_SYMLINK_NOFOLLOW)==0&&S_ISSOCK(socket.st_mode)&&socket.st_uid==0&&socket.st_nlink==1,"Untrusted system bus socket");break;}
            int next=openat(directory.n,part.c_str(),O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);require(next>=0,"Cannot pin bus directory");close(directory.n);directory.n=next;offset=slash+1;
        }
    }
    GVariant* call(const char*destination,const char*path,const char*interface,const char*method,GVariant*parameters,const GVariantType*expected){
        GError*error=nullptr;GVariant*reply=g_dbus_connection_call_sync(bus,destination,path,interface,method,parameters,expected,G_DBUS_CALL_FLAGS_NO_AUTO_START,1000,nullptr,&error);
        if(!reply){g_clear_error(&error);throw std::runtime_error("Trusted lock-state query failed");}return reply;
    }
public:
    // The production endpoint is /run/dbus/system_bus_socket (canonical path,
    // not /var/run). Tests may select a private root-owned bus explicitly.
    explicit MceState(const std::string&trusted_endpoint){
        check_path(trusted_endpoint);Fd fd(socket(AF_UNIX,SOCK_STREAM|SOCK_CLOEXEC|SOCK_NONBLOCK,0));require(fd.n>=0,"Cannot open lock-state bus socket");
        sockaddr_un address{};address.sun_family=AF_UNIX;memcpy(address.sun_path,trusted_endpoint.c_str(),trusted_endpoint.size()+1);
        int connected=connect(fd.n,reinterpret_cast<sockaddr*>(&address),sizeof(address));
        if(connected<0){require(errno==EINPROGRESS,"Cannot connect lock-state bus");pollfd ready{fd.n,POLLOUT,0};int result;do{result=poll(&ready,1,1000);}while(result<0&&errno==EINTR);require(result==1,"Lock-state bus connection timed out");int error=0;socklen_t length=sizeof(error);require(getsockopt(fd.n,SOL_SOCKET,SO_ERROR,&error,&length)==0&&error==0,"Lock-state bus connection failed");}
        ucred peer{};socklen_t length=sizeof(peer);require(getsockopt(fd.n,SOL_SOCKET,SO_PEERCRED,&peer,&length)==0&&length==sizeof(peer)&&peer.uid==0,"System bus peer must be root");
        int flags=fcntl(fd.n,F_GETFL);require(flags>=0&&fcntl(fd.n,F_SETFL,flags&~O_NONBLOCK)==0,"Cannot configure system bus transport");
        GError*error=nullptr;GSocket*socket=g_socket_new_from_fd(fd.n,&error);if(!socket){g_clear_error(&error);throw std::runtime_error("Cannot wrap trusted bus transport");}fd.n=-1;
        GSocketConnection*stream=g_socket_connection_factory_create_connection(socket);g_object_unref(socket);Deadline deadline;
        bus=g_dbus_connection_new_sync(G_IO_STREAM(stream),nullptr,static_cast<GDBusConnectionFlags>(G_DBUS_CONNECTION_FLAGS_AUTHENTICATION_CLIENT|G_DBUS_CONNECTION_FLAGS_MESSAGE_BUS_CONNECTION),nullptr,deadline.cancel,&error);g_object_unref(stream);
        if(!bus){g_clear_error(&error);throw std::runtime_error("System bus authentication failed or timed out");}g_dbus_connection_set_exit_on_close(bus,FALSE);
    }
    MceState(const MceState&)=delete;MceState&operator=(const MceState&)=delete;
    ~MceState(){if(bus){g_dbus_connection_close_sync(bus,nullptr,nullptr);g_object_unref(bus);}}
    bool unlocked(unsigned android_user,std::string*diagnostic=nullptr)noexcept {
        try {
            require(android_user==0,"Unsupported Sailfish Android user");
            GVariant*reply=call("org.freedesktop.DBus","/org/freedesktop/DBus","org.freedesktop.DBus","GetNameOwner",g_variant_new("(s)","com.nokia.mce"),G_VARIANT_TYPE("(s)"));
            const char*unique=nullptr;g_variant_get(reply,"(&s)",&unique);std::string owner(unique);g_variant_unref(reply);require(!owner.empty()&&owner[0]==':',"MCE must have a unique bus owner");
            reply=call("org.freedesktop.DBus","/org/freedesktop/DBus","org.freedesktop.DBus","GetConnectionUnixUser",g_variant_new("(s)",owner.c_str()),G_VARIANT_TYPE("(u)"));guint32 uid=~0u;g_variant_get(reply,"(u)",&uid);g_variant_unref(reply);require(uid==0,"MCE owner must be root");
            reply=call(owner.c_str(),"/com/nokia/mce/request","com.nokia.mce.request","get_tklock_mode",nullptr,G_VARIANT_TYPE("(s)"));const char*raw=nullptr;g_variant_get(reply,"(&s)",&raw);std::string state(raw);g_variant_unref(reply);
            // A retiring root MCE process must not supply an unlocked result
            // after it has already lost the well-known service name.
            reply=call("org.freedesktop.DBus","/org/freedesktop/DBus","org.freedesktop.DBus","GetNameOwner",g_variant_new("(s)","com.nokia.mce"),G_VARIANT_TYPE("(s)"));
            const char*current=nullptr;g_variant_get(reply,"(&s)",&current);bool same_owner=owner==current;g_variant_unref(reply);require(same_owner,"MCE owner changed during lock query");
            if(state=="unlocked"){if(diagnostic)*diagnostic="unlocked";return true;}
            require(state=="locked"||state=="locked-dim"||state=="locked-delay","Unknown MCE lock state");if(diagnostic)*diagnostic="locked";return false;
        }catch(const std::exception&error){if(diagnostic)*diagnostic=error.what();return false;}
    }
};
}
