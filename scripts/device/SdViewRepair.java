import android.view.View;
import android.view.ViewGroup;

/**
 * Repair children whose {@link ViewGroup.LayoutParams} are null before a layout traversal
 * measures them.
 *
 * <p>Why this exists (real crash, 2026-10-27): QQ's TBS engine falls back to the system WebView
 * when the X5 kernel is unavailable, and it attaches {@code com.tencent.smtt.sdk.WebView$a} to
 * {@code com.tencent.biz.ui.TouchWebView} without layout parameters. The next traversal then runs
 * {@code FrameLayout.onMeasure} -> {@code ViewGroup.measureChildWithMargins}, reads
 * {@code lp.leftMargin} on that null reference and throws
 * {@code NullPointerException: Attempt to read from field 'int
 * android.view.ViewGroup$MarginLayoutParams.leftMargin' on a null object reference}, after which
 * the runtime exits with status 10 and QQ disappears.
 *
 * <p>The view dump taken at fatal time ({@code build/evidence/npe21/app.log}) shows exactly one
 * node with {@code params=null} out of 136, and it is that TBS WebView, so this is not a guess.
 * Nothing in our runtime adds that view; the app code does, through an add path that skips
 * {@code generateDefaultLayoutParams()}. We therefore repair it at the last moment we control
 * before the traversal: the frame callback.
 *
 * <p>The repair only fills in missing parameters from the parent's
 * {@code generateDefaultLayoutParams()}. It never rewrites parameters that already exist, so a
 * correctly built hierarchy is untouched and the walk is a no-op.
 */
final class SdViewRepair{
    private static final int MAX_VIEWS=1200;
    private static volatile boolean enabled;
    private static boolean reported;

    private SdViewRepair(){}

    /** Enabled as soon as an app WebView exists: that is the only path that produces the null. */
    static void enable(){enabled=true;}

    static boolean enabled(){return enabled;}

    static void repair(){
        if(!enabled)return;
        Object[] clients;
        try{clients=SdWindowSession.windowClients();}
        catch(Throwable failure){return;}
        for(Object client:clients){
            Object root;
            try{root=decorView(client);}
            catch(Throwable failure){continue;}
            if(!(root instanceof View))continue;
            int[] budget={MAX_VIEWS};
            walk((View)root,budget);
        }
    }

    private static void walk(View view,int[] budget){
        if(budget[0]<=0)return;
        budget[0]--;
        if(view instanceof ViewGroup){
            ViewGroup group=(ViewGroup)view;
            int count;
            try{count=group.getChildCount();}
            catch(Throwable failure){return;}
            for(int index=0;index<count;index++){
                View child;
                try{child=group.getChildAt(index);}
                catch(Throwable failure){continue;}
                if(child==null)continue;
                if(child.getLayoutParams()==null)fill(child,group);
                walk(child,budget);
            }
        }
    }

    private static void fill(View child,ViewGroup parent){
        ViewGroup.LayoutParams params;
        try{
            java.lang.reflect.Method method=ViewGroup.class.getDeclaredMethod("generateDefaultLayoutParams");
            method.setAccessible(true);
            params=(ViewGroup.LayoutParams)method.invoke(parent);
        }catch(Throwable failure){
            System.err.println("SDREPAIR=failed|child="+child.getClass().getName()+"|parent="+parent.getClass().getName()+"|error="+failure.getClass().getName());
            return;
        }
        if(params==null){
            System.err.println("SDREPAIR=no_default|child="+child.getClass().getName()+"|parent="+parent.getClass().getName());
            return;
        }
        try{child.setLayoutParams(params);}
        catch(Throwable failure){
            System.err.println("SDREPAIR=refused|child="+child.getClass().getName()+"|parent="+parent.getClass().getName()+"|error="+failure.getClass().getName());
            return;
        }
        System.err.println("SDREPAIR=params|child="+child.getClass().getName()+"|parent="+parent.getClass().getName()+"|w="+params.width+"|h="+params.height);
        reported=true;
    }

    static boolean reported(){return reported;}

    private static Object decorView(Object client)throws ReflectiveOperationException{
        Object viewRoot=null;
        try{
            Object holder=field(client.getClass(),"mViewAncestor").get(client);
            if(holder instanceof java.lang.ref.WeakReference)viewRoot=((java.lang.ref.WeakReference<?>)holder).get();
            else if(holder!=null)viewRoot=holder;
        }catch(NoSuchFieldException older){/* fall back to this$0 below */}
        if(viewRoot==null)viewRoot=field(client.getClass(),"this$0").get(client);
        if(viewRoot==null)return null;
        return field(viewRoot.getClass(),"mView").get(viewRoot);
    }

    private static java.lang.reflect.Field field(Class<?> type,String name)throws NoSuchFieldException{
        for(Class<?> current=type;current!=null;current=current.getSuperclass()){
            try{
                java.lang.reflect.Field found=current.getDeclaredField(name);
                found.setAccessible(true);
                return found;
            }catch(NoSuchFieldException missing){/* keep walking up */}
        }
        throw new NoSuchFieldException(name);
    }
}
