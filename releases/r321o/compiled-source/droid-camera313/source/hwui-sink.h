// GLES sink for actual process-owned HWUI/Wayland queues. TextureView's real
// BufferQueue keeps its ANativeWindow lock path; no readback or dummy frame.
struct GpuApi {
 using P=void*;void *egl=nullptr,*gl=nullptr;
 P(*display)(P)=nullptr;unsigned(*initialize)(P,int*,int*)=nullptr;unsigned(*bind)(unsigned)=nullptr;
 unsigned(*choose)(P,const int*,P*,int,int*)=nullptr;P(*context)(P,P,P,const int*)=nullptr;P(*surface)(P,P,P,const int*)=nullptr;
 unsigned(*make)(P,P,P,P)=nullptr;unsigned(*swap)(P,P)=nullptr;unsigned(*destroySurface)(P,P)=nullptr;unsigned(*destroyContext)(P,P)=nullptr;unsigned(*query)(P,P,int,int*)=nullptr;
 P(*currentDisplay)()=nullptr;P(*currentContext)()=nullptr;P(*currentSurface)(int)=nullptr;int64_t(*frames)(P)=nullptr;
 void(*clearColor)(float,float,float,float)=nullptr;void(*clear)(unsigned)=nullptr;void(*viewport)(int,int,int,int)=nullptr;
 unsigned(*createShader)(unsigned)=nullptr;void(*shaderSource)(unsigned,int,const char*const*,const int*)=nullptr;void(*compileShader)(unsigned)=nullptr;void(*shaderiv)(unsigned,unsigned,int*)=nullptr;
 unsigned(*createProgram)()=nullptr;void(*attachShader)(unsigned,unsigned)=nullptr;void(*linkProgram)(unsigned)=nullptr;void(*programiv)(unsigned,unsigned,int*)=nullptr;void(*useProgram)(unsigned)=nullptr;
 int(*attrib)(unsigned,const char*)=nullptr;void(*vertex)(unsigned,int,unsigned,unsigned,int,const void*)=nullptr;void(*enableAttrib)(unsigned)=nullptr;void(*draw)(unsigned,int,int)=nullptr;
 void(*genTextures)(int,unsigned*)=nullptr;void(*bindTexture)(unsigned,unsigned)=nullptr;void(*textureParameter)(unsigned,unsigned,int)=nullptr;void(*textureImage)(unsigned,int,int,int,int,int,unsigned,unsigned,const void*)=nullptr;
 void(*deleteTextures)(int,const unsigned*)=nullptr;void(*deleteShader)(unsigned)=nullptr;void(*deleteProgram)(unsigned)=nullptr;unsigned(*error)()=nullptr;
 bool ready=false;
 GpuApi(){egl=dlopen("libEGL.so.1",RTLD_NOW|RTLD_LOCAL);gl=dlopen("libGLESv2.so.2",RTLD_NOW|RTLD_LOCAL);if(!egl||!gl)return;
#define LOAD(field,lib,name) field=(decltype(field))dlsym(lib,name);if(!field)return
 LOAD(display,RTLD_DEFAULT,"bionic_eglGetDisplay");LOAD(surface,RTLD_DEFAULT,"bionic_eglCreateWindowSurface");LOAD(swap,RTLD_DEFAULT,"bionic_eglSwapBuffers");LOAD(destroySurface,RTLD_DEFAULT,"bionic_eglDestroySurface");LOAD(frames,RTLD_DEFAULT,"sd_hwui_submitted_frames");
 LOAD(initialize,egl,"eglInitialize");LOAD(bind,egl,"eglBindAPI");LOAD(choose,egl,"eglChooseConfig");LOAD(context,egl,"eglCreateContext");LOAD(make,egl,"eglMakeCurrent");LOAD(destroyContext,egl,"eglDestroyContext");LOAD(query,egl,"eglQuerySurface");LOAD(currentDisplay,egl,"eglGetCurrentDisplay");LOAD(currentContext,egl,"eglGetCurrentContext");LOAD(currentSurface,egl,"eglGetCurrentSurface");
 LOAD(clearColor,gl,"glClearColor");LOAD(clear,gl,"glClear");LOAD(viewport,gl,"glViewport");LOAD(createShader,gl,"glCreateShader");LOAD(shaderSource,gl,"glShaderSource");LOAD(compileShader,gl,"glCompileShader");LOAD(shaderiv,gl,"glGetShaderiv");LOAD(createProgram,gl,"glCreateProgram");LOAD(attachShader,gl,"glAttachShader");LOAD(linkProgram,gl,"glLinkProgram");LOAD(programiv,gl,"glGetProgramiv");LOAD(useProgram,gl,"glUseProgram");LOAD(attrib,gl,"glGetAttribLocation");LOAD(vertex,gl,"glVertexAttribPointer");LOAD(enableAttrib,gl,"glEnableVertexAttribArray");LOAD(draw,gl,"glDrawArrays");LOAD(genTextures,gl,"glGenTextures");LOAD(bindTexture,gl,"glBindTexture");LOAD(textureParameter,gl,"glTexParameteri");LOAD(textureImage,gl,"glTexImage2D");LOAD(deleteTextures,gl,"glDeleteTextures");LOAD(deleteShader,gl,"glDeleteShader");LOAD(deleteProgram,gl,"glDeleteProgram");LOAD(error,gl,"glGetError");
#undef LOAD
 ready=true;
 }
};
static GpuApi&gpu_api(){static GpuApi api;return api;}
struct GpuSurface {
 GpuApi&a;void *window,*display=nullptr,*surface=nullptr,*context=nullptr;unsigned program=0,texture=0;bool ready=false;
 struct Current {GpuApi&a;void*d,*c,*draw,*read;Current(GpuApi&api):a(api),d(a.currentDisplay()),c(a.currentContext()),draw(a.currentSurface(0x3059)),read(a.currentSurface(0x305a)){}void restore(void*fallback){a.make(d?d:fallback,draw,read,c);}};
 explicit GpuSurface(void*w):a(gpu_api()),window(w){if(!a.ready)return;Current old(a);display=a.display(nullptr);int major,minor,count=0;void*config=nullptr;int attrs[]={0x3033,4,0x3040,4,0x3024,8,0x3023,8,0x3022,8,0x3021,8,0x3038};int ctx[]={0x3098,2,0x3038};if(display&&a.initialize(display,&major,&minor)&&a.bind(0x30a0)&&a.choose(display,attrs,&config,1,&count)&&count==1){context=a.context(display,config,nullptr,ctx);surface=a.surface(display,config,window,nullptr);ready=context&&surface;}old.restore(display);}
 bool color(float r,float g,float b){if(!ready)return false;Current old(a);if(!a.make(display,surface,surface,context))return false;a.clearColor(r,g,b,1);a.clear(0x4000);bool ok=a.error()==0&&a.swap(display,surface);old.restore(display);return ok;}
 bool pixels(const void*bytes,int width,int height){if(!ready)return false;Current old(a);if(!a.make(display,surface,surface,context))return false;bool ok=true;
 if(!program){const char*vs="attribute vec2 a;attribute vec2 t;varying vec2 uv;void main(){uv=t;gl_Position=vec4(a,0.,1.);}";const char*fs="precision mediump float;varying vec2 uv;uniform sampler2D image;void main(){gl_FragColor=texture2D(image,uv);}";unsigned v=a.createShader(0x8b31),f=a.createShader(0x8b30);a.shaderSource(v,1,&vs,nullptr);a.shaderSource(f,1,&fs,nullptr);a.compileShader(v);a.compileShader(f);int vc=0,fc=0;a.shaderiv(v,0x8b81,&vc);a.shaderiv(f,0x8b81,&fc);program=a.createProgram();a.attachShader(program,v);a.attachShader(program,f);a.linkProgram(program);int linked=0;a.programiv(program,0x8b82,&linked);a.deleteShader(v);a.deleteShader(f);ok=vc&&fc&&linked;a.genTextures(1,&texture);}
 if(ok){int w=0,h=0;ok=a.query(display,surface,0x3057,&w)&&a.query(display,surface,0x3056,&h);a.viewport(0,0,w,h);a.useProgram(program);a.bindTexture(0x0de1,texture);a.textureParameter(0x0de1,0x2801,0x2601);a.textureParameter(0x0de1,0x2800,0x2601);a.textureParameter(0x0de1,0x2802,0x812f);a.textureParameter(0x0de1,0x2803,0x812f);a.textureImage(0x0de1,0,0x1908,width,height,0,0x1908,0x1401,bytes);float vertices[]={-1,-1,0,1,1,-1,1,1,-1,1,0,0,1,1,1,0};int position=a.attrib(program,"a"),uv=a.attrib(program,"t");ok=ok&&position>=0&&uv>=0;if(ok){a.vertex(position,2,0x1406,0,4*sizeof(float),vertices);a.enableAttrib(position);a.vertex(uv,2,0x1406,0,4*sizeof(float),vertices+2);a.enableAttrib(uv);a.draw(0x0005,0,4);ok=a.error()==0&&a.swap(display,surface);}}
 old.restore(display);return ok;
 }
 ~GpuSurface(){if(!a.ready)return;if(context){Current old(a);if(a.make(display,surface,surface,context)){if(texture)a.deleteTextures(1,&texture);if(program)a.deleteProgram(program);}old.restore(display);}if(surface)a.destroySurface(display,surface);if(context)a.destroyContext(display,context);}
};
