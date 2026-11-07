#pragma once
#include "app-identity.hpp"
#include <cstdlib>
#include <sched.h>
#include <sys/mount.h>
namespace sd_identity {
inline std::string public_userdb(const char* name) {
  Fd etc(open_state_directory("/etc"));
  Fd file(openat(etc.value,name,O_RDONLY|O_CLOEXEC|O_NOFOLLOW));
  trusted_file(file.value,false);return read_all(file.value);
}
inline void bind_readonly_file(const std::string& source,const char* target) {
  require(mount(source.c_str(),target,nullptr,MS_BIND,nullptr)==0,
          (std::string("Cannot mount private user database view: ")+strerror(errno)).c_str());
  require(mount(nullptr,target,nullptr,MS_BIND|MS_REMOUNT|MS_RDONLY|MS_NOSUID|MS_NODEV|MS_NOEXEC,nullptr)==0,
          "Cannot make private user database view read-only");
}
inline void write_userdb_file(const fs::path& root,const char* name,const std::string& content) {
  Fd directory(open_state_directory(root));
  Fd file(openat(directory.value,name,O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC,0444));
  require(file.value>=0,"Cannot create private user database file");
  size_t offset=0;
  while(offset<content.size()) {
    ssize_t n=write(file.value,content.data()+offset,content.size()-offset);
    if(n<0&&errno==EINTR)continue;
    require(n>0,"Cannot populate private user database file");offset+=static_cast<size_t>(n);
  }
}
inline void enter_private_userdb(unsigned uid,const fs::path& home) {
  root_caller();
  require(uid>=FIRST_APP_ID&&uid<=LAST_APP_ID&&home.is_absolute()&&
              home.string().find_first_of(":\r\n")==std::string::npos,
          "Invalid private application account");
  const std::string name="u0_a"+std::to_string(uid-FIRST_APP_ID);
  errno=0;auto* user=getpwuid(uid);require(!user&&errno==0,"Application UID conflicts with a host account");
  errno=0;auto* group=getgrgid(uid);require(!group&&errno==0,"Application GID conflicts with a host group");
  errno=0;user=getpwnam(name.c_str());require(!user&&errno==0,"Application account name conflicts");
  errno=0;group=getgrnam(name.c_str());require(!group&&errno==0,"Application group name conflicts");
  auto passwd=public_userdb("passwd"),groups=public_userdb("group"),nss=public_userdb("nsswitch.conf");
  if(passwd.back()!='\n')passwd+='\n';
  if(groups.back()!='\n')groups+='\n';
  passwd+=name+":*:"+std::to_string(uid)+":"+std::to_string(uid)+":SailDroid application:"+home.string()+":/bin/false\n";
  groups+=name+":*:"+std::to_string(uid)+":\n";
  std::string filtered;size_t start=0;
  while(start<nss.size()) {
    auto end=nss.find('\n',start);if(end==std::string::npos)end=nss.size();
    const auto line=nss.substr(start,end-start);
    if(!std::regex_match(line,std::regex("[ \\t]*(passwd|group)[ \\t]*:.*")))filtered+=line+'\n';
    start=end+1;
  }
  filtered+="passwd: files\ngroup: files\n";
  require(passwd.size()+groups.size()+filtered.size()<3*1024*1024,"Host user database exceeds private view bound");
  require(unshare(CLONE_NEWNS)==0&&mount(nullptr,"/",nullptr,MS_REC|MS_PRIVATE,nullptr)==0,
          "Cannot create private application mount namespace");
  Fd run(open_state_directory("/run"));
  char temporary[]="/run/.saildroid-userdb-XXXXXX";
  require(mkdtemp(temporary)!=nullptr,"Cannot reserve private user database mountpoint");
  bool mounted=false;
  try {
    require(mount("tmpfs",temporary,"tmpfs",MS_NOSUID|MS_NODEV|MS_NOEXEC,
                  "mode=0700,size=4m,nr_inodes=16")==0,"Cannot mount private account tmpfs");
    mounted=true;
    write_userdb_file(temporary,"passwd",passwd);write_userdb_file(temporary,"group",groups);
    write_userdb_file(temporary,"nsswitch.conf",filtered);write_userdb_file(temporary,"no-cache","");
    require(mount(nullptr,temporary,nullptr,MS_REMOUNT|MS_RDONLY|MS_NOSUID|MS_NODEV|MS_NOEXEC,nullptr)==0,
            "Cannot make private account tmpfs read-only");
    bind_readonly_file(std::string(temporary)+"/passwd","/etc/passwd");
    bind_readonly_file(std::string(temporary)+"/group","/etc/group");
    bind_readonly_file(std::string(temporary)+"/nsswitch.conf","/etc/nsswitch.conf");
    // A host cache must not replace the application's actual private NSS view.
    for(const auto* socket:{"/run/nscd/socket","/var/run/nscd/socket"}) {
      struct stat info{};
      if(lstat(socket,&info)==0&&S_ISSOCK(info.st_mode))
        bind_readonly_file(std::string(temporary)+"/no-cache",socket);
    }
    require(umount2(temporary,MNT_DETACH)==0,"Cannot retire private account source mount");
    mounted=false;
    require(rmdir(temporary)==0,"Cannot remove temporary account mountpoint");
  } catch(...) {
    if(mounted)umount2(temporary,MNT_DETACH);
    rmdir(temporary);throw;
  }
}
} // namespace sd_identity
