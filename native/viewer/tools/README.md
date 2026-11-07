# 输入通路验证工具

`inject_touch.c` —— 通过 `/dev/uinput` 创建虚拟触摸设备并注入一次点击（aarch64，需 root，需要 `/dev/uinput`）。

```sh
gcc -O2 -o inject_touch inject_touch.c
./inject_touch 270 540     # 屏幕坐标
```

2026-10-24 实测：注入后 Wayland 客户端收到完整事件序列
`PTR_ENTER → TOUCH_DOWN → TOUCH_MOVE(x=270 y=540) → TOUCH_UP`，
证明「合成器 → 客户端」输入通路可用。
