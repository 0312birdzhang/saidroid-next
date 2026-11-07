package org.saildroid.keystore;

import android.security.keymaster.KeyCharacteristics;
import android.security.keymaster.KeymasterArguments;

/** VM prototype only. No key material crosses this service-side JNI boundary. */
public final class NativeSoftwareKeymaster {
    private NativeSoftwareKeymaster() {}
    public static final class Result {
        public int code;
        public KeyCharacteristics characteristics;
        public KeymasterArguments outParams;
        public byte[] output;
        public byte[][] certificates;
        public long handle;
        public long modificationTime;
        public int consumed;
        public String[] aliases;
    }
    // The trusted VM supervisor supplies an inherited directory FD and registry.
    // Production installer/lifecycle integration is deliberately not claimed.
    public static native void initialize(int rootFd, int[] verifiedUids,
            String abiQuery, String linker, String originalLibrary);
    public static native Result call(int operation, String alias, int requestedUid,
            KeymasterArguments arguments, byte[] input, byte[] signature,
            long operationHandle, int purposeOrFormat);
    // Platform service only; never exposed as an AIDL operation.
    public static native int abortOwned(long handle,int authenticatedOwnerUid);
    // Trusted service startup only; no Binder method selects this endpoint.
    public static native void configureLockState(String trustedBusSocket);
    public static native void configureAttestationIdentity(int uid, byte[] applicationId);
    public static native void close();
}
