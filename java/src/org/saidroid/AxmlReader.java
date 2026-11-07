package org.saidroid;

import java.io.*;
import java.nio.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

/**
 * 最小 AndroidManifest.xml（AXML）解析器。
 *
 * AXML 是二进制 XML，结构：
 *   Header (ResChunk_header: type=0x0003, headerSize, size)
 *   StringPool (字符串表)
 *   ResourceMap
 *   StartNamespace / StartElement / EndElement ...
 *
 * 本类只提取启动所需信息：
 *   - package 名
 *   - 入口 Activity（intent-filter 含 MAIN + LAUNCHER）
 */
public class AxmlReader {

    private static final int RES_XML_TYPE = 0x0003;
    private static final int RES_STRING_POOL_TYPE = 0x0001;
    private static final int RES_XML_START_ELEMENT = 0x0102;
    private static final int RES_XML_END_ELEMENT = 0x0103;
    private static final int RES_XML_RESOURCE_MAP = 0x0180;

    // 常用属性的资源 ID
    private static final int ATTR_NAME = 0x01010003;
    private static final int ATTR_EXPORTED = 0x01010010;

    private final byte[] data;
    private String[] stringPool = new String[0];
    private final int[] resIdMap = new int[256];

    public AxmlReader(byte[] data) { this.data = data; }

    /** 解析结果 */
    public static class Result {
        public String packageName;
        public String launcherActivity;
        public List<String> activities = new ArrayList<>();
        public int versionCode;
        public String versionName;
        public String label;
        public String toString() {
            return "package=" + packageName
                 + " launcher=" + launcherActivity
                 + " activities=" + activities.size()
                 + " version=" + versionName + "(" + versionCode + ")";
        }
    }

    public Result parse() throws IOException {
        Result r = new Result();
        ByteBuffer bb = ByteBuffer.wrap(data).order(ByteOrder.LITTLE_ENDIAN);

        int fileType = bb.getShort(0) & 0xFFFF;
        if (fileType != RES_XML_TYPE) {
            throw new IOException("not AXML: type=0x" + Integer.toHexString(fileType));
        }
        int fileSize = bb.getInt(4);
        int pos = bb.getShort(2) & 0xFFFF;  // headerSize

        // 遍历 chunk
        boolean inActivity = false;
        boolean hasMain = false, hasLauncher = false;
        String curActivity = null;
        Deque<String> tagStack = new ArrayDeque<>();

        while (pos + 8 <= Math.min(fileSize, data.length)) {
            int type = bb.getShort(pos) & 0xFFFF;
            int headerSize = bb.getShort(pos + 2) & 0xFFFF;
            int chunkSize = bb.getInt(pos + 4);
            if (chunkSize <= 0) break;

            switch (type) {
                case RES_STRING_POOL_TYPE:
                    parseStringPool(bb, pos, headerSize, chunkSize);
                    break;
                case RES_XML_RESOURCE_MAP:
                    parseResMap(bb, pos, headerSize, chunkSize);
                    break;
                case RES_XML_START_ELEMENT: {
                    String tag = readStartElementTag(bb, pos, headerSize);
                    tagStack.push(tag);

                    if ("manifest".equals(tag)) {
                        r.packageName = getAttrString(bb, pos, headerSize, "package");
                        r.versionCode = getAttrInt(bb, pos, headerSize, "versionCode", 0);
                        r.versionName = getAttrString(bb, pos, headerSize, "versionName");
                        r.label = getAttrString(bb, pos, headerSize, "label");
                    } else if ("activity".equals(tag) || "activity-alias".equals(tag)) {
                        curActivity = getAttrString(bb, pos, headerSize, "name");
                        inActivity = true;
                        hasMain = false; hasLauncher = false;
                        if (curActivity != null) r.activities.add(curActivity);
                    } else if ("action".equals(tag) && inActivity) {
                        String n = getAttrString(bb, pos, headerSize, "name");
                        if ("android.intent.action.MAIN".equals(n)) hasMain = true;
                    } else if ("category".equals(tag) && inActivity) {
                        String n = getAttrString(bb, pos, headerSize, "name");
                        if ("android.intent.category.LAUNCHER".equals(n)) hasLauncher = true;
                    }
                    break;
                }
                case RES_XML_END_ELEMENT: {
                    String tag = readEndElementTag(bb, pos, headerSize);
                    if (!tagStack.isEmpty() && tagStack.peek().equals(tag)) tagStack.pop();
                    if (("activity".equals(tag) || "activity-alias".equals(tag)) && inActivity) {
                        if (hasMain && hasLauncher && curActivity != null
                            && r.launcherActivity == null) {
                            r.launcherActivity = curActivity;
                        }
                        inActivity = false;
                        curActivity = null;
                    }
                    break;
                }
            }
            pos += chunkSize;
        }
        return r;
    }

