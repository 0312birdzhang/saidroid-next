#include "../app-identity.hpp"
#include <fstream>
#include <iostream>
#include <grp.h>
#include <linux/capability.h>
#include <signal.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <sys/wait.h>
using namespace sd_identity;
static unsigned checks;
static void check(bool condition, const char* label) {
  if (!condition) throw std::runtime_error(label);
  ++checks;
}
template<class F> static void rejected(F&& function, const char* label) {
  bool threw = false; try { function(); } catch (const std::exception&) { threw = true; }
  check(threw, label);
}
static void write_text(const fs::path& path, const std::string& text) {
  std::ofstream out(path); out << text; out.close(); check(out.good(), "Fixture write");
}
static std::string text(const fs::path& path) {
  std::ifstream input(path); return {std::istreambuf_iterator<char>(input), {}};
}
static void exited(pid_t pid, const char* label) {
  int status; check(waitpid(pid, &status, 0) == pid && WIFEXITED(status) &&
                    WEXITSTATUS(status) == 0, label);
}
static void become(unsigned id) {
  require(setgroups(0, nullptr) == 0 && setresgid(id, id, id) == 0 &&
              setresuid(id, id, id) == 0, "Real kernel UID transition failed");
  __user_cap_header_struct header{_LINUX_CAPABILITY_VERSION_3, 0};
  __user_cap_data_struct caps[2]{};
  require(syscall(SYS_capset, &header, caps) == 0 &&
              prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) == 0,
          "Cannot clear capabilities and prevent privilege elevation");
  require(getuid() == id && geteuid() == id && getgid() == id && getegid() == id,
          "Real process identity differs");
}
int main(int argc, char** argv) {
 try {
  require(argc == 3 && getuid() == 0, "Root VM state and data fixture paths required");
  const fs::path work = argv[1], data = argv[2];
  require(!fs::exists(work) && !fs::exists(data), "Test directories must be new");
  fs::create_directories(work); chmod(work.c_str(), 0700);
  fs::create_directories(data); chmod(data.c_str(), 0755);
  auto state = work / "state"; fs::create_directory(state); chmod(state.c_str(), 0700);
  const std::string signer_a(64, 'a'), signer_b(64, 'b');
  unsigned a, b;
  { Registry registry(state, true);
    a = registry.allocate_verified("org.example.identity.alpha", {signer_a});
    b = registry.allocate_verified("org.example.identity.beta", {signer_b});
    check(a != b && a >= FIRST_APP_ID && b <= LAST_APP_ID, "Distinct valid Android app identities");
    check(registry.allocate_verified("org.example.identity.alpha", {signer_a}) == a,
          "Idempotent same-signer update");
    const auto before = registry.snapshot();
    rejected([&] { registry.allocate_verified("org.example.identity.alpha", {signer_b}); },
             "Wrong-signer update must fail");
    check(registry.snapshot() == before, "Wrong-signer attempt does not mutate durable identity");
    for (const auto& name : {"android", "org.saildroid.manager", "../alpha", "a..b", "a/b.c"})
      rejected([&] { registry.allocate_verified(name, {signer_a}); }, "Unsafe/reserved package rejected");
    rejected([&] { registry.allocate_verified("org.example.bad", {}); }, "Missing verified signers rejected");
    rejected([&] { registry.allocate_verified("org.example.bad", {"bad"}); }, "Malformed digest rejected");
    rejected([&] { registry.allocate_verified("org.example.bad", {signer_a, signer_a}); }, "Duplicate digest rejected");
    registry.retire("org.example.identity.alpha");
    const auto c = registry.allocate_verified("org.example.identity.gamma", {signer_a});
    check(c != a && c != b, "Retired identity never assigned to a different app");
    check(registry.allocate_verified("org.example.identity.alpha", {signer_a}) == a,
          "Same-signer reinstall preserves reserved identity");
  }
  { Registry reopened(state);
    check(reopened.allocate_verified("org.example.identity.alpha", {signer_a}) == a,
          "Real registry reopen preserves app identity"); }
  rejected([&] { Registry initialized_again(state, true); }, "Existing identity domain cannot reinitialize");
  const auto real_state = text(state / "identities.json");
  write_text(state / "identities.json", "invalid JSON\n");
  rejected([&] { Registry corrupt(state); }, "Corrupt state does not reset allocator");
  check(text(state / "identities.json") == "invalid JSON\n", "Corrupt original state preserved");
  write_text(state / "identities.json", real_state);
  auto value = Json::parse(real_state); value["packages"]["org.example.identity.beta"]["app_id"] = a;
  write_text(state / "identities.json", value.dump());
  rejected([&] { Registry duplicate(state); }, "Duplicate UID state rejected");
  write_text(state / "identities.json", real_state);
  fs::rename(state / "identities.json", state / "retained.json");
  rejected([&] { Registry missing(state); }, "Missing existing state does not reuse identities");
  rejected([&] { Registry reset_missing(state, true); }, "Missing state cannot initialize over existing domain");
  fs::rename(state / "retained.json", state / "identities.json");
  fs::create_hard_link(state / "identities.json", state / "extra-link");
  rejected([&] { Registry linked(state); }, "Hard-linked state rejected"); fs::remove(state / "extra-link");
  fs::rename(state / "identities.json", state / "retained.json");
  fs::create_symlink("retained.json", state / "identities.json");
  rejected([&] { Registry linked(state); }, "Symlinked state rejected");
  fs::remove(state / "identities.json");fs::rename(state / "retained.json", state / "identities.json");
  chmod((state / "identities.json").c_str(), 0666);
  rejected([&] { Registry writable(state); }, "Writable state rejected");
  chmod((state / "identities.json").c_str(), 0600);
  rejected([&] { Registry writable_ancestor(data); }, "Writable /var/tmp ancestor rejected for authoritative state");
  // Actual concurrent processes allocate under one durable lock, not mocked calls.
  std::vector<pid_t> workers;
  for (unsigned i=0; i<8; ++i) {
    const pid_t pid=fork();require(pid>=0,"Fork allocation worker");
    if (!pid) { try { Registry registry(state); registry.allocate_verified("org.example.concurrent.p"+std::to_string(i),{signer_a}); _exit(0); } catch (...) { _exit(1); } }
    workers.push_back(pid);
  }
  for (auto pid:workers) exited(pid,"Concurrent real allocation process");
  { Registry registry(state); const auto after=registry.snapshot();
    check(after["packages"].size()==11,"Concurrent updates retained exactly once");
    std::set<unsigned> ids;for(const auto& entry:after["packages"])ids.insert(entry["app_id"].get<unsigned>());
    check(ids.size()==11,"Concurrent allocations never duplicate app IDs"); }
  // Real Linux DAC and signal-permission boundaries; no Java UID substitution.
  auto alpha=data/"alpha", beta=data/"beta";fs::create_directory(alpha);fs::create_directory(beta);
  write_text(alpha/"private.txt","private-alpha");write_text(beta/"private.txt","private-beta");
  for(auto path:{alpha,alpha/"private.txt"})require(chown(path.c_str(),a,a)==0,"Own alpha data");
  for(auto path:{beta,beta/"private.txt"})require(chown(path.c_str(),b,b)==0,"Own beta data");
  chmod(alpha.c_str(),0700);chmod(beta.c_str(),0700);chmod((alpha/"private.txt").c_str(),0600);chmod((beta/"private.txt").c_str(),0600);
  int ready[2], finish[2];require(pipe(ready)==0&&pipe(finish)==0,"Kernel synchronization pipes");
  pid_t beta_pid=fork();require(beta_pid>=0,"Fork beta identity");
  if(!beta_pid){try{close(ready[0]);close(finish[1]);become(b);require(write(ready[1],"B",1)==1,"Publish beta UID ready");char c;require(read(finish[0],&c,1)==1,"Wait owned beta shutdown");_exit(0);}catch(...){_exit(1);}}
  close(ready[1]);close(finish[0]);char marker;require(read(ready[0],&marker,1)==1&&marker=='B',"Actual beta identity ready");close(ready[0]);
  pid_t alpha_pid=fork();require(alpha_pid>=0,"Fork alpha identity");
  if(!alpha_pid){try{become(a);require(chdir("/")==0,"Ordinary process readable cwd");
    require(text(alpha/"private.txt")=="private-alpha","Own UID can read own private data");
    errno=0;Fd other(open((beta/"private.txt").c_str(),O_RDONLY|O_NOFOLLOW));require(other.value<0&&errno==EACCES,"Other UID private data inaccessible");
    errno=0;require(kill(beta_pid,0)==-1&&errno==EPERM,"Other UID process cannot be signaled");
    bool denied=false;try{Registry unprivileged(state);}catch(...){denied=true;}require(denied,"Ordinary UID cannot acquire allocator authority");
    _exit(0);
   }catch(const std::exception&e){dprintf(2,"KERNEL_IDENTITY_FAILURE=%s\n",e.what());_exit(1);}}
  int alpha_status;require(waitpid(alpha_pid,&alpha_status,0)==alpha_pid,"Wait alpha identity");
  require(write(finish[1],"Q",1)==1,"Stop only owned beta identity");close(finish[1]);exited(beta_pid,"Owned beta identity stopped");
  check(WIFEXITED(alpha_status)&&WEXITSTATUS(alpha_status)==0,"Real UID/private data/signal/root-authority checks");
  std::cout<<"APP_IDENTITIES=ready|checks="<<checks<<"|real_uid_alpha="<<a<<"|real_uid_beta="<<b<<"|concurrent_workers=8|cross_uid_data=denied|cross_uid_signal=denied|ordinary_allocator=denied|phone_changed=false\n";
  fs::remove_all(data);fs::remove_all(work);return 0;
 }catch(const std::exception&e){std::cerr<<"APP_IDENTITIES=failed|reason="<<e.what()<<'\n';return 1;}
}
