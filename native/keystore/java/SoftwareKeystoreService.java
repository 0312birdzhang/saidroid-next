package org.saildroid.keystore;

import android.os.Binder;
import android.os.IBinder;
import android.os.Parcel;
import android.os.RemoteException;
import android.os.ServiceSpecificException;
import android.security.keymaster.*;
import android.security.keystore.*;
import java.util.LinkedHashMap;
import java.util.ArrayList;
import java.util.Map;

/** VM-only standard AIDL prototype. No authentication, hardware or system daemon claim. */
public final class SoftwareKeystoreService extends IKeystoreService.Stub {
    private static final int OK=1, UNIMPLEMENTED=-100, INVALID_HANDLE=-28;
    private final class Client implements IBinder.DeathRecipient {
        final IBinder token; final int uid; int count;
        Client(IBinder token,int uid){this.token=token;this.uid=uid;}
        @Override public void binderDied(){synchronized(SoftwareKeystoreService.this){
            ArrayList<IBinder> dead=new ArrayList<>();
            for(Map.Entry<IBinder,Operation> e:operations.entrySet())if(e.getValue().client==this)dead.add(e.getKey());
            int failed=0;
            for(IBinder token:dead){Operation op=remove(token);int result=NativeSoftwareKeymaster.abortOwned(op.handle,op.uid);if(result!=0&&result!=INVALID_HANDLE)failed++;}
            System.err.println("SOFTWARE_KEYSTORE_LIFECYCLE=client-died|uid="+uid+"|reaped="+dead.size()+"|native_errors="+failed);
        }}
    }
    private final class Operation {
        final int uid; final long handle; final Client client;
        Operation(int uid,long handle,Client client){this.uid=uid;this.handle=handle;this.client=client;}
    }
    private final LinkedHashMap<IBinder,Operation> operations=new LinkedHashMap<>(16,0.75f,true);
    private final Map<IBinder,Client> clients=new LinkedHashMap<>();
    private Operation remove(IBinder token){
        Operation op=operations.remove(token);
        if(op!=null&&--op.client.count==0){clients.remove(op.client.token);op.client.token.unlinkToDeath(op.client,0);}
        return op;
    }
    private boolean pruneOldest(){
        if(operations.isEmpty())return false;
        IBinder token=operations.keySet().iterator().next();Operation op=operations.get(token);
        int code=NativeSoftwareKeymaster.abortOwned(op.handle,op.uid);
        remove(token);System.err.println("SOFTWARE_KEYSTORE_LIFECYCLE=pruned|uid="+op.uid+"|native_result="+code);
        return code==0||code==INVALID_HANDLE;
    }
    private static boolean empty(KeymasterBlob blob){return blob==null||blob.blob==null||blob.blob.length==0;}
    private static int status(int nativeCode){return nativeCode==0?OK:nativeCode;}
    private static KeymasterArguments outParams(NativeSoftwareKeymaster.Result r){return r.outParams==null?new KeymasterArguments():r.outParams;}
    private static OperationResult invalidOperation(){return new OperationResult(INVALID_HANDLE,null,0,0,null,new KeymasterArguments());}
    private static KeystoreResponse response(int code) {
        Parcel p=Parcel.obtain();
        try {p.writeInt(code);p.writeString(code==OK?null:"Software Keymaster result "+code);
            p.setDataPosition(0);return KeystoreResponse.CREATOR.createFromParcel(p);
        } finally {p.recycle();}
    }
    private static ExportResult exported(int code,byte[] bytes) {
        Parcel p=Parcel.obtain();
        try {p.writeInt(code);p.writeByteArray(bytes);p.setDataPosition(0);
            return ExportResult.CREATOR.createFromParcel(p);
        } finally {p.recycle();}
    }
    private static NativeSoftwareKeymaster.Result nativeCall(int op,String alias,int uid,
            KeymasterArguments arguments,byte[] input,byte[] signature,long handle,int purpose) {
        return NativeSoftwareKeymaster.call(op,alias,uid,arguments,input,signature,handle,purpose);
    }
    private static int mixEntropy(byte[] entropy){
        if(entropy==null||entropy.length==0)return OK;
        return status(nativeCall(10,null,-1,null,entropy,null,0,0).code);
    }
    @Override public int generateKey(IKeystoreKeyCharacteristicsCallback cb,String alias,
            KeymasterArguments arguments,byte[] entropy,int uid,int flags)throws RemoteException {
        if(flags!=0)return UNIMPLEMENTED;
        int mixed=mixEntropy(entropy);if(mixed!=OK)return mixed;
        NativeSoftwareKeymaster.Result r=nativeCall(1,alias,uid,arguments,null,null,0,0);
        cb.onFinished(response(status(r.code)),r.characteristics);return OK;
    }
    @Override public int getKeyCharacteristics(IKeystoreKeyCharacteristicsCallback cb,String alias,
            KeymasterBlob clientId,KeymasterBlob appData,int uid)throws RemoteException {
        if(!empty(clientId)||!empty(appData))return UNIMPLEMENTED;
        NativeSoftwareKeymaster.Result r=nativeCall(2,alias,uid,null,null,null,0,0);
        cb.onFinished(response(status(r.code)),r.characteristics);return OK;
    }
    @Override public int exportKey(IKeystoreExportKeyCallback cb,String alias,int format,
            KeymasterBlob clientId,KeymasterBlob appData,int uid)throws RemoteException {
        if(!empty(clientId)||!empty(appData))return UNIMPLEMENTED;
        NativeSoftwareKeymaster.Result r=nativeCall(3,alias,uid,null,null,null,0,format);
        cb.onFinished(exported(status(r.code),r.output));return OK;
    }
    @Override public synchronized int begin(IKeystoreOperationResultCallback cb,IBinder appToken,
            String alias,int purpose,boolean pruneable,KeymasterArguments arguments,
            byte[] entropy,int uid)throws RemoteException {
        if(appToken==null)return UNIMPLEMENTED;
        if(!Binder.isHandlingTransaction()||!pruneable)return 6;
        int owner=Binder.getCallingUid();Client client=clients.get(appToken);
        if(client!=null&&client.uid!=owner)return 6;
        int mixed=mixEntropy(entropy);if(mixed!=OK)return mixed;
        NativeSoftwareKeymaster.Result r;
        int remaining=operations.size();
        do {
            r=nativeCall(4,alias,uid,arguments,null,null,0,purpose);
        }while(r.code==-31&&remaining-->0&&pruneOldest());
        IBinder token=null;
        if(r.code==0){
            if(client==null){
                client=new Client(appToken,owner);
                try{appToken.linkToDeath(client,0);}catch(RemoteException dead){NativeSoftwareKeymaster.abortOwned(r.handle,owner);cb.onFinished(new OperationResult(4,null,0,0,null,new KeymasterArguments()));return OK;}
                clients.put(appToken,client);
            }
            token=new Binder();client.count++;operations.put(token,new Operation(owner,r.handle,client));
        }
        try{cb.onFinished(new OperationResult(status(r.code),token,r.handle,0,r.output,outParams(r)));}
        catch(RemoteException dead){if(token!=null){Operation op=remove(token);NativeSoftwareKeymaster.abortOwned(op.handle,op.uid);}throw dead;}
        return OK;
    }
    private synchronized Operation operation(IBinder token) {
        Operation op=operations.get(token);
        return Binder.isHandlingTransaction()&&op!=null&&op.uid==Binder.getCallingUid()?op:null;
    }
    @Override public synchronized int update(IKeystoreOperationResultCallback cb,IBinder token,
            KeymasterArguments arguments,byte[] input)throws RemoteException {
        Operation op=operation(token);
        if(op==null){cb.onFinished(invalidOperation());return OK;}
        NativeSoftwareKeymaster.Result r=nativeCall(5,null,-1,arguments,input,null,op.handle,0);
        if(r.code!=0)remove(token);
        cb.onFinished(new OperationResult(status(r.code),token,op.handle,r.consumed,r.output,outParams(r)));return OK;
    }
    @Override public synchronized int finish(IKeystoreOperationResultCallback cb,IBinder token,
            KeymasterArguments arguments,byte[] signature,byte[] entropy)throws RemoteException {
        int mixed=mixEntropy(entropy);if(mixed!=OK)return mixed;
        Operation op=operation(token);
        if(op==null){cb.onFinished(invalidOperation());return OK;}
        remove(token);
        NativeSoftwareKeymaster.Result r=nativeCall(6,null,-1,arguments,null,signature,op.handle,0);
        cb.onFinished(new OperationResult(status(r.code),token,op.handle,0,r.output,outParams(r)));return OK;
    }
    @Override public synchronized int abort(IKeystoreResponseCallback cb,IBinder token)throws RemoteException {
        Operation op=operation(token);
        if(op==null){cb.onFinished(response(INVALID_HANDLE));return OK;}
        remove(token);NativeSoftwareKeymaster.Result r=nativeCall(7,null,-1,null,null,null,op.handle,0);
        cb.onFinished(response(status(r.code)));return OK;
    }
    @Override public int del(String alias,int uid){return status(nativeCall(8,alias,uid,null,null,null,0,0).code);}
    @Override public int exist(String alias,int uid){return status(nativeCall(9,alias,uid,null,null,null,0,0).code);}
    @Override public int is_hardware_backed(String algorithm){return 0;}
    @Override public int getState(int a0) throws RemoteException {return UNIMPLEMENTED;}
    @Override public byte[] get(String alias,int uid){
        NativeSoftwareKeymaster.Result r=nativeCall(12,alias,uid,null,null,null,0,0);
        if(r.code==0)return r.output;if(r.code==7)return null;
        throw new ServiceSpecificException(r.code,"Private value read denied or invalid");
    }
    @Override public int insert(String alias,byte[] value,int uid,int flags){
        if(flags!=0)return UNIMPLEMENTED;if(value==null)return -38;
        return status(nativeCall(11,alias,uid,null,value,null,0,0).code);
    }
    @Override public String[] list(String prefix,int uid){
        NativeSoftwareKeymaster.Result r=nativeCall(13,prefix,uid,null,null,null,0,0);
        if(r.code==0)return r.aliases;throw new ServiceSpecificException(r.code,"Private alias enumeration denied or invalid");
    }
    @Override public int reset() throws RemoteException {return UNIMPLEMENTED;}
    @Override public int onUserPasswordChanged(int a0, java.lang.String a1) throws RemoteException {return UNIMPLEMENTED;}
    @Override public int lock(int a0) throws RemoteException {return UNIMPLEMENTED;}
    @Override public int unlock(int a0, java.lang.String a1) throws RemoteException {return UNIMPLEMENTED;}
    @Override public int isEmpty(int a0) throws RemoteException {return UNIMPLEMENTED;}
    @Override public java.lang.String grant(java.lang.String a0, int a1) throws RemoteException {throw new ServiceSpecificException(UNIMPLEMENTED,"Software prototype method not implemented");}
    @Override public int ungrant(java.lang.String a0, int a1) throws RemoteException {return UNIMPLEMENTED;}
    @Override public long getmtime(String alias,int uid){
        NativeSoftwareKeymaster.Result r=nativeCall(15,alias,uid,null,null,null,0,0);
        return r.code==0?r.modificationTime:-1L;
    }
    @Override public int clear_uid(long a0) throws RemoteException {return UNIMPLEMENTED;}
    @Override public int addRngEntropy(IKeystoreResponseCallback cb,byte[] entropy,int flags)throws RemoteException {if(flags!=0)return UNIMPLEMENTED;int code=status(nativeCall(10,null,-1,null,entropy,null,0,0).code);cb.onFinished(response(code));return OK;}
    @Override public int importKey(IKeystoreKeyCharacteristicsCallback cb,String alias,
            KeymasterArguments arguments,int format,byte[] data,int uid,int flags)throws RemoteException {
        if(flags!=0)return UNIMPLEMENTED;
        if(data==null||data.length==0)return -38;
        NativeSoftwareKeymaster.Result r=nativeCall(14,alias,uid,arguments,data,null,0,format);
        cb.onFinished(response(status(r.code)),r.characteristics);return OK;
    }
    @Override public int addAuthToken(byte[] a0) throws RemoteException {return UNIMPLEMENTED;}
    @Override public int onUserAdded(int a0, int a1) throws RemoteException {return UNIMPLEMENTED;}
    @Override public int onUserRemoved(int a0) throws RemoteException {return UNIMPLEMENTED;}
    @Override public int attestKey(IKeystoreCertificateChainCallback cb,String alias,
            KeymasterArguments arguments)throws RemoteException {
        NativeSoftwareKeymaster.Result r=nativeCall(16,alias,-1,arguments,null,null,0,0);
        KeymasterCertificateChain chain=new KeymasterCertificateChain(r.certificates==null
                ?new ArrayList<byte[]>():java.util.Arrays.asList(r.certificates));
        cb.onFinished(response(status(r.code)),chain);return OK;
    }
    @Override public int attestDeviceIds(android.security.keystore.IKeystoreCertificateChainCallback a0, android.security.keymaster.KeymasterArguments a1) throws RemoteException {return UNIMPLEMENTED;}
    @Override public int onDeviceOffBody() throws RemoteException {return UNIMPLEMENTED;}
    @Override public int importWrappedKey(android.security.keystore.IKeystoreKeyCharacteristicsCallback a0, java.lang.String a1, byte[] a2, java.lang.String a3, byte[] a4, android.security.keymaster.KeymasterArguments a5, long a6, long a7) throws RemoteException {return UNIMPLEMENTED;}
    @Override public int presentConfirmationPrompt(android.os.IBinder a0, java.lang.String a1, byte[] a2, java.lang.String a3, int a4) throws RemoteException {return UNIMPLEMENTED;}
    @Override public int cancelConfirmationPrompt(android.os.IBinder a0) throws RemoteException {return UNIMPLEMENTED;}
    @Override public boolean isConfirmationPromptSupported() throws RemoteException {return false;}
    @Override public int onKeyguardVisibilityChanged(boolean a0, int a1) throws RemoteException {return UNIMPLEMENTED;}
    @Override public int listUidsOfAuthBoundKeys(java.util.List<java.lang.String> a0) throws RemoteException {return UNIMPLEMENTED;}
}
