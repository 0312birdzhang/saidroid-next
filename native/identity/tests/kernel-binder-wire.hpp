#pragma once
// Actual kernel Binder sender credentials across two real Linux app UIDs.
#include <linux/android/binder.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <sys/prctl.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <fcntl.h>
#include <unistd.h>
#include <grp.h>
#include <cerrno>
#include <cstring>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <stdexcept>
#include <vector>

namespace sd_identity_wire {
static void require(bool value,const char* message){if(!value)throw std::runtime_error(std::string(message)+": "+strerror(errno));}
static void ordinary(unsigned uid){require(setgroups(0,nullptr)==0&&setresgid(uid,uid,uid)==0&&setresuid(uid,uid,uid)==0,"Enter real UID");require(prctl(PR_SET_NO_NEW_PRIVS,1,0,0,0)==0,"Prevent privilege elevation");}
template<class T> static void append(std::vector<uint8_t>&bytes,const T&value){const auto*p=reinterpret_cast<const uint8_t*>(&value);bytes.insert(bytes.end(),p,p+sizeof(value));}
struct Binder {
 int fd=-1;void* mapping=MAP_FAILED;
 explicit Binder(const char* path){fd=open(path,O_RDWR|O_CLOEXEC);require(fd>=0,"Open actual private Binder");binder_version v{};require(ioctl(fd,BINDER_VERSION,&v)==0&&v.protocol_version==8,"Actual64-bit Binder protocol");mapping=mmap(nullptr,1024*1024,PROT_READ,MAP_PRIVATE,fd,0);require(mapping!=MAP_FAILED,"Map real Binder transaction area");}
 ~Binder(){if(mapping!=MAP_FAILED)munmap(mapping,1024*1024);if(fd>=0)close(fd);}
 std::vector<uint8_t> exchange(const std::vector<uint8_t>&write,bool read){
  std::vector<uint8_t> result(read?4096:0);binder_write_read io{};io.write_size=write.size();io.write_buffer=reinterpret_cast<binder_uintptr_t>(write.data());io.read_size=result.size();io.read_buffer=reinterpret_cast<binder_uintptr_t>(result.data());
  int status;do{status=ioctl(fd,BINDER_WRITE_READ,&io);}while(status<0&&errno==EINTR);require(status==0&&io.write_consumed==write.size(),"Real Binder write/read");result.resize(io.read_consumed);return result;
 }
 binder_transaction_data transaction(bool reply){
  for(unsigned round=0;round<30;++round){auto bytes=exchange({},true);size_t offset=0;
   while(offset+sizeof(uint32_t)<=bytes.size()){
    uint32_t command;memcpy(&command,bytes.data()+offset,sizeof(command));offset+=sizeof(command);const size_t size=_IOC_SIZE(command);require(offset+size<=bytes.size(),"Complete Binder command");
    if(command==BR_ERROR||command==BR_DEAD_REPLY||command==BR_FAILED_REPLY)throw std::runtime_error("Kernel Binder transaction rejected");
    if(command==BR_TRANSACTION||command==BR_REPLY){binder_transaction_data data{};require(size==sizeof(data),"Actual transaction shape");memcpy(&data,bytes.data()+offset,sizeof(data));require((command==BR_REPLY)==reply,"Expected real transaction/reply role");return data;}
    offset+=size;
   }
  }throw std::runtime_error("Missing actual Binder transaction");
 }
};

} // namespace sd_identity_wire
