JAVA=/tmp/jdkfull/jdk-21.0.13+9/bin
W=/tmp/ap
echo "=== SdPackageManagerService 编译错误 ==="
$JAVA/javac --release 8 -nowarn -cp $W/cls:/tmp/fw23/cls -d $W/cls $W/SdDisplayShim.java $W/SdWindowManagerService.java $W/SdPackageManagerService.java 2>&1 | head -20
echo "=== QQProbe 错误 ==="
$JAVA/javac --release 8 -nowarn -cp $W/cls:/tmp/fw23/cls -d $W/cls $W/ViewProbe.java $W/TouchProbe.java $W/LiveProbe.java $W/QQProbe.java 2>&1 | head -14
