import java.util.*;
/** Actual batched SurfaceControl operations applied to the software scene. */
public final class SdSurfaceControls {
    private static final HashMap<Long,ArrayList<Runnable>> transactions=new HashMap<Long,ArrayList<Runnable>>();
    private static long serial=1;
    private static ArrayList<Runnable> transaction(long id){ArrayList<Runnable> result=transactions.get(id);if(result==null)throw new IllegalArgumentException("Unknown transaction");return result;}
    public static synchronized long createTransaction(){long id=serial++;transactions.put(id,new ArrayList<Runnable>());return id;}
    public static synchronized void freeTransaction(long id){transactions.remove(id);}
    public static synchronized void apply(long id,boolean synchronous){ArrayList<Runnable> operations=transaction(id);for(Runnable operation:operations)operation.run();operations.clear();SdSurfaceStore.transactionComplete();}
    public static synchronized void merge(long target,long source){if(target==source)return;transaction(target).addAll(transaction(source));transaction(source).clear();}
    public static synchronized void position(long t,final long id,final float x,final float y){transaction(t).add(new Runnable(){public void run(){SdSurfaceStore.position(id,x,y);}});}
    public static synchronized void size(long t,final long id,final int w,final int h){transaction(t).add(new Runnable(){public void run(){SdSurfaceStore.size(id,w,h);}});}
    public static synchronized void layer(long t,final long id,final int layer){transaction(t).add(new Runnable(){public void run(){SdSurfaceStore.z(id,layer);}});}
    public static synchronized void alpha(long t,final long id,final float alpha){transaction(t).add(new Runnable(){public void run(){SdSurfaceStore.alpha(id,alpha);}});}
    public static synchronized void flags(long t,final long id,final int flags,final int mask){transaction(t).add(new Runnable(){public void run(){SdSurfaceStore.flags(id,flags,mask);}});}
    public static synchronized void matrix(long t,final long id,final float a,final float b,final float c,final float d){transaction(t).add(new Runnable(){public void run(){SdSurfaceStore.matrix(id,a,b,c,d);}});}
    public static synchronized void crop(long t,final long id,final int x,final int y,final int w,final int h){transaction(t).add(new Runnable(){public void run(){SdSurfaceStore.crop(id,x,y,w,h);}});}
    public static synchronized void remove(long t,final long id){transaction(t).add(new Runnable(){public void run(){SdSurfaceStore.remove(id);}});}
}
