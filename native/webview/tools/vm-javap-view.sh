#!/bin/sh
JDK=/tmp/jdkfull/jdk-21.0.13+9/bin
JAR=/media/psf/Home/WorkSpace/saidroid-next/build/codex-api29/inputs/android-all-10-robolectric-5803371.jar
$JDK/javap -p -cp "$JAR" android.view.View | grep -iE 'willNotDraw|isDirty|PFLAG|setVisibility|getVisibility|isAttachedToWindow|getAlpha|getLayerType|getWindowVisibility|isHardwareAccelerated|isShown|getGlobalVisibleRect|getLocalVisibleRect|setWillNotDraw'
