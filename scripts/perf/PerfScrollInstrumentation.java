package org.example.saildroid.perfscroll;

import android.app.Activity;
import android.app.Instrumentation;
import android.content.Intent;
import android.os.Bundle;
import android.os.SystemClock;

/** Ordinary self-targeted instrumentation for a bounded rendering diagnostic. */
public final class PerfScrollInstrumentation extends Instrumentation {
    private Bundle arguments;

    @Override public void onCreate(Bundle supplied) {
        super.onCreate(supplied);
        arguments = supplied == null ? new Bundle() : new Bundle(supplied);
        start();
    }

    @Override public void onStart() {
        final Bundle result = new Bundle();
        Activity launched = null;
        int code = 0;
        try {
            final String mode = arguments.getString("mode", "touch");
            final String driver = arguments.getString("driver", "choreographer");
            final int seconds = Integer.parseInt(arguments.getString("seconds", "20"));
            if (seconds < 5 || seconds > 20) throw new IllegalArgumentException("seconds outside 5..20");
            if (!(mode.equals("touch") || mode.equals("heavy") || mode.equals("light")
                    || mode.equals("blank") || mode.equals("pulse"))) {
                throw new IllegalArgumentException("Unsupported diagnostic mode");
            }
            if (!(driver.equals("choreographer") || driver.equals("handler") || driver.equals("both"))) {
                throw new IllegalArgumentException("Unsupported diagnostic driver");
            }
            final Intent intent = new Intent(getTargetContext(), PerfScrollActivity.class);
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            intent.putExtra("mode", mode);
            intent.putExtra("driver", driver);
            launched = startActivitySync(intent);
            if (!(launched instanceof PerfScrollActivity)) throw new IllegalStateException("Wrong activity");
            waitForIdleSync();
            final long started = SystemClock.elapsedRealtime();
            System.err.println("PERFINSTRUMENT=ready|mode=" + mode + "|seconds=" + seconds);
            SystemClock.sleep(seconds * 1000L);
            result.putString("diagnostic", "perfscroll");
            result.putString("mode", mode);
            result.putLong("elapsed_ms", SystemClock.elapsedRealtime() - started);
            result.putString("activity", launched.getClass().getName());
            code = -1;
        } catch (Throwable failure) {
            failure.printStackTrace();
            result.putString("error", failure.toString());
        } finally {
            final Activity activity = launched;
            if (activity != null) {
                try {
                    runOnMainSync(new Runnable() {
                        @Override public void run() { activity.finish(); }
                    });
                    waitForIdleSync();
                } catch (Throwable failure) {
                    code = 0;
                    result.putString("cleanup_error", failure.toString());
                }
            }
            System.err.println("PERFINSTRUMENT=finished|code=" + code);
            finish(code, result);
        }
    }
}
