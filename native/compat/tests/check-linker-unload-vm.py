from pathlib import Path
import json,os,resource,subprocess,tempfile
repo=Path(__file__).resolve().parents[3];build=Path('/var/tmp/saidroid-linker-unload-20261031')
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
with tempfile.TemporaryDirectory(prefix='sd-linker-unload-')as directory:
 out=Path(directory);(out/'config').mkdir()
 fixture=out/'fixture.c';fixture.write_text('extern void fixture_loaded(void);extern void fixture_unloaded(void);__attribute__((constructor))static void init(void){fixture_loaded();}__attribute__((destructor))static void fini(void){fixture_unloaded();}int fixture_value(void){return 73;}\n')
 subprocess.run(['gcc','-shared','-fPIC','-nostdlib','-Wl,--hash-style=both','-o',str(out/'libunload.so'),str(fixture)],check=True)
 subprocess.run(['gcc','-O2','-Wall','-rdynamic',str(repo/'native/compat/tests/linker-unload.c'),'-o',str(out/'test'),'-ldl'],check=True)
 env=dict(os.environ,SAILDROID_STRICT_LINK='1',BIONIC_TRANSLATION_CONFIG_DIR=str(out/'config'));rows=[]
 for name,library,expected in [('control',build/'control/libdl_bio.so.0',-11),('fixed',build/'libdl_bio.so.0',0)]:
  p=subprocess.run([str(out/'test'),str(library),str(out)],env=env,capture_output=True,text=True,timeout=10)
  row=dict(case=name,expected=expected,exit=p.returncode,output=p.stdout.strip(),error=p.stderr[-2000:]);rows.append(row);assert p.returncode==expected,row
 print(json.dumps(dict(status='PASS',scope='Same-source linker A/B, actual destructor/refcount/unmap/reload behavior',cases=rows),indent=2))
