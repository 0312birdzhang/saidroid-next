JAVA=/tmp/jdkfull/jdk-21.0.13+9/bin
echo "=== StorageManager 字段/方法 ==="
$JAVA/javap -p -classpath /tmp/fw23/cls android.os.storage.StorageManager 2>/dev/null | grep -E "sStorageManager|mMountService|getVolumeList|getVolumeState|public StorageManager" | head -8
echo "=== StorageVolume 构造器 ==="
$JAVA/javap -p -classpath /tmp/fw23/cls android.os.storage.StorageVolume 2>/dev/null | grep -E "StorageVolume\(|public" | head -8
echo "=== IMountService 方法数 ==="
$JAVA/javap -p -classpath /tmp/fw23/cls android.os.storage.IMountService 2>/dev/null | grep -c abstract
echo "=== getVolumeList 签名 ==="
$JAVA/javap -p -classpath /tmp/fw23/cls android.os.storage.IMountService 2>/dev/null | grep -E "getVolumeList|getVolumeState|isExternalStorageEmulated" | head -5
