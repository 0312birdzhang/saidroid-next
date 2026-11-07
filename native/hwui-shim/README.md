# libhwui 最小替身

`libandroid_runtime.so` 直接 NEEDED `libhwui.so`，而真 hwui 会把
`libRS` / `libbcc` / `libLLVM`（RenderScript 链）一起拉进来；实测这条链在
bionic→glibc 翻译环境下会在加载期损坏 glibc 堆（`malloc(): invalid size (unsorted)`）。

本项目当前渲染走 **Skia 软件 Canvas**（`libskia` + `GraphicsJNI`），不使用硬件渲染器，
因此这里提供只导出链接期所需 **12 个符号**的最小替身：

- `android::uirenderer::renderthread::RenderProxy::setName(char const*)`
- `android::uirenderer::Caches::sInstance`、`Singleton<ResourceCache>::sLock`、`::sInstance`
- 9 个插值器的 vtable（Cycle/Bounce/Overshoot/Accelerate/Anticipate/Decelerate/
  AnticipateOvershoot/AccelerateDecelerate/LinearInterpolator）

## 实测效果（VM）

| | 真 libhwui | 替身 |
|---|---|---|
| `libandroid_runtime` 加载 | 成功 | 成功 |
| 堆错误 | 有 | **0** |
| 加载库数 | 65 | 57（不含 LLVM/RS/bcc） |

## 注意

这是**明确的占位实现**：若将来要走硬件渲染（`ThreadedRenderer` / `RenderNode` / GPU Canvas），
必须换成从 AOSP 真实构建的 `libhwui.so`，不能沿用本替身。
