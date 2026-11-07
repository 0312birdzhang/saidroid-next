echo "=== 554 字节内容 ==="
head -c 400 /tmp/fw51/android-all-5.1.1_r1-robolectric-r1.jar; echo
echo "=== maven-metadata 里 5.x 版本 ==="
curl -sSL https://repo1.maven.org/maven2/org/robolectric/android-all/maven-metadata.xml | tr '>' '>\n' | grep -o "5\.[0-9.]*_r[0-9]*-robolectric-r[0-9]*" | sort -u | head -20
