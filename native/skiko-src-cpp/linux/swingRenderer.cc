#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <GLES2/gl2.h>
#include <cstdlib>
#include <cstring>
#include <unistd.h>
#include <stdio.h>
#include "jni_helpers.h"

/* SaiDroid: EGL 后端替代 GLX，支持 Wayland/嵌入式环境 */

class OffScreenContext
{
public:
    EGLDisplay display;
    EGLContext context;
    EGLConfig config;

    OffScreenContext(EGLDisplay _display, EGLContext _context, EGLConfig _config) {
        display = _display;
        context = _context;
        config = _config;
    }

    ~OffScreenContext() {
        if (display != EGL_NO_DISPLAY) {
            eglMakeCurrent(display, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT);
            if (context != EGL_NO_CONTEXT) {
                eglDestroyContext(display, context);
            }
            eglTerminate(display);
        }
    }

    static OffScreenContext* create() {
        EGLDisplay display = eglGetDisplay(EGL_DEFAULT_DISPLAY);
        if (display == EGL_NO_DISPLAY) {
            fprintf(stderr, "[skiko-egl] eglGetDisplay failed\n");
            return nullptr;
        }

        EGLint major = 0, minor = 0;
        if (!eglInitialize(display, &major, &minor)) {
            fprintf(stderr, "[skiko-egl] eglInitialize failed: 0x%x\n", eglGetError());
            return nullptr;
        }
        fprintf(stderr, "[skiko-egl] EGL %d.%d\n", major, minor);

        const EGLint configAttribs[] = {
            EGL_SURFACE_TYPE, EGL_PBUFFER_BIT,
            EGL_RENDERABLE_TYPE, EGL_OPENGL_ES2_BIT,
            EGL_RED_SIZE, 8,
            EGL_GREEN_SIZE, 8,
            EGL_BLUE_SIZE, 8,
            EGL_ALPHA_SIZE, 8,
            EGL_NONE
        };
        EGLConfig config;
        EGLint numConfigs = 0;
        if (!eglChooseConfig(display, configAttribs, &config, 1, &numConfigs) || numConfigs < 1) {
            fprintf(stderr, "[skiko-egl] eglChooseConfig failed: 0x%x\n", eglGetError());
            eglTerminate(display);
            return nullptr;
        }

        const EGLint contextAttribs[] = {
            EGL_CONTEXT_CLIENT_VERSION, 2,
            EGL_NONE
        };
        EGLContext context = eglCreateContext(display, config, EGL_NO_CONTEXT, contextAttribs);
        if (context == EGL_NO_CONTEXT) {
            fprintf(stderr, "[skiko-egl] eglCreateContext failed: 0x%x\n", eglGetError());
            eglTerminate(display);
            return nullptr;
        }

        return new OffScreenContext(display, context, config);
    }
};

class OffScreenBuffer
{
public:
    EGLDisplay display;
    EGLSurface surface;
    int width;
    int height;

    OffScreenBuffer(EGLDisplay _display, EGLSurface _surface, int _width, int _height) {
        display = _display;
        surface = _surface;
        width = _width;
        height = _height;
    }

    ~OffScreenBuffer() {
        if (display != EGL_NO_DISPLAY && surface != EGL_NO_SURFACE) {
            eglDestroySurface(display, surface);
        }
    }

    static OffScreenBuffer* create(OffScreenContext* context, int width, int height) {
        const EGLint pbufferAttribs[] = {
            EGL_WIDTH, width,
            EGL_HEIGHT, height,
            EGL_NONE
        };
        EGLSurface surface = eglCreatePbufferSurface(context->display, context->config, pbufferAttribs);
        if (surface == EGL_NO_SURFACE) {
            fprintf(stderr, "[skiko-egl] eglCreatePbufferSurface failed: 0x%x\n", eglGetError());
            return nullptr;
        }
        return new OffScreenBuffer(context->display, surface, width, height);
    }
};

class OffScreenTexture
{
public:
    GLuint tex;
    GLuint fbo;

    OffScreenTexture(GLuint _tex, GLuint _fbo) {
        tex = _tex;
        fbo = _fbo;
    }

    ~OffScreenTexture() {
        glDeleteFramebuffers(1, &fbo);
        glDeleteTextures(1, &tex);
    }
};

