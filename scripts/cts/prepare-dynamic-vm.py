"""Prepare an original dynamic-config snapshot with official merge semantics."""
from pathlib import Path
import hashlib,subprocess,sys,fcntl,json
source=Path(sys.argv[1]);module=sys.argv[2];version=sys.argv[3];target=Path(sys.argv[4]);repo=Path('/media/psf/Home/WorkSpace/saidroid-next')
toolkit=repo/'build/evidence/cts-modules-20261030/official-layout';jars=sorted(toolkit.rglob('*.jar'));assert len(jars)>150
classpath=':'.join(str(p)for p in jars);java=Path('/tmp/jdkfull/jdk-21.0.13+9/bin');classes=repo/'build/evidence/cts-round2-20261030/config-helper';classes.mkdir(exist_ok=True)
with(classes/'compile.lock').open('a+b')as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);helper=repo/'scripts/cts/PrepareDynamicConfig.java';stamp=classes/'source.sha256';sha=hashlib.sha256(helper.read_bytes()).hexdigest()
 if not stamp.exists()or stamp.read_text()!=sha:
  subprocess.run([str(java/'javac'),'-cp',classpath,'-d',str(classes),str(helper)],check=True,timeout=25);stamp.write_text(sha)
subprocess.run([str(java/'java'),'-cp',str(classes)+':'+classpath,'PrepareDynamicConfig',str(source),module,version,str(target)],check=True,timeout=20)
metadata=json.loads(Path(str(target)+'.metadata.json').read_text());metadata['prepared_sha256']=hashlib.sha256(target.read_bytes()).hexdigest();print(json.dumps(metadata))
