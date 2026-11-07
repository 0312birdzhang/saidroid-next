JAVA=/tmp/jdkfull/jdk-21.0.13+9/bin
echo "=== IDisplayManager\$Stub ==="
$JAVA/javap -p -classpath /tmp/fw23/cls 'android.hardware.display.IDisplayManager$Stub' 2>/dev/null | head -12
echo "=== 是否有 abstract 方法 ==="
$JAVA/javap -p -classpath /tmp/fw23/cls 'android.hardware.display.IDisplayManager$Stub' 2>/dev/null | grep -c "abstract"
echo "=== Display 里的常量 ==="
$JAVA/javap -p -classpath /tmp/fw23/cls android.view.Display 2>/dev/null | grep -E "TYPE_INTERNAL|STATE_ON|ROTATION_0|DEFAULT_DISPLAY" | head -5
