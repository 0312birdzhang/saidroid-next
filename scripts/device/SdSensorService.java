import android.os.*;
import android.system.*;
import java.io.*;
import java.util.*;

/** API29 native sensor protocol. No host sensors are exposed by this component. */
public final class SdSensorService extends Binder {
    private static final String SERVER="android.gui.SensorServer",EVENT="android.gui.SensorEventConnection";
    private final SdBinderRegistry registry;
    private final HashSet<Connection> connections=new HashSet<Connection>();
    SdSensorService(SdBinderRegistry registry){this.registry=registry;attachInterface(null,SERVER);}
    private static void checkUid(){if(Binder.getCallingUid()!=android.os.Process.myUid())throw new SecurityException("Sensor caller UID differs");}
    private static void skipString8(Parcel data){
        int length=data.readInt();long end=(long)data.dataPosition()+(((long)length+1+3)&~3L);
        if(length<0||length>65536||end>data.dataSize())throw new IllegalArgumentException("Invalid native sensor package name");
        data.setDataPosition((int)end);
    }
    @Override protected boolean onTransact(int code,Parcel data,Parcel reply,int flags)throws RemoteException{
        if(code==INTERFACE_TRANSACTION){reply.writeString(SERVER);return true;}
        if(code<1||code>6)return super.onTransact(code,data,reply,flags);
        checkUid();data.enforceInterface(SERVER);
        // These native interfaces use raw replies, without a Java exception header.
        if(code==1||code==4){data.readString();reply.writeInt(0);return true;}
        if(code==2){
            skipString8(data);int mode=data.readInt();data.readString();
            IBinder endpoint=registry.endpointForPid(Binder.getCallingPid());
            if(mode!=0||endpoint==null){reply.writeStrongBinder(null);return true;}
            Connection connection;
            try{connection=new Connection(Binder.getCallingPid(),endpoint);}
            catch(IOException failure){throw new IllegalStateException("Sensor channel unavailable",failure);}
            reply.writeStrongBinder(connection);return true;
        }
        if(code==3){reply.writeInt(0);return true;}
        if(code==5){reply.writeStrongBinder(null);return true;}
        reply.writeInt(-38);return true; // INVALID_OPERATION: no operation parameters.
    }
    private final class Connection extends Binder implements IBinder.DeathRecipient {
        final int pid;final IBinder endpoint;
        final FileDescriptor receive=new FileDescriptor(),send=new FileDescriptor();
        boolean closed;
        Connection(int pid,IBinder endpoint)throws IOException,RemoteException{
            this.pid=pid;this.endpoint=endpoint;attachInterface(null,EVENT);
            synchronized(connections){
                int count=0;for(Connection item:connections)if(item.pid==pid)count++;
                if(count>=32)throw new IOException("Sensor connection limit reached");
                try{
                    Os.socketpair(OsConstants.AF_UNIX,OsConstants.SOCK_SEQPACKET,0,receive,send);
                    for(FileDescriptor descriptor:new FileDescriptor[]{receive,send}){
                        Os.fcntlInt(descriptor,OsConstants.F_SETFL,OsConstants.O_NONBLOCK);
                        Os.fcntlInt(descriptor,OsConstants.F_SETFD,OsConstants.FD_CLOEXEC);
                    }
                }catch(ErrnoException failure){
                    for(FileDescriptor descriptor:new FileDescriptor[]{receive,send})if(descriptor.valid())try{Os.close(descriptor);}catch(ErrnoException ignored){}
                    throw new IOException(failure);
                }
                connections.add(this);
            }
            try{endpoint.linkToDeath(this,0);}catch(RemoteException failure){close();throw failure;}
        }
        public void binderDied(){close();}
        private synchronized void close(){
            if(closed)return;closed=true;
            endpoint.unlinkToDeath(this,0);
            for(FileDescriptor descriptor:new FileDescriptor[]{receive,send})try{Os.close(descriptor);}catch(ErrnoException ignored){}
            synchronized(connections){connections.remove(this);}
        }
        @Override protected synchronized boolean onTransact(int code,Parcel data,Parcel reply,int flags)throws RemoteException{
            if(code==INTERFACE_TRANSACTION){reply.writeString(EVENT);return true;}
            if(code<1||code>6)return super.onTransact(code,data,reply,flags);
            checkUid();if(Binder.getCallingPid()!=pid)throw new SecurityException("Sensor channel owner differs");
            // AOSP's BpSensorEventConnection sends DESTROY without an interface token.
            if(code==6){close();return true;}
            data.enforceInterface(EVENT);
            if(code==1){if(closed)throw new IllegalStateException("Sensor channel closed");reply.writeFileDescriptor(receive);return true;}
            // The advertised inventory is empty, so every handle is invalid.
            reply.writeInt(-22);return true;
        }
    }
}
