JAVA=/tmp/jdkfull/jdk-21.0.13+9/bin
$JAVA/javap -p -classpath /tmp/fw23/cls android.view.DisplayInfo 2>/dev/null | head -40
