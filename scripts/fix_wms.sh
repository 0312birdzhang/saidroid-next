#!/bin/bash
set -u
F=/tmp/ap/SdWindowManagerService.java
python3 - "$F" <<'PY'
import sys
p=sys.argv[1]
s=open(p).read()

def sub(old,new):
    global s
    assert old in s, "没找到: " + old[:70]
    s=s.replace(old,new,1)

sub('''    public void getInitialDisplaySize(int arg0, android.graphics.Point arg1) {
    }''','''    public void getInitialDisplaySize(int displayId, android.graphics.Point size) {
        if (size != null) { size.x = SdDisplayShim.WIDTH; size.y = SdDisplayShim.HEIGHT; }
    }''')
sub('''    public void getBaseDisplaySize(int arg0, android.graphics.Point arg1) {
    }''','''    public void getBaseDisplaySize(int displayId, android.graphics.Point size) {
        if (size != null) { size.x = SdDisplayShim.WIDTH; size.y = SdDisplayShim.HEIGHT; }
    }''')
sub('''    public int getInitialDisplayDensity(int arg0) {
        return 0;
    }''','''    public int getInitialDisplayDensity(int displayId) {
        return SdDisplayShim.DENSITY;
    }''')
sub('''    public int getBaseDisplayDensity(int arg0) {
        return 0;
    }''','''    public int getBaseDisplayDensity(int displayId) {
        return SdDisplayShim.DENSITY;
    }''')
sub('''    public float getCurrentAnimatorScale() {
        return 0.0f;
    }''','''    public float getCurrentAnimatorScale() {
        /* WindowManagerGlobal 拿到服务后立刻用它设 ValueAnimator 时标；
         * 返回 0 会让所有动画时长为 0，1.0f 才是正常值 */
        return 1.0f;
    }''')
open(p,'w').write(s)
print("SdWindowManagerService 关键方法已定制")
PY
