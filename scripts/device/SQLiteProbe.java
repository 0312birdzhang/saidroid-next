import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteStatement;
import java.io.File;

/** Persistent Android SQLite I/O, real prepared statements and transaction rollback. */
public final class SQLiteProbe {
    public static void main(String[] args) throws Exception {
        System.load(args[1]);
        if (!SdBridge.loadBionicLibrary(args[0] + "/libandroid_runtime.so", args[0])) {
            throw new IllegalStateException("Framework natives unavailable");
        }
        SdBridge.registerFrameworkNatives();
        SdServices.installAll();
        android.os.Looper.prepareMainLooper();
        android.app.ActivityThread.systemMain();
        File file = new File(args[4], "native-sqlite-check.db");
        if (file.exists()) throw new IllegalStateException("Use a fresh SQLite test path");
        SQLiteDatabase db = SQLiteDatabase.openOrCreateDatabase(file, null);
        try {
            db.execSQL("CREATE TABLE evidence (id INTEGER PRIMARY KEY, text_value TEXT, bytes_value BLOB)");
            SQLiteStatement insert = db.compileStatement("INSERT INTO evidence VALUES (?, ?, ?)");
            try {
                insert.bindLong(1, 7);
                insert.bindString(2, "SailDroid 数据库");
                insert.bindBlob(3, new byte[]{1, 0, 42});
                if (insert.executeInsert() != 7) throw new AssertionError("Native SQLite insert failed");
            } finally { insert.close(); }
            db.beginTransaction();
            try { db.execSQL("DELETE FROM evidence"); }
            finally { db.endTransaction(); } // Deliberately roll back an actual SQL transaction.
        } finally { db.close(); }
        db = SQLiteDatabase.openDatabase(file.getAbsolutePath(), null, SQLiteDatabase.OPEN_READONLY);
        try {
            Cursor rows = db.rawQuery("SELECT id, text_value, bytes_value FROM evidence", null);
            try {
                if (!rows.moveToFirst() || rows.getLong(0) != 7
                        || !"SailDroid 数据库".equals(rows.getString(1))
                        || !java.util.Arrays.equals(rows.getBlob(2), new byte[]{1, 0, 42})
                        || rows.moveToNext()) throw new AssertionError("Persistent SQLite query/rollback failed");
            } finally { rows.close(); }
        } finally { db.close(); }
        if (!file.isFile() || file.length() == 0) throw new AssertionError("SQLite file not persisted");
        System.out.println("SQLITE_TESTS=PASS|native=true|reopen=true|rollback=true|blob=true");
    }
}
