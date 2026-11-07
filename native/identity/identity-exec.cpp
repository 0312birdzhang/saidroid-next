// Root-only process-launch primitive for previously verified app identities.
// No setuid installation or network/socket API. A future authenticated installer
// supervisor must select the fixed executable, data directory and arguments.
#include "app-identity.hpp"
#include "private-userdb.hpp"
#include <grp.h>
#include <iostream>
#include <linux/capability.h>
#include <sys/prctl.h>
#include <sys/resource.h>
#include <sys/syscall.h>
#include <sys/xattr.h>
using namespace sd_identity;
extern char** environ;
static int executable(const fs::path& path) {
  require(path.is_absolute(), "Absolute application executable required");
  Fd parent(open_state_directory(path.parent_path()));
  const auto name=path.filename().string();
  require(name!="."&&name!=".."&&!name.empty(),"Invalid executable name");
  Fd file(openat(parent.value,name.c_str(),O_RDONLY|O_CLOEXEC|O_NOFOLLOW));
  struct stat st{};unsigned char elf[4]{};
  require(file.value>=0&&fstat(file.value,&st)==0&&S_ISREG(st.st_mode)&&st.st_uid==0&&
              st.st_nlink==1&&!(st.st_mode&0022)&&!(st.st_mode&06000)&&(st.st_mode&0111),
          "Untrusted application executable");
  require(pread(file.value,elf,sizeof(elf),0)==sizeof(elf)&&
              !memcmp(elf,"\177ELF",sizeof(elf)),"Only native ELF entrypoints supported");
  errno=0;const auto cap=fgetxattr(file.value,"security.capability",nullptr,0);
  require(cap<0&&(errno==ENODATA||errno==EOPNOTSUPP),"File-capability entrypoints are forbidden");
  int result=file.value;file.value=-1;return result;
}
static void private_directory(const fs::path& path,unsigned uid,bool create) {
  require(path.is_absolute(),"Absolute private application directory required");
  Fd parent(open_state_directory(path.parent_path()));
  const auto name=path.filename().string();require(!name.empty()&&name!="."&&name!="..","Invalid private application directory");
  if(create) {
    if(mkdirat(parent.value,name.c_str(),0700)==0) {
      require(fchownat(parent.value,name.c_str(),uid,uid,AT_SYMLINK_NOFOLLOW)==0,
              "Cannot assign application runtime ownership");
    } else require(errno==EEXIST,"Cannot create application runtime directory");
  }
  Fd child(openat(parent.value,name.c_str(),O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC));
  struct stat info{};
  require(child.value>=0&&fstat(child.value,&info)==0&&S_ISDIR(info.st_mode)&&
              info.st_uid==uid&&info.st_gid==uid&&(info.st_mode&0777)==0700,
          "Application private directory identity or mode differs");
}
static void close_other_fds(int keep) {
  DIR* files=opendir("/proc/self/fd");require(files!=nullptr,"Cannot enumerate inherited descriptors");
  const int enumeration=dirfd(files);
  while(auto* file=readdir(files)) {
    char* end=nullptr;long fd=strtol(file->d_name,&end,10);
    if(!end||*end||fd<=2||fd==keep||fd==enumeration)continue;
    close(static_cast<int>(fd));
  }
  closedir(files);
}
int main(int argc,char**argv) {
 try {
  root_caller();require(argc>=5,"usage: identity-exec STATE PACKAGE DATA EXECUTABLE [ARG...]");
  const std::string package=argv[2];require(valid_package(package),"Invalid application package");
  unsigned uid;
  { Registry registry(argv[1]);const auto state=registry.snapshot();
    require(state["packages"].contains(package),"Application identity is not allocated");
    const auto entry=state["packages"][package];require(!entry["retired"].get<bool>(),"Application identity is retired");
    uid=entry["app_id"].get<unsigned>(); }
  const fs::path data=argv[3],program=argv[4];
  private_directory(data,uid,false);
  const auto runtime=fs::path("/run/user")/std::to_string(uid);
  private_directory(runtime,uid,true);
  Fd binary(executable(program));
  enter_private_userdb(uid,data);
  // Establish the actual scheduler limit while privileged; apps inherit no caps.
  const rlimit nice{40,40};require(setrlimit(RLIMIT_NICE,&nice)==0,"Cannot establish application scheduling limit");
  require(setsid()>=0||getpgrp()==getpid(),"Cannot create application-owned process session");
  require(chdir("/")==0,"Cannot set application working directory");
  Fd null(open("/dev/null",O_RDONLY|O_CLOEXEC));require(null.value>=0&&dup2(null.value,0)==0,"Cannot detach application stdin");
  require(clearenv()==0,"Cannot clear inherited privileged environment");
  const std::string name="u0_a"+std::to_string(uid-FIRST_APP_ID);
  const std::string address="unix:path="+runtime.string()+"/saildroid-bus";
  require(setenv("PATH","/usr/bin:/bin",1)==0&&setenv("USER",name.c_str(),1)==0&&
              setenv("LOGNAME",name.c_str(),1)==0&&setenv("HOME",data.c_str(),1)==0&&
              setenv("XDG_RUNTIME_DIR",runtime.c_str(),1)==0&&
              setenv("DBUS_SESSION_BUS_ADDRESS",address.c_str(),1)==0,
          "Cannot create application-scoped environment");
  close_other_fds(binary.value);
  require(prctl(PR_SET_NO_NEW_PRIVS,1,0,0,0)==0,"Cannot prevent privilege elevation");
  for(int cap=0;cap<64;++cap) {
    errno=0;int present=prctl(PR_CAPBSET_READ,cap,0,0,0);
    if(present<0) {require(errno==EINVAL,"Cannot inspect capability bounding set");break;}
    if(present)require(prctl(PR_CAPBSET_DROP,cap,0,0,0)==0,"Cannot drop capability bounding set");
  }
  require(setgroups(0,nullptr)==0&&setresgid(uid,uid,uid)==0&&setresuid(uid,uid,uid)==0,
          "Cannot enter the actual allocated Linux identity");
  __user_cap_header_struct header{_LINUX_CAPABILITY_VERSION_3,0};__user_cap_data_struct caps[2]{};
  require(syscall(SYS_capset,&header,caps)==0&&getuid()==uid&&geteuid()==uid&&
              getgid()==uid&&getegid()==uid,"Application privilege drop failed");
  umask(0077);
  // Execute the pinned ELF descriptor; reopening a caller-selected path cannot
  // race an executable replacement after validation.
  fexecve(binary.value,&argv[4],environ);
  throw std::runtime_error(std::string("Application exec failed: ")+strerror(errno));
 }catch(const std::exception&e){std::cerr<<"APP_IDENTITY_EXEC_ERROR="<<e.what()<<'\n';return 125;}
}
