#pragma once
// Private software-key blob storage primitive. Caller identity must come from
// authenticated IPC credentials; alias/request contents never supply it.
// This is not an Android KeyStore service, an APK verifier, or encrypted storage.
#include <sys/stat.h>
#include <dirent.h>
#include <sys/file.h>
#include <sys/random.h>
#include <sys/syscall.h>
#include <linux/fs.h>
#include <fcntl.h>
#include <unistd.h>
#include <cerrno>
#include <cstdint>
#include <cstring>
#include <string>
#include <vector>
#include <set>
#include <stdexcept>
#include <utility>
#include <mutex>
#include <algorithm>
#include <memory>

namespace sd_keyblob {
inline void check(bool ok,const char* message) { if(!ok)throw std::runtime_error(message); }
struct Fd {
 int value=-1;explicit Fd(int fd=-1):value(fd){}~Fd(){if(value>=0)close(value);}Fd(const Fd&)=delete;Fd&operator=(const Fd&)=delete;
 Fd(Fd&&other)noexcept:value(std::exchange(other.value,-1)){};
};
struct Missing:std::runtime_error { Missing():std::runtime_error("Private key alias absent"){} };
struct Exists:std::runtime_error { Exists():std::runtime_error("Private key alias already exists"){} };
struct Denied:std::runtime_error { Denied():std::runtime_error("Caller UID not assigned by trusted app registry"){} };
inline void wipe_bytes(void* bytes,size_t length) noexcept {
 auto* p=static_cast<volatile uint8_t*>(bytes);while(length--)*p++=0;
}
struct Blob {
 uint32_t algorithm;std::vector<uint8_t> data;
 Blob(uint32_t a,std::vector<uint8_t> bytes):algorithm(a),data(std::move(bytes)){}
 Blob(const Blob&)=delete;Blob&operator=(const Blob&)=delete;Blob(Blob&&)=default;
 ~Blob(){wipe_bytes(data.data(),data.size());}
};
class Store {
 Fd root;uid_t owner;std::set<uid_t> allowed;std::set<uint32_t> kinds;mutable std::mutex local;
 static constexpr size_t limit=1024*1024;
 static void directory(int fd,uid_t owner) {
  struct stat s{};check(fd>=0&&fstat(fd,&s)==0&&S_ISDIR(s.st_mode)&&s.st_uid==owner&&(s.st_mode&07777)==0700,"Untrusted private key directory");
 }
 static void file(int fd,uid_t owner) {
  struct stat s{};check(fd>=0&&fstat(fd,&s)==0&&S_ISREG(s.st_mode)&&s.st_uid==owner&&s.st_nlink==1&&(s.st_mode&07777)==0600&&s.st_size>=0&&s.st_size<=static_cast<off_t>(limit+16),"Untrusted private key blob file");
 }
 static std::string name(const std::string&alias) {
  check(!alias.empty()&&alias.size()<=120,"Key alias must contain 1..120 bytes");
  static const char hex[]="0123456789abcdef";std::string s="key-";
  for(unsigned char c:alias){s+=hex[c>>4];s+=hex[c&15];}return s+".blob";
 }
 Fd space(uid_t caller,bool create)const {
  if(!allowed.count(caller))throw Denied();
  const auto label="uid-"+std::to_string(caller);
  if(create) {
   if(mkdirat(root.value,label.c_str(),0700)<0)check(errno==EEXIST,"Cannot create private UID namespace");
   else check(fsync(root.value)==0,"Cannot synchronize new UID namespace");
  }
  Fd d(openat(root.value,label.c_str(),O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC));
  if(d.value<0&&errno==ENOENT)throw Missing();
  directory(d.value,owner);return d;
 }
 struct Lock { int fd;explicit Lock(int v):fd(v){check(flock(fd,LOCK_EX)==0,"Cannot lock private key state");}~Lock(){flock(fd,LOCK_UN);} };
 static void write_bytes(int fd,const void* bytes,size_t size) {
  auto*p=static_cast<const uint8_t*>(bytes);while(size){ssize_t n=write(fd,p,size);if(n<0&&errno==EINTR)continue;check(n>0,"Cannot write complete private key blob");p+=n;size-=static_cast<size_t>(n);}
 }
 public:
 // Root installer passes an already-open, pinned directory descriptor. The
 // service may access only this inode; a request can never choose a state path.
 Store(int inherited_root,uid_t service_owner,std::set<uid_t> registry_uids,std::set<uint32_t> record_kinds={1,3}):root(openat(inherited_root,".",O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC)),owner(service_owner),allowed(std::move(registry_uids)),kinds(std::move(record_kinds)) {
  check(getuid()==owner&&geteuid()==owner,"Key service must use its real configured UID");directory(root.value,owner);check(!allowed.empty(),"Trusted application UID registry required");check(!kinds.empty()&&std::all_of(kinds.begin(),kinds.end(),[](uint32_t k){return k==1||k==3||k==4||k==32||k==128;}),"Unsupported private record kind");
  check(fcntl(root.value,F_SETFD,FD_CLOEXEC)==0,"Cannot pin private key directory");
 }
 void create(uid_t caller,const std::string&alias,uint32_t algorithm,const std::vector<uint8_t>&data,bool replace_value=false) {
  const auto target=name(alias);check(kinds.count(algorithm)&&(!data.empty()||algorithm==4)&&data.size()<=limit,"Invalid private typed blob");check(!replace_value||algorithm==4,"Only value records may be atomically replaced");std::lock_guard<std::mutex> thread_guard(local);Lock guard(root.value);auto d=space(caller,true);uint64_t nonce=0;
  // Replacement is a separate trusted value-store operation, never key creation.
  // The common lock covers inspection and rename. Refuse an existing native key
  // record or a non-canonical file; app-controlled aliases cannot change kind.
  Fd existing;
  struct stat pinned{};
  if(replace_value){
   existing.value=openat(d.value,target.c_str(),O_RDONLY|O_NONBLOCK|O_NOFOLLOW|O_CLOEXEC);
   if(existing.value>=0){
    file(existing.value,owner);uint32_t h[4]{};check(pread(existing.value,h,sizeof(h),0)==sizeof(h)&&fstat(existing.value,&pinned)==0,"Cannot inspect existing typed value");
    if(h[0]!=0x53444b31||h[1]!=1||h[2]!=4||h[3]!=pinned.st_size-16)throw Denied();
   }else check(errno==ENOENT,"Cannot inspect value replacement target");
  }
  check(getrandom(&nonce,sizeof(nonce),0)==sizeof(nonce),"Cannot obtain secure private filename randomness");const auto temporary=".pending-"+std::to_string(getpid())+"-"+std::to_string(nonce);
  Fd f(openat(d.value,temporary.c_str(),O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC,0600));check(f.value>=0,"Cannot create private key transaction");
  bool pending=true;
  try {
   file(f.value,owner);const uint32_t header[]={0x53444b31,1,algorithm,static_cast<uint32_t>(data.size())};write_bytes(f.value,header,sizeof(header));write_bytes(f.value,data.data(),data.size());check(fsync(f.value)==0,"Cannot synchronize private key blob");
   if(existing.value>=0){struct stat current{};check(fstatat(d.value,target.c_str(),&current,AT_SYMLINK_NOFOLLOW)==0&&current.st_dev==pinned.st_dev&&current.st_ino==pinned.st_ino,"Existing value changed before replacement");}
   int status=syscall(SYS_renameat2,d.value,temporary.c_str(),d.value,target.c_str(),replace_value&&existing.value>=0?0:RENAME_NOREPLACE);
   if(status<0&&errno==EEXIST)throw Exists();
   check(status==0,"Cannot commit private key blob without replacement");pending=false;check(fsync(d.value)==0,"Cannot synchronize committed private key alias");
  }catch(...){if(pending)unlinkat(d.value,temporary.c_str(),0);throw;}
 }
 Blob read(uid_t caller,const std::string&alias)const {
  const auto target=name(alias);std::lock_guard<std::mutex> thread_guard(local);Lock guard(root.value);auto d=space(caller,false);Fd f(openat(d.value,target.c_str(),O_RDONLY|O_NONBLOCK|O_NOFOLLOW|O_CLOEXEC));if(f.value<0&&errno==ENOENT)throw Missing();file(f.value,owner);
  struct stat metadata{};check(fstat(f.value,&metadata)==0,"Cannot inspect pinned private key blob");
  std::vector<uint8_t> bytes(static_cast<size_t>(metadata.st_size));struct WipeOnExit {std::vector<uint8_t>&value;~WipeOnExit(){wipe_bytes(value.data(),value.size());}}wipe{bytes};
  size_t offset=0;
  while(offset<bytes.size()){ssize_t n=::read(f.value,bytes.data()+offset,bytes.size()-offset);if(n<0&&errno==EINTR)continue;check(n>0,"Private key blob shortened during read");offset+=static_cast<size_t>(n);}
  uint8_t extra=0;ssize_t more;do{more=::read(f.value,&extra,1);}while(more<0&&errno==EINTR);wipe_bytes(&extra,1);check(more==0,"Private key blob grew during read");
  check(bytes.size()>=16,"Incomplete private key blob");uint32_t header[4];memcpy(header,bytes.data(),sizeof(header));check(header[0]==0x53444b31&&header[1]==1&&kinds.count(header[2])&&(header[3]>0||header[2]==4)&&header[3]==bytes.size()-16,"Invalid private key blob format");return {header[2],std::vector<uint8_t>(bytes.begin()+16,bytes.end())};
 }
 // API29 getmtime uses actual pinned file st_mtime in whole Unix seconds.
 // Validate the same UID namespace/file/header as other record access, without
 // returning or allocating the private payload.
 int64_t modification_time(uid_t caller,const std::string&alias)const {
  const auto target=name(alias);std::lock_guard<std::mutex> thread_guard(local);Lock guard(root.value);auto d=space(caller,false);
  Fd f(openat(d.value,target.c_str(),O_RDONLY|O_NONBLOCK|O_NOFOLLOW|O_CLOEXEC));if(f.value<0&&errno==ENOENT)throw Missing();file(f.value,owner);
  struct stat metadata{};uint32_t h[4]{};
  check(fstat(f.value,&metadata)==0&&pread(f.value,h,sizeof(h),0)==sizeof(h)&&h[0]==0x53444b31&&h[1]==1&&kinds.count(h[2])&&(h[3]>0||h[2]==4)&&h[3]==metadata.st_size-16&&metadata.st_mtime>=0,"Invalid private record metadata");
  return static_cast<int64_t>(metadata.st_mtime);
 }
 // Return full literal aliases; the standard frontend applies prefix stripping.
 // Enumeration stays under the same UID/pinned-directory/file validation rules.
 std::vector<std::string> list(uid_t caller,const std::string&prefix)const {
  check(prefix.size()<=120,"Value prefix exceeds alias bound");std::lock_guard<std::mutex> thread_guard(local);Lock guard(root.value);Fd d;
  try{auto opened=space(caller,false);d.value=std::exchange(opened.value,-1);}catch(const Missing&){return {};}
  DIR* raw=fdopendir(openat(d.value,".",O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC));check(raw,"Cannot enumerate private alias directory");
  struct CloseDirectory{void operator()(DIR*d)const noexcept{closedir(d);}};
  std::unique_ptr<DIR,CloseDirectory> directory_guard(raw);std::vector<std::string> aliases;
  errno=0;
  while(auto*entry=readdir(raw)){
   std::string filename(entry->d_name);if(filename=="."||filename=="..")continue;
   // A process crash may leave a private pending file; it is not a committed alias.
   if(filename.rfind(".pending-",0)==0)continue;
   check(filename.size()>9&&filename.rfind("key-",0)==0&&filename.compare(filename.size()-5,5,".blob")==0,"Unknown private alias record");
   auto hex=filename.substr(4,filename.size()-9);check(hex.size()%2==0&&hex.size()<=240,"Malformed private alias filename");std::string alias;
   auto nibble=[](char c)->int{return c>='0'&&c<='9'?c-'0':c>='a'&&c<='f'?c-'a'+10:-1;};
   for(size_t i=0;i<hex.size();i+=2){int hi=nibble(hex[i]),lo=nibble(hex[i+1]);check(hi>=0&&lo>=0,"Noncanonical private alias encoding");alias+=static_cast<char>((hi<<4)|lo);}
   Fd f(openat(d.value,filename.c_str(),O_RDONLY|O_NONBLOCK|O_NOFOLLOW|O_CLOEXEC));file(f.value,owner);struct stat metadata{};uint32_t h[4]{};
   check(fstat(f.value,&metadata)==0&&pread(f.value,h,sizeof(h),0)==sizeof(h)&&h[0]==0x53444b31&&h[1]==1&&kinds.count(h[2])&&(h[3]>0||h[2]==4)&&h[3]==metadata.st_size-16,"Invalid enumerated private record");
   if(alias.rfind(prefix,0)==0){aliases.push_back(std::move(alias));}
   check(aliases.size()<=10000,"Private alias list exceeds bound");errno=0;
  }
  check(errno==0,"Private alias enumeration failed");std::sort(aliases.begin(),aliases.end());return aliases;
 }
 void erase(uid_t caller,const std::string&alias) {
  const auto target=name(alias);std::lock_guard<std::mutex> thread_guard(local);Lock guard(root.value);auto d=space(caller,false);Fd f(openat(d.value,target.c_str(),O_RDONLY|O_NONBLOCK|O_NOFOLLOW|O_CLOEXEC));if(f.value<0&&errno==ENOENT)throw Missing();file(f.value,owner);struct stat before{},now{};check(fstat(f.value,&before)==0&&fstatat(d.value,target.c_str(),&now,AT_SYMLINK_NOFOLLOW)==0&&before.st_dev==now.st_dev&&before.st_ino==now.st_ino,"Key alias changed during deletion");check(unlinkat(d.value,target.c_str(),0)==0&&fsync(d.value)==0,"Cannot durably remove own key alias");
 }
};
} // namespace sd_keyblob
