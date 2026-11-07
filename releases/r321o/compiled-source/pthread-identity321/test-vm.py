from pathlib import Path
import subprocess,sys,json
b=Path(sys.argv[1]);source=Path(__file__).parent/'fixture.c';exe=b/'fixture';subprocess.run(['gcc','-O2','-pthread',str(source),'-ldl','-o',str(exe)],check=True);rows=[]
for label,name,expected in [('baseline','baseline.so',7),('candidate','libpthread_bio.so.0',0)]:
 p=subprocess.run([str(exe),str(b/name),label],capture_output=True,text=True,timeout=30);rows.append(dict(label=label,code=p.returncode,stdout=p.stdout,stderr=p.stderr));(b/(label+'-fixture.log')).write_text(p.stdout+p.stderr);assert p.returncode==expected,rows[-1]
(b/'fixture-results.json').write_text(json.dumps(dict(passed=True,rows=rows),indent=2)+'\n');print(json.dumps(rows))
