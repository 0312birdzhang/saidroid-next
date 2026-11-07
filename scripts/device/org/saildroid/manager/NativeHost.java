package org.saildroid.manager;

import java.lang.reflect.InvocationTargetException;

/** Installer-only bridge to the runtime's system-loader native API.
 * Android's APK loader keeps its normal boot parent; it must not gain the
 * entire private runtime class path just to open another application. */
final class NativeHost {
    private NativeHost(){}
    private static Object invoke(String method,String name)throws Exception{
        Class<?> api=Class.forName("org.saildroid.host.HostApi",true,ClassLoader.getSystemClassLoader());
        try{return api.getMethod(method,String.class).invoke(null,name);}
        catch(InvocationTargetException failure){
            Throwable cause=failure.getCause();
            if(cause instanceof Exception)throw(Exception)cause;
            throw new IllegalStateException("应用管理服务调用失败",cause);
        }
    }
    static void open(String name)throws Exception{invoke("openApplication",name);}
    static String state(String name)throws Exception{return(String)invoke("state",name);}
}
