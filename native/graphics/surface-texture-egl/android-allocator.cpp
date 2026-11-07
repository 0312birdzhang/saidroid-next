#include <string>
#include <cstdint>
#include <cutils/native_handle.h>
#include <system/window.h>

/* This TU is built with Android libc++, not the host C++ runtime. A by-value
 * requestorName remains governed by that exact ABI and is destroyed normally. */
static int (*allocate_host)(unsigned,unsigned,int,unsigned,uint64_t,
                           const native_handle_t**,unsigned*);
extern "C" void sd_texture_set_host_allocator(void* callback) {
    allocate_host=reinterpret_cast<decltype(allocate_host)>(callback);
}
extern "C" int sd_texture_android_allocate(void*,unsigned w,unsigned h,int format,
        unsigned layers,uint64_t usage,const native_handle_t** handle,unsigned* stride,
        uint64_t, std::string requestorName) {
    (void)requestorName;
    return allocate_host?allocate_host(w,h,format,layers,usage,handle,stride):-19;
}
extern "C" const native_handle_t* sd_texture_buffer_handle(void* pointer) {
    const auto* buffer=static_cast<const ANativeWindowBuffer*>(pointer);
    return buffer && buffer->common.magic==ANDROID_NATIVE_BUFFER_MAGIC?buffer->handle:nullptr;
}
