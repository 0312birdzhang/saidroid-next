#!/usr/bin/env python3
from pathlib import Path
import argparse,subprocess,os,hashlib
p=argparse.ArgumentParser();p.add_argument('product',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
repo=Path(__file__).resolve().parents[2];inputs=repo/'build/codex-api29/inputs';jdk=Path(os.environ.get('JAVA_HOME','/tmp/jdkfull/jdk-21.0.13+9'))/'bin';fw=inputs/'android-all-10-robolectric-5803371.jar'
a.output.mkdir(parents=True,exist_ok=True);classes=a.output/'classes';classes.mkdir(exist_ok=True)
subprocess.run([str(jdk/'javac'),'--release','8','-nowarn','-cp',str(fw)+':'+str(a.product/'classes'),'-d',str(classes),str(repo/'native/hwui/HwuiWindowProbe.java')],check=True)
jar=a.output/'probe.jar'
subprocess.run([str(jdk/'java'),'-cp',str(inputs/'r8-8.3.37.jar'),'com.android.tools.r8.D8','--release','--min-api','29','--lib',str(fw),'--output',str(jar),*[str(f)for f in classes.rglob('*.class')]],check=True)
print('HWUI_PROBES=compiled|sha256='+hashlib.sha256(jar.read_bytes()).hexdigest())