    // ---------- StringPool ----------
    private void parseStringPool(ByteBuffer bb, int pos, int headerSize, int chunkSize) {
        int stringCount = bb.getInt(pos + 8);
        int styleCount = bb.getInt(pos + 12);
        int flags = bb.getInt(pos + 16);
        int stringsStart = bb.getInt(pos + 20);
        boolean utf8 = (flags & (1 << 8)) != 0;

        int offsetsBase = pos + headerSize;
        int dataBase = pos + stringsStart;
        stringPool = new String[stringCount];
        for (int i = 0; i < stringCount; i++) {
            int off = bb.getInt(offsetsBase + i * 4);
            int p = dataBase + off;
            try {
                stringPool[i] = utf8 ? readUtf8(bb, p) : readUtf16(bb, p);
            } catch (Exception e) {
                stringPool[i] = "";
            }
        }
    }

    private String readUtf8(ByteBuffer bb, int p) {
        // UTF-8 长度可能是 1 或 2 字节
        int len = bb.get(p) & 0xFF;
        if ((len & 0x80) != 0) {
            len = ((len & 0x7F) << 8) | (bb.get(p + 1) & 0xFF);
            p += 2;
        } else {
            p += 1;
        }
        int byteLen = bb.get(p) & 0xFF;
        if ((byteLen & 0x80) != 0) {
            byteLen = ((byteLen & 0x7F) << 8) | (bb.get(p + 1) & 0xFF);
            p += 2;
        } else {
            p += 1;
        }
        byte[] buf = new byte[byteLen];
        for (int i = 0; i < byteLen; i++) buf[i] = bb.get(p + i);
        return new String(buf, StandardCharsets.UTF_8);
    }

    private String readUtf16(ByteBuffer bb, int p) {
        int len = bb.getShort(p) & 0xFFFF;
        if ((len & 0x8000) != 0) {
            len = ((len & 0x7FFF) << 16) | (bb.getShort(p + 2) & 0xFFFF);
            p += 4;
        } else {
            p += 2;
        }
        char[] buf = new char[len];
        for (int i = 0; i < len; i++) buf[i] = bb.getChar(p + i * 2);
        return new String(buf);
    }

    private void parseResMap(ByteBuffer bb, int pos, int headerSize, int chunkSize) {
        int n = (chunkSize - headerSize) / 4;
        for (int i = 0; i < Math.min(n, resIdMap.length); i++) {
            resIdMap[i] = bb.getInt(pos + headerSize + i * 4);
        }
    }

    // ---------- Element ----------
    private String readStartElementTag(ByteBuffer bb, int pos, int headerSize) {
        int ext = pos + headerSize;
        int nameIdx = bb.getInt(ext + 4);
        return str(nameIdx);
    }

    private String readEndElementTag(ByteBuffer bb, int pos, int headerSize) {
        int ext = pos + headerSize;
        int nameIdx = bb.getInt(ext + 4);
        return str(nameIdx);
    }

    private String str(int idx) {
        if (idx >= 0 && idx < stringPool.length) return stringPool[idx];
        return "";
    }

    /** 从 StartElement 的 attributes 里找指定名称的属性值（字符串） */
    private String getAttrString(ByteBuffer bb, int pos, int headerSize, String attrName) {
        int ext = pos + headerSize;
        int attrStart = bb.getShort(ext + 8) & 0xFFFF;
        int attrSize = bb.getShort(ext + 10) & 0xFFFF;
        int attrCount = bb.getShort(ext + 12) & 0xFFFF;
        int base = ext + attrStart;

        for (int i = 0; i < attrCount; i++) {
            int p = base + i * attrSize;
            int nsIdx = bb.getInt(p);
            int nameIdx = bb.getInt(p + 4);
            int rawIdx = bb.getInt(p + 8);
            int dataType = bb.get(p + 15) & 0xFF;
            int data = bb.getInt(p + 16);

            String n = str(nameIdx);
            if (attrName.equals(n)) {
                if (rawIdx >= 0 && rawIdx < stringPool.length && !stringPool[rawIdx].isEmpty()) {
                    return stringPool[rawIdx];
                }
                if (dataType == 0x03) return str(data);  // TYPE_STRING
                return String.valueOf(data);
            }
        }
        return null;
    }

    private int getAttrInt(ByteBuffer bb, int pos, int headerSize, String attrName, int def) {
        String s = getAttrString(bb, pos, headerSize, attrName);
        if (s == null) return def;
        try { return Integer.parseInt(s); } catch (Exception e) { return def; }
    }
}
