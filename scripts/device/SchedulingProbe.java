import android.os.Handler;
import android.os.HandlerThread;
import android.os.Process;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

/** Actual Android HandlerThread execution after inheriting background priority. */
public final class SchedulingProbe {
    public static void main(String[] args) throws Exception {
        System.load(args[1]);
        if (!SdBridge.loadBionicLibrary(args[0] + "/libandroid_runtime.so", args[0])) {
            throw new IllegalStateException("Framework natives unavailable");
        }
        SdBridge.registerFrameworkNatives();
        final int original = Process.getThreadPriority(Process.myTid());
        int[] priorities = {Process.THREAD_PRIORITY_DEFAULT, Process.THREAD_PRIORITY_URGENT_DISPLAY};
        for (int priority : priorities) {
            Process.setThreadPriority(Process.THREAD_PRIORITY_BACKGROUND);
            HandlerThread worker = new HandlerThread("SaiDroidSchedulingCheck", priority);
            final CountDownLatch done = new CountDownLatch(1);
            final int[] observed = new int[]{Integer.MAX_VALUE};
            try {
                worker.start();
                new Handler(worker.getLooper()).post(new Runnable() {
                    @Override public void run() {
                        observed[0] = Process.getThreadPriority(Process.myTid());
                        done.countDown();
                    }
                });
                if (!done.await(5, TimeUnit.SECONDS) || observed[0] != priority) {
                    throw new AssertionError("HandlerThread priority/callback failed: " + observed[0]);
                }
            } finally {
                worker.quitSafely();
                worker.join(5000);
                Process.setThreadPriority(original);
            }
            if (worker.isAlive() || Process.getThreadPriority(Process.myTid()) != original) {
                throw new AssertionError("Scheduling test did not restore its owned threads");
            }
        }
        try {
            Process.setThreadPriority(Process.THREAD_PRIORITY_URGENT_DISPLAY - 1);
            throw new AssertionError("Priority beyond the application grant was accepted");
        } catch (SecurityException expected) {
            if (Process.getThreadPriority(Process.myTid()) != original) {
                throw new AssertionError("Denied priority operation changed scheduling");
            }
        }
        System.out.println("SCHEDULING_TESTS=PASS|worker_nice=0,-8|beyond_grant_denied=true"
                + "|main_restored=" + original + "|uid=" + Process.myUid());
    }
}
