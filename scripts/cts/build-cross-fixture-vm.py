"""Signed two-APK contract for actual target and instrumentation contexts."""
from pathlib import Path
import subprocess,os,zipfile,hashlib,json,sys
repo=Path('/media/psf/Home/WorkSpace/saidroid-next');tag=sys.argv[1];assert tag.replace('-','').isalnum();out=Path('/var/tmp/saidroid-cross-instrumentation-'+tag);out.mkdir(exist_ok=False)
java=Path('/tmp/jdkfull/jdk-21.0.13+9/bin');inputs=repo/'build/codex-api29/inputs';fw=inputs/'android-all-10-robolectric-5803371.jar';r8=inputs/'r8-8.3.37.jar';tools=Path('/var/tmp/saidroid-next-aapt-tools-20261025-r1/root');sign=Path('/var/tmp/saidroid-next-private-signing-20261025');metadata=[]
for kind,cls in [('target','TargetState'),('runner','ContextInstrumentation')]:
 folder=out/kind;folder.mkdir();classes=folder/'classes';classes.mkdir();assets=folder/'assets';assets.mkdir();(assets/'proof.txt').write_text(kind+'-resource')
 source=repo/'scripts/cts/fixtures/cross-instrumentation'/(cls+'.java')
 sources=[str(source)]+([str(source.with_name('ModeActivity.java'))]if kind=='target'else[])
 subprocess.run([str(java/'javac'),'--release','8','-nowarn','-cp',str(fw),'-d',str(classes),*sources],check=True)
 subprocess.run([str(java/'java'),'-cp',str(r8),'com.android.tools.r8.D8','--release','--min-api','29','--lib',str(fw),'--output',str(folder/'dex.jar'),*[str(f)for f in classes.rglob('*.class')]],check=True)
 package='org.example.saildroid.instrument'+kind
 manifest='<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="'+package+'"><uses-sdk android:minSdkVersion="29" android:targetSdkVersion="29"/><application android:label="Private instrumentation contract" android:theme="@android:style/Theme.Material.Light.NoActionBar">'+('<activity android:name="org.example.saildroid.instrumenttarget.ModeActivity"/>'if kind=='target'else'')+'</application>'
 if kind=='runner':manifest+='<instrumentation android:name="'+package+'.ContextInstrumentation" android:targetPackage="org.example.saildroid.instrumenttarget"/>'
 if kind=='target':manifest=manifest.replace('</application>','<uses-library android:name="android.test.runner" android:required="true"/></application>')
 manifest=manifest.replace('<application ', '<uses-permission android:name="android.permission.'+('INTERNET'if kind=='runner'else'VIBRATE')+'"/><application ',1)
 manifest+='</manifest>';(folder/'AndroidManifest.xml').write_text(manifest);apk=out/(kind+'.apk')
 subprocess.run([str(tools/'usr/bin/aapt'),'package','-f','-M',str(folder/'AndroidManifest.xml'),'-A',str(assets),'-I','/home/art/api29-root/system/framework/framework-res.apk','-F',str(apk)],check=True,env=dict(os.environ,LD_LIBRARY_PATH=str(tools/'usr/lib/aarch64-linux-gnu/android')))
 with zipfile.ZipFile(apk,'a',zipfile.ZIP_DEFLATED)as z,zipfile.ZipFile(folder/'dex.jar')as dex:z.writestr('classes.dex',dex.read('classes.dex'))
 subprocess.run([str(java/'jarsigner'),'-keystore',str(sign/'manager.jks'),'-storepass:env','SAILDROID_BUILD_KEY_PASSWORD','-keypass:env','SAILDROID_BUILD_KEY_PASSWORD','-sigalg','SHA256withRSA','-digestalg','SHA-256',str(apk),'saildroid'],env=dict(os.environ,SAILDROID_BUILD_KEY_PASSWORD=(sign/'password').read_text().strip()),check=True,capture_output=True)
 metadata.append(dict(package=package,file=apk.name,sha256=hashlib.sha256(apk.read_bytes()).hexdigest()))
(out/'apks.json').write_text(json.dumps(metadata,indent=2)+'\n');print('CROSS_FIXTURE=BUILT|dir='+str(out))
