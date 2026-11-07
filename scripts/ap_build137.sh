export JAVA_HOME=/tmp/jdkfull/jdk-21.0.13+9
export PATH=$JAVA_HOME/bin:$PATH
cd /tmp/ap
for j in /tmp/fw23/jars/framework*.jar; do
  n=$(unzip -l $j 2>/dev/null | grep -c "android/os/Build.class")
  [ "$n" != "0" ] && echo "在 $j" && unzip -o -q $j android/os/Build.class -d /tmp/ap/b137 && break
done
echo "=== Build.<clinit> 行号表附近 ==="
javap -p -c -l -cp /tmp/ap/b137 android.os.Build 2>/dev/null | awk '/static \{\};/{p=1} p' | head -80
