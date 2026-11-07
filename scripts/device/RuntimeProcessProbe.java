public final class RuntimeProcessProbe {
    public static void main(String[] args)throws Exception{
        System.load(args[1]);if(!SdBridge.loadBionicLibrary(args[0]+"/libandroid_runtime.so",args[0]))throw new IllegalStateException("bootstrap");SdBridge.registerFrameworkNatives();
        String expected="org.saildroid.process-test";android.os.Process.setArgV0(expected);
        byte[] bytes=new byte[1024];int count;try(java.io.FileInputStream file=new java.io.FileInputStream("/proc/self/cmdline")){count=file.read(bytes);}
        int end=0;while(end<count&&bytes[end]!=0)end++;
        if(!expected.equals(new String(bytes,0,end,"UTF-8")))throw new AssertionError("Linux process title differs");
        if(android.os.Binder.getCallingPid()!=android.os.Process.myPid()||android.os.Binder.getCallingUid()!=android.os.Process.myUid())throw new AssertionError("Local Binder identity is not this Linux process");
        System.out.println("RUNTIME_PROCESS_TEST=PASS|pid="+android.os.Process.myPid()+"|uid="+android.os.Process.myUid());
    }
}
