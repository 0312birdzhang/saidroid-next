#!/bin/bash
set -u
J=/tmp/jdkfull/jdk-21.0.13+9/bin/javap
CP=/var/tmp/saidroid-next-api29-framework-20261025-r2/classes.jar
echo "=== WebView class decl ==="
$J -p -classpath "$CP" android.webkit.WebView 2>&1 | head -6
echo "=== WebView layout-related methods ==="
$J -p -classpath "$CP" android.webkit.WebView 2>&1 | grep -iE "LayoutParams|onMeasure|onLayout" | head -20
echo "=== AbstractLayout: AbsoluteLayout decl+params ==="
$J -p -classpath "$CP" android.widget.AbsoluteLayout 2>&1 | head -8
$J -p -classpath "$CP" android.widget.AbsoluteLayout 2>&1 | grep -i "generateDefaultLayoutParams\|generateLayoutParams" | head -8
echo "=== ViewGroup measureChildWithMargins bytecode (looking for stub) ==="
$J -c -p -classpath "$CP" android.view.ViewGroup 2>&1 | grep -A3 "protected void measureChildWithMargins" | head -12
