#pragma once
// Root-owned durable Android app-ID allocation. This is a privileged backend
// primitive, not an APK verifier, installer, permission service or setuid program.
#include "../host/third_party/json.hpp"
#include <algorithm>
#include <atomic>
#include <dirent.h>
#include <pwd.h>
#include <grp.h>
#include <cerrno>
#include <cstring>
#include <fcntl.h>
#include <filesystem>
#include <regex>
#include <set>
#include <stdexcept>
#include <string>
#include <sys/file.h>
#include <sys/stat.h>
#include <unistd.h>
#include <vector>

namespace sd_identity {
namespace fs = std::filesystem;
using Json = nlohmann::json;
constexpr unsigned FIRST_APP_ID = 10000;
constexpr unsigned LAST_APP_ID = 19999;
constexpr size_t MAX_STATE_BYTES = 32 * 1024 * 1024;
struct Fd {
  int value;
  explicit Fd(int v = -1) : value(v) {}
  ~Fd() { if (value >= 0) close(value); }
  Fd(const Fd&) = delete;
  Fd& operator=(const Fd&) = delete;
};
inline void require(bool condition, const char* message) {
  if (!condition) throw std::runtime_error(message);
}
inline void root_caller() {
  require(getuid() == 0 && geteuid() == 0, "Root install authority required");
}
inline void trusted_directory(int fd) {
  struct stat info{};
  require(fd >= 0 && fstat(fd, &info) == 0 && S_ISDIR(info.st_mode) &&
              info.st_uid == 0 && !(info.st_mode & 0022),
          "Identity state must have root-owned non-writable ancestors");
}
// Walk using pinned directory descriptors. Symlinks, dot components and writable
// ancestors are refused rather than normalized into a different state location.
inline int open_state_directory(const fs::path& path) {
  root_caller();
  require(path.is_absolute() && path != path.root_path(), "Absolute private state directory required");
  Fd current(open("/", O_RDONLY | O_DIRECTORY | O_CLOEXEC | O_NOFOLLOW));
  trusted_directory(current.value);
  for (const auto& component : path.relative_path()) {
    const std::string name = component.string();
    require(!name.empty() && name != "." && name != "..", "Invalid identity state path");
    Fd next(openat(current.value, name.c_str(), O_RDONLY | O_DIRECTORY | O_CLOEXEC | O_NOFOLLOW));
    trusted_directory(next.value);
    std::swap(current.value, next.value);
  }
  int result = current.value; current.value = -1; return result;
}
inline void trusted_file(int fd, bool empty_allowed) {
  struct stat info{};
  require(fd >= 0 && fstat(fd, &info) == 0 && S_ISREG(info.st_mode) &&
              info.st_uid == 0 && info.st_nlink == 1 && !(info.st_mode & 0022) &&
              info.st_size <= static_cast<off_t>(MAX_STATE_BYTES) && (empty_allowed || info.st_size > 0),
          "Untrusted identity registry file");
}
inline std::string read_all(int fd) {
  std::string result; char bytes[4096];
  for (;;) {
    ssize_t n = read(fd, bytes, sizeof(bytes));
    if (n < 0 && errno == EINTR) continue;
    require(n >= 0, "Identity registry read failed");
    if (!n) return result;
    result.append(bytes, static_cast<size_t>(n));
    require(result.size() <= MAX_STATE_BYTES, "Identity registry too large");
  }
}
inline bool valid_package(const std::string& value) {
  return value.size() <= 255 && std::regex_match(value,
      std::regex("[A-Za-z][A-Za-z0-9_]*(\\.[A-Za-z_][A-Za-z0-9_]*)+")) &&
      value != "android" && value.rfind("org.saildroid.", 0) != 0;
}
inline std::vector<std::string> signer_set(std::vector<std::string> signers) {
  require(!signers.empty() && signers.size() <= 8, "Verified signer set required");
  for (const auto& signer : signers)
    require(signer.size() == 64 && signer.find_first_not_of("0123456789abcdef") == signer.npos,
            "Invalid verified certificate digest");
  std::sort(signers.begin(), signers.end());
  require(std::adjacent_find(signers.begin(), signers.end()) == signers.end(),
          "Duplicate verified certificate digest");
  return signers;
}
inline void validate(const Json& state) {
  require(state.is_object() && state.size() == 3 &&
              state.at("schema") == "saildroid-app-identities-v1" &&
              state.at("next_app_id").is_number_unsigned() &&
              state.at("packages").is_object(), "Invalid identity registry schema");
  const auto next = state.at("next_app_id").get<unsigned long long>();
  require(next >= FIRST_APP_ID && next <= LAST_APP_ID + 1, "Invalid next app identity");
  std::set<unsigned> used;
  for (auto it = state.at("packages").begin(); it != state.at("packages").end(); ++it) {
    const auto& entry = it.value();
    require(valid_package(it.key()) && entry.is_object() && entry.size() == 3 &&
                entry.at("app_id").is_number_unsigned() && entry.at("retired").is_boolean() &&
                entry.at("signers").is_array(), "Invalid package identity record");
    const auto wide_id = entry.at("app_id").get<unsigned long long>();
    require(wide_id >= FIRST_APP_ID && wide_id < next && wide_id <= LAST_APP_ID,
            "Package identity outside allocated app range");
    require(used.insert(static_cast<unsigned>(wide_id)).second, "Duplicate app identity");
    const auto signers = entry.at("signers").get<std::vector<std::string>>();
    require(signer_set(signers) == signers, "Noncanonical saved signer set");
  }
}
class Registry {
  Fd directory;
  Fd lock;
  Json load() const {
    Fd file(openat(directory.value, "identities.json", O_RDONLY | O_CLOEXEC | O_NOFOLLOW));
    require(file.value >= 0, "Identity registry missing or inaccessible; explicit recovery required");
    trusted_file(file.value, false);
    auto value = Json::parse(read_all(file.value)); validate(value); return value;
  }
  void commit(const Json& value) const {
    validate(value);
    const auto content = value.dump(2) + "\n";
    require(content.size() <= MAX_STATE_BYTES, "Identity registry too large");
    static std::atomic<unsigned long> serial{0};
    const auto name = ".identities-" + std::to_string(getpid()) + "-" + std::to_string(serial.fetch_add(1) + 1);
    Fd file(openat(directory.value, name.c_str(),
                   O_CREAT | O_EXCL | O_WRONLY | O_NOFOLLOW | O_CLOEXEC, 0600));
    require(file.value >= 0, "Cannot create pending identity state");
    try {
      trusted_file(file.value, true);
      size_t offset = 0;
      while (offset < content.size()) {
        ssize_t n = write(file.value, content.data() + offset, content.size() - offset);
        if (n < 0 && errno == EINTR) continue;
        require(n > 0, "Cannot write pending identity state"); offset += static_cast<size_t>(n);
      }
      require(fsync(file.value) == 0, "Cannot synchronize identity state");
      require(renameat(directory.value, name.c_str(), directory.value, "identities.json") == 0,
              "Cannot publish identity state");
      require(fsync(directory.value) == 0, "Cannot synchronize identity directory");
    } catch (...) { unlinkat(directory.value, name.c_str(), 0); throw; }
  }
 public:
  explicit Registry(const fs::path& path, bool initialize = false)
      : directory(open_state_directory(path)) {
    if (initialize) {
      DIR* entries = fdopendir(dup(directory.value));
      require(entries != nullptr, "Cannot inspect initial identity directory");
      bool empty = true;
      while (auto* entry = readdir(entries)) {
        std::string name = entry->d_name;
        if (name != "." && name != "..") empty = false;
      }
      closedir(entries);
      require(empty, "Identity initialization requires an empty new state directory");
    }
    lock.value = openat(directory.value, ".lock",
        O_CREAT | O_RDWR | O_NOFOLLOW | O_CLOEXEC | (initialize ? O_EXCL : 0), 0600);
    trusted_file(lock.value, true);
    require(flock(lock.value, LOCK_EX) == 0, "Cannot lock app identity allocation");
    if (initialize) commit(Json{{"schema", "saildroid-app-identities-v1"},
                               {"next_app_id", FIRST_APP_ID}, {"packages", Json::object()}});
    else (void)load();
  }
  // Call only AFTER an immutable staged APK has been genuinely parsed and its
  // certificate signatures verified. Arbitrary client claims are not proof.
  unsigned allocate_verified(const std::string& package,
                             std::vector<std::string> verified_signers) {
    root_caller(); require(valid_package(package), "Invalid Android application package");
    verified_signers = signer_set(std::move(verified_signers));
    auto value = load(); auto& packages = value["packages"];
    if (packages.contains(package)) {
      auto& saved = packages[package];
      require(saved["signers"].get<std::vector<std::string>>() == verified_signers,
              "Installed application signer differs");
      if (saved["retired"].get<bool>()) { saved["retired"] = false; commit(value); }
      return saved["app_id"].get<unsigned>();
    }
    unsigned next = value["next_app_id"].get<unsigned>();
    while (next <= LAST_APP_ID) {
      const std::string name = "u0_a" + std::to_string(next - FIRST_APP_ID);
      errno = 0; bool used_user = getpwuid(next) != nullptr;
      require(used_user || errno == 0, "Host account lookup failed");
      errno = 0; bool used_group = getgrgid(next) != nullptr;
      require(used_group || errno == 0, "Host group lookup failed");
      errno = 0; bool used_name = getpwnam(name.c_str()) != nullptr;
      require(used_name || errno == 0, "Host account name lookup failed");
      errno = 0; bool used_group_name = getgrnam(name.c_str()) != nullptr;
      require(used_group_name || errno == 0, "Host group name lookup failed");
      if (!used_user && !used_group && !used_name && !used_group_name) break;
      ++next;
    }
    require(next <= LAST_APP_ID, "Android application identity range exhausted");
    packages[package] = Json{{"app_id", next}, {"signers", verified_signers}, {"retired", false}};
    value["next_app_id"] = next + 1; commit(value); return next;
  }
  void retire(const std::string& package) {
    root_caller(); require(valid_package(package), "Invalid Android application package");
    auto value = load(); auto& packages = value["packages"];
    require(packages.contains(package), "Unknown application identity");
    packages[package]["retired"] = true; commit(value);
    // Retired IDs are retained and never assigned to another package.
  }
  Json snapshot() const { root_caller(); return load(); }
};
} // namespace sd_identity
