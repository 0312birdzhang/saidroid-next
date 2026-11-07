#include <android/hardware/keymaster/4.0/IKeymasterDevice.h>
#include <stdint.h>
#include <stddef.h>
#include <string.h>

// C-only, versioned output boundary to the native host. This component is built
// against actual Android10 libc++/HIDL interfaces and loaded by the translated
// Android linker, never by the host C++ ABI. It cannot create or inspect keys.
struct SdKeymaster4HardwareInfo {
    uint32_t version;
    int32_t security_level;
    char implementation[256];
    char author[256];
};
extern "C" __attribute__((visibility("default"))) int
sd_keymaster4_hardware_info(SdKeymaster4HardwareInfo* output, size_t size) {
    if (!output || size != sizeof(*output)) return -1;
    memset(output, 0, sizeof(*output));
    output->version = 1;
    output->security_level = -1;
    using android::hardware::hidl_string;
    using android::hardware::keymaster::V4_0::IKeymasterDevice;
    using android::hardware::keymaster::V4_0::SecurityLevel;
    // No wait-for-registration loop. The owning process must independently
    // bound the Binder RPC and exit even if the external service hangs.
    auto device = IKeymasterDevice::tryGetService("default", false);
    if (!device) return -2;
    unsigned callbacks = 0;
    bool valid = false;
    auto result = device->getHardwareInfo([&](SecurityLevel level,
            const hidl_string& implementation, const hidl_string& author) {
        ++callbacks;
        int raw = static_cast<int>(level);
        if (callbacks != 1 || raw < 0 || raw > 2
                || implementation.size() >= sizeof(output->implementation)
                || author.size() >= sizeof(output->author)) return;
        output->security_level = raw;
        memcpy(output->implementation, implementation.c_str(), implementation.size());
        memcpy(output->author, author.c_str(), author.size());
        valid = true;
    });
    if (!result.isOk()) return -3;
    if (callbacks != 1 || !valid) return -4;
    return 0;
}