extern "C"
{
    JNIEXPORT jlong JNICALL Java_org_jetbrains_skiko_swing_LinuxOpenGLSwingRenderer_makeOffScreenContext(
        JNIEnv *env, jobject renderer)
    {
        OffScreenContext* context = OffScreenContext::create();
        return toJavaPointer(context);
    }

    JNIEXPORT void JNICALL Java_org_jetbrains_skiko_swing_LinuxOpenGLSwingRenderer_disposeOffScreenContext(
        JNIEnv *env, jobject renderer, jlong contextPtr)
    {
        OffScreenContext* context = fromJavaPointer<OffScreenContext *>(contextPtr);

        if (context) {
            delete context;
        }
    }

    JNIEXPORT jlong JNICALL Java_org_jetbrains_skiko_swing_LinuxOpenGLSwingRenderer_makeOffScreenBuffer(
        JNIEnv *env, jobject renderer, jlong contextPtr, jlong oldBufferPtr, jint width, jint height)
    {
        OffScreenContext* context = fromJavaPointer<OffScreenContext *>(contextPtr);
        OffScreenBuffer* oldBuffer = fromJavaPointer<OffScreenBuffer *>(oldBufferPtr);
        
        OffScreenBuffer* buffer;
        if (oldBuffer == nullptr || oldBuffer->width != width || oldBuffer->height != height) {
            if (oldBuffer != nullptr) {
                delete oldBuffer;
            }
            buffer = OffScreenBuffer::create(context, width, height);
        } else {
            buffer = oldBuffer;
        }

        return toJavaPointer(buffer);
    }

    JNIEXPORT void JNICALL Java_org_jetbrains_skiko_swing_LinuxOpenGLSwingRenderer_disposeOffScreenBuffer(
        JNIEnv *env, jobject renderer, jlong bufferPtr)
    {
        OffScreenBuffer* buffer = fromJavaPointer<OffScreenBuffer *>(bufferPtr);
        if (buffer) {
            delete buffer;
        }
    }

    JNIEXPORT void JNICALL Java_org_jetbrains_skiko_swing_LinuxOpenGLSwingRenderer_startRendering(
        JNIEnv *env, jobject renderer, jlong contextPtr, jlong bufferPtr)
    {
        OffScreenContext* context = fromJavaPointer<OffScreenContext *>(contextPtr);
        OffScreenBuffer* buffer = fromJavaPointer<OffScreenBuffer *>(bufferPtr);

        eglMakeCurrent(context->display, buffer->surface, buffer->surface, context->context);
    }

    JNIEXPORT void JNICALL Java_org_jetbrains_skiko_swing_LinuxOpenGLSwingRenderer_finishRendering(
        JNIEnv *env, jobject renderer, jlong contextPtr)
    {
        OffScreenContext* context = fromJavaPointer<OffScreenContext *>(contextPtr);
        eglMakeCurrent(context->display, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT);
    }

    JNIEXPORT jlong JNICALL Java_org_jetbrains_skiko_swing_LinuxOpenGLSwingRenderer_createAndBindTexture(
        JNIEnv *env, jobject renderer, jint width, jint height)
    {
        GLuint tex;
        glGenTextures(1, &tex);
        glBindTexture(GL_TEXTURE_2D, tex);
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, NULL);

        GLuint fbo;
        glGenFramebuffers(1, &fbo);
        glBindFramebuffer(GL_FRAMEBUFFER, fbo);

        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, tex, 0);

        OffScreenTexture *texture = new OffScreenTexture(tex, fbo);

        return toJavaPointer(texture);
    }

    JNIEXPORT GLuint JNICALL Java_org_jetbrains_skiko_swing_LinuxOpenGLSwingRenderer_getFboId(
        JNIEnv *env, jobject renderer, jlong texturePtr)
    {
        OffScreenTexture *texture = fromJavaPointer<OffScreenTexture *>(texturePtr);

        return texture->fbo;
    }

    JNIEXPORT void JNICALL Java_org_jetbrains_skiko_swing_LinuxOpenGLSwingRenderer_unbindAndDisposeTexture(
        JNIEnv *env, jobject renderer, jlong texturePtr)
    {
        glBindFramebuffer(GL_FRAMEBUFFER, 0);
        glBindTexture(GL_TEXTURE_2D, 0);
        OffScreenTexture *texture = fromJavaPointer<OffScreenTexture *>(texturePtr);

        if (texture) {
            delete texture;
        }
    }

    JNIEXPORT jlong JNICALL Java_org_jetbrains_skiko_graphicapi_OpenGLOffscreenContext_makeOffScreenContext(
        JNIEnv *env, jobject contextHandler)
    {
        OffScreenContext* context = OffScreenContext::create();
        return toJavaPointer(context);
    }

    JNIEXPORT void JNICALL Java_org_jetbrains_skiko_graphicapi_OpenGLOffscreenContext_disposeOffScreenContext(
        JNIEnv *env, jobject contextHandler, jlong contextPtr)
    {
        OffScreenContext* context = fromJavaPointer<OffScreenContext *>(contextPtr);

        if (context) {
            delete context;
        }
    }

    JNIEXPORT jlong JNICALL Java_org_jetbrains_skiko_graphicapi_OpenGLOffscreenContext_makeOffScreenBuffer(
        JNIEnv *env, jobject contextHandler, jlong contextPtr, jlong oldBufferPtr, jint width, jint height)
    {
        OffScreenContext* context = fromJavaPointer<OffScreenContext *>(contextPtr);
        OffScreenBuffer* oldBuffer = fromJavaPointer<OffScreenBuffer *>(oldBufferPtr);

        OffScreenBuffer* buffer;
        if (oldBuffer == nullptr || oldBuffer->width != width || oldBuffer->height != height) {
            if (oldBuffer != nullptr) {
                delete oldBuffer;
            }
            buffer = OffScreenBuffer::create(context, width, height);
        } else {
            buffer = oldBuffer;
        }

        return toJavaPointer(buffer);
    }

    JNIEXPORT void JNICALL Java_org_jetbrains_skiko_graphicapi_OpenGLOffscreenContext_disposeOffScreenBuffer(
        JNIEnv *env, jobject contextHandler, jlong bufferPtr)
    {
        OffScreenBuffer* buffer = fromJavaPointer<OffScreenBuffer *>(bufferPtr);
        if (buffer) {
            delete buffer;
        }
    }

    JNIEXPORT void JNICALL Java_org_jetbrains_skiko_graphicapi_OpenGLOffscreenContext_startRendering(
        JNIEnv *env, jobject contextHandler, jlong contextPtr, jlong bufferPtr)
    {
        OffScreenContext* context = fromJavaPointer<OffScreenContext *>(contextPtr);
        OffScreenBuffer* buffer = fromJavaPointer<OffScreenBuffer *>(bufferPtr);

        eglMakeCurrent(context->display, buffer->surface, buffer->surface, context->context);
    }

    JNIEXPORT void JNICALL Java_org_jetbrains_skiko_graphicapi_OpenGLOffscreenContext_finishRendering(
        JNIEnv *env, jobject contextHandler, jlong contextPtr)
    {
        OffScreenContext* context = fromJavaPointer<OffScreenContext *>(contextPtr);
        eglMakeCurrent(context->display, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT);
    }

    JNIEXPORT jlong JNICALL Java_org_jetbrains_skiko_graphicapi_OpenGLOffscreenContext_createAndBindTexture(
        JNIEnv *env, jobject contextHandler, jint width, jint height)
    {
        GLuint tex;
        glGenTextures(1, &tex);
        glBindTexture(GL_TEXTURE_2D, tex);
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, NULL);

        GLuint fbo;
        glGenFramebuffers(1, &fbo);
        glBindFramebuffer(GL_FRAMEBUFFER, fbo);

        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, tex, 0);

        OffScreenTexture *texture = new OffScreenTexture(tex, fbo);

        return toJavaPointer(texture);
    }

    JNIEXPORT GLuint JNICALL Java_org_jetbrains_skiko_graphicapi_OpenGLOffscreenContext_getFboId(
        JNIEnv *env, jobject contextHandler, jlong texturePtr)
    {
        OffScreenTexture *texture = fromJavaPointer<OffScreenTexture *>(texturePtr);

        return texture->fbo;
    }

    JNIEXPORT void JNICALL Java_org_jetbrains_skiko_graphicapi_OpenGLOffscreenContext_unbindAndDisposeTexture(
        JNIEnv *env, jobject contextHandler, jlong texturePtr)
    {
        glBindFramebuffer(GL_FRAMEBUFFER, 0);
        glBindTexture(GL_TEXTURE_2D, 0);
        OffScreenTexture *texture = fromJavaPointer<OffScreenTexture *>(texturePtr);

        if (texture) {
            delete texture;
        }
    }
} // extern "C"
