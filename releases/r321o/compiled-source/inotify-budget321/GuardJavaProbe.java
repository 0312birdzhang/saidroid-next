import android.os.FileObserver;
import java.io.IOException;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
public final class GuardJavaProbe {
    static int[] counts() throws Exception {
        int fds=0,watches=0;
        try(DirectoryStream<Path> entries=Files.newDirectoryStream(Paths.get("/proc/self/fd"))) {
            for(Path fd:entries) {
                String target;try{target=Files.readSymbolicLink(fd).toString();}catch(IOException e){continue;}
                if(!target.equals("anon_inode:inotify"))continue;fds++;
                for(String line:Files.readAllLines(Paths.get("/proc/self/fdinfo",fd.getFileName().toString())))if(line.startsWith("inotify "))watches++;
            }
        }
        return new int[]{fds,watches};
    }
    public static void main(String[] args)throws Exception {
        Path base=Paths.get(args[0]);int[] before=counts();
        if(before[1]!=0)throw new AssertionError("unexpected baseline watches "+before[1]);
        System.out.println("GUARD_JAVA_BASELINE|fds="+before[0]+"|watches="+before[1]);
        ArrayList<FileObserver> capObservers=new ArrayList<>();
        AtomicInteger capCallbacks=new AtomicInteger(),deniedCallbacks=new AtomicInteger();
        for(int i=0;i<513;i++) {
            final int index=i;Path directory=Files.createDirectory(base.resolve("capwatch"+i));
            FileObserver observer=new FileObserver(directory.toString(),FileObserver.CREATE) {
                public void onEvent(int event,String name){if((event&FileObserver.CREATE)!=0){if(index==512)deniedCallbacks.incrementAndGet();else capCallbacks.incrementAndGet();}}
            };
            capObservers.add(observer);observer.startWatching();
        }
        if(counts()[1]!=512)throw new AssertionError("Android FileObserver guard cap expected512 actual"+counts()[1]);
        Files.write(base.resolve("capwatch0/event"),new byte[]{1});Files.write(base.resolve("capwatch512/event"),new byte[]{1});
        long capDeadline=System.nanoTime()+3000000000L;
        while(capCallbacks.get()==0&&System.nanoTime()<capDeadline)Thread.sleep(10);
        Thread.sleep(50);
        if(capCallbacks.get()!=1||deniedCallbacks.get()!=0)throw new AssertionError("Android accepted/denied callbacks");
        for(FileObserver observer:capObservers)observer.stopWatching();
        if(counts()[1]!=0)throw new AssertionError("Android cap-watch cleanup");
        ArrayList<FileObserver> observers=new ArrayList<>();AtomicInteger callbacks=new AtomicInteger();
        for(int i=0;i<32;i++) {
            Path dir=Files.createDirectory(base.resolve("observer"+i));
            FileObserver observer=new FileObserver(dir.toString(),FileObserver.CREATE) {
                public void onEvent(int event,String name){if((event&FileObserver.CREATE)!=0)callbacks.incrementAndGet();}
            };
            observers.add(observer);observer.startWatching();
        }
        WatchService service=FileSystems.getDefault().newWatchService();
        ArrayList<WatchKey> keys=new ArrayList<>();
        for(int i=0;i<480;i++)keys.add(Files.createDirectory(base.resolve("nio"+i)).register(service,StandardWatchEventKinds.ENTRY_CREATE));
        int[] full=counts();if(full[1]!=512)throw new AssertionError("cap watches "+full[1]);
        Path denied=Files.createDirectory(base.resolve("denied"));String refusal="";
        try{denied.register(service,StandardWatchEventKinds.ENTRY_CREATE);throw new AssertionError("new watch accepted beyond process cap");}
        catch(IOException expected){refusal=expected.toString();}
        if(counts()[1]!=512)throw new AssertionError("failed watch left kernel allocation");
        for(int i=0;i<32;i++)Files.write(base.resolve("observer"+i).resolve("event"),new byte[]{1});
        Files.write(base.resolve("nio0/event"),new byte[]{1});
        WatchKey key=service.poll(3,TimeUnit.SECONDS);
        if(key==null||key.pollEvents().size()!=1)throw new AssertionError("NIO event missing");key.reset();
        long deadline=System.nanoTime()+3000000000L;
        while(callbacks.get()!=32&&System.nanoTime()<deadline)Thread.sleep(10);
        if(callbacks.get()!=32)throw new AssertionError("observer callbacks "+callbacks);
        for(FileObserver observer:observers)observer.stopWatching();
        if(counts()[1]!=480)throw new AssertionError("observer release");
        WatchKey recovered=denied.register(service,StandardWatchEventKinds.ENTRY_CREATE);
        if(!recovered.isValid()||counts()[1]!=481)throw new AssertionError("capacity not recovered");
        service.close();int[] after=counts();if(after[1]!=0)throw new AssertionError("watch cleanup "+after[1]);
        System.out.println("GUARD_JAVA=passed|android_native_cap=512|android_denied_callback=0|file_observer_callbacks="+callbacks+"|nio_callbacks=1|cap=512|denied="+refusal+"|after_watches="+after[1]+"|before_fds="+before[0]+"|after_fds="+after[0]);
        System.exit(0);
    }
}
