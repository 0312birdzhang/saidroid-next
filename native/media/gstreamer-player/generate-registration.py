import re,json
from pathlib import Path
import argparse,hashlib
parser=argparse.ArgumentParser();parser.add_argument('aosp_native_source');args=parser.parse_args();p=Path(__file__).parent;source=Path(args.aosp_native_source);meta=json.loads((p/'sources.json').read_text());assert hashlib.sha256(source.read_bytes()).hexdigest()==meta['upstream']['android_media_MediaPlayer.cpp']['sha256'];t=source.read_text().split('static const JNINativeMethod gMethods[] = {')[1].split('\n};')[0];t=re.sub(r'//[^\n]*','',t)
rows=[]
for x in re.finditer(r'\{(.*?)\}',t,re.S):
 s=x[1];a=re.findall(r'"([^"]*)"',s);rows.append((a[0],''.join(a[1:])))
known={'nativeSetDataSource':'source_uri','_setDataSource':None,'_setVideoSurface':'set_surface','_prepare':'prepare_sync','prepareAsync':'prepare_async','_start':'start','_stop':'stop','getVideoWidth':'width','getVideoHeight':'height','_seekTo':'seek','_pause':'pause_player','isPlaying':'isplaying','getCurrentPosition':'position','getDuration':'duration','_release':'release','_reset':'reset','_setAudioStreamType':'stream','_getAudioStreamType':'getstream','setParameter':'parameter','setLooping':'looping','isLooping':'islooping','_setVolume':'volume','native_invoke':'invoke','native_setMetadataFilter':'filter','native_getMetadata':'metadata','native_init':'no_init','native_setup':'setup','native_finalize':'release','_notifyAt':'notify','setNextMediaPlayer':'next_player','attachAuxEffect':'aux','_setAuxEffectSendLevel':'aux_level','getAudioSessionId':'getsession','setAudioSessionId':'session'}
lines=[];entries=[];rt={'V':'void','I':'jint','Z':'jboolean','J':'jlong','F':'jfloat','D':'jdouble'}
for i,(n,sig)in enumerate(rows):
 fn=known.get(n)
 if n=='_setDataSource':fn='source_fd'if'FileDescriptor'in sig else'source_callback'
 if not fn:
  fn=f'unsupported_{i}';kind=sig.rsplit(')',1)[1];ret=rt.get(kind,'jobject');lines.append(f'static {ret} {fn}(JNIEnv*e,jobject,...){{unsupported(e,"{n}{sig}");'+('return nullptr;'if ret=='jobject'else'return 0;'if ret!='void'else'')+'}')
 entries.append(' {const_cast<char*>("'+n+'"),const_cast<char*>("'+sig+'"),(void*)'+fn+'},')
(p/'registration.inc').write_text('\n'.join(lines)+'\nstatic JNINativeMethod methods[]={\n'+'\n'.join(entries)+'\n};\n');assert rows==[tuple(v)for v in json.loads((p/'media-player-api29-natives.json').read_text())];print('MediaPlayer native registrations:',len(rows))
