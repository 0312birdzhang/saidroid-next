# Native display events on API28

`native-display-events.c` routes the API28 `DisplayEventReceiver` instance ABI
through the window host. Mapped application processes receive events from
Wayland frame acknowledgements and the existing startup frame clock. Headless
service processes use an on-demand monotonic timer. Android's original
`DisplayEventDispatcher` and NDK `Choreographer` own their Looper callbacks and
delayed callback queues.

The adapter matches the shipped API28 libgui constructor, destructor, instance
methods, 16-byte receiver storage, and 24-byte event layout. Receiver state and
file descriptors are host-owned. Destruction removes the state under the same
lock used by event delivery and closes its descriptors. Repeated one-shot
requests coalesce. Rate zero disables the periodic subscription.

## Building the verified release library

The builder requires the extracted r323g payload and the retained cross-build
inputs referenced by its window build record. Use a fresh output directory.

```sh
python3 native/window/build-native-display-vm.py \
  --baseline-root /tmp/saildroid-webview-runtime-r323g-20261109/root \
  --output /tmp/saildroid-native-display-build
```

It reproduces the baseline library byte-for-byte before compiling the adapter.
The resulting `build-result.json` records compiler commands, input hashes,
dynamic dependencies, and preserved and added exports. The product builder and
native transition recipe include the adapter source and header.

## Regression checks

```sh
gcc -std=c11 -O2 -Wall -Wextra -Werror -pthread \
  native/window/tests/native-display-events.c -o /tmp/native-display-test
/tmp/native-display-test
```

`tests/NativeDisplayActivity.java` and `tests/choreographer-probe.c` form a normal
APK fixture. The fixture checks receiver initialization and disposal, then
creates two independent original NDK Choreographers. Each dispatches three
callbacks on its owning Looper, including a 40 ms delayed callback. The result
records callback counts, thread and timestamp errors, and initialization and
delay measurements.
