package org.example.saildroid.compatprobe;

import android.app.Activity;
import android.content.*;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.net.Uri;
import android.os.*;
import android.util.*;
import android.webkit.CookieManager;
import android.widget.TextView;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;
import java.util.concurrent.*;
import java.util.zip.*;

/** Public API29 contract regression; deliberately not a CTS certification runner. */
public final class CompatibilityActivity extends Activity {
    int passed, failed;
    interface Check { void run() throws Exception; }
    static void require(boolean value) { if (!value) throw new AssertionError("contract mismatch"); }
    void test(String name, Check check) {
        try { check.run(); passed++; System.err.println("SDCOMPAT=pass|case="+name); }
        catch(Throwable error) { failed++; System.err.println("SDCOMPAT=fail|case="+name+"|type="+error.getClass().getName()+"|message="+error.getMessage()); error.printStackTrace(); }
    }
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        TextView content=new TextView(this);content.setText("Android API29 compatibility checks");content.setTextSize(24);content.setBackgroundColor(0xff125930);content.setTextColor(-1);setContentView(content);
        new Thread(() -> { checks(); runOnUiThread(() -> { content.setText("Compatibility: "+passed+" passed, "+failed+" failed");System.err.println("SDCOMPAT=complete|passed="+passed+"|failed="+failed+"|api="+Build.VERSION.SDK_INT); }); },"sd-compat-worker").start();
    }
    void checks() {
        test("aosp-libcore-junit",() -> {
            junit.framework.TestSuite suite=new junit.framework.TestSuite();
            suite.addTestSuite(org.apache.harmony.tests.java.util.zip.CRC32Test.class);
            suite.addTestSuite(org.apache.harmony.tests.java.util.zip.Adler32Test.class);
            suite.addTestSuite(org.apache.harmony.tests.java.lang.reflect.ArrayTest.class);
            suite.addTestSuite(org.apache.harmony.tests.java.lang.IntegerTest.class);
            junit.framework.TestResult result=new junit.framework.TestResult();suite.run(result);
            for(java.util.Enumeration<junit.framework.TestFailure> e=result.failures();e.hasMoreElements();)System.err.println("SDCOMPAT=upstream_failure|"+e.nextElement());
            for(java.util.Enumeration<junit.framework.TestFailure> e=result.errors();e.hasMoreElements();)System.err.println("SDCOMPAT=upstream_error|"+e.nextElement());
            System.err.println("SDCOMPAT=upstream_junit|tests="+result.runCount()+"|failures="+result.failureCount()+"|errors="+result.errorCount());
            require(result.runCount()>80&&result.wasSuccessful());
        });
        test("parcel-primitives",() -> { Parcel p=Parcel.obtain();try{p.writeInt(42);p.writeLong(Long.MIN_VALUE);p.writeDouble(3.25);p.writeString("你好😀");p.setDataPosition(0);require(p.readInt()==42&&p.readLong()==Long.MIN_VALUE&&p.readDouble()==3.25&&p.readString().equals("你好😀")&&p.dataAvail()==0);}finally{p.recycle();} });
        test("parcel-arrays-marshalling",() -> {Parcel p=Parcel.obtain(),q=Parcel.obtain();try{p.writeByteArray(new byte[]{0,-1,7});p.writeStringArray(new String[]{"a",null,"中"});byte[] bytes=p.marshall();q.unmarshall(bytes,0,bytes.length);q.setDataPosition(0);require(Arrays.equals(q.createByteArray(),new byte[]{0,-1,7})&&Arrays.equals(q.createStringArray(),new String[]{"a",null,"中"}));}finally{p.recycle();q.recycle();}});
        test("bundle-roundtrip",() -> {Bundle b=new Bundle();b.putInt("number",31);b.putString("text","value");b.putStringArrayList("list",new ArrayList<String>(Arrays.asList("a","b")));Bundle nested=new Bundle();nested.putBoolean("yes",true);b.putBundle("nested",nested);Parcel p=Parcel.obtain();try{p.writeBundle(b);p.setDataPosition(0);Bundle r=p.readBundle();require(r.getInt("number")==31&&r.getString("text").equals("value")&&r.getStringArrayList("list").size()==2&&r.getBundle("nested").getBoolean("yes")&&r.getInt("missing",-1)==-1);}finally{p.recycle();}});
        test("intent-parcel-extras",() -> {Intent i=new Intent("example.TEST",Uri.parse("https://example.test/a"));i.putExtra("n",9);i.addCategory("example.CATEGORY");Parcel p=Parcel.obtain();try{i.writeToParcel(p,0);p.setDataPosition(0);Intent r=Intent.CREATOR.createFromParcel(p);require(r.getAction().equals("example.TEST")&&r.getIntExtra("n",0)==9&&r.hasCategory("example.CATEGORY")&&r.getData().getHost().equals("example.test"));}finally{p.recycle();}});
        test("uri-encoding",() -> {Uri u=Uri.parse("https://example.test/base").buildUpon().appendPath("a/b").appendQueryParameter("q","你好 a+b").build();require(u.getLastPathSegment().equals("a/b")&&u.getQueryParameter("q").equals("你好 a+b"));});
        test("base64-binary",() -> {byte[] b=new byte[256];for(int i=0;i<256;i++)b[i]=(byte)i;require(Arrays.equals(b,android.util.Base64.decode(android.util.Base64.encodeToString(b,android.util.Base64.NO_WRAP),android.util.Base64.DEFAULT)));});
        test("json-unicode-null",() -> {org.json.JSONObject j=new org.json.JSONObject("{\"n\":7,\"s\":\"你好\",\"x\":null,\"a\":[true,3]}");require(j.getInt("n")==7&&j.getString("s").equals("你好")&&j.isNull("x")&&j.getJSONArray("a").getBoolean(0));});
        test("resources-density",() -> {require(getResources().getDisplayMetrics().widthPixels==1080&&getResources().getDisplayMetrics().heightPixels==2160&&getResources().getDisplayMetrics().density>1&&getString(android.R.string.ok).length()>0);});
        test("context-identity",() -> {require(getPackageName().equals("org.example.saildroid.compatprobe")&&getApplicationInfo().targetSdkVersion==29&&getClassLoader().loadClass(getClass().getName())==getClass());});
        test("private-file-roundtrip",() -> {String name="compat-private.txt";try{try(FileOutputStream f=openFileOutput(name,MODE_PRIVATE)){f.write("private-你好".getBytes(StandardCharsets.UTF_8));}byte[] b=new byte[64];int n;try(FileInputStream f=openFileInput(name)){n=f.read(b);}require(new String(b,0,n,StandardCharsets.UTF_8).equals("private-你好")&&getFileStreamPath(name).getCanonicalPath().startsWith(getApplicationInfo().dataDir+"/"));}finally{deleteFile(name);}});
        test("sharedpreferences-commit",() -> {SharedPreferences p=getSharedPreferences("compat-contract",MODE_PRIVATE);try{require(p.edit().clear().putString("s","hello").putInt("i",42).putBoolean("b",true).commit());require(p.getString("s",null).equals("hello")&&p.getInt("i",0)==42&&p.getBoolean("b",false));require(p.edit().remove("i").commit()&&!p.contains("i"));}finally{p.edit().clear().commit();}});
        test("sqlite-bind-transaction-rollback",() -> {File f=getDatabasePath("compat-contract.db");SQLiteDatabase db=openOrCreateDatabase("compat-contract.db",MODE_PRIVATE,null);try{db.execSQL("DROP TABLE IF EXISTS sample");db.execSQL("CREATE TABLE sample (id INTEGER PRIMARY KEY, value TEXT)");db.execSQL("INSERT INTO sample(value) VALUES (?)",new Object[]{"quote ' 中"});db.beginTransaction();try{db.execSQL("INSERT INTO sample(value) VALUES ('rolled back')");}finally{db.endTransaction();}try(Cursor c=db.rawQuery("SELECT value FROM sample",null)){require(c.getCount()==1&&c.moveToFirst()&&c.getString(0).equals("quote ' 中"));}}finally{db.close();deleteDatabase("compat-contract.db");}});
        test("sqlite-blob-null",() -> {SQLiteDatabase db=SQLiteDatabase.create(null);try{db.execSQL("CREATE TABLE x (b BLOB, n TEXT)");db.execSQL("INSERT INTO x VALUES (?,?)",new Object[]{new byte[]{1,0,-1},null});try(Cursor c=db.rawQuery("SELECT b,n FROM x",null)){require(c.moveToFirst()&&Arrays.equals(c.getBlob(0),new byte[]{1,0,-1})&&c.isNull(1));}}finally{db.close();}});
        test("handler-main-thread",() -> {CountDownLatch done=new CountDownLatch(1);boolean[] correct={false};new Handler(Looper.getMainLooper()).post(() -> {correct[0]=Looper.myLooper()==Looper.getMainLooper();done.countDown();});require(done.await(3,TimeUnit.SECONDS)&&correct[0]);});
        test("handlerthread-order-cancel",() -> {HandlerThread t=new HandlerThread("compat-handler");t.start();try{Handler h=new Handler(t.getLooper());List<Integer> values=Collections.synchronizedList(new ArrayList<Integer>());CountDownLatch done=new CountDownLatch(1);Runnable canceled=()->values.add(99);h.postDelayed(canceled,1000);h.removeCallbacks(canceled);h.post(()->values.add(1));h.post(()->{values.add(2);done.countDown();});require(done.await(3,TimeUnit.SECONDS)&&values.equals(Arrays.asList(1,2)));}finally{t.quitSafely();t.join(3000);require(!t.isAlive());}});
        test("monotonic-clock",() -> {long a=SystemClock.elapsedRealtimeNanos(),b=System.nanoTime();Thread.sleep(20);require(SystemClock.elapsedRealtimeNanos()>a+10000000&&System.nanoTime()>b+10000000);});
        test("executor-future-exception",() -> {ExecutorService e=Executors.newSingleThreadExecutor();try{require(e.submit(()->6*7).get(3,TimeUnit.SECONDS)==42);try{e.submit(()->{throw new IllegalStateException("expected");}).get(3,TimeUnit.SECONDS);throw new AssertionError();}catch(ExecutionException expected){require(expected.getCause() instanceof IllegalStateException);}}finally{e.shutdownNow();}});
        test("sha256-known-answer",() -> {byte[] d=MessageDigest.getInstance("SHA-256").digest("abc".getBytes("UTF-8"));StringBuilder s=new StringBuilder();for(byte b:d)s.append(String.format(Locale.ROOT,"%02x",b&255));require(s.toString().equals("ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"));});
        test("zip-deflate-roundtrip",() -> {ByteArrayOutputStream out=new ByteArrayOutputStream();try(ZipOutputStream z=new ZipOutputStream(out)){z.putNextEntry(new ZipEntry("中.txt"));z.write("payload".getBytes("UTF-8"));z.closeEntry();}try(ZipInputStream z=new ZipInputStream(new ByteArrayInputStream(out.toByteArray()))){require(z.getNextEntry().getName().equals("中.txt"));byte[] b=new byte[16];int n=z.read(b);require(new String(b,0,n,"UTF-8").equals("payload"));}});
        test("cookie-host-domain-path-secure",() -> {CookieManager c=CookieManager.getInstance();c.removeAllCookies(null);c.setAcceptCookie(true);c.setCookie("https://a.example.test/root/index","host=1");c.setCookie("https://a.example.test/","domain=2; Domain=example.test; Path=/");c.setCookie("https://a.example.test/","secure=3; Secure; Path=/");String local=c.getCookie("https://a.example.test/root/child");String other=c.getCookie("https://b.example.test/root/child");String http=c.getCookie("http://a.example.test/root/child");require(local!=null&&local.contains("host=1")&&local.contains("domain=2")&&local.contains("secure=3")&&other!=null&&!other.contains("host=1")&&other.contains("domain=2")&&http!=null&&!http.contains("secure=3"));require(!String.valueOf(c.getCookie("https://a.example.test/rooted")).contains("host=1"));});
        test("cookie-replace-delete-reject",() -> {CookieManager c=CookieManager.getInstance();c.removeAllCookies(null);c.setCookie("https://example.test/","a=one; Path=/");c.setCookie("https://example.test/","a=two; Path=/");require("a=two".equals(c.getCookie("https://example.test/")));c.setCookie("https://example.test/","evil=1; Domain=unrelated.test; Path=/");require(!String.valueOf(c.getCookie("https://example.test/")).contains("evil"));c.setCookie("https://example.test/","a=deleted; Max-Age=0; Path=/");require(c.getCookie("https://example.test/")==null);});
        test("cookie-session-clear",() -> {CookieManager c=CookieManager.getInstance();c.removeAllCookies(null);c.setCookie("https://example.test/","session=1; Path=/");c.setCookie("https://example.test/","persist=2; Max-Age=3600; Path=/");c.removeSessionCookies(null);require("persist=2".equals(c.getCookie("https://example.test/")));c.flush();c.removeAllCookies(null);require(!c.hasCookies());});
        test("cookie-accept-policy",() -> {CookieManager c=CookieManager.getInstance();c.setAcceptCookie(false);c.setCookie("https://example.test/","blocked=1; Path=/");require(!c.acceptCookie()&&c.getCookie("https://example.test/")==null);c.setAcceptCookie(true);});
    }
}
