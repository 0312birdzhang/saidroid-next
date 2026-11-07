package org.saildroid.keystore;

import android.content.pm.PackageParser;
import android.content.pm.Signature;
import android.system.Os;
import android.system.OsConstants;
import android.system.StructStat;
import java.io.*;
import java.security.MessageDigest;
import java.util.*;

/** VM prototype startup adapter. The root supervisor supplies the genuinely
 * allocated UID and immutable APK path. No app Binder entry point calls this.
 * No code from the inspected APK is loaded. Shared UIDs remain unsupported. */
public final class TrustedAttestationIdentity {
    private static void check(boolean ok,String why){if(!ok)throw new SecurityException(why);}
    private static StructStat staged(File apk)throws Exception {
        check(apk.isAbsolute()&&apk.getCanonicalFile().equals(apk),"Canonical APK path required");
        StructStat file=Os.lstat(apk.getPath());
        check(OsConstants.S_ISREG(file.st_mode)&&file.st_uid==0&&(file.st_mode&0222)==0
                &&file.st_size>0&&file.st_size<=1024L*1024*1024,"Immutable root-staged APK required");
        for(File parent=apk.getParentFile();parent!=null;parent=parent.getParentFile()){
            StructStat dir=Os.lstat(parent.getPath());
            check(OsConstants.S_ISDIR(dir.st_mode)&&dir.st_uid==0&&(dir.st_mode&0022)==0,"Trusted APK ancestors required");
        }
        return file;
    }
    private static byte[] digest(File file)throws Exception {
        MessageDigest d=MessageDigest.getInstance("SHA-256");
        try(InputStream in=new FileInputStream(file)){
            byte[] buffer=new byte[65536];int n;while((n=in.read(buffer))!=-1)d.update(buffer,0,n);
        }return d.digest();
    }
    private static String hex(byte[] bytes){StringBuilder s=new StringBuilder();for(byte b:bytes)s.append(String.format(Locale.US,"%02x",b&255));return s.toString();}
    private static byte[] join(byte[]...arrays)throws IOException{
        ByteArrayOutputStream out=new ByteArrayOutputStream();for(byte[] a:arrays)out.write(a);return out.toByteArray();
    }
    private static byte[] der(int tag,byte[] value)throws IOException{
        check(value.length<=65536,"Bounded ASN.1 required");ByteArrayOutputStream out=new ByteArrayOutputStream();out.write(tag);
        if(value.length<128)out.write(value.length);
        else {int length=value.length,n=0;for(int x=length;x!=0;x>>>=8)n++;out.write(128|n);for(int i=n-1;i>=0;i--)out.write(length>>>(8*i));}
        out.write(value);return out.toByteArray();
    }
    public static void configure(int uid,String path,String expectedSha256)throws Exception{
        check(Os.getuid()==10050&&!android.os.Binder.isHandlingTransaction(),"Trusted service startup only");
        check(uid>=10000&&uid<20000&&uid!=10050,"Actual allocated client UID required");
        File apk=new File(path);StructStat before=staged(apk);byte[] hash=digest(apk);
        check(hex(hash).equals(expectedSha256),"APK differs from root supervisor verified input");
        PackageParser.Package parsed=new PackageParser().parsePackage(apk,0);PackageParser.collectCertificates(parsed,false);
        check(parsed.mSharedUserId==null&&parsed.mSigningDetails!=PackageParser.SigningDetails.UNKNOWN
                &&parsed.mSigningDetails.signatures!=null&&parsed.mSigningDetails.signatures.length>0
                &&parsed.mSigningDetails.signatures.length<=8,"Genuine nonshared APK signature required");
        ArrayList<byte[]> signers=new ArrayList<>();MessageDigest sha=MessageDigest.getInstance("SHA-256");
        for(Signature signature:parsed.mSigningDetails.signatures)signers.add(der(4,sha.digest(signature.toByteArray())));
        Collections.sort(signers,new Comparator<byte[]>(){public int compare(byte[] a,byte[] b){int n=Math.min(a.length,b.length);for(int i=0;i<n;i++){int d=(a[i]&255)-(b[i]&255);if(d!=0)return d;}return a.length-b.length;}});
        long version=parsed.getLongVersionCode();check(version>=0,"Unsigned version exceeds prototype range");
        byte[] packageInfo=der(0x30,join(der(4,parsed.packageName.getBytes("UTF-8")),der(2,java.math.BigInteger.valueOf(version).toByteArray())));
        byte[] appId=der(0x30,join(der(0x31,packageInfo),der(0x31,join(signers.toArray(new byte[signers.size()][])))));
        StructStat after=staged(apk);check(before.st_dev==after.st_dev&&before.st_ino==after.st_ino
                &&before.st_size==after.st_size&&Arrays.equals(hash,digest(apk)),"APK changed during verification");
        NativeSoftwareKeymaster.configureAttestationIdentity(uid,appId);
        System.err.println("SOFTWARE_ATTESTATION_IDENTITY=verified|uid="+uid+"|package="+parsed.packageName+"|version="+version+"|signers="+signers.size()+"|apk_sha256="+hex(hash)+"|shared_uid=false|application_id_sha256="+hex(sha.digest(appId)));
    }
}
