/* API29-side Surface identity for the host EGL buffer queue. Compile with the
 * matching Android headers/libc++ ABI; no glibc C++ object crosses this boundary.
 * EGL owns gralloc allocation, dequeue/queue and fences in libhybris. This
 * producer supplies Surface metadata, and rejects any accidental CPU/Android
 * buffer allocation path instead of silently falling back to a bitmap. */
#include <gui/Surface.h>
#include <gui/IProducerListener.h>
#include <cstdio>
#include <atomic>

using namespace android;
static constexpr int kHostWindowQuery = 0x53440001;
class HostProducer final : public BnGraphicBufferProducer {
    int mId;
    std::atomic<uint32_t> mWidth,mHeight;
public:
    HostProducer(int id, uint32_t width, uint32_t height)
        : mId(id), mWidth(width), mHeight(height) {}
    status_t requestBuffer(int, sp<GraphicBuffer>*) override { return INVALID_OPERATION; }
    status_t setMaxDequeuedBufferCount(int) override { return OK; }
    status_t setAsyncMode(bool) override { return OK; }
    status_t dequeueBuffer(int*, sp<Fence>*, uint32_t, uint32_t, PixelFormat,
                          uint64_t, uint64_t*, FrameEventHistoryDelta*) override {
        std::fprintf(stderr, "SDHWUI=unexpected_android_dequeue|id=%d\n", mId);
        return INVALID_OPERATION;
    }
    status_t detachBuffer(int) override { return INVALID_OPERATION; }
    status_t detachNextBuffer(sp<GraphicBuffer>*, sp<Fence>*) override { return INVALID_OPERATION; }
    status_t attachBuffer(int*, const sp<GraphicBuffer>&) override { return INVALID_OPERATION; }
    status_t queueBuffer(int, const QueueBufferInput&, QueueBufferOutput*) override { return INVALID_OPERATION; }
    status_t cancelBuffer(int, const sp<Fence>&) override { return INVALID_OPERATION; }
    int query(int what, int* value) override {
        if (!value) return BAD_VALUE;
        switch (what) {
        case kHostWindowQuery: *value=mId; break;
        case NATIVE_WINDOW_WIDTH: case NATIVE_WINDOW_DEFAULT_WIDTH: *value=mWidth; break;
        case NATIVE_WINDOW_HEIGHT: case NATIVE_WINDOW_DEFAULT_HEIGHT: *value=mHeight; break;
        case NATIVE_WINDOW_FORMAT: *value=HAL_PIXEL_FORMAT_RGBA_8888; break;
        case NATIVE_WINDOW_MIN_UNDEQUEUED_BUFFERS: *value=1; break;
        case NATIVE_WINDOW_CONSUMER_RUNNING_BEHIND: case NATIVE_WINDOW_CONSUMER_USAGE_BITS:
        case NATIVE_WINDOW_DEFAULT_DATASPACE: case NATIVE_WINDOW_CONSUMER_IS_PROTECTED:
        case NATIVE_WINDOW_TRANSFORM_HINT: *value=0; break;
        default: return BAD_VALUE;
        }
        return OK;
    }
    status_t connect(const sp<IProducerListener>&, int api, bool, QueueBufferOutput* output) override {
        if (api!=NATIVE_WINDOW_API_EGL) return INVALID_OPERATION;
        output->width=mWidth.load();output->height=mHeight.load();output->nextFrameNumber=1;
        return OK;
    }
    status_t disconnect(int, DisconnectMode) override { return OK; }
    status_t setSidebandStream(const sp<NativeHandle>&) override { return INVALID_OPERATION; }
    void allocateBuffers(uint32_t,uint32_t,PixelFormat,uint64_t) override {}
    status_t allowAllocation(bool) override { return OK; }
    status_t setGenerationNumber(uint32_t) override { return OK; }
    String8 getConsumerName() const override { return String8("SailDroid libhybris GPU queue"); }
    status_t setSharedBufferMode(bool enabled) override { return enabled?INVALID_OPERATION:OK; }
    status_t setAutoRefresh(bool enabled) override { return enabled?INVALID_OPERATION:OK; }
    status_t setDequeueTimeout(nsecs_t) override { return OK; }
    status_t getLastQueuedBuffer(sp<GraphicBuffer>*,sp<Fence>*,float[16]) override { return INVALID_OPERATION; }
    status_t getUniqueId(uint64_t* id) const override { *id=uint64_t(mId);return OK; }
    status_t getConsumerUsage(uint64_t* usage) const override { *usage=0;return OK; }
    void resize(uint32_t width,uint32_t height) {mWidth=width;mHeight=height;}
};
extern "C" void* sd_hwui_new_surface(int id, int width, int height) {
    sp<IGraphicBufferProducer> producer = new HostProducer(id,width,height);
    sp<Surface> surface = new Surface(producer, true);
    int status = native_window_api_connect(surface.get(), NATIVE_WINDOW_API_EGL);
    if (status) return nullptr;
    surface->incStrong((void*)sd_hwui_new_surface);
    std::fprintf(stderr,"SDHWUI=android_surface_created|id=%d|size=%dx%d|surface=%p\n",id,width,height,surface.get());
    return surface.get();
}
extern "C" void sd_hwui_delete_surface(void* pointer) {
    static_cast<Surface*>(pointer)->decStrong((void*)sd_hwui_new_surface);
}
extern "C" void sd_hwui_retain_surface(void* pointer) {
    static_cast<Surface*>(pointer)->incStrong((void*)sd_hwui_new_surface);
}
extern "C" void sd_hwui_resize_surface(void* pointer,int width,int height) {
    auto producer=static_cast<Surface*>(pointer)->getIGraphicBufferProducer();
    static_cast<HostProducer*>(producer.get())->resize(width,height);
}
extern "C" int sd_hwui_window_id(void* pointer) {
    auto* window=static_cast<ANativeWindow*>(pointer);int id=0;
    return window && window->query(window,kHostWindowQuery,&id)==OK ? id : 0;
}
