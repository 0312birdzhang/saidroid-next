from pathlib import Path
import subprocess,json,hashlib,re
p=Path(__file__).resolve().parent;assert str(p).startswith('/media/psf/Home/WorkSpace/saidroid-next/');out=p/'bytecode-audit-v3';out.mkdir();javap=Path('/tmp/jdkfull/jdk-21.0.13+9/bin/javap');maps={}
for v in ['baseline','candidate']:
 cmd=[str(javap),'-c','-p','-classpath',str(p/('build-v2/'+v+'-classes')),'SdAudio'];s=subprocess.check_output(cmd,text=True);(out/(v+'-javap.txt')).write_text(s)
 s=s.replace('  private static final int APPLIED_ANDROID_MODE;\n\n','')
 # Compare symbolic operands and exact control-flow instruction targets; javac can
 # renumber constant-pool entries and widen ldc when the added field shifts them.
 normalized=[];rows=s.splitlines();i=0;method_header=None;removed_getter=False
 while i<len(rows):
  line=rows[i]
  if line.strip()=='Code:':
   block=[];i+=1
   while i<len(rows) and re.match(r'\s*\d+:',rows[i]):
    m=re.match(r'\s*(\d+):\s*(\S+)(.*)',rows[i]);block.append((int(m[1]),m[2],m[3]));i+=1
   redirect={}
   if v=='candidate' and method_header.startswith('public java.lang.Object invoke('):
    at=next(n for n,row in enumerate(block)if '// String getMode' in row[2]);stop=next(n for n,row in enumerate(block)if '// String getStreamVolume' in row[2]);first,last=at-1,stop-1
    assert block[first][1]=='aload' and block[last][1]=='aload'
    redirect={offset:block[last][0]for offset,op,arg in block[first:last]};block=block[:first]+block[last:];removed_getter=True
   offsets={offset:n for n,(offset,op,arg)in enumerate(block)}
   for offset,op,arg in block:
    arg=re.sub(r'#\d+','#CP',arg)
    if op.startswith('if') or op in ('goto','goto_w','jsr','jsr_w'):
     target=int(arg.strip());target=redirect.get(target,target);arg='target-instruction='+str(offsets[target])
    normalized.append(('ldc'if op=='ldc_w'else op,' '.join(arg.split())))
   continue
  if line.strip().endswith(';') and '('in line:method_header=line.strip()
  normalized.append(' '.join(line.split()));i+=1
 assert removed_getter==(v=='candidate')
 maps[v]=normalized
assert maps['baseline']==maps['candidate'],'other existing method code changed'
b=(p/'baseline/SdAudio.java').read_text();s=(p/'source/SdAudio.java').read_text();field='    // This bridge accepts no Android mode transition; host HAL/call mode is unintegrated.\n    private static final int APPLIED_ANDROID_MODE=AudioManager.MODE_NORMAL;\n';addition='''        if(name.equals("getMode")&&method.getDeclaringClass()==IAudioService.class
                &&method.getReturnType()==Integer.TYPE&&method.getParameterTypes().length==0){
            System.err.println("SDAUDIO=mode|source=android-applied-mode|mode="+APPLIED_ANDROID_MODE+"|supported_transitions=none|host_call_mode=unintegrated");
            return APPLIED_ANDROID_MODE;
        }
''';assert s.count(field)==s.count(addition)==1;assert s.replace(field,'').replace(addition,'')==b
r=dict(passed=True,all_existing_method_symbolic_bytecode_and_controlflow_identical_after_removing_exact_new_branch=True,constant_pool_and_ldc_width_normalized=True,all_existing_invoke_branches_exact_source=True,only_change_exact_getMode_branch_and_constant=True,baseline_source_sha256=hashlib.sha256(b.encode()).hexdigest(),candidate_source_sha256=hashlib.sha256(s.encode()).hexdigest(),javap_sha256={v:hashlib.sha256((out/(v+'-javap.txt')).read_bytes()).hexdigest()for v in maps},phone_accessed=False);(out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
