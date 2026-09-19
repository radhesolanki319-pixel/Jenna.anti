package ai.jenna.app.db;

import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;
import java.util.ArrayList;
import java.util.List;

public class JennaDbHelper extends SQLiteOpenHelper {
    private static final String DATABASE_NAME = "jenna_companion_memory.db";
    private static final int DATABASE_VERSION = 1;

    public static final String TABLE_MESSAGES = "messages";
    public static final String COLUMN_ID = "_id";
    public static final String COLUMN_SENDER = "sender";
    public static final String COLUMN_TEXT = "text";
    public static final String COLUMN_PLATFORM = "platform";
    public static final String COLUMN_TIMESTAMP = "timestamp";

    private static JennaDbHelper instance;

    public static synchronized JennaDbHelper getInstance(Context context) {
        if (instance == null) {
            instance = new JennaDbHelper(context.getApplicationContext());
        }
        return instance;
    }

    public JennaDbHelper(Context context) {
        super(context, DATABASE_NAME, null, DATABASE_VERSION);
    }

    @Override
    public void onCreate(SQLiteDatabase db) {
        String createTable = "CREATE TABLE " + TABLE_MESSAGES + " ("
                + COLUMN_ID + " INTEGER PRIMARY KEY AUTOINCREMENT, "
                + COLUMN_SENDER + " TEXT NOT NULL, "
                + COLUMN_TEXT + " TEXT NOT NULL, "
                + COLUMN_PLATFORM + " TEXT DEFAULT 'app', "
                + COLUMN_TIMESTAMP + " INTEGER NOT NULL);";
        db.execSQL(createTable);
    }

    @Override
    public void onUpgrade(SQLiteDatabase db, int oldVersion, int newVersion) {
        db.execSQL("DROP TABLE IF EXISTS " + TABLE_MESSAGES);
        onCreate(db);
    }

    public synchronized void saveMessage(String sender, String text, String platform) {
        try {
            SQLiteDatabase db = getWritableDatabase();
            ContentValues values = new ContentValues();
            values.put(COLUMN_SENDER, sender);
            values.put(COLUMN_TEXT, text);
            values.put(COLUMN_PLATFORM, platform != null ? platform : "app");
            values.put(COLUMN_TIMESTAMP, System.currentTimeMillis());
            db.insert(TABLE_MESSAGES, null, values);
        } catch (Exception ignored) {}
    }

    public static class SavedMessage {
        public final long id;
        public final String sender;
        public final String text;
        public final String platform;
        public final long timestamp;

        public SavedMessage(long id, String sender, String text, String platform, long timestamp) {
            this.id = id;
            this.sender = sender;
            this.text = text;
            this.platform = platform;
            this.timestamp = timestamp;
        }
    }

    public synchronized List<SavedMessage> getRecentMessages(int limit) {
        List<SavedMessage> list = new ArrayList<>();
        try {
            SQLiteDatabase db = getReadableDatabase();
            String query = "SELECT * FROM (SELECT * FROM " + TABLE_MESSAGES
                    + " ORDER BY " + COLUMN_ID + " DESC LIMIT " + limit + ") ORDER BY " + COLUMN_ID + " ASC";
            Cursor cursor = db.rawQuery(query, null);
            if (cursor != null) {
                while (cursor.moveToNext()) {
                    long id = cursor.getLong(cursor.getColumnIndexOrThrow(COLUMN_ID));
                    String sender = cursor.getString(cursor.getColumnIndexOrThrow(COLUMN_SENDER));
                    String text = cursor.getString(cursor.getColumnIndexOrThrow(COLUMN_TEXT));
                    String platform = cursor.getString(cursor.getColumnIndexOrThrow(COLUMN_PLATFORM));
                    long timestamp = cursor.getLong(cursor.getColumnIndexOrThrow(COLUMN_TIMESTAMP));
                    list.add(new SavedMessage(id, sender, text, platform, timestamp));
                }
                cursor.close();
            }
        } catch (Exception ignored) {}
        return list;
    }
}
