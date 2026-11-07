package org.saildroid.setup;
/** Application-owned CLI entry. The boot bridge exposes only launcher refresh. */
public final class RefreshLaunchers {
    public static void main(String[] args) throws Exception {
        if (args.length != 1) throw new IllegalArgumentException("Selected runtime required");
        RegistryBridge.refresh(args[0]);
    }
}
