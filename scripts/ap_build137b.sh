export JAVA_HOME=/tmp/jdkfull/jdk-21.0.13+9
export PATH=$JAVA_HOME/bin:$PATH
cd /tmp/ap
rm -rf b137; mkdir -p b137
found=""
for j in /tmp/fw23/jars/framework*.jar /tmp/fw23/multi.jar; do
  if unzip -l "$j" 2>/dev/null | grep -q "android/os/Build.class"; then found=$j; break; fi
done
echo "jar=$found"
unzip -o -q "$found" 'android/os/Build*.class' -d /tmp/ap/b137
ls -R /tmp/ap/b137 | head
echo "=== 静态块行号 ==="
javap -p -c -l -cp /tmp/ap/b137 android.os.Build 2>/dev/null | grep -n "line 13[0-9]\|line 14[0-9]\|putstatic\|aaload\|arraylength" | head -30
