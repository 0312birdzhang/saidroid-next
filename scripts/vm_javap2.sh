export JAVA_HOME=/tmp/jdkfull/jdk-21.0.13+9
export PATH=$JAVA_HOME/bin:$PATH
javap -p -c -cp /tmp/res2/cls ResProbe2 2>&1 | sed -n '90,220p'
echo "=== /home/art on VM? ==="
ls -d /home/art 2>/dev/null && ls /home/art
