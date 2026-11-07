# 源码与构建

本仓库包含 2026-11-06 工作源码、固定上游依赖、本地补丁和 r321o 随包编译源码来源。首次公开快照尚未通过从空环境重建完整 RPM 的验收。

## 获取源码

```sh
git clone --recurse-submodules https://github.com/ZeroX-S/saidroid-next.git
cd saidroid-next
python3 tools/apply-third-party-patches.py
```

依赖 URL、精确提交和补丁 SHA256 见 `third-party-sources.json`。补丁应用工具先检查所有仓库都处于固定提交及干净状态，再应用已校验的补丁；重复运行会拒绝已改动的子模块。上游项目的许可文本位于子模块和 `LICENSES/`。ART 和 bionic 的补丁包含本地提交及工作区改动，固定基点是可从公开上游取得的提交。

## API29 构建入口

使用 aarch64 Linux 构建环境。当前开发环境为 `MeeGo Build`，共享源码路径为 `/media/psf/Home/WorkSpace/saidroid-next`。部分历史脚本将此路径、`/tmp` 工具链和 SSH 别名写在代码中，移植构建环境时需逐项调整。

主要入口：

- `scripts/api29/fetch-inputs.py INPUTS`：下载并校验固定 Android API29 / Robolectric / R8 输入。
- `scripts/api29/build-core.py`：构建兼容 Java 核心层，具体参数见脚本 CLI。
- `scripts/api29/build-product.py INPUTS OUTPUT`：构建工作源码的 Java 运行时和原生宿主。
- `scripts/packaging/README.md`：版本隔离、闭包核对、RPM 打包与显式激活流程。
- `scripts/packaging/build-runtime-rpm-vm.py --help`：从已有、哈希锁定的 runtime root 构建 RPM，并完整提取比对。

JDK、Android 构建输入、宿主开发包和目标平台支持库需要独立准备。商业 APK、设备数据、签名密钥和应用缓存不在仓库中；签名相关脚本读取调用者自行准备的私有密钥文件。

## 工作源码与已发布二进制

`native/` 和 `scripts/` 是工作区源码快照，其中包含尚未重新打包的开发修改。`releases/r321o/compiled-source/` 是原安装包内保存的已编译源码和来源记录，其中 `startup-proxy-permission321/SdConnectivity.java` 是本次实际编译的权限修复源文件。较旧的基础 `scripts/device/SdConnectivity.java` 不能替代这一最终覆盖层。公开导出还去除开发脚本认证默认值。`SOURCE-SNAPSHOT.json` 记录每份文件的来源哈希与公开哈希。

因此直接运行 `build-product.py` 不应被视作 r321o 的逐位重建。完整历史构建链的外部输入及路径尚未全部转成自包含流水线。Release 中的打包差异与校验结果只证明已提供的安装包完整性，不替代完整源码重建证明。
