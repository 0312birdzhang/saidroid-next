export JAVA_HOME=/tmp/jdkfull/jdk-21.0.13+9
export PATH=$JAVA_HOME/bin:$PATH
echo "=== ResProbe2 ==="
javap -p -c -cp /tmp/res2/cls ResProbe2 2>&1 | head -80
