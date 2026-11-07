# SaiDroid 看图器（sdview）

把 Android（ART + 真实 Skia）渲染出的 ARGB 帧贴到 Wayland 窗口。

## 用法

```sh
export XDG_RUNTIME_DIR=/run/user/100000
export WAYLAND_DISPLAY=../../display/wayland-0
./sdview /home/art/frame.rgba -t 60     # 60 秒后自动退出
```

## 安全须知（2026-10-24 事故）

第一次上屏时窗口是全屏且长期驻留，结果把手机界面锁死到只能重启。

现在的约束：
- **不再请求全屏**（去掉了 `xdg_toplevel_set_max_size`）
- **默认 90 秒自动退出**，`-t` 可调；任何演示都必须在有限时间内结束
- 帧来源是 `/home/art/frame.rgba`，格式：`SDRGBA\0`(7B) + uint32 w + uint32 h + w*h 个 ARGB(uint32 LE)

## 渲染端

`RenderFrame.java`：在设备上用真实 `Bitmap`/`Canvas`/`Paint` 画图，导出上面的格式。
必须先经 `SdBridge` 引导（加载 `libandroid_runtime` 并注册框架 natives），见 `scripts/device/sdbridge.c`。
